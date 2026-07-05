---
name: document-work
description: Maintain project docs and work logs using the repo's standard reverse-chronological format. Use after non-trivial code, tooling, skill, or documentation changes.
---

# Document Work

Follow these conventions whenever doing non-trivial work in a project.
Do not document small changes related to temporary uncommitted work.
Document work ONLY after finishing and testing a full block of work, not partway.

## Required Structure

Create if missing: `docs/NOTES.md`, `docs/CHANGELOG.md`, `logs/`, and a `Justfile` when there are repeatable commands.

## Chronology

Keep `docs/NOTES.md` and `docs/CHANGELOG.md` in reverse chronological order, with the latest date at the top.

Use exactly one `## YYYY-MM-DD` header per day. If the day already exists, add a new change group under that existing date instead of creating a second date header. If the day does not exist, insert a new date section above older dates.

Preserve the existing text of prior entries unless you are fixing chronology, heading structure, or a clear documentation error. When normalizing old docs, group duplicate same-day entries under one date header rather than leaving repeated dates.

## docs/NOTES.md

Running work log. Group by date (`## YYYY-MM-DD`), then by logical work item (`### Title`). Use lower-level subsections such as `#### Goal`, `#### Discovery`, `#### Decision`, `#### Verification`, and `#### Next steps` to record goals, key decisions, discoveries, and follow-ups.

## docs/CHANGELOG.md

Log of code changes. Group by date (`## YYYY-MM-DD`), then by logical change (`### Change Group`). Record what was added, removed, or modified and why.

## Scoped Task Documentation

For narrowly scoped tasks (migrations, investigations, one-off projects), create a dedicated `docs/YYYY-MM-DD-task-name/` folder with its own README.md, plans, and artifacts. Keep the top-level NOTES.md and CHANGELOG.md for repo-wide concerns.

## Git Commits

Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`). Commit at each logical step, not one giant commit at the end.

## logs/

Store script and service output here. Prefer JSONL structured logging. Use descriptive filenames.

## Justfile

do not bloat a justfile with too many commands. prefer to extend an existing command where possible
