# Transcription conventions and verification

Read this before writing a verbatim transcript. Two parts: how to represent form
structure in Markdown, and how to prove afterwards that nothing was dropped.

## Contents

- [Representing form structure](#representing-form-structure)
- [Page boundaries](#page-boundaries)
- [Tables that were not tables](#tables-that-were-not-tables)
- [Where the user's answers go](#where-the-users-answers-go)
- [Verification scripts](#verification-scripts)

## Representing form structure

State the conventions once at the top of the transcript so a reader knows how to
interpret the notation, then apply them consistently.

**Text areas and boxes.** Use a fenced block. Empty fence = unanswered field; text
inside = what the user entered. One notation for both states means a reader can tell
answered from unanswered at a glance, and it visually echoes a box on paper.

````markdown
**What are you hoping to get out of this program?**

```
I want to waste less time and feel like I am making progress.
```

**When have you experienced 'blaming the victim'?**

```

```
````

**Ruled lines.** When the PDF prints underscore rules, reproduce them — the number of
lines tells the user how much was expected.

```markdown
1. _________________________________________________
2. _________________________________________________
```

**Checkboxes.** Markdown task list items, carrying real state from `--checkboxes`:

```markdown
- [x] Medication
- [ ] Therapy
- [x] Sleep
```

**Rating scales.** Reproduce the row as printed rather than describing it:

```markdown
| 5 | 4 | 3 | 2 | 1 | How are you feeling right now? |
|---|---|---|---|---|---|
```

## Page boundaries

Mark pages with a light separator and the printed page number. This is structural,
not editorial — it lets someone hold the PDF beside the Markdown and stay in sync,
and makes gaps obvious during verification.

```markdown
---

*p. 7*

## Section Heading As Printed
```

Repeating headers and footers (logo, copyright line, "Page N of M") do not need to
appear on every page. Reproduce the footer once near the top of the document and note
that it repeats.

## Tables that were not tables

Worksheets often lay out content in visual columns that `pdftotext -layout` renders as
aligned whitespace. Reconstructing them as Markdown tables is faithful — the structure
was in the original, only the rendering changes. What is *not* faithful is inventing
columns that weren't there, or dropping a column because it was empty.

When a checklist has a score column, keep the scores against their statements rather
than summarizing the totals:

```markdown
| Cluster | Score | Statement |
|---|---|---|
| **Activation** | `2` | Difficulty getting started |
| | `0` | Struggle to organize things |
```

If the form has total fields the user left blank, leave them blank and note it. If you
compute the totals because they're useful, mark them as computed — the user needs to
know which numbers came from the document and which came from you.

## Where the user's answers go

Keep a clear line between what the form prints and what a person wrote. A fenced block
inside the prompt does this naturally.

If an answer exists somewhere other than the PDF — the user told you in conversation,
or it lives in another note — the printed field still shows as blank, and the outside
answer goes in a marked aside beneath it. Filling the form field with information that
isn't in the form makes the transcript unreliable as a record of the document.

## Verification scripts

Run these before reporting completion. Each takes seconds.

### Page coverage

```python
import re
t = open("transcript.md").read()
found = {int(m) for m in re.findall(r'^\*p\. (\d+)\*$', t, re.M)}
expected = set(range(2, 24))          # from pdfinfo
print("missing pages:", sorted(expected - found) or "none")
```

### Prompt diff — catches summarization

The highest-value check. Pull every question-shaped line from the PDF text and confirm
each survives into the Markdown. Normalize punctuation first: curly quotes, em-dashes,
and ligatures differ between PDF text and hand-written Markdown and will otherwise
produce a wall of false positives.

```python
import re, unicodedata

def norm(s):
    s = unicodedata.normalize('NFKD', s)
    for a, b in [('’', "'"), ('“', '"'), ('”', '"'),
                 ('–', '-'), ('—', '-')]:
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()

note = norm(open("transcript.md").read())
prompts = [l.strip() for l in open("source.txt")
           if l.strip().endswith('?') and 5 < len(l.strip()) < 120]
missing = [p for p in prompts if norm(p)[:55] not in note]
print(f"{len(prompts)} prompts, {len(missing)} missing")
for p in missing:
    print("  MISSING:", p)
```

Expect false positives where you legitimately reformatted a heading — check each hit
by hand rather than trusting the count. Question marks only catch interrogative
prompts, so also grep the source for imperative ones: `List at least`, `Record your`,
`Check off`, `Select your`, `Write down`, `Draw`, `Circle`.

### Field coverage

```bash
scripts/pdf_probe.py FILE.pdf --fields | grep '^\s*\[x\]'
```

Confirm each filled value appears in the transcript.

### Link integrity

```python
import re, os
t = open("transcript.md").read()
media = "_resources/media"
embeds = re.findall(r'!\[\[([^\]|]+)\]\]', t)          # Obsidian; adjust for ![](path)
broken = [e for e in embeds if not os.path.exists(os.path.join(media, e))]
unused = sorted(set(os.listdir(media)) - set(embeds))
print("broken:", broken or "none")
print("unused:", unused or "none")
```

Unused files are usually crops you meant to delete or meant to embed — check which
before moving on.

## Obsidian vaults

If the destination is an Obsidian vault, follow the vault's own `AGENTS.md`/`CLAUDE.md`
conventions. Typical ones:

- Attachments go in a `_resources/media/` sibling folder, not next to the note.
- Links use the shortest unambiguous form — bare basename `![[figure.png]]` — which
  survives moving either file. Verify basenames are unique vault-wide first.
- The PARA tree may be read-only to agents unless the user explicitly asked for a file
  there.
