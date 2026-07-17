---
name: web-search
description: Route any general web-search or web-research request to the right existing capability. Use this first for current information, source discovery, or broad research; it makes SearXNG the default and selects fallbacks only when needed.
---

# Web Search

Each route below is a sibling skill directory. Read its `SKILL.md`; do not look
for an MCP unless that skill says it provides one.

1. General public-web discovery → `{baseDir}/../searxng/`.
2. SearXNG weak / need Google or DDG ranking, or fetch a URL as clean Markdown → `{baseDir}/../browser-web-search/`. Better at bypassing Cloudflare and getting content through than agent-browser; use this for reading pages (persistent daemon, auto-markdown).
3. JS, login, clicks, forms, screenshots, app testing → `{baseDir}/../agent-browser/`. Use for interactive browser tasks, not for simple content extraction.
4. Save a source → `{baseDir}/../web-clip/`. Summarize one → `{baseDir}/../summarize/`.
5. PDF, GitHub repo, YouTube, local video → Pi `pi-web-access` only when its extractor is enabled.
6. X → `{baseDir}/../x-research-skill/`; Reddit → `{baseDir}/../rdt-cli/`;
   cross-social recency → `{baseDir}/../last30days/`; opportunities →
   `{baseDir}/../opportunity-finder/`.

Search first; fetch or interact only after choosing a result.
