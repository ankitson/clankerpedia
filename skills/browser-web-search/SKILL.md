---
name: browser-web-search
description: Browser-driven Google or DuckDuckGo search and readable-page fetch fallback. Use only when SearXNG results are insufficient, a second search ranking is useful, or direct browser search is specifically needed; do not use for ordinary web discovery.
disable-model-invocation: true
license: MIT
compatibility: Requires Node.js 20.19+, Bun for dependency installation, network access, and a local Chromium-family browser.
---

# Browser Web Search

Fallback layer. Default broad-web discovery goes through the `web-search`
router to SearXNG. Use this skill only for a second opinion from Google/DDG or
when its browser-backed fetch path is specifically useful.

Use the bundled CLI to search through a local browser, visit results, and extract pages as clean Markdown for agent context. The persistent browser daemon reduces bot-detection failures and avoids repeated browser startup costs.

The entry point is `{baseDir}/web-search.js`, where `{baseDir}` is the absolute directory containing this `SKILL.md`. Always invoke that absolute path. Never run `./web-search.js` from the caller's project directory.

## Setup

If dependencies are missing, run `bun install` in the skill directory.

The CLI auto-detects Chromium-family browsers. Override detection with
`WEB_SEARCH_BROWSER_BIN` or `--browser-bin <path>`.

## Search and fetch

```bash
{baseDir}/web-search.js "query"
{baseDir}/web-search.js "query" -n 10
{baseDir}/web-search.js --from <result-set-id> --fetch 1,3,5
{baseDir}/web-search.js --url https://example.com
{baseDir}/web-search.js --url https://example.com --full
```

Each search prints a result-set ID. Always pass that ID with `--from` when fetching numbered results; result sets expire after ten minutes. Use `--full` only when the complete page text is needed.

## Browser daemon

Direct calls use a local daemon by default for a warm browser session.

```bash
{baseDir}/web-search.js --daemon status
{baseDir}/web-search.js --daemon start
{baseDir}/web-search.js --daemon stop
{baseDir}/web-search.js --daemon restart
{baseDir}/web-search.js --no-daemon --url https://example.com
```

## Troubleshooting

Treat one blocked page as a normal site-specific failure. Retry once, use another result, or try the direct URL before changing browser state.

For repeated timeouts, daemon errors, or blocks across multiple attempts:

1. Check `{baseDir}/web-search.js --daemon status`.
2. Run `{baseDir}/web-search.js --daemon restart` and retry.
3. If blocks persist, inspect `health.profileDir` in the status output. Stop the daemon, delete only that hidden skill profile directory, then start the daemon again. This resets stale cookies and browser storage without touching the user's normal browser profile.

Never clear the profile after a single block. Profile reset is a last resort for persistent failures.

## Reporting

Use the URLs actually searched or fetched as sources. Cite those URLs when
answering from web material.
