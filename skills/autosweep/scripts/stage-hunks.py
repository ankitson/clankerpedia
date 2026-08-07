#!/usr/bin/env python3
"""Stage selected diff hunks of one file — non-interactive `git add -p`.

Use when your change is tangled with the user's unrelated work in the same file.
Builds a patch of the named hunks (1-based) and `git apply --cached`; rest stays
unstaged in the working tree. Only adds to index; never edits working tree.

Usage:
  stage-hunks.py R FILE --list     # numbered hunks, stage nothing
  stage-hunks.py R FILE 1 3 4      # stage those hunks

Then commit WITHOUT pathspec so only staged hunks land:
  git -C R commit -m "..."         # ensure nothing else pre-staged first
"""
from __future__ import annotations

import subprocess
import sys


def hunks_of(repo: str, path: str) -> tuple[list[str], list[list[str]]]:
    diff = subprocess.run(["git", "-C", repo, "diff", "--", path],
                          capture_output=True, text=True).stdout
    header: list[str] = []
    hunks: list[list[str]] = []
    cur: list[str] | None = None
    for ln in diff.splitlines(keepends=True):
        if ln.startswith("@@"):
            if cur is not None:
                hunks.append(cur)
            cur = [ln]
        elif cur is None:
            header.append(ln)
        else:
            cur.append(ln)
    if cur is not None:
        hunks.append(cur)
    return header, hunks


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 3:
        print(__doc__)
        return 2
    repo, path, *rest = args

    header, hunks = hunks_of(repo, path)
    if not hunks:
        print(f"stage-hunks: no unstaged hunks for {path} in {repo}", file=sys.stderr)
        return 2

    if rest == ["--list"]:
        for i, h in enumerate(hunks, 1):
            print(f"--- hunk {i} ---\n{h[0]}", end="")
            # show a couple of changed lines for orientation
            changed = [l for l in h[1:] if l[:1] in "+-"][:6]
            print("".join(changed))
        return 0

    try:
        want = sorted({int(x) for x in rest})
    except ValueError:
        print(f"stage-hunks: indices must be integers or --list, got {rest}", file=sys.stderr)
        return 2
    if want[0] < 1 or want[-1] > len(hunks):
        print(f"stage-hunks: indices out of range 1..{len(hunks)}", file=sys.stderr)
        return 2

    patch = "".join(header) + "".join("".join(hunks[i - 1]) for i in want)
    check = subprocess.run(["git", "-C", repo, "apply", "--cached", "--check"],
                           input=patch, text=True, capture_output=True)
    if check.returncode != 0:
        print("stage-hunks: patch does not apply cleanly:\n" + check.stderr, file=sys.stderr)
        return 1
    subprocess.run(["git", "-C", repo, "apply", "--cached"], input=patch, text=True, check=True)
    print(f"Staged hunk(s) {want} of {path}. Commit with NO pathspec to land only these.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
