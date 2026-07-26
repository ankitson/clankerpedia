#!/usr/bin/env bash
# run-powershell.sh — run PowerShell on a remote Windows host over SSH without
# quoting/encoding pain. Uses -EncodedCommand (base64 UTF-16LE), forces UTF-8
# output, silences progress (CLIXML) noise, and strips any residual CLIXML.
#
# Usage:
#   run-powershell.sh <ssh-host> "Get-Date"
#   run-powershell.sh <ssh-host> <<'PS'
#     Get-ChildItem -LiteralPath "C:/Users/me/Documents" | Select-Object Name
#   PS
#
# Requires: ssh access to <ssh-host>; python3 OR iconv+base64 on this machine.
set -euo pipefail

host="${1:?usage: run-powershell.sh <ssh-host> [command]   (or pipe a script via stdin)}"
if [ "$#" -ge 2 ]; then ps_body="$2"; else ps_body="$(cat)"; fi

# Hardening prelude: UTF-8 output + no progress stream => no CLIXML noise, no mojibake.
prelude='$ProgressPreference="SilentlyContinue"; $ErrorActionPreference="Stop"; [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;'
script="$prelude
$ps_body"

# Encode as base64 of UTF-16LE (what -EncodedCommand expects). No newlines in output.
if command -v python3 >/dev/null 2>&1; then
  b64="$(printf '%s' "$script" | python3 -c 'import sys,base64; sys.stdout.write(base64.b64encode(sys.stdin.buffer.read().decode("utf-8").encode("utf-16-le")).decode())')"
else
  b64="$(printf '%s' "$script" | iconv -f utf-8 -t utf-16le | base64 | tr -d '\n')"
fi

# 2>&1 so stderr is visible; drop residual CLIXML framing just in case.
ssh "$host" "powershell -NoProfile -NonInteractive -EncodedCommand $b64" 2>&1 \
  | grep -av '^#< CLIXML' \
  | grep -av '^<Objs '
