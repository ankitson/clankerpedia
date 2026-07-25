#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pypdf>=4", "pdfplumber>=0.11"]
# ///
"""Reconnaissance for PDF -> Markdown transcription.

Answers the three questions you need before writing a single line of Markdown:
  1. Which pages have a usable text layer, and which are image-only?
     (image-only pages must be READ AS IMAGES; pdftotext returns nothing useful)
  2. Does this PDF carry AcroForm field values? Filled form fields are frequently
     invisible in both `pdftotext` output and rendered pages, so they are the
     single easiest thing to silently lose.
  3. Where are the figures, and which are just the repeating header logo?

Usage:
    pdf_probe.py FILE.pdf                # per-page survey
    pdf_probe.py FILE.pdf --fields       # every form field: page, position, value
    pdf_probe.py FILE.pdf --checkboxes   # checkboxes grouped by page, top-to-bottom
    pdf_probe.py *.pdf --summary         # one line per file
"""
from __future__ import annotations

import argparse
import glob
import sys

import pdfplumber
from pypdf import PdfReader

LOGO_MAX_WIDTH = 250   # pts; repeating header logos are narrow and sit at the top
LOGO_MAX_BOTTOM = 90   # pts from top of page
MIN_FIGURE_AREA = 4000  # pts^2; below this it is an icon or bullet glyph


def widget_pages(reader: PdfReader) -> dict[int, int]:
    """Map annotation object id -> 1-based page number."""
    out: dict[int, int] = {}
    for i, page in enumerate(reader.pages, 1):
        for annot in page.get("/Annots") or []:
            try:
                out[annot.indirect_reference.idnum] = i
            except AttributeError:
                pass
    return out


def iter_fields(reader: PdfReader):
    """Yield (name, type, value, page, rect) for every form widget.

    Field names live on the parent field object while position lives on the child
    widget annotation, so neither alone tells you where a value belongs on the page.
    Walking both together is what lets you map, say, a checked box back to the list
    item printed next to it.
    """
    acro = (reader.trailer.get("/Root") or {}).get("/AcroForm")
    if not acro:
        return
    pmap = widget_pages(reader)

    def walk(fields, inherited_name=""):
        for ref in fields:
            obj = ref.get_object()
            name = str(obj.get("/T") or inherited_name)
            kids = obj.get("/Kids")
            if kids and any("/T" in k.get_object() for k in kids):
                walk(kids, name)
                continue
            ftype = str(obj.get("/FT") or "")
            value = obj.get("/V")
            for widget in (kids or [ref]):
                try:
                    page = pmap.get(widget.indirect_reference.idnum)
                except AttributeError:
                    page = None
                rect = widget.get_object().get("/Rect")
                rect = [round(float(x)) for x in rect] if rect else None
                yield name, ftype, value, page, rect

    yield from walk(acro["/Fields"])


def survey(path: str) -> None:
    reader = PdfReader(path)
    fields = list(iter_fields(reader))
    by_page: dict[int, list] = {}
    for f in fields:
        by_page.setdefault(f[3], []).append(f)

    print(f"=== {path}  ({len(reader.pages)} pages, {len(fields)} form widgets)")
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = (page.extract_text() or "").strip()
            figs = [
                im for im in page.images
                if (float(im["x1"]) - float(im["x0"])) * (float(im["bottom"]) - float(im["top"])) >= MIN_FIGURE_AREA
                and not (float(im["bottom"]) < LOGO_MAX_BOTTOM and float(im["x1"]) - float(im["x0"]) < LOGO_MAX_WIDTH)
            ]
            pf = by_page.get(i, [])
            filled = sum(1 for f in pf if f[2] not in (None, ""))
            flags = []
            if len(text) < 400:
                flags.append("SPARSE-TEXT->read this page as an image")
            if figs:
                flags.append(f"{len(figs)} figure(s)")
            if pf:
                flags.append(f"{len(pf)} field(s), {filled} filled")
            print(f"  p{i:3d}  {len(text):5d} chars  {'  '.join(flags)}")

    filled_total = sum(1 for f in fields if f[2] not in (None, ""))
    if filled_total:
        print(f"  !! {filled_total} FILLED form fields — run --fields, these are easy to miss")


def dump_fields(path: str, checkboxes_only: bool = False) -> None:
    reader = PdfReader(path)
    rows = [f for f in iter_fields(reader) if f[3] is not None]
    if checkboxes_only:
        rows = [r for r in rows if r[1] == "/Btn"]
    # Top-to-bottom within a page: PDF y grows upward, so sort by -y.
    rows.sort(key=lambda r: (r[3], -(r[4][1] if r[4] else 0)))
    print(f"=== {path}")
    page = None
    for name, ftype, value, pg, rect in rows:
        if pg != page:
            print(f"\n  --- page {pg} (listed top-to-bottom; match against the printed list) ---")
            page = pg
        kind = {"/Tx": "text", "/Btn": "check", "/Ch": "choice"}.get(ftype, ftype or "?")
        mark = "[x]" if value not in (None, "", "/Off") else "[ ]"
        shown = "" if value in (None, "") else repr(value)
        print(f"  {mark} {kind:6} y={rect[1] if rect else '?':>4}  {name:24} {shown}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="+")
    ap.add_argument("--fields", action="store_true", help="dump every form field with page + position + value")
    ap.add_argument("--checkboxes", action="store_true", help="checkboxes only, ordered top-to-bottom per page")
    ap.add_argument("--summary", action="store_true", help="one line per file")
    args = ap.parse_args()

    paths = [p for pat in args.pdfs for p in sorted(glob.glob(pat))] or args.pdfs
    for path in paths:
        try:
            if args.fields or args.checkboxes:
                dump_fields(path, checkboxes_only=args.checkboxes)
            elif args.summary:
                r = PdfReader(path)
                fs = list(iter_fields(r))
                filled = sum(1 for f in fs if f[2] not in (None, ""))
                print(f"{path}: {len(r.pages)} pages, {len(fs)} fields, {filled} filled")
            else:
                survey(path)
        except Exception as exc:  # keep going across a batch
            print(f"!! {path}: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
