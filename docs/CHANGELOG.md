# Toolbox Changelog

## 2026-08-02

### td-reschedule-overdue: keep daily catch-up on today

- Changed overdue daily tasks to use a recurrence-safe full-datetime
  reschedule to today's calendar occurrence instead of re-sending the rule,
  which silently skipped today.
- Kept non-daily occurrence advancement intact and strengthened post-write
  verification to require the exact daily destination and time-of-day.
- Added focused regression coverage, a Justfile test command, corrected the
  Todoist CLI skill, and documented the live API behavior and incident.

## 2026-07-26

### wezterm-session: retained layout backup and restore

- Added `bin/wezterm-session`, which saves the live WezTerm window/tab/split
  layout, directories, workspaces, and tab titles; it retains four snapshots
  by default and restores fresh login shells into the saved layout.
- Added a user-level systemd timer that invokes the backup every 15 minutes.
  It safely skips an interval when no WezTerm mux is available.

## 2026-07-24

### todoist-cli: verified recurrence-preserving reschedule

- Replaced the stale warning that egress policy blocks every reschedule with
  verified guidance to use `td task reschedule` for recurring tasks.

## 2026-07-17

### x-research: Bird CLI route

- Added the external `bird` skill from `windhood-jza/openclaw-bird-skill`.
- Switched `x-research` to Bird while retaining its research workflow for
  query decomposition, thread follow-up, source verification, and synthesis.

### web-search: routing layer and browser fallback

- Added the custom `web-search` skill as the canonical routing policy for web
  research, with SearXNG as the default discovery backend.
- Renamed the imported browser-driven search skill to `browser-web-search`,
  made it an explicit Google/DDG fallback, and retained its upstream registry
  record as a local fork so future syncs preserve the routing-specific edits.
- Disabled automatic invocation for `searxng` and `browser-web-search`; the
  `web-search` router explicitly selects them when warranted.
- Made every Toolbox route a relative sibling-skill pointer rather than an MCP
  reference or a hardcoded implementation command.

## 2026-07-14

### chatterbox-tts: local text-to-speech skill

- Added `skills/chatterbox-tts`, which produces local audio files through the
  OpenAI-compatible Chatterbox `/v1/audio/speech` endpoint.
- Defaults to model `chatterbox` and voice `Alice`, with per-request and
  environment-based endpoint, model, and voice overrides.
- Added an atomic, standard-library Python client with text-file input, output
  format, and speech-speed options.

### disk-space-audit: host-aware disk and model cleanup

- Expanded `skills/disk-space-audit/SKILL.md` with the homeserver filesystem
  map, Compose sources, Docker orphan/shared-layer classification, and explicit
  locations to inspect for logs, databases, caches, and model weights.
- Added a verified cross-filesystem model-move workflow and the convention that
  container model storage belongs under `/mnt/store-ext4/models`.
- Kept `disable-model-invocation: true`; the skill must be invoked explicitly.

### parakeet-asr: reusable OpenAI-compatible transcription skill

- Added `skills/parakeet-asr`, a shared audio-transcription skill for Parakeet
  behind Bifrost or another OpenAI-compatible `/audio/transcriptions` endpoint.
- Added configurable endpoint, credential, and model environment variables plus
  language, prompt, JSON, and output-path options.
- Made writes atomic and normalized compatible API responses that return a JSON
  `text` field despite requesting plain text, preventing API failures or JSON
  wrappers from becoming bogus `.txt` transcripts.

## 2026-07-11

### frag: standalone fragment-composition utility + AGENTS.md compose
- Added `bin/frag` (uv + PEP 723; jinja2): a generic tool that renders a Jinja
  template to stdout (or `-o FILE`, atomic), resolving `{% include %}` against
  `-I` search dirs. Knows nothing about toolbox/profiles — reusable for any
  fragment-assembly job. Supports `-` (stdin template) and
  `{% include "x" ignore missing %}`.
- Added `context/fragments/{security,core,routing}.md` and
  `context/templates/AGENTS.md.j2`. The template inlines the per-host
  `~/AGENTS.env.md` (chezmoi output) and the machine index
  `~/hroot/allplace/wiki/INDEX.md` between `<!-- BEGIN/END generated -->`
  markers. `security.md` rescues the secrets-redaction rules that previously
  existed only in a drifted `/home/ankit/AGENTS.md` hand-copy.
- `AGENTS.md` is now a composed artifact (header comment says so); the
  Claude-only `@~/AGENTS.env.md` import is gone — env + machine index are
  inlined for every harness. `just agents` runs the compose (`bin/frag
  context/templates/AGENTS.md.j2 -I context/fragments -I ~ -I
  ~/hroot/allplace/wiki -o AGENTS.md`); toolbox-specific wiring lives in the
  recipe, not the tool.

## 2026-07-01

### untangle: new skill for extracting publishable repos from personal tangle
- Added `skills/untangle/SKILL.md`: a process skill for turning code tangled in
  personal infrastructure into a stranger-runnable module, repo, package, or
  product. Phases: qualify demand → find the seam (second-user test,
  parameterize/adapt/cut lists) → stranger-README first → extract with cold
  tests and fresh git history → privacy scrub → cold-clone verification →
  report with the remaining productization rungs.
- Names the four recurring personal adapters (devbox exec, Bifrost, OpenClaw,
  AgentsView) so extractions treat them as interfaces with the personal setup
  as the reference implementation.
- Ends with a `# human version (agents skip this)` section — a brief
  Ankit-tailored summary; agents consuming the skill should skip it.

## 2026-06-30

### wezterm-sync: one-ref build + deploy across all hosts
- Added `bin/wezterm-sync`, a Python orchestrator that builds a custom wezterm
  from one canonical git ref and deploys it natively to every host that talks to
  the mux (server = Linux, `m2book` = macOS, `desktop-win` = Windows).
- Binaries are not portable across os/arch, so each host fetches the exact commit
  from `origin` and builds it *over ssh*; we install into each platform's wezterm
  path with a timestamped backup and verify the resulting `--version`.
- Server builds in an isolated `git worktree` (shared `CARGO_TARGET_DIR`) so the
  working branch is never disturbed; macOS re-signs the bundle ad-hoc.
- Windows uses a `.tag`-seeded source tarball (no git clone) built on the server
  and a shipped `bin/wezterm-build-windows.cmd` that encodes the toolchain recipe
  (VsDevCmd, Strawberry Perl, rustup-shim bypass) and assembles the portable
  `WezTerm-windows-<tag>\` bundle (exes + ANGLE/mesa DLLs) under `wezterm-builds`.
- **First real run (2026-06-30):** deployed the blessed custom build
  (`fix/panefocused-client-focus-metadata` @ `06c71b67`, 5 PaneFocused
  focus-metadata commits on top of upstream) to server, `m2book`, and
  `desktop-win`. All three now report `wezterm 20260625-133254-06c71b67`. Fixed
  three bugs the run surfaced: an scp destination wrapped in literal quotes
  (broken with no intervening shell), `bash -lc` ssh wrapping that split `&&`
  chains apart, and git-mode hosts not seeding `.tag` (stale embedded version on
  incremental builds — `wezterm-version/build.rs` only re-reads `.tag` when
  `build.rs` itself is touched, since its `rerun-if-changed` is keyed to the HEAD
  ref file, which a detached checkout doesn't change). Also fixed the Windows
  batch: the `cmd /c ""..."" ` wrapper corrupted `%SRC%`'s quoting and silently
  packaged an empty bundle while still exiting 0; added a post-package
  existence check so that fails loudly, and moved `CARGO_TARGET_DIR` outside the
  re-extracted source tree so reruns build incrementally.
- Safe by default: dry-run unless `--apply`; never restarts the live mux unless
  `--restart-mux`; unreachable hosts are skipped, not fatal.
- Justfile: `just wezterm-sync` (plan) and `just wezterm-sync-apply [ref]` (deploy).

## 2026-06-27

### AgentsView search API documentation
- Updated `skills/agentsview-api/SKILL.md` to use the dedicated
  `/api/v1/search` endpoint for transcript content search.
- Documented the search response shape, including `results[].session_id`,
  snippet fields, `count`, and `next`.
- Fixed the transcript formatting example to read from `.messages[]` and pass a
  larger message `limit` for long sessions.

## 2026-06-24

### Document work chronology
- Normalized `docs/CHANGELOG.md` and `docs/NOTES.md` to use reverse
  chronological day sections with one `## YYYY-MM-DD` header per day.
- Updated `skills/document-work/SKILL.md` so future work logs group multiple
  same-day changes under a single date header.

### Chezmoi skill safety
- Reworked `skills/chezmoi-skill/SKILL.md` so agents preview changes and get
  explicit user consent before applying to live dotfiles.
- Removed broad `Bash(chezmoi *)` guidance and replaced it with narrower
  command patterns focused on previews, source lookup, source updates, and
  noninteractive targeted apply.
- Replaced routine `chezmoi apply --refresh-externals --force` guidance with
  consent-gated `chezmoi apply --no-tty <target...>` and last-resort force
  language.

### Network listener audit helper
- Added `bin/network-listeners` to audit TCP/UDP sockets from `ss`, grouping
  listeners by wildcard binds, LAN/private IP binds, Tailscale-only exposure,
  and other non-loopback interfaces.
- Text output filters binds to the relevant section and wraps wide cells so
  mixed-interface services do not create unreadable table rows.
- Consecutive listener runs of five or more ports with the same protocol,
  process name, bind pattern, and notes are collapsed into one range row.
- Text output now groups rows by process name by default; use
  `--no-process-groups` to show the protocol/port table.
- Added focused parser/classification tests plus `just network-listeners` and
  README usage notes.

## 2026-06-22

### WezTerm Windows freeze tracing
- Added `bin/wezterm-win-trace` to capture Windows-side WezTerm GUI diagnostics
  over SSH, including process samples, hot thread state, command line, log file
  inventory, optional minidump capture, and optional WPR CPU traces.
- Added `just wezterm-win-trace` and README usage notes for pairing Windows GUI
  traces with the existing Unix mux-side `bin/wezterm-trace`.

## 2026-06-19

### Autoresearch skill
- Added `skills/autoresearch` from `uditgoenka/autoresearch` at upstream commit
  `166755a2600a`.
- Registered the external source in `skills.toml` with `ref = "master"` and
  `path = ".agents/skills/autoresearch"` so future `skillctl sync` runs can
  refresh it.

### Summarize output copies
- Changed `bin/summarize` to stream stdout as before while saving successful
  stdout-producing runs under `/tmp/summarize/`.
- Added timestamped saved-file names that distinguish summaries from
  `--extract` transcript/source output.
- Updated the summarize skill guidance, OpenAI agent metadata, and README usage
  notes to mention saved output copies.
- Added focused regression coverage for saved stdout copies and a
  `just summarize-test` helper.

## 2026-06-18

### Skill router generation
- Added `bin/skillctl router` to generate a portable router skill from installed
  skills by explicit skill names, `skills.sh.json` group titles, or glob
  source-group labels.
- Added `skills.toml` router tables with `absorbs = ["repo:path"]` entries as
  the authoritative source for bundled skill provenance.
- Added generated root `skills.sh.json` output using the existing Skills.sh
  grouping convention.
- Added `templates/skillctl/router.SKILL.md`, rendered with stdlib
  `string.Template`, so router wording lives outside the Python CLI.
- Added `just skills-router` and README examples for explicit, group-based, and
  source-group router generation.
- Made `skillctl sync` sync standalone sources first, then materialize all
  routers and absorb their component skills from the active top-level skill
  tree by default.
- Changed bundled router references from nested `SKILL.md` files to
  `instructions.md`, preventing recursive skill scanners from showing duplicate
  skills.
- Added `skills/minimalist-entrepreneur`, generated from the
  `Minimalist Entrepreneur` group with ten absorbed reference skills.
- Added absorbed `cloudflare` and `agent-workflows` routers. `zoom-out` is kept
  via a local vendored copy from historical upstream commit
  `801a01cc7d265e06dd9dbcef5a4c471add05a0b3`.
- Added regression coverage for router generation, copied references, source
  marker exclusion, explicit skill selection, `skills.sh.json` groups, and
  overwrite/absorb protection.

## 2026-06-15

### Serializd review fixes
- Fixed `review-add` failing with `500 Internal Server Error`: Serializd's
  `reviews/add` endpoint requires both `backdate` and `rating`, but the payload
  builder stripped any field that was unset. `backdate` is now always sent,
  defaulting to the current time (bare dates like `2024-01-15` are expanded to a
  full ISO 8601 datetime).
- Made `--rating` required for `review-add` and stopped silently sending a `0`;
  an explicit `--rating 0` is still accepted and recorded as "unrated".
- Forced every review the CLI writes to be logged (`is_log` is no longer
  user-toggleable). Unlogged reviews never appear in the diary or logged-episode
  lists, so they can't be found, updated, or deleted from any Serializd surface —
  the CLI no longer creates that orphaned state. Removed the `--log`/`--no-log`
  flags accordingly.
- Improved HTTP error reporting across all requests: errors now include the
  method, URL, status, reason, and server response body, and flag `5xx` as a
  server-side failure and `429` as rate limiting.

## 2026-06-12

### Docme
- Generated fallback sites now always include a `Docs` listing page.
- When a project already has a root `README.md` or `index.md`, `docme` keeps that homepage and writes the listing to `docs.md` or the next available fallback name.

## 2026-06-11

### Docme
- Added `bin/docme`, a PEP 723 `uv run --script` tool for building or serving a quick MkDocs Material site from Markdown files.
- `docme` scans all `.md` files under the current directory up to depth 3 by default; `--depth` and `--root` make the scan configurable.
- `docme build --output DIR` writes the built site to a configurable output directory and does not know about webby or deployment.
- `docme` uses an existing `mkdocs.yml`/`mkdocs.yaml` in the root directory before falling back to generated Markdown staging.
- Generated fallback config uses the `pymdownx.slugs.slugify` GitHub-compatible slugifier so hand-written anchors with punctuation resolve.
- `docme` sets `NO_MKDOCS_2_WARNING=true` for MkDocs subprocesses to suppress Material's MkDocs 2.0 banner while preserving normal build output.
- Fallback staging now includes local files linked from Markdown, using symlinks where possible and copies as a fallback.
- `docme` no longer runs MkDocs in strict mode; skipped missing, outside-root, or over-size linked files are reported separately.
- Added a configurable linked-file size cap, defaulting to 25 MiB via `--max-linked-file-size-mib`.
- Generated fallback sites default to Material's slate palette with IBM Plex Sans text and IBM Plex Mono code fonts.

### Remeddy remote editor launcher
- Renamed the utility to `bin/remeddy`.
- Changed the CLI to `remeddy <host> [app]`, defaulting the app to
  `Visual Studio Code - Insiders`.
- Added remote OS auto-detection over SSH, probing macOS with `uname` and
  Windows with `powershell.exe`.
- Split app handling between Remote-SSH editors and generic GUI apps, so
  commands like `remeddy m2book Spotify` launch the app without VS Code flags.
- Changed macOS launch behavior to use the `code-insiders` CLI and default to a
  new window, avoiding `open -a` activating an unrelated existing workspace.
- Added Windows, macOS, app override, and platform override regression coverage.

## 2026-06-10

### Wined launcher
- Added `bin/wined`, which SSHes to a Windows host and starts VS Code
  Insiders with a Remote-SSH window pointed at the current machine and directory.
- Changed launch behavior to use a short-lived interactive scheduled task so
  the app appears in the logged-in Windows desktop session.
- Preferred the GUI `Code - Insiders.exe` over `code-insiders.cmd` to avoid
  leaving a foreground terminal window behind.
- Suppressed PowerShell CLIXML progress noise from Windows OpenSSH.
- Added focused unit coverage for command construction and argument validation.
- Added `just test-wined` for the focused regression test.

## 2026-06-04

### Cloudflare skills
- Added Cloudflare's official external skills from `cloudflare/skills`.
- Registered `cloudflare`, `agents-sdk`, `durable-objects`, `sandbox-sdk`,
  `wrangler`, `web-perf`, `cloudflare-email-service`, and
  `workers-best-practices` in `skills.toml`.
- Copied the skill folders into `skills/` so the existing Codex skills symlink
  can discover them.

### Summarize CLI integration
- Added `bin/summarize`, a Node 24+ preflight wrapper around
  `npx -y @steipete/summarize`.
- Added `skills/summarize` with terse CLI-only usage guidance for agents.
- Added `just summarize` and README usage examples.

## 2026-06-02

### Resume-session submit handling
- Changed `bin/resume-session` to send scheduled prompt text and the submit
  carriage return separately, with a short delay between writes.
- Added a regression test and a `just test-resume-session` command.

### Simplify skill registry
- Replaced `skills.json` with `skills.toml`, listing external Git sources only.
- Reduced `bin/skillctl` to add, sync, list, and check copied snapshots.
- Removed generated `VENDORED.md`, repo-backed symlinks, clone caches, custom
  skill records, revision records, and manager-owned deletion.
- Treat every unlisted directory under `skills/` as an ordinary custom skill.
- Added repo-only `skillctl add owner/repo` support with default-path detection
  for root skills, `skills/<name>/`, `<name>/`, and single-skill repos.

### Web clipper
- Added `bin/web-clip`, a URL-to-Markdown folder clipper that stores `index.md`,
  fetched `source.html`, and downloaded image media.
- Added `skills/web-clip` with usage guidance for clipping/archive requests.
- Added a `just web-clip <url> [output]` recipe.
- Added file-URL test coverage and optional Playwright `--browser` mode for
  JavaScript-rendered pages.
- Verified the required All Things Distributed article, Python docs, and an AWS
  blog smoke case.

### Declarative skill manager
- Added `skills.json` as the source of truth for custom, vendored, and
  repo-backed skills.
- Added `bin/skillctl` to add, sync, remove, list, validate, and document skills.
- Replaced manual edits to `VENDORED.md` with generated provenance docs.
- Replaced the destructive one-off `just vendor` recipe with `just skills-*`
  manager commands.
- Added local-Git regression coverage for custom, vendored, and repo-backed
  workflows and overwrite guardrails.
- Documented the ownership boundary: `devdocker/dotfiles` chezmoi wiring handles
  distribution; toolbox only manages canonical skill contents and provenance.

## 2026-05-29

### Skill management cleanup
- Removed the old `sync-skills.py` + `skills.yaml` sync system.
- Evaluated and rejected `npx skills` (vercel-labs/skills) as the manager: it
  installs into per-agent skill dirs, which here are all chezmoi symlinks to this
  one directory — it would fight the symlinks for no gain (multi-agent
  distribution is already solved by the symlinks). Removed its `.skill-lock.json`
  and the `just skills-*` wrappers.
- New flow: skills are plain files under `skills/`; committing them IS the
  distribution. Third-party skills are vendored via `just vendor` (plain git) and
  their sources tracked in `VENDORED.md`.
- Vendored `rdt-cli` (Reddit CLI skill) — requires `uv tool install rdt-cli`.
- `/projects/toolbox` is the canonical clone; `~/toolbox` and `~/.agents` are
  chezmoi symlinks to it; agent skill dirs symlink to `skills/`.
