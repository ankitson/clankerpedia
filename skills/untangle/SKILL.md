---
name: untangle
description: Extract a general, publishable repo/module/product from code tangled in personal infrastructure. Use when asked to extract, productize, open-source, "spin out", "make shareable", or untangle a project or piece of one.
---

# Untangle

Turn a piece of working-but-tangled personal software into something a stranger can run: a module, a standalone repo, a published package, or a sellable service.

Core doctrine: **products are extracted, not built.** Tangle is evidence the code solves a real problem; the job is to find the seam between the general core and the personal installation, and freeze the core out. Never rewrite from scratch — extract from the working thing.

## Phase 0: Qualify

Most personal software should stay personal. Before extracting, confirm with the user:

- What is the demand signal? (Someone asked for it, a recurring complaint it solves, a gap the user verified.) If none, recommend the smallest publishable artifact (often a writeup, not code) and stop.
- What is the target rung? Module inside the repo → standalone repo → published package → hosted service → paid product. Extract to the **lowest rung the demand justifies**. Each rung adds maintenance cost forever.

## Phase 1: Find the seam

Run the **second-user test**: enumerate everything that would have to change for one other person to run this. Search the code for:

- Hardcoded paths (`/home/<user>/...`, workspace roots, helper-script paths)
- Hostnames and network assumptions (tailnet hosts, LAN IPs, `docker exec <container>`, SSH targets)
- Personal services behind the code. Common touchpoints in this environment: sandbox execution (agent-devbox), model gateway (Bifrost), messaging (OpenClaw), trace sink (AgentsView). Each is an **adapter**, not a dependency.
- Account-specific values: repo owners, emails, API key conventions (`op://` refs), model ids
- Sibling-repo imports and toolbox skill paths

Everything found goes on one of three lists: **parameterize** (config with a sane default), **adapt** (define an interface; the personal setup becomes the reference implementation, kept on the private side), or **cut** (not part of the product). If the general core disappears when the lists are applied, report that — there is no product here, only configuration.

## Phase 2: Stranger-README first

Before moving any code, write the README for someone who has never seen the user's infrastructure:

1. The problem, in the stranger's terms (not the user's incident history)
2. What it does, in one paragraph
3. Install + a `just demo` (or equivalent) that works on a fresh clone with no personal services
4. Configuration/adapter docs

Any sentence that cannot be written without explaining the personal infrastructure marks something that belongs on the parameterize/adapt/cut lists. Iterate until the README holds. The README is the spec for the extraction; do not skip to code.

## Phase 3: Extract

- Create the new module/repo. **Fresh git history for new repos** — do not port tangled history (it may reference private hosts, paths, or incidents).
- Move the general core; implement adapters as interfaces with (a) a null/local implementation used by tests and the demo, and (b) the user's personal implementation living outside the published artifact.
- Tests and the demo must run **cold**: no Docker containers assumed, no tailnet, no secrets, no network beyond package installs. If the core can't be tested cold, the seam is in the wrong place — move it.
- Follow the standard conventions: uv + PEP 723 or pyproject for Python, bun + TypeScript for JS, a Justfile with `check`, `test`, `demo`.

## Phase 4: Scrub

- Privacy pass over every file and the README: tailnet hosts, private IPs/CIDRs, secrets, `op://` refs, personal emails/hostnames, sensitive model/content names. Use the autosweep privacy-scan script (`/home/ankit/toolbox/skills/autosweep/scripts/privacy-scan.py`) when available; grep manually otherwise.
- Check example/fixture data too — planted "realistic" values must be documentation-safe (`example.com`, RFC 5737 IPs, `your-tailnet.ts.net`).
- Names: strip internal codenames the stranger doesn't need (project-internal identities, run-id schemes) unless they're part of the product.

## Phase 5: Verify cold

The acceptance test, non-negotiable: **fresh clone in a clean directory, follow the README exactly, `just demo` and `just test` pass** without touching any personal service. Do this literally — a fresh `git clone` into a temp dir, not the working checkout. If any step needed knowledge not in the README, fix the README or the code and repeat.

## Phase 6: Report

Deliver to the user:

- The seam lists (parameterized / adapted / cut) — this is the explanation of the product boundary
- Cold-clone verification transcript (commands + outcomes)
- Remaining rungs: what publishing/packaging/selling at the next rung would additionally require
- Suggested announcement skeleton (problem → pattern → demo), since the accompanying writeup often travels further than the code

Do not publish, push to public remotes, or register packages without explicit user approval.

# human version (agents skip this)

You don't have a "builds messy" problem; you have an extraction muscle you haven't trained. The tangle is ore. Water and ice, one level up: extraction is freezing a repo out of your infrastructure, and like every freeze it needs a verifier — here, the cold-clone test: *could a stranger run `just demo` from a fresh clone with none of your machines alive?* That single question does most of the work of this whole skill.

Your personal infra touches everything through the same four sockets: devbox exec, Bifrost, OpenClaw, AgentsView. Treat them as adapters with "ankit" as the first implementation and most of the tangle falls away by itself. You already do this when forced (`AZIMUTH_OPENCLAW_CMD`, the `openai+http://...#model` URIs) — just do it on purpose.

Two habits: write the stranger-README *before* extracting (NOTES.md is your work log, it's great, but it's for you — the README is a different genre and it's the actual test of whether you understand what you built); and demand one signal of external interest before polishing anything (a post, a reply, one person asking). Most things should stay personal — that's fine, it's not failure.

First rep: `bench/` out of autosweep-spike. Generator + scorer + a README that never says "autosweep". Weekend-sized, real demand (everyone has the no-metric problem), and you can hand this very skill to an agent and grade its output with the cold-clone test. The essay ("water and ice") is the other product hiding in this month — doctrines port even when code doesn't.
