#!/usr/bin/env python3
"""Scan a repo's *pending* changes for things that must never be published.

Looks only at what a sweep would commit: added lines in tracked diffs (staged +
unstaged) and the contents of untracked, non-ignored files. Emits JSON findings
so the caller can remediate (move to a secret/op ref, swap a placeholder, etc.)
BEFORE committing. Secret *values* are redacted in output — never printed raw.

Categories: secret, tailnet (*.ts.net), ip, sensitive.
Also reports detected repo secret-conventions to guide remediation.

Usage: privacy-scan.py REPO [--sensitive-file PATH]
  --sensitive-file  newline-separated terms to flag (default: <skill>/sensitive-terms.txt,
                    gitignored so the denylist itself is never published)
Exit: 0 always (findings are data, not failure). JSON on stdout.
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys
from pathlib import Path

# Placeholders / references that are SAFE — a match here is never a leak.
SAFE = re.compile(
    r"op://|env\.[A-Z0-9_]+|\$\{[A-Z0-9_]+\}|\{\{\s*op://|"
    r"=\s*(none|changeme|example|placeholder|xxx+|redacted|\*+|<[^>]+>)\b|"
    r"REDACTED|EXAMPLE|YOUR_|<[a-z0-9_-]+>",
    re.I,
)

SECRET_PATTERNS = [
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("openai_key",  re.compile(r"\bsk-(ant-|or-|proj-)?[A-Za-z0-9_-]{16,}")),
    ("github_token",re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")),
    ("aws_key",     re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}")),
    ("google_key",  re.compile(r"\bAIza[0-9A-Za-z_-]{30,}")),
    ("bearer",      re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{20,}")),
    # generic key/secret/token/password assignment with a non-placeholder value
    ("assigned_secret", re.compile(
        r"(?i)(api[_-]?key|secret|token|password|passwd|client[_-]?secret|access[_-]?key)"
        r"\s*[:=]\s*['\"]?([^\s'\"#]{12,})")),
]
TAILNET = re.compile(r"\b[a-z0-9-]+\.ts\.net\b", re.I)
# IPv4 that is NOT a harmless sentinel; private+public both identify a network.
IPV4 = re.compile(r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b")
IP_OK = {"0.0.0.0", "127.0.0.1", "255.255.255.255", "1.1.1.1", "8.8.8.8", "8.8.4.4"}

DEFAULT_SENSITIVE = []  # the real list lives in the gitignored sensitive-terms.txt beside the skill


def sh(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True).stdout


def added_lines(repo):
    """Yield (file, lineno, text) for added lines in staged+unstaged diffs."""
    for extra in ([], ["--staged"]):
        diff = sh(repo, "diff", "--unified=0", "--no-color", *extra)
        f, ln = None, 0
        for line in diff.splitlines():
            if line.startswith("+++ b/"):
                f = line[6:]
            elif line.startswith("@@"):
                m = re.search(r"\+(\d+)", line)
                ln = int(m.group(1)) if m else 0
            elif line.startswith("+") and not line.startswith("+++"):
                yield f, ln, line[1:]
                ln += 1


def untracked_lines(repo):
    out = sh(repo, "ls-files", "--others", "--exclude-standard")
    for rel in out.splitlines():
        p = Path(repo) / rel
        try:
            if p.stat().st_size > 2_000_000:  # skip big blobs
                continue
            for i, text in enumerate(p.read_text(errors="replace").splitlines(), 1):
                yield rel, i, text
        except (OSError, UnicodeError):
            continue


def ipv4_bad(text):
    out = []
    for m in IPV4.finditer(text):
        ip = m.group(0)
        if ip in IP_OK:
            continue
        if any(int(o) > 255 for o in m.groups()):
            continue  # version string like 4.10.512.0, not an IP
        out.append(ip)
    return out


def conventions(repo):
    g = sh(repo, "ls-files").splitlines()
    ign = (Path(repo) / ".gitignore")
    igntext = ign.read_text() if ign.exists() else ""
    return {
        "has_secrets_dir": (Path(repo) / "secrets").is_dir()
                           or any(x.startswith("secrets/") for x in g)
                           or "secrets/" in igntext,
        "has_tmpl": any(x.endswith(".tmpl") for x in g),
        "uses_op_refs": bool(sh(repo, "grep", "-rIl", "op://", "--", ".").strip()),
        "gitignores_env": ".env" in igntext or "secrets/" in igntext,
    }


def scan(repo, sensitive_terms):
    sensitive_re = re.compile("|".join(re.escape(t) for t in sensitive_terms), re.I) if sensitive_terms else None
    findings = []

    def emit(cat, sev, f, ln, text, hint):
        snippet = text.strip()[:80]
        if cat == "secret":  # never echo a secret value
            snippet = re.sub(r"[A-Za-z0-9_\-]{12,}", "****", snippet)
        findings.append({"category": cat, "severity": sev, "file": f, "line": ln,
                         "snippet": snippet, "hint": hint})

    for f, ln, text in list(added_lines(repo)) + list(untracked_lines(repo)):
        if f is None:
            continue
        safe = SAFE.search(text)
        for name, pat in SECRET_PATTERNS:
            m = pat.search(text)
            if not m:
                continue
            if safe:  # value is an op:// ref / env placeholder → fine
                continue
            emit("secret", "block", f, ln, text, f"{name}: move to repo secret convention (op:// ref or .env.secret); NEVER commit raw")
        for host in TAILNET.findall(text):
            emit("tailnet", "high", f, ln, text, f"replace {host} with a placeholder/env var or example host")
        for ip in ipv4_bad(text):
            emit("ip", "med", f, ln, text, f"replace {ip} with a placeholder/env var unless clearly non-identifying")
        if sensitive_re and sensitive_re.search(text):
            emit("sensitive", "high", f, ln, text, "move to .env.secret or swap for an example in docs")

    return {"repo": repo, "conventions": conventions(repo), "findings": findings,
            "counts": {c: sum(1 for x in findings if x["category"] == c)
                       for c in ("secret", "tailnet", "ip", "sensitive")}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    default_terms = str(Path(__file__).resolve().parent.parent / "sensitive-terms.txt")
    ap.add_argument("--sensitive-file", default=default_terms)
    a = ap.parse_args()
    terms = list(DEFAULT_SENSITIVE)
    if os.path.exists(a.sensitive_file):
        terms += [t.strip() for t in open(a.sensitive_file) if t.strip() and not t.startswith("#")]
    print(json.dumps(scan(a.repo, terms), indent=2))


if __name__ == "__main__":
    sys.exit(main())
