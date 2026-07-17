---
name: searxng
description: Privacy-respecting metasearch using your local SearXNG instance. Search the web, images, news, and more without external API dependencies.
disable-model-invocation: true
author: Avinash Venkatswamy
version: 1.0.1
homepage: https://searxng.org
triggers:
  - "search for"
  - "search web"
  - "find information"
  - "look up"
metadata: {"clawdbot":{"emoji":"🔍","requires":{"bins":["python3"]},"config":{"env":{"SEARXNG_URL":{"description":"SearXNG instance URL","default":"http://localhost:8080","required":true}}}}}
---

# SearXNG Search

Search the web using your local SearXNG instance - a privacy-respecting metasearch engine.

## Commands

### Web Search
```bash
uv run {baseDir}/scripts/searxng.py search "query"              # Top 10 results
uv run {baseDir}/scripts/searxng.py search "query" -n 20        # Top 20 results
uv run {baseDir}/scripts/searxng.py search "query" --format json # JSON output
```

### Category Search
```bash
uv run {baseDir}/scripts/searxng.py search "query" --category images
uv run {baseDir}/scripts/searxng.py search "query" --category news
uv run {baseDir}/scripts/searxng.py search "query" --category videos
```

### Advanced Options
```bash
uv run {baseDir}/scripts/searxng.py search "query" --language en
uv run {baseDir}/scripts/searxng.py search "query" --time-range day
```

## Configuration

**Required:** Set the `SEARXNG_URL` environment variable to your SearXNG instance:

```bash
export SEARXNG_URL=https://search.home.ankitson.com
```

Default (if not set): `https://search.home.ankitson.com`

## Features

- 🔒 Privacy-focused (uses your local instance)
- 🌐 Multi-engine aggregation
- 📰 Multiple search categories
- 🎨 Rich formatted output
- 🚀 Fast JSON mode for programmatic use

## Post-Search: Fetching Page Contents

SearXNG returns titles, URLs, and snippets only. To fetch the full content of a
result page as clean Markdown, do **not** use curl + regex scraping.
Instead, use the **browser-web-search** skill (sibling of searxng under
web-search):

```bash
# Fetch a specific URL as clean Markdown
{baseDir}/../browser-web-search/web-search.js --url https://example.com

# Or fetch results by index from a previous search (pass the result-set ID)
{baseDir}/../browser-web-search/web-search.js --from <result-set-id> --fetch 1,3
```

This uses a persistent browser daemon that bypasses Cloudflare and other
anti-scraping measures, producing clean readable Markdown — far more reliable
than raw HTTP fetching or manual regex extraction.

**Note:** `searxng.py` has no built-in fetch command. Always route content
retrieval through `browser-web-search`.

## API

Uses your local SearXNG JSON API endpoint (no authentication required by default).
