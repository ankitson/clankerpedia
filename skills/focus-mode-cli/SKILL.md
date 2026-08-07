---
name: focus-mode-cli
description: Block/unblock distracting websites via the Focus Mode tool's API (which talks to AdGuard Home). Use whenever the user says &quot;focus mode&quot;, &quot;block distractions&quot;, &quot;block sites&quot;, &quot;unblock sites&quot;, &quot;list blocked sites&quot;, &quot;focus&quot;, or wants to manage DNS-level site blocking for productivity.
metadata:
  openclaw:
    emoji: "🧘"
    requires:
      bins: ["curl"]
---

# Focus Mode CLI

Block/unblock distraction sites via the Focus Mode API (`focus.home.ankitson.com`),
which toggles AdGuard Home user rules between `#FOCUS-TOGGLE-SCRIPT-START` and
`#FOCUS-TOGGLE-SCRIPT-END` markers.

## Prerequisites

- `curl` and the 1Password CLI (`op`) are available
- The Focus Mode app is running (check with `just focus-test` in `~/hroot/devserver`)
- Admin cookies are cached in `/tmp/adguard-cookies.txt`
- `ADGUARD_URL` points at the AdGuard admin endpoint. It listens on the tailnet
  address only (port 8053), so set it in your environment rather than assuming
  localhost:

  ```bash
  export ADGUARD_URL="http://<adguard-host>:8053"
  ```

## Authenticate (if needed)

Credentials come from 1Password; never inline them. Piping the body keeps the
password out of the argument list.

```bash
: "${ADGUARD_URL:?set ADGUARD_URL to the AdGuard admin endpoint}"
printf '{"name":"%s","password":"%s"}' \
  "$(op read op://clankers/local-service/username)" \
  "$(op read op://clankers/local-service/password)" \
  | curl -s -c /tmp/adguard-cookies.txt -X POST "$ADGUARD_URL/control/login" \
      -H 'Content-Type: application/json' --data-binary @- > /dev/null
```

## List blocked/allowed sites

```bash
curl -s -b /tmp/adguard-cookies.txt "$ADGUARD_URL/control/filtering/status" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
rules = data.get('user_rules', [])
in_focus = False
for r in rules:
    if '#FOCUS-TOGGLE-SCRIPT-START' in r:
        in_focus = True
        print('╭─ Focus Mode Rules ─────────────────────╮')
        continue
    if '#FOCUS-TOGGLE-SCRIPT-END' in r:
        in_focus = False
        print('╰──────────────────────────────────────────╯')
        continue
    if in_focus and r.strip():
        blocked = '🔴' if not r.startswith('#') else '🟢'
        site = r.lstrip('#').strip()
        print(f'  {blocked} {site}')
"
```

## Block one or more sites

```bash
# Block single site
curl -s -b /tmp/adguard-cookies.txt "$ADGUARD_URL/control/filtering/set_rules" \
  -H 'Content-Type: application/json' \
  -d "$(curl -s -b /tmp/adguard-cookies.txt "$ADGUARD_URL/control/filtering/status" \
    | python3 -c "
import sys, json
data = json.load(sys.stdin)
rules = data.get('user_rules', [])
for i, r in enumerate(rules):
    if '||reddit.com^' in r.lstrip('#'):
        rules[i] = r.lstrip('#')
print(json.dumps({'rules': rules}))
")"
```

## Unblock one or more sites

```bash
# Unblock single site (comment out its rule)
curl -s -b /tmp/adguard-cookies.txt "$ADGUARD_URL/control/filtering/set_rules" \
  -H 'Content-Type: application/json' \
  -d "$(curl -s -b /tmp/adguard-cookies.txt "$ADGUARD_URL/control/filtering/status" \
    | python3 -c "
import sys, json
data = json.load(sys.stdin)
rules = data.get('user_rules', [])
for i, r in enumerate(rules):
    if '||youtube.com^' in r and not r.startswith('#'):
        rules[i] = '#' + r
print(json.dumps({'rules': rules}))
")"
```

## Block all focus sites

```bash
curl -s -b /tmp/adguard-cookies.txt "$ADGUARD_URL/control/filtering/set_rules" \
  -H 'Content-Type: application/json' \
  -d "$(curl -s -b /tmp/adguard-cookies.txt "$ADGUARD_URL/control/filtering/status" \
    | python3 -c "
import sys, json
data = json.load(sys.stdin)
rules = data.get('user_rules', [])
in_focus = False
for i, r in enumerate(rules):
    if '#FOCUS-TOGGLE-SCRIPT-START' in r:
        in_focus = True
        continue
    if '#FOCUS-TOGGLE-SCRIPT-END' in r:
        break
    if in_focus and r.strip():
        rules[i] = r.lstrip('#')
print(json.dumps({'rules': rules}))
")"
```

## Unblock all focus sites

```bash
curl -s -b /tmp/adguard-cookies.txt "$ADGUARD_URL/control/filtering/set_rules" \
  -H 'Content-Type: application/json' \
  -d "$(curl -s -b /tmp/adguard-cookies.txt "$ADGUARD_URL/control/filtering/status" \
    | python3 -c "
import sys, json
data = json.load(sys.stdin)
rules = data.get('user_rules', [])
in_focus = False
for i, r in enumerate(rules):
    if '#FOCUS-TOGGLE-SCRIPT-START' in r:
        in_focus = True
        continue
    if '#FOCUS-TOGGLE-SCRIPT-END' in r:
        break
    if in_focus and r.strip() and not r.startswith('#'):
        rules[i] = '#' + r
print(json.dumps({'rules': rules}))
")"
```

## Toggle single site (block ↔ unblock)

```bash
# Replace DOMAIN with the actual domain entry, e.g. '||reddit.com^'
DOMAIN='||reddit.com^'
curl -s -b /tmp/adguard-cookies.txt "$ADGUARD_URL/control/filtering/set_rules" \
  -H 'Content-Type: application/json' \
  -d "$(curl -s -b /tmp/adguard-cookies.txt "$ADGUARD_URL/control/filtering/status" \
    | python3 -c "
import sys, json
data = json.load(sys.stdin)
rules = data.get('user_rules', [])
target = '$DOMAIN'
for i, r in enumerate(rules):
    if target in r.lstrip('#'):
        if r.startswith('#'):
            rules[i] = r.lstrip('#')     # uncomment to block
        else:
            rules[i] = '#' + r            # comment to unblock
print(json.dumps({'rules': rules}))
")"
```
