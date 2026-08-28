#!/usr/bin/env python3
"""Check that every date in a built PDF sits in the right-hand date column.

The CV sets dates two ways (see LL_Preamble.tex):

  \\when{...}       left-aligned in a fixed-width box against the right margin,
                   so a run of dates shares one left edge -- the date column
  \\whenflush{...}  at natural width, flush against the right margin

Either is fine; anything in between is a bug.  Three have shipped so far, all
one word space wide and all invisible in the source: a stray space token
surviving next to an edition block, a \\vspace pair trapping one in a paragraph
tail, and a date column too narrow for the text face's digits.

Both reference positions are measured from the document itself -- the column
edge as the most common left edge among dated lines, the margin as the largest
right edge -- so this keeps working when the font, the margins, or the column
width change.

Usage:  tools/check_alignment.py LL_CV.pdf LL_CV_internal.pdf ...
Exit status is non-zero if any date is off its reference.
"""

from __future__ import annotations

import collections
import html
import re
import subprocess
import sys

WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" '
                  r'xMax="([\d.]+)" yMax="[\d.]+">([^<]*)</word>')
DATE = re.compile(r"^(19|20)\d{2}([-–—]+\d{0,4})?$")

# A date this far off its reference is a real misalignment.  One word space at
# 11pt is about 2.5pt, and that is the smallest error seen in practice.
TOLERANCE = 0.6


def lines_of(pdf: str):
    """Yield (page number, [(x0, x1, word), ...]) for each visual line."""
    xml = subprocess.run(["pdftotext", "-bbox", pdf, "-"],
                         capture_output=True, text=True, check=True).stdout
    for pageno, page in enumerate(xml.split("<page")[1:], 1):
        words = sorted((float(m.group(2)), float(m.group(1)),
                        float(m.group(3)), html.unescape(m.group(4)))
                       for m in WORD.finditer(page))
        line, top = [], None
        for y, x0, x1, text in words:
            # pdftotext reports each word's own yMin, and a line's words differ
            # slightly; group anything within 3pt of the line's first word.
            if top is not None and y - top > 3.0:
                yield pageno, line
                line, top = [], None
            if top is None:
                top = y
            line.append((x0, x1, text))
        if line:
            yield pageno, line


def dated_lines(pdf: str):
    """Lines that end in a date, as (page, x0, x1, rendered text)."""
    for pageno, line in lines_of(pdf):
        if len(line) < 2:
            continue                      # a lone date is a wrapped entry tail
        x0, x1, last = line[-1]
        if DATE.match(last):
            yield pageno, x0, x1, " ".join(w[2] for w in line)


def check(pdf: str) -> int:
    rows = list(dated_lines(pdf))
    if not rows:
        print(f"{pdf}: no dated lines found -- is this the right document?")
        return 1

    # The column edge is where most dates start; the margin is the far right.
    column = collections.Counter(round(r[1], 1) for r in rows).most_common(1)[0][0]
    margin = max(r[2] for r in rows)

    # Only lines that actually reach the date region are candidates; this drops
    # centred text that happens to end in a year, such as the "Last updated"
    # footer, without needing to know what that text says.
    rows = [r for r in rows if r[2] >= column - TOLERANCE]

    bad = [r for r in rows
           if abs(r[1] - column) > TOLERANCE and abs(r[2] - margin) > TOLERANCE]
    print(f"{pdf}: {len(rows)} dated lines, column x={column:.1f}, "
          f"margin x={margin:.1f} -> {len(bad)} misaligned")
    for pageno, x0, x1, text in bad:
        print(f"    p{pageno}  x0={x0:7.2f} x1={x1:7.2f}  {text[:76]}")
    return len(bad)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        return 2
    return 1 if sum(check(pdf) for pdf in argv) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
