# Toolbox Notes

## 2026-08-02

### Todoist overdue daily catch-up

#### Goal

- Keep an unfinished daily routine on today's occurrence when repairing an
  overdue task, including when today's scheduled time has already passed.

#### Discovery

- Live `Tester` experiments disproved the assumption that re-sending a task's
  `due.string` idempotently re-evaluates its rule. A current daily task advanced
  one day on every call; an overdue Aug 1 daily task skipped Aug 2 and landed on
  Aug 3 regardless of whether its clock time was before or after the current
  Pacific time.
- Full-datetime `task reschedule` to today preserved the exact rule, recurrence
  flag, clock time, and relative reminder. Completing an already-passed 9 AM
  occurrence then advanced normally to tomorrow with the reminder intact.

#### Decision

- Daily rules now reschedule directly to the current calendar day using their
  existing time component. Non-daily rules retain recurrence advancement, so
  an overdue Saturday task still lands on the following Saturday.
- Verification now checks the exact time component and requires a daily task to
  land on today's exact due value, not merely today or later.

#### Verification

- Five deterministic unit tests cover morning/afternoon/evening daily times,
  supported daily spellings, anchored daily rules, all-day tasks, dry-run, and
  the retained Saturday path.
- A live production-CLI run advanced daily 9 AM and 4 PM fixtures from Aug 1 to
  Aug 2, and a Saturday fixture from Aug 1 to Aug 8. All retained recurrence,
  exact rules, times, and relative reminders. Safety cleanup returned `Tester`
  to zero tasks.

## 2026-07-26

### WezTerm session-layout recovery

#### Goal

- Preserve a small rolling set of open WezTerm layouts so the user can rebuild
  their working set after a reboot.

#### Decision

- Back up structural state only: windows, tabs, split geometry, working
  directories, workspaces, and tab titles.  A reboot cannot safely restore the
  interactive processes or their in-memory terminal contents, so restore opens
  new login shells in the saved directories.
- Use a user systemd timer at a 15-minute cadence and retain four snapshots.
  The backup command uses WezTerm's no-auto-start mode, preventing the timer
  from accidentally starting an empty mux while WezTerm is closed.

#### Verification

- Python compilation passed.  With no live mux on this host, a backup exits
  successfully and reports that it was intentionally skipped.

## 2026-07-24

### Todoist recurring-task guidance

#### Decision

- Updated the Todoist CLI skill to prefer `td task reschedule` for recurring
  tasks now that the egress proxy resolves Sync API task updates by project.

#### Verification

- Live rescheduling succeeded in an allowlisted project, and the same Sync API
  operation remained blocked for a non-allowlisted project.

## 2026-07-17

### X research: Bird-backed route

#### Decision

- Added the upstream `bird` skill from `windhood-jza/openclaw-bird-skill` as a
  refreshable external snapshot.
- Kept `x-research` as the research workflow and switched its X transport to
  the sibling Bird skill: query decomposition, thread follow-up, linked-source
  verification, and thematic synthesis remain explicit.

#### Verification

- Confirmed the local `bird` binary is available and its read/search commands
  are exposed.

### Web-search routing

#### Decision

- Added `web-search` as the compact routing layer: SearXNG is the default for
  public-web discovery; browser search is an explicit fallback; browser
  interaction, preservation, summarization, rich-media extraction, and
  platform-native research each have a distinct owner.
- Renamed the former generic `web-search` skill to `browser-web-search` and
  narrowed its trigger so Google/DDG browser search is not selected by default.
- Marked `searxng` and `browser-web-search` explicit-only; `web-search` is now
  the sole automatic entry point for broad web research.
- The router points to sibling skill directories and delegates implementation
  details to each selected skill, preventing agents from treating skill names
  as nonexistent MCP servers.

#### Verification

- `skillctl` discovers `web-search` as custom, `browser-web-search` as custom,
  and keeps the SearXNG source separately available.

## 2026-07-14

### Chatterbox text-to-speech skill

#### Goal

- Add a reusable local text-to-speech workflow alongside the Parakeet
  transcription skill.

#### Discovery

- The `chatterbox-tts` Docker service is exposed to the host at
  `127.0.0.1:8833`, while its intended internal API base is
  `http://chatterbox-tts:8000/v1`.
- Its OpenAPI schema accepts `input`, `model`, `voice`, `response_format`, and
  `speed` at `/v1/audio/speech`.

#### Decision

- Added `skills/chatterbox-tts` with model `chatterbox` and voice `Alice` as
  the defaults, plus narrow per-invocation and environment-based overrides.
- The client has no third-party dependencies and uses an atomic temporary file
  so failed requests never leave a partial audio artifact at the output path.

#### Verification

- Generated a WAV through the live local service; `file` identified it as
  24 kHz, 16-bit mono PCM audio.

### Disk-space audit skill

#### Goal

- Capture the repeatable homeserver disk-audit and cleanup workflow, including
  where Docker, service state, logs, databases, and ML models actually live.

#### Decision

- Expanded `skills/disk-space-audit/SKILL.md` with explicit searches across
  `/home`, `~/hroot/{devserver,homeserver,projects}`, Docker metadata, and
  `/mnt/store-ext4/models`.
- The workflow distinguishes Docker virtual/shared size from reclaimable unique
  size, retained cold services from orphans, and model weights from durable
  application data.
- Model moves use metadata-preserving copy, dry-run comparison, and source
  deletion only after verification. Runtime model mounts should use
  `/mnt/store-ext4/models`.
- Automatic model invocation remains disabled so disk inspection or destructive
  cleanup starts only when the skill is selected explicitly.

#### Verification

- Frontmatter retains `disable-model-invocation: true`; the host path map,
  read-only audit, approval gate, cleanup validation, and report contract are
  all present.

### Shared Parakeet transcription skill

#### Goal

Replace an OpenClaw-bundled transcription skill whose hard-coded OpenAI model
could be routed to an incompatible provider with a reusable skill owned in the
shared toolbox.

#### Discovery

- Bifrost request `44733b2a-062e-4649-8e71-08fcf800ba79` used provider `codex`
  and model `gpt-4o-transcribe`; Codex rejected transcription as an unsupported
  operation.
- OpenClaw's bundled `openai-whisper-api` script defaults to that model and does
  not consume its configured `config.model`, so setting only the OpenClaw skill
  config did not affect the multipart request.
- The Parakeet-compatible endpoint may return `{"text":"..."}` even when the
  request asks for plain text.

#### Decision

- Added `skills/parakeet-asr` with a deterministic Parakeet default model while
  keeping the API base, credential, and model override environment-driven so it
  can be reused by any harness mounting toolbox skills.
- The script uses an atomic temporary output, fails on non-2xx responses, and
  unwraps JSON text responses for `.txt` output.
- OpenClaw configuration and deployment remain in devserver; toolbox contains
  no deployment-specific credential.

#### Verification

- Shell syntax and ShellCheck passed.
- OpenClaw discovered the skill from `agents-skills-personal` with all runtime
  requirements satisfied.
- An end-to-end fixture request through OpenClaw's configured environment,
  Bifrost, and Parakeet produced an 871-character plain-text transcript.

## 2026-07-11

### Stack unification migration 1: knowledge fold + composed AGENTS.md

#### Goal
- First step of untangling the LLM/agent stack: one place to write things down,
  and one global-instructions artifact that actually reaches every harness.
  Follow-ups (task hub, per-agent profiles/launcher, deletions, sandboxing) are
  sequenced in `~/.claude/plans/i-want-help-unifying-lexical-pixel.md`.

#### Discovery
- The infra layer was already unified (Bifrost = models, mcpproxy = tools,
  toolbox/skills = one shared dir); the fragmentation was words + context
  distribution.
- `@~/AGENTS.env.md` imports only work in Claude Code — Codex/OpenCode saw a
  dead literal line, so the env/path index never reached them. OpenCode's
  primary config root `~/.config/opencode/` had **no AGENTS.md at all**.
- `/home/ankit/AGENTS.md` was a drifted hand-copy of toolbox/AGENTS.md — the
  only copy carrying the secrets-redaction section. Manual sync had already
  failed once; hence a build step.
- The AGENTS.md symlink fan-out (claude/codex/opencode/pi) is chezmoi-managed
  (`/projects/devdocker/dotfiles`), so durable wiring had to go through the
  dotfiles repo, not ad-hoc `ln -s`.
- qmd only indexed allplace collections — the standalone `~/hroot/wiki` was
  never searchable; folding it into the vault *gained* search coverage.

#### Decision
- Boundary rule: allplace = the only place notes are written (wiki/ = shared
  engineering KB, agents may write `wiki/` + `agents/` only); cybernetics =
  OpenClaw operating memory, not a knowledge base; repo docs/ = dies with the
  repo; to-dos → beads. Recorded in `allplace/wiki/README.md` and the rendered
  AGENTS.md routing section.
- Full migration, no compat symlinks: `~/hroot/wiki` → `allplace/wiki`,
  `~/hroot/INDEX.md` → `allplace/wiki/INDEX.md`; all live references updated
  (memory files, local-llm ADR 0004 got a superseded-note).
- Context composition = a standalone `bin/frag` utility (Jinja `{% include %}`
  over `-I` search dirs, stdout or `-o`), not a bespoke build script. The
  template *is* the profile: `context/templates/AGENTS.md.j2` lists its
  includes directly — no YAML profile layer (dropped as overengineering; the
  per-agent skills/mcp/model config for migration 3 is launcher config, a
  separate artifact from this text compose). `~/AGENTS.env.md` stays as
  chezmoi's per-host env output (plan originally deleted it) — frag inlines it,
  fixing the Claude-only import.

#### Verification
- All six entry points (`~/AGENTS.md`, `~/.claude`, `~/.codex`, `~/.opencode`,
  `~/.config/opencode`, `~/.pi/agent`) resolve to one identical rendered file
  (same sha256). Fresh `claude -p --model haiku` one-shot answered
  desktop-win / `allplace/wiki` from instructions alone.
- `qmd update` indexed the new `wiki` collection (5 files); search resolves
  `agent-project-process`. Note: `qmd embed` has ~2446 hashes pending vectors
  (backlog predates this change; not run).

#### Next steps
- Migration 2: central beads hub + migrate scattered backlogs (Technical
  Tinkering doc, cybernetics tasks.md).
- Migration 3: per-agent profiles (skills/mcp/model subsets) + launcher with
  full system-prompt control; `delegate` MCP tool on mcpproxy for cross-model
  subagents. Migration 5: OS-level vault sandboxing (bwrap/binds) — policy
  alone doesn't confine an agent.
- Run `chezmoi apply` on other machines to pick up the new symlinks; run
  `just agents` there after (INDEX/env fragments are per-host, missing files
  are skipped gracefully).

## 2026-06-30 (cont.) — the real root cause: SSHMUX proxy PATH, not version

#### Problem
- After deploying matching `06c71b67` builds to all three hosts, `m2book` still
  failed `wezterm cli spawn --domain-name SSHMUX:desktop` with the same
  "Please install the same version of wezterm on both the client and server!"
  error (decode error: EOF while reading leb128 PDU length).

#### Discovery
- The SSHMUX client (`wezterm-client/src/client.rs:686-691`) runs
  `<remote_wezterm_path or "wezterm"> cli --prefer-mux proxy` over a plain,
  **non-interactive, non-login** SSH exec (`ssh host cmd`, not an interactive
  shell). `~/.bashrc:4` has the standard `case $- in *i*) ;; *) return;; esac`
  guard, so it returns before line 116's `PATH=...vendor:...` export — a
  non-interactive SSH command therefore gets the bare system default PATH
  (`/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:...`), which
  has no wezterm binary at all (`/usr/bin/wezterm` doesn't exist on this box).
- So `wezterm` was simply **command-not-found** on every non-interactive SSH
  session to this server — this was true regardless of which version was
  deployed, and had nothing to do with the version drift this session started
  by chasing. The client's version-mismatch message is misleading here; its own
  hint ("it could also happen if the remote host outputs to stdout prior to
  running commands") was the real clue.
- Confirmed via `ssh -o BatchMode=yes ankit@desktop-linux.<tailnet>.ts.net
  'wezterm --version'` (genuine non-interactive exec, not the harness's shell,
  which inherits an already-exported PATH and masked the bug).

#### Decision
- Symlinked the vendor binaries into `/usr/local/bin` (root-owned but on every
  default PATH, incl. non-interactive SSH sessions): `sudo ln -sf
  ~/.local/bin/vendor/{wezterm,wezterm-mux-server} /usr/local/bin/`. One-time
  sudo, trivially reversible (`rm`), and since it's a symlink it always tracks
  whatever `wezterm-sync` deploys to vendor — no re-fix needed after future
  rebuilds.
- Rejected: overriding `remote_wezterm_path` on the mac/windows `wezterm.lua`
  `ssh_domains` — `config.ssh_domains = wezterm.default_ssh_domains()` derives
  one domain per `~/.ssh/config` `Host` entry, so a scoped override is possible
  but a server-side fix covers every client (present and future) at once and
  matches the June-2026 session's own conclusion ("the cleaner durability path
  is patching /usr/bin too").
- Verified: replayed the exact proxy invocation over a genuine non-interactive
  SSH session — it now runs and stays alive waiting for PDU input (previously:
  instant `command not found`). Full end-to-end (`wezterm cli spawn
  --domain-name SSHMUX:desktop`) needs a real Aqua/Win32 display to finish, which
  isn't reachable over a headless SSH session — ask the user to retry from an
  actual terminal on each client.
- User confirmed the reconnect worked. **User's follow-up bug: `eza --icons`
  colors work over plain SSH but not through wezterm mux.**

### Follow-up: eza colors missing only through wezterm mux (NO_COLOR poisoning)

#### Discovery
- `wezterm-mux-server` has no restart-on-schedule; per `config/src/unix.rs:107-130`,
  ANY client connection that can't reach the local socket auto-spawns
  `<dir of current_exe()>/wezterm-mux-server --daemonize` on demand — this is
  by design, so "I don't start it manually" is correct, expected behavior.
- The catch: whatever process happens to trigger that very first auto-spawn
  determines the daemon's environment **forever** — every pane it ever creates
  inherits that daemon's own env, not a freshly computed one.
- Found the live daemon's parent was `claude --allow-dangerously-skip-permissions`
  (started 2026-06-27 16:38, orphaned to init after `--daemonize`) — it had been
  started from inside a Claude Code agent shell at some point, and agent/CLI
  harnesses commonly export `NO_COLOR=1` so tool output stays clean of ANSI for
  capture. `eza` (like many tools) unconditionally disables all color when
  `NO_COLOR` is present, regardless of `CLICOLOR`/`TERM`/tty-ness. Confirmed via
  `sudo cat /proc/<mux-pid>/environ`: `NO_COLOR=1` present on the daemon and both
  its live panes. Plain SSH is unaffected because it's a completely fresh login
  session with no such inheritance.
- Confirmed no system-wide source (`/etc/environment`, `/etc/profile.d`,
  `sshd_config SetEnv`) sets `NO_COLOR` — a genuinely fresh non-interactive SSH
  exec has none of it. So a clean respawn stays clean, UNLESS something
  daemonizes it again from a poisoned shell.

#### Decision
- Killed the poisoned daemon (`kill <pid>` — `pkill -x` silently no-ops here,
  the process name truncates to 15 chars and `-x` requires an exact match) and
  relaunched via `env -u NO_COLOR -u CLICOLOR_FORCE wezterm-mux-server
  --daemonize`. Verified the new daemon's default auto-spawned pane has no
  `NO_COLOR` in `/proc/<pid>/environ`.
- Hardened `bin/wezterm-sync`'s `restart_mux()` to always strip
  `NO_COLOR`/`CLICOLOR_FORCE` via `env -u` before daemonizing, so `--restart-mux`
  can never reproduce this regardless of which shell invokes the tool (this
  session's own shell had `CLICOLOR=1`, harmless, but the risk pattern is real).
- Did NOT add a config-level `set_environment_variables` override in
  `~/.wezterm.lua` to force-clear `NO_COLOR` for every pane — a clean daemon
  spawn is the correct fix per wezterm's own design, and a per-pane env
  override would only mask a bad daemon environment rather than preventing it.
- Not fully addressed: nothing stops a **future** agent session from
  accidentally `--daemonize`-ing this again outside of `wezterm-sync`. The only
  guard is this note + the hardened tool path.

## 2026-06-30

### Keeping the custom wezterm in sync across server + mac + windows

#### Problem
- We run a custom wezterm build on this Linux server (the mux host) and on the
  clients `m2book` (macOS) and `desktop-win` (Windows). The server's deployed
  binary had drifted to `20260625-133254-06c71b67` (branch
  `fix/panefocused-client-focus-metadata`, 17 commits past `main`), while
  `desktop-win` still runs stock `20260117-154428-05343b38` and `m2book` was on
  the earlier patched build. "Clients no longer compatible" = version drift.

#### Discovery
- wezterm only *hard*-rejects a mux connection when `codec::CODEC_VERSION`
  differs (`wezterm-client/src/client.rs:1160`). That constant has been **45**
  for every build we touch — `05343b38`, `main`/`607fa84f`, `06c71b67`, and
  current `upstream/main` — and `codec/` is byte-identical across them. So no
  build is wire-incompatible; the divergence is behavioural (PaneFocused storm /
  resize dead-loop / focus-metadata fixes in `mux/` + `wezterm-client/`).
- Therefore "staying compatible" means **running the same commit everywhere**,
  not matching a magic protocol number.
- Binaries are not portable across linux-x64 / macos-arm64 / win-x64, so a build
  must happen natively on each host; we can't copy one binary around.

#### Decision
- `bin/wezterm-sync`: resolve a canonical git ref → commit + expected version
  string (`<commitdate>-<HHMMSS>-<shorthash8>`), then per host: fetch `origin`,
  check out that exact sha, init submodules, build natively over ssh, back up +
  install into the platform's wezterm path, and verify `--version` contains the
  short hash. Origin is the fork `git@github.com:ankitson/wezterm.git`.
- Canonical ref defaults to `main` (`607fa84f`, the consolidated custom build);
  override with `--ref`.

#### Windows is special (per agentsview codex:019ef140)
- Windows does NOT use a git clone. The server builds a clean source tree from
  the sha (worktree + submodules), seeds repo-root `.tag` with the version
  string, tars it to `wezterm-win-src-<short>.tar.gz` (~121 MB), and ships it to
  `C:\Users\ankit\wezterm-builds\`. `wezterm-version/build.rs:7` reads `../.tag`
  into `WEZTERM_CI_TAG`, so the archive build reports the exact version without
  `.git`.
- Build runs via `bin/wezterm-build-windows.cmd` (shipped to the host), which
  encodes the toolchain recipe: VS2022 Build Tools `VsDevCmd.bat` for cl/link,
  Strawberry Perl (`C:\Strawberry`) ahead of Git's perl for OpenSSL, and — key —
  it bypasses the rustup shims (which fail under OpenSSH's symlink policy) by
  calling the real `cargo`/`rustc` under `.rustup\toolchains\*-windows-msvc\bin`
  and pinning `RUSTC`. Must run under cmd.exe, not PowerShell.
- Output is a PORTABLE bundle `C:\Users\ankit\wezterm-builds\WezTerm-windows-<tag>\`
  containing the four exes + `wezterm.pdb` + conpty/OpenConsole + ANGLE
  `libEGL`/`libGLESv2` + `mesa\opengl32.dll` (mirrors `ci/deploy.sh` msys
  branch). The user launches `wezterm-gui.exe` from there; the stock
  `C:\Program Files\WezTerm` install is left untouched. Note `wezterm-gui
  --version` prints a "forgot assign_version_info" string — validate via
  `wezterm.exe --version` (CLI), which reports the tag.

#### Caveats (verify when hosts are online)
- Validated this round: ref→version resolution, isolated server worktree +
  `.tag`, and the 121 MB Windows source tarball (correct layout + `.tag`).
- `m2book` was offline; its macOS bundle/codesign path is encoded from June 2026
  but untested here.
- `desktop-win`'s on-host build is encoded from the session but untested this
  round: its rustup shim was erroring over ssh and no source was present, so the
  prereqs (VS2022 Build Tools, Strawberry Perl, nightly-msvc toolchain) must be
  in place before `--apply` to that host will complete.

## 2026-06-27

### AgentsView search endpoint correction

#### Discovery
- AgentsView transcript search is served by `/api/v1/search?q=...&limit=...&sort=relevance`.
- The older skill guidance incorrectly described full-text search as a
  `search` query parameter on `/api/v1/sessions`, which produced broad and
  misleading results for transcript lookups.

#### Decision
- Use `/api/v1/search` first when locating sessions by message content.
- Treat `results[].session_id` as the identifier to pass to session detail and
  message endpoints.

## 2026-06-24

### Document work chronology

#### Discovery
- The work logs had drifted into repeated same-day date headers and mixed
  chronological order, especially after append-only updates.
- The `document-work` skill did not state the reverse-chronological,
  one-header-per-day convention.

#### Decision
- Normalize notes and changelog sections by date, latest first.
- Use one `## YYYY-MM-DD` header per day, with same-day work items grouped as
  `###` sections below it.
- Update the `document-work` skill so future agents preserve this structure.

### Chezmoi skill apply safety

#### Discovery
- The chezmoi skill advised agents to run `chezmoi apply --refresh-externals
  --force`, which bypasses chezmoi's overwrite prompts and can discard local
  dotfile edits.
- Running `chezmoi apply` without `--force` can require interactive decisions,
  which is a poor fit for agent environments.

#### Decision
- Treat source-state edits and destination applies as separate phases.
- Require preview plus explicit current-conversation consent before applying
  changes to live dotfiles.
- Prefer targeted `chezmoi apply --no-tty <target...>` after approval, stop if
  chezmoi needs an interactive decision, and reserve `--force` for exact
  target paths the user explicitly approved.

### Network listener range grouping

#### Discovery
- Docker publishes host port ranges as individual socket listeners. A mapping
  like `3000-3100:3000-3100` produces one listener per port and can use distinct
  proxy PIDs for IPv4/IPv6.

#### Decision
- Collapse text report rows for consecutive runs of at least five ports when
  protocol, process name, bind pattern, and notes match.
- Group text report rows by process name by default, with
  `--no-process-groups` available for the protocol/port detail view.
- Keep JSON output uncollapsed so exact per-listener details remain available.

### Network listener audit helper

#### Goal
- Add a portable toolbox command for checking which local services are exposed
  through wildcard binds, LAN/private IPs, Tailscale-only binds, or other
  non-loopback interfaces.

#### Decision
- Use Linux `ss` as the socket source and `ip -j addr show` for interface
  context, so Docker/libvirt bridge addresses are not mistaken for physical LAN
  addresses.
- Keep the helper dependency-free and provide JSON output for follow-up
  automation.

#### Verification
- Added unit coverage for socket parsing, interface classification, and
  Tailscale-only grouping.

## 2026-06-22

### Windows WezTerm SSHMUX freeze tracing

#### Discovery
- A frozen Windows client was still connected to the Linux mux as
  `desktop-win`, PID `64616`, through proxy PID `3151073`.
- Linux-side `wezterm-trace` showed 0 focus transitions during the freeze, so it
  did not match the June 13 PaneFocused storm signature.
- Windows process sampling showed `wezterm-gui.exe` was `Responding=True` but
  consuming roughly one CPU-second per wall-second on a single hot thread.
- Windows was running `wezterm 20260117-154428-05343b38`, while the Linux tool
  reported `20260425-155631-44a8f937`; the local fork keeps the resize dead-loop
  and activate-tab resize fixes on separate branches from the PaneFocused fix.

#### Artifacts
- Linux mux trace:
  `/home/ankit/wezterm_traces/wezterm-trace-20260622-143642.tar.gz`.
- Manual Windows minidump and process evidence:
  `logs/wezterm-windows-freeze-20260622-144023/`.
- Repeatable Windows trace-helper run with fetched minidump:
  `/home/ankit/wezterm_traces/wezterm-win-trace-20260622-145036/`.

#### Decision
- Add a Windows-side SSH trace helper so future freezes can capture process
  samples, thread CPU, logs, optional minidumps, and optional WPR traces without
  hand-written PowerShell.

## 2026-06-19

### Autoresearch skill import

#### Goal
- Add the Autoresearch agent skill to the canonical toolbox skill tree.

#### Decisions
- Use `uditgoenka/autoresearch` instead of `karpathy/autoresearch`.
- Track the upstream `master` branch explicitly because the repository does not
  publish a `main` branch.
- Import the portable skill from `.agents/skills/autoresearch`, which contains
  the `SKILL.md` and companion command/reference markdown files.

#### Verification
- Synced `skills/autoresearch` from upstream commit `166755a2600a`.

### Summarize saved output copies

#### Goal
- Preserve `summarize` stdout for later lookup without changing the normal
  streaming CLI behavior.

#### Decision
- Keep `summarize` as a custom local skill. `skills.toml` remains only for
  external skill sources and generated router bundles.
- Save successful stdout-producing wrapper runs under `/tmp/summarize/`, using
  timestamped Markdown filenames with `summary` or `transcript` in the name.
- Treat `--extract` output as transcript/source output; all other runs are
  summary output.
- Update `skills/summarize/SKILL.md`, `skills/summarize/agents/openai.yaml`, and
  README usage notes so agents and humans know where saved copies land.

## 2026-06-18

### Portable skill router generation

#### Goal
- Add a `skillctl` workflow for turning a related set of installed skills into
  one portable router skill, starting with the Sahil Lavingia minimalist
  entrepreneur skills.

#### Decisions
- Keep `.skillctl-source` as a registry-label ownership marker. It continues to
  contain values like `slavingia`, not repo provenance such as
  `slavingia/skills`; the authoritative repo and path stay in `skills.toml`.
- Add `bin/skillctl router <name>` as the generator interface. It accepts
  explicit installed skill names, `--group <title>` for semantic groupings in
  `skills.sh.json`, and `--source-group <label>` as a fallback for skills copied
  by a glob registry entry.
- Make router sync the default "one visible router" workflow. It bundles
  selected skills into `references/<skill>/instructions.md` and removes their
  top-level active skill directories while preserving provenance in
  `skills.toml`.
- Move router membership and provenance into `skills.toml` router tables. Router
  `absorbs` entries use `repo:path` specs, with `local:path` reserved for
  locally vendored historical sources.
- Add root `skills.sh.json` using the existing Skills.sh grouping convention.
  This file is generated from `skills.toml` routers; `.skillctl-source` remains
  only a sync ownership marker.
- Render the router `SKILL.md` from
  `templates/skillctl/router.SKILL.md` using Python's stdlib
  `string.Template`, keeping the template separate without adding a runtime
  dependency.
- Copy selected skills into `references/<skill-name>/`, rename bundled
  `SKILL.md` files to `instructions.md`, and omit `.skillctl-source` markers
  from the bundled references. This prevents recursive skill scanners from
  discovering bundled references as duplicate skills.
- Generate `skills/minimalist-entrepreneur` from the
  `routers.minimalist-entrepreneur` `skills.toml` table as the first absorbed
  router skill.
- Add absorbed routers for Cloudflare platform skills and agent workflow skills.
  `zoom-out` was removed upstream from `mattpocock/skills`, so its last upstream
  copy from commit `801a01cc7d265e06dd9dbcef5a4c471add05a0b3` is vendored under
  `vendor/skills/mattpocock/zoom-out` and referenced with a `local:` absorb.

## 2026-06-13

### WezTerm bug investigations (moved to the wezterm repo)

The detailed root-cause / reproduction / fix-verification / deployment notes for the
WezTerm bugs worked on this day — PaneFocused notification storm (#4390 / PR #7763),
`adjust_x_size`/`adjust_y_size` resize dead loop (#7765), and mux resize-sync
(attach undersize #5117, drag desync #5142/#3694) — were relocated to the wezterm
fork at `/projects/external-repo/wezterm/investigations/` (fixes on the `fix/*`
branches of `github.com/ankitson/wezterm`). All three fixes are deployed locally
(Mac `wezterm-gui` bundle + Linux `wezterm-mux-server`); durability needs a one-time
`sudo cp ~/wezterm-patched-bin/* /usr/bin/` (now done).

## 2026-06-12

### Docme generated docs listing

#### Discovery
- Toolbox's root `AGENTS.md` was included in the fallback build as `/AGENTS/`, but projects with a root `README.md` skipped the generated all-docs index because the README became the homepage.

#### Decision
- Keep an existing root `README.md` or `index.md` as the homepage.
- Add a separate generated `Docs` listing page for fallback builds with a homepage, using `docs.md` unless that name is already taken.

#### Verification
- Built `/projects/toolbox` in fallback mode and confirmed the generated `/docs/` page links to `/AGENTS/`.

## 2026-06-11

### Docme Markdown site helper

#### Goal
- Add a standalone toolbox command for turning a directory of Markdown files into a quick MkDocs Material site.

#### Decisions
- Name the tool `docme`.
- Keep the tool self-contained: it builds and serves docs, but does not publish to webby.
- Use PEP 723 metadata with `uv run --script` and depend on `mkdocs-material` directly.
- If `mkdocs.yml` or `mkdocs.yaml` exists in the root directory, delegate to it and only override the build output directory.
- Scan all `.md` files recursively from the current directory, capped at depth 3 by default and configurable with `--depth`.
- Stage discovered Markdown files into a temporary MkDocs docs tree, preserving relative paths, so the output directory can safely be anywhere, including `./site`.
- For generated fallback config, use `pymdownx.slugs.slugify` so anchors such as `#ask--semantic-search` match docs that expect GitHub-compatible punctuation handling.
- Suppress Material for MkDocs' MkDocs 2.0 banner via its `NO_MKDOCS_2_WARNING` environment flag inside `docme` subprocesses.
- Include linked local files in fallback mode so images and other assets referenced by Markdown are present in the built site.
- Do not stage files outside the selected root. Rewrite those links to `file://` URLs and report them as skipped to avoid quietly publishing unrelated local files.
- Avoid strict MkDocs builds for ad hoc docs; report skipped links separately instead of aborting on warnings.
- Cap linked non-Markdown files at 25 MiB by default, configurable with `--max-linked-file-size-mib`.
- Use the same default visual baseline as the job-search docs for generated fallback sites: Material theme, slate palette, IBM Plex Sans text, and IBM Plex Mono code.

#### Verification
- Built a scratch Markdown tree with default depth and confirmed a depth-4 file was excluded.
- Rebuilt with `--depth 4` and confirmed the deeper file was included.
- Verified global dotfiles `just docs-deploy` can use `docme build --output <tmp>` and publish that output separately via webby.
- Built `/projects/job-search` and confirmed `docme` uses its `mkdocs.yml`; the previous anchor warnings disappear.
- Built a fallback scratch doc with `Ask — semantic search` and confirmed `#ask--semantic-search` resolves.
- Verified configured and fallback builds no longer print the Material MkDocs 2.0 banner.
- Built `/projects/toolbox` in fallback mode and confirmed linked media/static files are included while outside-root links are reported without aborting.

### Remeddy remote editor launcher

#### Goal
- Turn the remote editor launcher into a generic command that accepts a remote
  desktop SSH host, detects whether it is macOS or Windows, and opens the
  current directory via VS Code Remote-SSH.

#### Decision
- Rename the utility to `remeddy` for "remote editor".
- Use `remeddy <host> [app]` as the main interface. The optional app name
  defaults to `Visual Studio Code - Insiders`.
- Default `--platform` to `auto`. Probe macOS with `/usr/bin/uname -s`, then
  probe Windows with `powershell.exe` if the Unix probe fails.
- Treat VS Code-like apps (`code`, `codium`, `cursor`) as Remote-SSH editors.
  Those receive `--remote ssh-remote+<target> <path>` arguments.
- Treat other apps as ordinary GUI apps. On macOS this means `open -a <app>`;
  on Windows this means launching the executable without Remote-SSH arguments.
- For macOS Remote-SSH editors, use the app CLI from PATH or the normal app
  bundle locations instead of `open -a`, because `open` can simply activate an
  existing editor window and drop the Remote-SSH folder arguments.
- Default macOS Remote-SSH editor launches to `--new-window` unless
  `--reuse-window` is explicitly passed, so an unrelated already-open workspace
  is not reused accidentally.
- Keep explicit `--platform windows|macos` for debugging and dry-run cases where
  probing is not wanted.

## 2026-06-10

### Wined launcher

#### Goal
- Add a small command that can be run from any directory on this Linux machine
  to open that directory in VS Code Insiders running on a remote Windows desktop.
- Name the utility `wined`.

#### Decision
- Use SSH to the Windows host and run a short encoded PowerShell command there.
- Launch the GUI app through a short-lived interactive scheduled task. Direct
  `Start-Process` from Windows OpenSSH can run in the SSH service session and
  never appear on the logged-in desktop.
- Prefer `Code - Insiders.exe` over `code-insiders.cmd`; the batch wrapper can
  leave a foreground terminal window behind when launched from the task.
- Suppress PowerShell progress output and request text output format because
  Windows OpenSSH can otherwise print CLIXML progress records.
- Default the Windows SSH host to `ts-desktop-win`, matching the local SSH
  config, while allowing `CODE_INSIDERS_WINDOWS_HOST` or `--windows-host` to
  override it.
- Use VS Code Remote-SSH's CLI shape: `code-insiders --remote
  ssh-remote+<target> <path>`. The target defaults to this machine's hostname
  and can be overridden with `CODE_INSIDERS_REMOTE_TARGET` or `--remote-target`.
- Preserve the shell's logical `$PWD` when it points at the same directory as
  Python's current working directory, so symlinked project paths remain stable.

## 2026-06-04

### Cloudflare skill bundle

#### Goal
- Add Cloudflare's official Agent Skills to the canonical toolbox skill tree.

#### Discovery
- `cloudflare/skills` is the official upstream and documents compatibility with
  OpenAI Codex.
- The upstream repo has eight actual skill folders under `skills/`: `cloudflare`,
  `agents-sdk`, `durable-objects`, `sandbox-sdk`, `wrangler`, `web-perf`,
  `cloudflare-email-service`, and `workers-best-practices`.
- The README also lists build-agent/build-mcp entries, but those are command
  folders rather than skill folders.

#### Verification
- Added each Cloudflare skill through `bin/skillctl add` so `skills.toml` can
  refresh them later.
- Ran `bin/skillctl check`: 18 external skills, 14 custom skills.

### Summarize CLI wrapper

#### Goal
- Integrate steipete/summarize as a portable CLI helper and agent skill.

#### Decision
- Use `npx -y @steipete/summarize` through `bin/summarize` instead of vendoring a
  binary. This avoids platform-specific artifacts while keeping a stable command
  in the toolbox PATH.
- Keep the integration CLI-only. Do not install or configure daemon/browser
  extension mode unless explicitly requested later.
- Followed the local `agent-scripts` skill style: short quoted description,
  terse operational body, no grammar-heavy skill material.

#### Verification
- Confirmed local Node is v24.13.0 and npm is 11.6.2.
- Ran `bin/summarize --help` outside the sandbox; npm fetched
  `@steipete/summarize` and the CLI printed help successfully.

## 2026-06-03

### Web clipper

#### Goal
- Add a portable tool and skill that saves a URL as Markdown plus local media.
- Test first on the All Things Distributed storage-system article, which should
  produce hundreds of words and multiple images.

#### Discovery
- Steipete's `markdown-converter` skill uses MarkItDown for file/HTML
  conversion, but does not archive webpage media.
- Steipete's `browser-use` skill and `browser-tools.ts` are useful references
  for future rendered-page fallback, but the first implementation should not
  depend on an interactive browser session.
- Steipete's `summarize` CLI handles URLs/files/media and extract-only modes,
  but is summary-oriented rather than a folder-based web archive.

#### Initial design
- Add `bin/web-clip` as a Python CLI.
- Static-fetch public HTML, choose likely article/main content, convert common
  HTML structures to Markdown, download image media, and write `index.md`,
  `source.html`, and `media/`.
- Add `skills/web-clip` so agents know when and how to use it.

#### Verification
- Local file fixture: Markdown conversion, image download/rewrite, figure
  captions, links, lists, code, and source HTML preservation.
- Browser fixture: Playwright-rendered JavaScript page clips correctly outside
  the sandbox; the sandbox itself blocks Chromium launch.
- Required article:
  `allthingsdistributed.com/2023/07/building-and-operating-a-pretty-big-storage-system.html`
  clipped to ~6.6k words and 9 downloaded images with no mojibake.
- Extra smoke checks:
  `docs.python.org/3/library/urllib.parse.html` clipped to ~5.7k words;
  `aws.amazon.com/blogs/aws/amazon-s3-update-strong-read-after-write-consistency/`
  clipped to ~700 words and 2 images.

## 2026-06-02

### Simplified external skill registry

#### Decision
- Replace the broad all-skills manager with a shadcn-style TOML registry.
- `skills.toml` lists external Git sources only. Everything else under `skills/`
  is implicitly custom and edited directly.
- External skills are copied snapshots refreshed by `skillctl sync`.
- Omitted `path` means auto-detect common skill package layouts: repo root,
  `skills/<name>/`, `<name>/`, or the single obvious skill folder.
- Remove generated provenance docs, repo-backed symlinks, local clone caches,
  custom-skill records, revision records, and manager-owned deletion.
- Chezmoi in `devdocker/dotfiles` remains the sole distribution mechanism.

### Resume-session submit handling

#### Discovery
- `wezterm cli send-text` injects text rather than a dedicated key event.
- Sending a Claude Code prompt and `\r` in one write can populate the input box
  without submitting it.

#### Change
- Send prompt text and the submit carriage return as separate direct writes,
  with a short delay so the terminal UI processes them independently.
- Added a focused regression test and `just test-resume-session`.

### Declarative skill manager

#### Goal
- Replace hand-maintained vendored-skill provenance rows with a single
  machine-readable source of truth.
- Support authored skills, portable vendored snapshots, and local repo-backed
  symlinks without taking ownership of distribution.

#### Decisions
- `devdocker/dotfiles` chezmoi wiring remains the sole distribution layer.
- `skills.json` declares managed skills. `bin/skillctl` materializes external
  sources, validates the live tree, and generates `VENDORED.md`.
- `custom` skills remain tracked directories authored here.
- `vendored` skills remain tracked copies suitable for `git pull` portability.
- Existing vendored snapshots predate source-commit tracking, so their initial
  manifest revisions are explicitly `unknown` until deliberately refreshed.
- `repo` skills point into ignored `.skill-repos/` local checkouts and require a
  local `skillctl sync` after cloning toolbox on a new machine.
- Leave `skills/.system/` outside the manifest because Codex owns that hidden
  subtree and updates it independently.

## 2026-05-29

### Third-party skill management

#### What changed
- Removed the old `sync-skills.py` / `skills.yaml` tarball sync path.
- Evaluated `npx skills` (vercel-labs/skills) and **rejected it** as the manager.
- Settled on: vendor files + commit; `VENDORED.md` tracks provenance.

#### Why not `npx skills`
- It installs into each agent's skill dir (`~/.claude/skills`, `~/.codex/skills`,
  …). Here those are all chezmoi symlinks to this one `skills/` directory, so the
  tool's multi-agent fan-out either writes symlinks-into-the-repo (symlink mode)
  or redundant 4× copies (copy mode) — fighting the symlinks for zero benefit.
- Multi-agent distribution is already solved by the chezmoi symlinks. The only
  thing the CLI added beyond that was fetch-from-GitHub + a lockfile, both of
  which `just vendor` (plain git) + `VENDORED.md` cover without the conflict.
- Removed its `.skill-lock.json` and the `just skills-*` wrappers.

#### Current model
- `/projects/toolbox` is the canonical clone (on the shared `/projects` path, so
  containers see it via the existing bind mount — no per-container clone).
- `~/toolbox` and `~/.agents` are chezmoi symlinks to it; agent skill dirs symlink
  to `skills/`. chezmoi's `run_before_clone-toolbox` clones `/projects/toolbox`
  if absent (no-op when the bind mount already provides it in a container).
- Skills are plain dirs under `skills/`. Committing them IS the distribution.
- Third-party skills: `just vendor <owner/repo> <subpath> <name>` (or hand-copy
  for tool skills like `rdt-cli`), then record in `VENDORED.md`.

#### Follow-up
- Skills that wrap a CLI need the CLI installed separately (see VENDORED.md "Tool
  dependencies"). `rdt-cli` → `uv tool install rdt-cli`.
- Decide whether the untracked `agent-scripts/` clone (steipete reference repo,
  currently gitignored) should be vendored selectively or removed.
