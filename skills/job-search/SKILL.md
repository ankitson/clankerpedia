---
name: job-search
description: Self-hosted job-search tracker HTTP API — fetch/discover jobs, watch ATS boards, job status & fit, per-job resume tailoring, application questions, draft answers, autofill apply (draft-only).
---

# job-search

Self-hosted job tracker. REST, JSON in/out, no auth.

- Base: `https://jobs.dev.ankitson.com/api` (local: `http://localhost:9006/api`)
- Full spec: `GET /openapi.json` · browse: `/docs`
- IDs are ints. Dates ISO. Errors: `{error}` + 4xx/5xx.
- Never auto-submits applications — all "apply" steps draft only.

## fetch / discover jobs

- `POST /pipeline/sync` — poll watched boards + HN + X. → counts.
- `POST /pipeline/discover` — web-search new Canada-eligible postings. → `{added,dropped}`.
- `POST /jobs {company,title,posted_at,...}` — add one posting you've **already researched** (you have the fields). Stores your metadata as-is and, if `url`/`source_id` resolves to an ATS board, **links the company to that board and watches it** (first add only; aggregators skipped). This is the scan path.
- `POST /jobs/quick-add {"url"}` — add by URL when you have **only a link**; the server fetches + extracts it. If url is an ATS board/posting (Greenhouse/Lever/Ashby/Workable), **harvests the whole board AND watches it**.
- `POST /pipeline/tick` — one full background pass (sync+enrich+extract+fit).

**Adding from web/Exa search:** prefer the **canonical** posting URL (the company's
own ATS/careers page), NOT an aggregator/listing link (talent.com, himalayas,
remotive, builtin, linkedin, indeed, bebee, …). Aggregator URLs are accepted but
flagged `url_status='aggregator'` and auto-resolved server-side (web-search by
company+title → real posting) on the next enrich pass — so always pass an accurate
`company` and role `title`; resolution keys off them. Unresolvable ones end
`url_status='unresolved'` (visible badge, skipped by autofill).

## watch a job board / company

- ATS url → `POST /jobs/quick-add {"url"}` (auto-watches). Best path.
- Manual: find company `GET /companies` → `PATCH /companies/{id} {"watch":1,"ats_type":"greenhouse","ats_board":"<slug>"}`.
  ats_type ∈ greenhouse|lever|ashby|workable|jobvite. Then `POST /pipeline/sync`.

## status of jobs

- List/search: `GET /jobs?q=<text>&status=<s>&canada=<yes|likely|no>&sort=<priority|score|posted|added>&limit=`.
  q = full-text (title/JD/tech). → array w/ `fit_score,fit_verdict,status,company,title`.
- One job (full): `GET /jobs/{id}` → job + `fits,form,answers,notes,history,dossier`.
- Counts: `GET /stats` (by_status, by_canada, …). Natural-language: `POST /ask {"q"}`.
- statuses: inbox interested applied interviewing offer rejected ghosted passed archived.
- Set status: `PATCH /jobs/{id} {"status":"interested"}`. Note: `POST /jobs/{id}/notes {"body"}`.

## tailor a resume + read application questions

Prep (idempotent): `POST /jobs/{id}/enrich` (full JD) → `POST /jobs/{id}/extract` (fields) → `POST /jobs/{id}/fit?profile=<id>` (score+tips, optional but feeds the resume).

- Profiles: `GET /profiles` → `{profiles:[{id,is_default}],default}`.
- Generate resume: `POST /jobs/{id}/kit/generate {"kind":"resume","profile":"<id>"}` → `{name,content,profile}`. `kind:"cover-letter"` too.
- List kit files: `GET /jobs/{id}/kit` → `{files:[{name,profile,submitted_at}]}`.
- Read one: `GET /jobs/{id}/kit/file?name=resume.v1.md`. PDF: `POST /jobs/{id}/kit/pdf {"name"}` → application/pdf.
- **Extracted questions**: `GET /jobs/{id}` → `.form.questions` = `[{key,label,type,required,options}]`; `.answerable` = count worth drafting (greenhouse/ashby only).

## apply (draft-only)

- Draft answers: `POST /jobs/{id}/answers?profile=<id>` → answers; read via `GET /jobs/{id}` `.answers` (`state`: draft|edited|final). Edit: `PATCH /answers/{aid} {"answer","state"}`.
- Autofill the live form (fills drafts in a browser, **never clicks submit**): `POST /jobs/{id}/autofill`.
- After you submit by hand: `POST /jobs/{id}/kit/submitted {"name"}` then `PATCH /jobs/{id} {"status":"applied"}`.

## recipes

```bash
B=https://jobs.dev.ankitson.com/api
# top fits in the inbox
curl -s "$B/jobs?status=inbox&sort=score&limit=10" | jq -r '.[]|"\(.fit_score) \(.company) — \(.title) #\(.id)"'
# tailor + show questions for job 1354
curl -s -XPOST "$B/jobs/1354/enrich"; curl -s -XPOST "$B/jobs/1354/extract"
curl -s -XPOST "$B/jobs/1354/kit/generate" -d '{"kind":"resume","profile":"default"}' -H content-type:application/json | jq .name
curl -s "$B/jobs/1354" | jq '.form.questions[]|{label,type,required}'
curl -s -XPOST "$B/jobs/1354/answers" | jq -r '.[]|"Q \(.question)\nA \(.answer)\n"'
```
