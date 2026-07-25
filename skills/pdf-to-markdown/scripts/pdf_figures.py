#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pdfplumber>=0.11", "pillow>=10"]
# ///
"""Extract figures from a PDF as cropped page regions.

Why crop the rendered page instead of using `pdfimages`?
`pdfimages` pulls the raw embedded raster, which loses everything drawn *on top of*
it in the PDF: caption text, axis labels, callouts, and hand-drawn annotations a
previous reader added. A diagram whose labels are live text comes out as an
unlabelled blob. Cropping the rendered page keeps the figure exactly as a human
sees it, at the cost of a little surrounding whitespace — a good trade.

The band is taken at full page width because side captions and definition columns
next to a diagram are part of the figure's meaning.

Usage:
    pdf_figures.py FILE.pdf OUTDIR --prefix myfile
    pdf_figures.py FILE.pdf OUTDIR --prefix wk1 --skip-pages 1 --dpi 150
    pdf_figures.py FILE.pdf OUTDIR --prefix wk1 --dry-run     # list bands, write nothing

Output names are PREFIX-pNN-figK.png. Rename them to something descriptive once
you know what each one is — future readers of the Markdown see the filename.
"""
from __future__ import annotations

import argparse
import os

import pdfplumber

LOGO_MAX_WIDTH = 250
LOGO_MAX_BOTTOM = 90


def figure_bands(page, min_area: float, pad: float, gap: float) -> list[tuple[float, float]]:
    """Vertical bands of the page that contain figures.

    Bands closer together than `gap` are merged: a diagram is often several stacked
    images plus overlays, and slicing between them produces confetti.
    """
    bands: list[list[float]] = []
    for im in page.images:
        top, bottom = float(im["top"]), float(im["bottom"])
        x0, x1 = float(im["x0"]), float(im["x1"])
        width = x1 - x0
        if bottom < LOGO_MAX_BOTTOM and width < LOGO_MAX_WIDTH:
            continue  # repeating header logo
        if width * (bottom - top) < min_area:
            continue  # icon / bullet glyph
        bands.append([top, bottom])

    if not bands:
        return []
    bands.sort()
    merged = [bands[0]]
    for band in bands[1:]:
        if band[0] - merged[-1][1] < gap:
            merged[-1][1] = max(merged[-1][1], band[1])
        else:
            merged.append(band)

    out = []
    for top, bottom in merged:
        top = max(0, top - pad)
        bottom = min(float(page.height), bottom + pad)
        if bottom - top >= 60:  # ignore slivers
            out.append((top, bottom))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("outdir")
    ap.add_argument("--prefix", required=True, help="filename prefix, e.g. 'week1'")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--skip-pages", type=int, nargs="*", default=[1],
                    help="pages to ignore (default: 1, usually a cover/copyright page)")
    ap.add_argument("--min-area", type=float, default=4000)
    ap.add_argument("--pad", type=float, default=24, help="pts of whitespace kept around a band")
    ap.add_argument("--gap", type=float, default=60, help="merge bands closer than this many pts")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    written = 0
    with pdfplumber.open(args.pdf) as pdf:
        for pageno, page in enumerate(pdf.pages, 1):
            if pageno in args.skip_pages:
                continue
            for i, (top, bottom) in enumerate(figure_bands(page, args.min_area, args.pad, args.gap), 1):
                name = f"{args.prefix}-p{pageno:02d}-fig{i}.png"
                print(f"{name}  page {pageno}  y {top:.0f}-{bottom:.0f}")
                if not args.dry_run:
                    crop = page.crop((0, top, page.width, bottom))
                    crop.to_image(resolution=args.dpi).save(os.path.join(args.outdir, name))
                    written += 1
    if not args.dry_run:
        print(f"\n{written} figures -> {args.outdir}")
        print("Next: view each one, rename descriptively, then embed. Delete decorative crops.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
