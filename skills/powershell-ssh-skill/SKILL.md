---
name: powershell-ssh
description: Run PowerShell on a remote Windows host over SSH from macOS/Linux without quoting, encoding, or output-noise pain. Use whenever you invoke PowerShell through `ssh <host>` and hit broken nested quotes (`\$var` mangled, `$OutputEncoding` parse errors), mojibake on Chinese/UTF-8 output, `#< CLIXML` / `<Objs ...>` junk on stderr, Windows paths with spaces or non-ASCII names, or you need to copy files off a Windows machine. Built from real breakage, not theory.
---

# PowerShell over SSH (from macOS / Linux)

> This skill covers *delivering* PowerShell to a remote Windows host. For how to
> *write* the PowerShell itself (script structure, parameters, error handling,
> Gallery modules, GUI), see the **powershell-expert** skill.

Running `ssh windows "powershell -Command \"...\""` directly is a trap: the command
passes through **bash → ssh → cmd.exe → powershell**, and each layer eats quotes. You get
mangled tokens (`\$f.FullName` becomes literal text), `$OutputEncoding=... : not found`
parse errors, mojibake, and CLIXML noise. The fixes below make it reliable.

## TL;DR — use the helper

`scripts/run-powershell.sh` encapsulates every fix (base64 `-EncodedCommand`, UTF-8 output,
progress/CLIXML suppression). Prefer it over hand-rolling `ssh ... powershell`.

```bash
# inline command
scripts/run-powershell.sh windows "Get-Date"

# multi-line script via heredoc (no escaping needed inside)
scripts/run-powershell.sh windows <<'PS'
  $dir = "C:/Users/me/Documents/Some Folder"
  Get-ChildItem -LiteralPath $dir -Filter "*report*.xlsx" | Select-Object Name, Length
PS
```

## The core trick: `-EncodedCommand` (base64 UTF-16LE)

If you can't use the helper, encode the script yourself. This sidesteps **all** quoting —
the entire script travels as one base64 token, so quotes/`$`/backslashes/newlines inside it
are never re-parsed by bash or cmd:

```bash
PS='$ProgressPreference="SilentlyContinue"; [Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
Get-ChildItem -LiteralPath "C:/Users/me/Documents" | Select-Object Name'
B64=$(python3 -c 'import sys,base64; sys.stdout.write(base64.b64encode(sys.argv[1].encode("utf-16-le")).decode())' "$PS")
ssh windows "powershell -NoProfile -EncodedCommand $B64"
```

Key points:
- Encoding must be **UTF-16LE** then base64 (that is exactly what `-EncodedCommand` decodes).
- `base64` output must have **no newlines** (python's `b64encode` is fine; with the
  `base64` CLI add `| tr -d '\n'`).
- No `iconv`? `python3` works everywhere. No `python3`? `printf %s "$PS" | iconv -f utf-8 -t utf-16le | base64 | tr -d '\n'`.

## Mojibake (garbled Chinese / UTF-8)

Console output defaults to a legacy codepage, so non-ASCII prints as `���ɴ`. Fix inside the
script (the helper does this for you):

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

Note: text read **from files** (`Get-Content`, `Select-String`) usually comes back correct
even when the surrounding console echo is garbled — the garbling is a display-codepage issue,
not data loss.

## CLIXML noise on stderr

PowerShell over SSH serializes its progress stream as XML to stderr, so `2>&1` output gets
polluted with:

```
#< CLIXML
<Objs Version="1.1.0.1" ...><Obj S="progress">...正在准备首次使用模块...</Obj></Objs>
```

Two defenses (use both):
- **Prevent it:** put `$ProgressPreference = "SilentlyContinue"` at the top of the script.
- **Strip it:** pipe through `grep -av '^#< CLIXML' | grep -av '^<Objs '`.

## Windows paths with spaces & non-ASCII

- **Use forward slashes** — PowerShell accepts `C:/Users/me/...`; avoids backslash escaping.
- **Always `-LiteralPath`** (not `-Path`) so `[` `]` and spaces aren't treated as wildcards.
- **Don't type exact non-ASCII names** — match by wildcard instead:
  `Get-ChildItem -LiteralPath $dir -Filter "*65 Schiaparelli*.md" | Select-Object -First 1`
- Build child paths with `Join-Path $dir $name` rather than string concatenation.

## Copying files off Windows (the reliable way)

Per-file `scp` with spaces/Chinese in names is fragile. **Zip on Windows → scp → unzip:**

```bash
# 1) stage + zip on Windows (temp dir under $env:TEMP has no spaces => scp-friendly)
scripts/run-powershell.sh windows <<'PS'
  $stage = Join-Path $env:TEMP "pull_xyz"
  if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
  New-Item -ItemType Directory -Force $stage | Out-Null
  Copy-Item -LiteralPath "C:/Users/me/Documents/Some Folder/note.md" -Destination "$stage/note.md"
  $zip = Join-Path $env:TEMP "pull_xyz.zip"
  if (Test-Path $zip) { Remove-Item -Force $zip }
  Compress-Archive -Path "$stage/*" -DestinationPath $zip
  Write-Output ("ZIP=" + $zip)
PS

# 2) pull it (forward-slash absolute path, no spaces) and unzip locally
scp windows:"C:/Users/me/AppData/Local/Temp/pull_xyz.zip" ./pull_xyz.zip
unzip -o pull_xyz.zip -d ./pulled

# 3) clean up the Windows temp afterwards
scripts/run-powershell.sh windows 'Remove-Item -Force "$env:TEMP/pull_xyz.zip"; Remove-Item -Recurse -Force "$env:TEMP/pull_xyz"'
```

Notes:
- Keep staging under `$env:TEMP` (path `C:/Users/<user>/AppData/Local/Temp`, no spaces) so the
  `scp` source path is trivial.
- `Compress-Archive` + Mac `unzip` handles ASCII attachment names cleanly; if a file you must
  keep has a non-ASCII name, rename it to ASCII in the staging dir before zipping.

## Anti-patterns (these break)

- `ssh host "powershell -Command \"... \$x ...\""` — nested quotes/`$` get mangled. Use `-EncodedCommand`.
- `-Path` with names containing `[ ]` or spaces — silently wrong; use `-LiteralPath`.
- Forgetting `$ProgressPreference` and then parsing stdout that contains CLIXML.
- `scp 'host:C:\Users\me\My Folder\file'` — backslashes + spaces; zip instead.
