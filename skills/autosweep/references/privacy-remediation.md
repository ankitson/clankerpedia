# Privacy remediation playbook

This is the part of the sweep with no human in the loop, so it's where care
matters most. The goal isn't to *block* commits — the user explicitly prefers
remediation over skipping — it's to make every change safe to publish by moving
the sensitive bit somewhere appropriate and leaving a working reference behind.

Run `scripts/privacy-scan.py <repo>` first. It returns:
- `conventions`: what secret machinery the repo already uses (`uses_op_refs`,
  `has_secrets_dir`, `has_tmpl`, `gitignores_env`) — match these.
- `findings`: redacted hits with `category`, `file`, `line`, `hint`.

After remediating, **re-run the scan** until clean. Then commit.

## Golden rules
- **Never commit a raw secret.** This is the one hard stop. If you can't move it,
  skip the hunk and flag it — do not commit it.
- **Prefer the repo's existing convention** over inventing a new one. A repo that
  renders `*.tmpl` with `{{ op://… }}` wants another `op://` ref, not a `.env.secret`.
- **A reference is not a leak.** `op://vault/item/field`, `env.FOO`, `${FOO}`,
  `{{ op://… }}`, `=none`, `<placeholder>` are all safe — the scanner already
  ignores them. Your remediation should produce one of these.
- **Keep the code working.** When you move a value out, leave the equivalent
  reference in place and, if needed, add the real value to the gitignored side so
  the user's local setup still runs.
- **When genuinely unsure** whether something is sensitive (especially nsfw), ship
  the PR — a human reviews before merge. Reserve hard handling for clear secrets.

## By category

### secret
Decide where the real value should live, by repo convention:

1. **Repo uses `op://` refs / `*.tmpl`** (`uses_op_refs` or `has_tmpl`): replace the
   literal with an `op://` reference in the template file, mirroring siblings. If a
   matching 1Password item doesn't obviously exist, use a clearly-named ref and note
   it in the PR body as "needs a vault item" rather than guessing a path.
   ```
   - API_KEY=sk-live-abcd1234efgh5678
   + API_KEY={{ op://clankers/<item>/password }}
   ```
2. **Repo gitignores `.env` / has `secrets/`** (`gitignores_env`/`has_secrets_dir`):
   move the value into the gitignored file and reference it by env var in code.
   ```
   # code
   - const key = "sk-live-…";
   + const key = process.env.API_KEY;
   # .env.secret  (gitignored — NOT committed)
   API_KEY=sk-live-…
   ```
3. **No convention yet**: create `.env.secret`, add it to `.gitignore` (commit the
   `.gitignore` change), move the value there, reference via env var. This
   establishes a convention the repo can keep using.

Always confirm the destination file is actually ignored (`git check-ignore <file>`)
before writing a real secret into it.

### tailnet (`*.ts.net`)
The tailnet name identifies the user's private network. Replace it:
- **Config/code** that needs a real value at runtime → env var or the repo's secret
  convention (`TAILNET_HOST`, or an `op://`/`.env.secret` entry).
- **Docs / comments / examples** → a generic placeholder reads fine:
  `https://<tailnet-host>/…` or a real tailnet host → `your-tailnet.ts.net`.
- A bare hostname used as a service address in committed config → prefer an env var
  so the published file carries no real host.

### ip
Judgment call by what the IP is:
- **Private/LAN** (`192.168.*`, `10.*`, `172.16–31.*`) or a public IP that is
  clearly the user's box → treat like tailnet: env var or placeholder.
- **Well-known/unidentifying** (already filtered: `0.0.0.0`, `127.0.0.1`, public
  DNS like `1.1.1.1`/`8.8.8.8`) → the scanner won't flag these; if something
  similar slips through and is plainly not the user's, it's fine to keep.
- Docs/examples → `<ip>` or a `192.0.2.x` (RFC 5737 documentation range) placeholder.

### sensitive
A hit against `sensitive-terms.txt` (the gitignored denylist beside the skill) —
usually just a vague model-name reference, not explicit content. Lightest touch
that keeps the public artifact clean:
- **Config/env** → move the name to `.env.secret` and reference by env var.
- **README / docs** → swap for a neutral example model (`example/model-name`) or
  drop the specific name.
- **Genuinely ambiguous** → ship the PR; a human will catch it in review.

## After remediation
- Re-run `privacy-scan.py`; confirm `findings` is empty (or only intentional,
  explained residue remains).
- In the PR body, add a **"Privacy remediations applied"** section listing what was
  moved/replaced (by category and file — never the secret value), plus anything
  skipped and why, so the reviewer knows exactly what changed and what still needs
  a human.
