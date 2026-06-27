---
name: agentsview-api
description: Query, search, and export coding-agent session transcripts from a local AgentsView instance over HTTP. Use when you need to find sessions by text content, download a full session transcript, or programmatically access session metadata and messages.
---

# AgentsView HTTP API Reference

AgentsView stores all coding-agent session data in a local SQLite DB and exposes REST API endpoints. Default URL is the Tailscale-reachable public endpoint, which works from any machine on the network; override with `AGENTSVIEW_URL` (e.g. `http://agentsview:8080` inside the devbox docker network, `http://localhost:8080` when running on the host of the agentsview container).

## Variables

```bash
AGENTSVIEW_URL="${AGENTSVIEW_URL:-https://agentsview.dev.ankitson.com}"
AGENTSVIEW_DB="${AGENTSVIEW_DB:-}"  # set to SQLite path for local queries
```

## Search Transcripts

### `GET /api/v1/search`

Use this endpoint first when looking for a session by message content. It
searches transcript text and returns matching snippets with highlighted terms.

Query parameters:
- `q` — search query
- `limit` — page size, for example `30`
- `sort` — sort order, usually `relevance`

Examples:

```bash
# Search all transcripts for a term
curl -s "$AGENTSVIEW_URL/api/v1/search?q=birdclaw&limit=30&sort=relevance"

# URL-encode multi-word queries
python3 - <<'PY'
import json, urllib.parse, urllib.request

base = "https://agentsview.dev.ankitson.com"
query = urllib.parse.urlencode({"q": "24.04 upgrade", "limit": 30, "sort": "relevance"})
with urllib.request.urlopen(f"{base}/api/v1/search?{query}") as response:
    print(json.dumps(json.load(response), indent=2))
PY
```

Response includes:
- `query` — the query string
- `results[]` — matching transcript snippets
- `results[].session_id` — pass this to `/api/v1/sessions/{id}` or
  `/api/v1/sessions/{id}/messages`
- `results[].project`, `results[].agent`, `results[].snippet`, and
  `results[].rank`
- `count` — number of returned results
- `next` — pagination cursor or URL when more results are available

## List Sessions

### `GET /api/v1/sessions`

Query parameters:
- `agent` — filter by agent (claude, opencode, codex, gemini, etc.)
- `project` — filter by project name
- `limit` — page size (default ~50)
- `cursor` — pagination cursor from previous response

Examples:

```bash
# Get latest Claude Code sessions
curl -s "$AGENTSVIEW_URL/api/v1/sessions?agent=claude&limit=5"

# Filter by project
curl -s "$AGENTSVIEW_URL/api/v1/sessions?project=homeserver"
```

Response includes `sessions[]` with metadata (message_count, token usage, outcome, health_score, timestamps) and a `next_cursor` for pagination.

## Get Session Details

### `GET /api/v1/sessions/{id}`

```bash
curl -s "$AGENTSVIEW_URL/api/v1/sessions/$SESSION_ID"
```

Returns the session metadata object (same shape as items in the list endpoint).

## Download Full Transcript

### `GET /api/v1/sessions/{id}/messages`

Returns all messages in JSON array form, ordered by `ordinal`.

```bash
# Full transcript as JSON
curl -s "$AGENTSVIEW_URL/api/v1/sessions/$SESSION_ID/messages?limit=200"
```

Each message has:
- `role` — "user" | "assistant" | "system"
- `content` — the message text (includes tool calls, bash commands, etc.)
- `timestamp` — ISO 8601
- `ordinal` — sequence number
- `has_thinking`, `has_tool_use` — boolean flags
- `model`, `token_usage`, etc.

### Format as plain-text transcript

```bash
curl -s "$AGENTSVIEW_URL/api/v1/sessions/$SESSION_ID/messages?limit=200" \
  | jq -r '.messages[] | "## \(.role) (\(.timestamp))\n\n\(.content)\n"' \
  > transcript.md
```

The endpoint defaults to about 100 messages, so pass a larger `limit` for long
sessions.

## Local SQLite (faster for large exports)

If `AGENTSVIEW_DB` is set to the SQLite DB path, query directly:

```bash
sqlite3 "$AGENTSVIEW_DB" \
  "SELECT '## ' || role || x'0a' || x'0a' || content \
   FROM messages \
   WHERE session_id = '$SESSION_ID' \
   ORDER BY ordinal" \
  > transcript.md
```

If the DB path is unknown, common locations include:
- Docker named volume: inspect `docker volume inspect <name>` to find the mount point
- Default local install: check `agentsview server --help` or look for `sessions.db` under the data directory passed at startup
