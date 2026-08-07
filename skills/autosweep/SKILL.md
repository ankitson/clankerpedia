---
name: autosweep
description: >-
  Hands-off unattended sweep of EVERY changed git repo under ~/hroot: group changes
  into conventional commits, remediate privacy leaks (tailscale
  *.ts.net hosts, raw IPs, secrets, NSFW model refs) via each repo's conventions,
  then push a dated branch and open one PR per repo. Use for "the daily sweep",
  "sweep everything and open PRs", or committing all repos at once without reviewing
  each commit. Automatic sibling of commit-sweep — pick THIS when it should run on
  its own and produce PRs to merge later, not gate commits interactively.
---

# autosweep

The unattended sibling of `commit-sweep`. One invocation sweeps **all** changed
repos under `~/hroot`, makes clean grouped commits, and leaves the user a set of
**PRs to merge** — designed to be run on a schedule (e.g. once a day).

The trade: nobody approves each commit, so **you** are the safety net. The whole
point of the privacy step is that anything which lands in a public PR has already
been cleaned. When unsure, you still lean toward shipping the PR (a human reviews
before merge) — *except* hard secrets, which are never committed under any
circumstance.

## How this differs from `commit-sweep`
- **Scope**: every changed repo under `~/hroot`, no scoping question.
- **No gating**: commits are made without per-commit approval.
- **Privacy remediation**: a mandatory scan+fix pass before any commit.
- **Output**: a dated branch + one PR per repo, not local commits.

Everything about *grouping* (feature = one intent; shared/foundational first;
docs & chore last; entangled files split with `stage-hunks.py`; date commits to
mtime with `clear-mtime.py`) is identical to `commit-sweep` — see that skill for
the grouping and hunk-splitting mechanics. Don't re-derive them here.

## Core guardrails
1. **Never publish**: a real secret, any `*.ts.net` host, an IP
   that identifies the user's network, or NSFW content. The scan + remediation
   step guarantees this.
2. **Remediate, don't skip** (the user's explicit preference). Skipping a hunk is a
   last resort; secrets that truly can't be moved are the only must-skip.
3. **No** force-push, history rewrite, or merge. Respect `.gitignore`. Only ever
   push the dated sweep branch — never the user's default branch.
4. **Only push to a remote the user owns.** A repo whose only remote is someone
   else's (a fork/upstream) gets local commits and a flag, never a cross-owner PR.
5. Skip repos mid-operation (`in_progress`: merge/rebase/cherry-pick) and report
   them — don't stack commits on an unresolved state.

## Flow

### 1. Discover
```bash
python3 scripts/find-changed-repos.py ~/hroot
```
Process every repo in the output. Note any with `in_progress` set and skip them.

### 2. Per repo — identity & remote
```bash
GH_USER=$(gh api user -q .login)
git -C <repo> remote -v          # remote name may be 'origin', 'github', etc.
```
- **Push remote** = the remote whose URL owner equals `$GH_USER`. Handle non-`origin`
  names. Base branch = that remote's HEAD (`git -C <repo> remote show <name>` →
  "HEAD branch", fallback `main`).
- No user-owned remote → **local-only mode**: still commit on the sweep branch, but
  don't push or open a PR; record it in the report for manual handling.

### 3. Privacy scan + remediate  ← the heart
```bash
python3 scripts/privacy-scan.py <repo>
```
Returns the repo's secret conventions plus redacted `findings`
(categories: `secret`, `tailnet`, `ip`, `sensitive`). For each finding, **fix it in the
working tree following that repo's convention**, then re-run the scan until
`findings` is empty (or only deliberate, justified residue remains).

The decision table, per-category remediation recipes, and worked examples live in
**`references/privacy-remediation.md`** — read it before remediating; this is where
the judgment lives and getting it wrong means a leak.

Quick orientation:
- **secret** → move the value to the repo's secret convention (an `op://` ref in a
  `*.tmpl`, or a gitignored `.env.secret`) and reference it; never commit the raw
  value. If it cannot be moved, skip that hunk — never commit it.
- **tailnet / ip** → replace with a placeholder (`<tailnet-host>`), an env var, or an
  example value; in prose/docs an example host is usually fine.
- **sensitive** (a hit against `sensitive-terms.txt`, e.g. an NSFW model name) → move
  the reference to `.env.secret`, or swap for an example name in READMEs/docs. If
  ambiguous, ship the PR.

### 4. Group + commit
Group like `commit-sweep` (feature = one intent). Stage entangled files with
`scripts/stage-hunks.py`; commit with NO pathspec so only staged hunks land. Date
commits to mtime via `scripts/clear-mtime.py`. Create/checkout the branch:
```bash
BR="sweep/$(date +%F)"
git -C <repo> rev-parse --verify "$BR" >/dev/null 2>&1 \
  && git -C <repo> checkout "$BR" \
  || git -C <repo> checkout -b "$BR" <base-branch>
```
Same-day re-run reuses the branch and appends. End commit messages with the
`Claude-Session:` trailer (see the environment's git rules).

### 5. Push + PR (skip in local-only mode)
```bash
git -C <repo> push -u <remote> "$BR"
gh -R <owner>/<repo> pr list --head "$BR" --json number -q '.[0].number'   # exists?
# none → create; exists → the push already updated it
gh -R <owner>/<repo> pr create --base <base> --head "$BR" \
   --title "chore: automated sweep $(date +%F)" --body-file <body>
```
PR body = per-repo commit subjects + a **"Privacy remediations applied"** section +
anything skipped/flagged. End PR bodies with the session URL (environment git rule).

### 6. Report
Print a summary table: `repo · #commits · PR url (or local-only / skipped) ·
remediations · flags`. Make skips and flags impossible to miss — they're the items
that need a human.

## Bundled scripts (self-contained)
- `scripts/find-changed-repos.py` — discover changed repos under a root.
- `scripts/privacy-scan.py` — pre-commit privacy detector (this skill's addition).
- `scripts/stage-hunks.py` — stage selected hunks of an entangled file.
- `scripts/clear-mtime.py` — newest mtime of staged paths, for commit dating.

Sensitive terms (e.g. NSFW model names) are read from `sensitive-terms.txt` in this
skill directory — kept self-contained, with no external dependency. That file is
gitignored (see `.gitignore`) so the denylist itself is never published; copy
`sensitive-terms.example.txt` to `sensitive-terms.txt` and populate it. With no
file present, the `sensitive` category simply finds nothing.
