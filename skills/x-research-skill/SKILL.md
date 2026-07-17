---
name: x-research
description: General-purpose X/Twitter research using the local Bird CLI. Use for real-time perspectives, developer discussion, product feedback, cultural takes, breaking news, expert voices, tweet/thread reading, profile research, and sourced X briefings. Trigger on “x research”, “search X/Twitter”, “what are people saying on X”, “check Twitter”, or “X search”. Use Bird for X access; keep research read-only unless the user explicitly asks for an account-changing action.
---

# X Research

Use the sibling Bird skill as the X transport: `{baseDir}/../bird/SKILL.md`.

Research, not just search: decompose the question, follow relevant threads and
linked primary sources, then synthesize findings by theme with tweet links.

## Read-only command map

Use `--json` when results need filtering, comparison, or citation extraction.

```bash
bird search "<query>" -n 20 --json
bird search "<query>" --all --max-pages 3 --json
bird user-tweets @handle -n 30 --json
bird read <tweet-url-or-id> --json
bird thread <tweet-url-or-id> --all --max-pages 3 --json
bird replies <tweet-url-or-id> --all --max-pages 3 --json
bird news -n 20 --json
bird lists
bird list-timeline <list-id> -n 30 --json
bird bookmarks -n 30 --json
```

Run `bird check` when authentication is unclear. Never print cookies or pass
cookie values on the command line. Do not use the legacy `x-search.ts` wrapper.

## Research loop

1. Make 3–5 focused queries: core topic, known voices (`from:handle`), pain
   points, positive evidence, and primary-source links. Pass X operators
   through to `bird search`.
2. Start with 10–20 results per query. Page only when the first pass has real
   signal; narrow noisy results with more specific terms, `from:`, or
   `-is:reply` / `-is:retweet` where X supports them.
3. Read high-signal tweets in full. Follow threads, then inspect linked docs,
   repositories, or articles using the appropriate web-reading skill.
4. Cross-check consequential claims with primary sources. Distinguish a claim,
   an anecdote, and broad sentiment.
5. Synthesize by theme, not query. Include author, concise paraphrase or short
   quote, engagement context when relevant, and a direct tweet link. State the
   search window and meaningful gaps. Save only when the user asks and to their
   requested destination.

## Common routes

- **What are people saying?** Search the topic plus 2–3 sentiment/experience
  angles; report the range of views rather than a popularity contest.
- **Developer or product research:** Search exact names, release terms,
  `from:` maintainers, issues/bugs, and linked GitHub/docs URLs.
- **Person/account research:** Use `bird user-tweets @handle`; then search
  `from:handle <topic>` and follow relevant threads.
- **One tweet or thread:** `bird read` first; use `bird thread` / `bird replies`
  only when context changes the answer.
- **News pulse:** `bird news` or targeted search; confirm important claims
  outside X before treating them as fact.

Posting, replying, following, unfollowing, unbookmarking, and any other
account-changing Bird command require an explicit user request in the current
turn.
