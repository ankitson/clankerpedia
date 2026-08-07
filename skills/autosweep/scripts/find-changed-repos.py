#!/usr/bin/env python3
"""Discover changed git repos under ROOT (default ~/hroot).

Walks ROOT; finds every working tree (incl. linked worktrees: `.git` file).
JSON on stdout for repos with staged/unstaged/untracked changes; clean omitted.
Fields: path, branch, detached, staged, unstaged, untracked, in_progress, porcelain.

Usage: find-changed-repos.py [ROOT] [--all] [--exclude SUBSTR ...]
  --all      include clean repos too
  --exclude  skip repos whose path contains SUBSTR (repeatable)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Directories that never contain repos we care about and are expensive to walk.
PRUNE = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "target", "dist", "build", ".next",
    ".cache", ".terraform", "vendor",
}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True,
    ).stdout.strip()


def in_progress(repo: Path) -> str | None:
    gitdir = Path(git(repo, "rev-parse", "--git-dir") or repo / ".git")
    if not gitdir.is_absolute():
        gitdir = repo / gitdir
    if (gitdir / "MERGE_HEAD").exists():
        return "merge"
    if (gitdir / "rebase-merge").exists() or (gitdir / "rebase-apply").exists():
        return "rebase"
    if (gitdir / "CHERRY_PICK_HEAD").exists():
        return "cherry-pick"
    return None


def inspect(repo: Path) -> dict | None:
    porcelain = git(repo, "status", "--porcelain")
    lines = [ln for ln in porcelain.splitlines() if ln]
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    detached = branch == "HEAD"
    staged = unstaged = untracked = 0
    for ln in lines:
        x, y = ln[0], ln[1]
        if ln.startswith("??"):
            untracked += 1
            continue
        if x != " ":
            staged += 1
        if y != " ":
            unstaged += 1
    return {
        "path": str(repo),
        "branch": branch,
        "detached": detached,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "in_progress": in_progress(repo),
        "porcelain": lines,
    }


def find_repos(root: Path) -> list[Path]:
    repos: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        # A git working tree has a `.git` dir (normal) or `.git` file (worktree).
        if ".git" in dirnames or ".git" in filenames:
            repos.append(here)
            # Don't descend further: nested submodules/worktrees inside a tree
            # are rare here and keep the scan fast and predictable.
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in PRUNE and not d.startswith(".")]
    return repos


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=str(Path.home() / "hroot"))
    ap.add_argument("--all", action="store_true",
                    help="include clean repos (default: only changed)")
    ap.add_argument("--exclude", action="append", default=[], metavar="SUBSTR",
                    help="skip repos whose path contains SUBSTR (repeatable), "
                         "e.g. --exclude external-repo --exclude /archive/")
    args = ap.parse_args()

    root = Path(args.root).expanduser()
    if not root.is_dir():
        print(f"find-changed-repos: not a directory: {root}", file=sys.stderr)
        return 1

    out = []
    for repo in sorted(find_repos(root)):
        if any(sub in str(repo) for sub in args.exclude):
            continue
        info = inspect(repo)
        if info is None:
            continue
        has_changes = info["staged"] or info["unstaged"] or info["untracked"]
        if args.all or has_changes:
            out.append(info)

    print(json.dumps(out, indent=2))
    changed = sum(1 for r in out if r["staged"] or r["unstaged"] or r["untracked"])
    print(f"# {changed} repo(s) with changes under {root}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
