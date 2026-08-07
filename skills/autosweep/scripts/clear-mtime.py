#!/usr/bin/env python3
"""Latest mtime of paths IF they cluster (one work session), else nothing.

Prints epoch seconds of the newest path when all paths' mtimes span <= window
(default 6h) — a "clear" change time to date the commit with. Span too wide,
or no existing paths -> exit 1, print nothing (caller dates the commit as now).

Usage: clear-mtime.py [--window-hours H] R PATH [PATH ...]
Use:   D=$(clear-mtime.py R p1 p2) && \\
       GIT_AUTHOR_DATE=@$D GIT_COMMITTER_DATE=@$D git -C R commit -m "..."
"""
import argparse
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--window-hours", type=float, default=6.0)
ap.add_argument("repo")
ap.add_argument("paths", nargs="+")
a = ap.parse_args()

mts = []
for p in a.paths:
    fp = Path(a.repo) / p
    if fp.is_file():
        mts.append(fp.stat().st_mtime)
if not mts:                                   # all deletions / nothing on disk
    sys.exit(1)
if max(mts) - min(mts) > a.window_hours * 3600:   # scattered -> not clear
    sys.exit(1)
print(int(max(mts)))
