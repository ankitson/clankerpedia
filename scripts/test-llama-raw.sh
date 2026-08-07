#!/usr/bin/env bash
# Test llama-server directly on Windows (bypasses Studio, Bifrost, Caddy).
# Shows exactly what goes in and what comes out.
set -euo pipefail

WIN_HOST="${WIN_HOST:-desktop-win}"
KEY=$(ssh "$WIN_HOST" "cmd /c \"type E:\root\projects\unsloth\auth\cli-api-key.txt\"" 2>/dev/null | tr -d '\r\n')

echo "=== RAW LLAMA-SERVER TEST (direct to llama.cpp port 8080) ==="
echo ""

QUESTION="${1:-Think step by step: what is 15 * 7?}"

# Test 1: thinking OFF
echo "--- Test 1: enable_thinking=false ---"
echo "REQUEST:"
jq -n --arg q "$QUESTION" '{
  model: "any",
  messages: [{role: "user", content: $q}],
  stream: false,
  max_tokens: 256,
  chat_template_kwargs: {enable_thinking: false}
}' | tee /tmp/llama-req-off.json

echo ""
echo "RESPONSE:"
ssh "$WIN_HOST" "curl -s http://127.0.0.1:8080/v1/chat/completions -H 'Content-Type: application/json' -d @-" < /tmp/llama-req-off.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
m = d.get('choices',[{}])[0].get('message',{})
c = m.get('content','')
print(f'  completion_tokens: {d.get(\"usage\",{}).get(\"completion_tokens\")}')
print(f'  content length:    {len(c)}')
print(f'  has <think>:       {\"<think>\" in c}')
think_match = __import__('re').search(r'<think>(.*?)</think>', c, __import__('re').DOTALL)
if think_match:
    print(f'  THINK section:     {len(think_match.group(1))} chars')
    print(f'  THINK preview:     {think_match.group(1)[:200]}')
    final = c[think_match.end():]
    if final.strip():
        print(f'  FINAL content:     {final.strip()[:200]}')
    else:
        print(f'  FINAL content:     (none - all thinking)')
else:
    print(f'  CONTENT preview:   {c[:300]}')
print(f'  All message keys:  {list(m.keys())}')
"

echo ""
echo "--- Test 2: enable_thinking=true ---"
echo "REQUEST:"
jq -n --arg q "$QUESTION" '{
  model: "any",
  messages: [{role: "user", content: $q}],
  stream: false,
  max_tokens: 256,
  chat_template_kwargs: {enable_thinking: true}
}' | tee /tmp/llama-req-on.json

echo ""
echo "RESPONSE:"
ssh "$WIN_HOST" "curl -s http://127.0.0.1:8080/v1/chat/completions -H 'Content-Type: application/json' -d @-" < /tmp/llama-req-on.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
m = d.get('choices',[{}])[0].get('message',{})
c = m.get('content','')
print(f'  completion_tokens: {d.get(\"usage\",{}).get(\"completion_tokens\")}')
print(f'  content length:    {len(c)}')
print(f'  has <think>:       {\"<think>\" in c}')
think_match = __import__('re').search(r'<think>(.*?)</think>', c, __import__('re').DOTALL)
if think_match:
    print(f'  THINK section:     {len(think_match.group(1))} chars')
    print(f'  THINK preview:     {think_match.group(1)[:200]}')
    final = c[think_match.end():]
    if final.strip():
        print(f'  FINAL content:     {final.strip()[:200]}')
    else:
        print(f'  FINAL content:     (none - all thinking)')
else:
    print(f'  CONTENT preview:   {c[:300]}')
print(f'  All message keys:  {list(m.keys())}')
"

echo ""
echo "--- Test 3: no chat_template_kwargs (uses server default) ---"
echo "REQUEST:"
jq -n --arg q "$QUESTION" '{
  model: "any",
  messages: [{role: "user", content: $q}],
  stream: false,
  max_tokens: 256
}' | tee /tmp/llama-req-default.json

echo ""
echo "RESPONSE:"
ssh "$WIN_HOST" "curl -s http://127.0.0.1:8080/v1/chat/completions -H 'Content-Type: application/json' -d @-" < /tmp/llama-req-default.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
m = d.get('choices',[{}])[0].get('message',{})
c = m.get('content','')
print(f'  completion_tokens: {d.get(\"usage\",{}).get(\"completion_tokens\")}')
print(f'  content length:    {len(c)}')
print(f'  has <think>:       {\"<think>\" in c}')
think_match = __import__('re').search(r'<think>(.*?)</think>', c, __import__('re').DOTALL)
if think_match:
    print(f'  THINK section:     {len(think_match.group(1))} chars')
    print(f'  THINK preview:     {think_match.group(1)[:200]}')
    final = c[think_match.end():]
    if final.strip():
        print(f'  FINAL content:     {final.strip()[:200]}')
    else:
        print(f'  FINAL content:     (none - all thinking)')
else:
    print(f'  CONTENT preview:   {c[:300]}')
print(f'  All message keys:  {list(m.keys())}')
"
