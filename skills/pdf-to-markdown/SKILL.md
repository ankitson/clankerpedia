---
name: pdf-to-markdown
description: Transcribe a PDF into Markdown faithfully — worksheets, workbooks, forms, handouts, reports, scanned documents, slide decks. Use whenever the user wants a PDF turned into Markdown or notes, wants a document "in the vault"/"as a note", wants text or tables or diagrams pulled out of a PDF, or wants a filled-in form's answers recovered. Also use when the user says a previous extraction "missed things" or "editorialized". Reach for this even when the PDF looks like plain text — filled form fields and image-only pages are invisible to naive extraction and are the usual cause of silent data loss.
---

# pdf-to-markdown

A PDF is three overlapping documents: a **text layer**, an **image layer**, and — for
anything fillable — an **AcroForm data layer**. Naive extraction reads the first and
silently drops the other two. That failure is quiet: you get pages of plausible
Markdown and no error, so the omission surfaces only when the person who owns the
document reads it and spots their own answers missing.

The whole job is making sure all three layers land in the output.

## Decide the mode first

Before extracting anything, settle what the user wants — the two modes need different
source handling, and guessing wrong means redoing the work:

- **Transcript** — page-by-page, verbatim, blanks preserved. For worksheets, forms,
  contracts, anything the user will fill in, act on, or compare against the original.
- **Notes** — reorganized, condensed, summarized. For reference material the user
  wants to absorb rather than reproduce.

If the request is ambiguous ("put this in my vault", "make a markdown version"), ask.
When a user says "all of it", they mean transcript. If the PDF is a fillable
worksheet, default to transcript — the blanks *are* the content.

Producing both is reasonable for a document someone is actively working through: a
verbatim transcript to work from, and a condensed note to think with. Keep them in
separate files and cross-link.

## Workflow

### 1. Probe before you read

```bash
scripts/pdf_probe.py FILE.pdf              # per-page: text volume, figures, form fields
scripts/pdf_probe.py *.pdf --summary       # triage a batch
```

This tells you which pages have a real text layer, which are image-only, and whether
there is form data hiding in the file. Read the output before deciding anything else —
it is the difference between a 20-minute job and a redo.

### 2. Pull the text layer

```bash
pdftotext -layout FILE.pdf out.txt
```

`-layout` preserves column alignment, which is what lets you see that a stray column
of numbers belongs to a checklist rather than a table. This text is your verbatim
source — read it directly rather than paraphrasing from memory.

### 3. Recover form field values — the step everyone skips

```bash
scripts/pdf_probe.py FILE.pdf --fields       # every field: page, position, value
scripts/pdf_probe.py FILE.pdf --checkboxes   # checkboxes top-to-bottom per page
```

Filled fields frequently do not appear in `pdftotext` output, and **checkbox states
routinely render as empty boxes in every PDF viewer** while carrying a real value in
the file. Someone's answers can be fully present in the data and fully invisible on
screen.

Field names are opaque (`checkbox_67edgr`), so a value alone doesn't tell you what it
answers. `--checkboxes` sorts by vertical position, letting you walk the printed list
in the same order and map each state to its label. Verify the mapping against the item
spacing rather than assuming — lists often have a tight group followed by a loose one,
and the y-gaps will show you where the groups break.

### 4. Read image-only pages as images

Pages flagged `SPARSE-TEXT` carry their content as pixels. Render and actually look
at them:

```bash
pdftoppm -r 110 -png -f 7 -l 7 FILE.pdf /tmp/pg   # single page
```

110–150 dpi is enough to read comfortably. There is no shortcut here: a decision tree
or a labelled diagram has to be looked at to be transcribed.

### 5. Extract figures as cropped page regions

```bash
scripts/pdf_figures.py FILE.pdf OUTDIR --prefix week1 --dry-run   # preview bands
scripts/pdf_figures.py FILE.pdf OUTDIR --prefix week1
```

Crop the rendered page rather than pulling raw rasters with `pdfimages` — captions,
axis labels, and any marks a reader drew on top are separate objects layered over the
image, so raw extraction yields unlabelled blobs. The script filters repeating header
logos and merges adjacent bands.

Then **view every crop and rename it descriptively** (`week1-p11-fig1.png` →
`adhd-management-wheel-example.png`). Filenames are what a future reader sees. Delete
decorative crops — stock photography, product logos, clip art, portrait illustrations.
Keep anything that carries information the text doesn't.

For a figure that encodes structure — a decision tree, a cycle, a hierarchy — put a
Mermaid or table reproduction *next to* the image rather than instead of it. The image
is the evidence; the reproduction is searchable, diffable, and readable when images
don't render. Neither replaces the other.

### 6. Write it, then verify mechanically

Read `references/fidelity.md` before writing the transcript — it covers how to
represent blank fields, checkboxes, tables, and page boundaries, and the verification
scripts that catch omissions.

## What faithful means

The dominant failure mode is not garbled text. It is **helpful summarization**:
turning "How has the willpower assumption impacted you?" into a bullet about the
willpower assumption, collapsing a five-option checklist into prose, or dropping a
blank prompt because it had no answer to carry.

For a worksheet this is destructive in a specific way — the prompts *are* the
document. A blank field is content: it tells the user what they haven't answered yet.
So:

- Reproduce headings, prompts, instructions, and source credits as printed.
- **Keep typos and awkward phrasing.** "Tortoise Trial" where they meant Trail,
  "What is you intention this month?" — these confirm the transcript is a transcript.
  Silently fixing them means the user can't trust that anything else is verbatim.
- Represent an empty field as an empty field, not as absence.
- Keep the user's own entries visually distinct from the printed form.
- Reproduce underscore rules, checkbox lists, and table structure rather than
  flattening them to prose.

Interpretation goes in a clearly marked aside, or in the separate notes file. If you
compute something the document doesn't state — a column total the user left blank —
label it as computed.

## Verify before reporting done

Claiming complete extraction without checking is how the omission reaches the user.
Every check is a few lines of script; run them:

- **Page coverage** — every page accounted for.
- **Prompt diff** — extract every question-shaped line from the source text and
  confirm each appears in the output. This is the check that catches summarization,
  because summarized prompts vanish while surrounding prose survives.
- **Field coverage** — every filled form value present in the output.
- **Link integrity** — every embedded image path resolves; no orphaned files.

`references/fidelity.md` has runnable versions. Normalize punctuation before
comparing — curly quotes, em-dashes, and ligatures differ between the PDF and your
Markdown and will produce false mismatches.

When a check does find gaps, say so plainly and fix them rather than reporting
success with a caveat.

## Tools

`pdftotext`, `pdftoppm`, `pdfinfo`, `pdfimages` come from **poppler-utils**. The
bundled scripts are PEP 723 and self-installing via `uv run`; they use `pypdf` and
`pdfplumber`.

Bad or absent text layer everywhere (a scan) means OCR — `ocrmypdf --skip-text` adds
a text layer in place, then restart at step 2. Verify a sample against the rendered
page before trusting OCR output wholesale.
