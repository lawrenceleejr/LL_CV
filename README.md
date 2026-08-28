# LL_CV

The LaTeX source for Lawrence Lee's CV. One source tree produces three PDFs,
and the citation counts in them are read live from
[INSPIRE-HEP](https://inspirehep.net/authors/1071846) rather than typed in by
hand.

| PDF | Contents |
| --- | --- |
| `LL_CV.pdf` | the external CV, for general circulation |
| `LL_CV_internal.pdf` | the same, plus the internal-only material below |
| `LL_Publications.pdf` | the publication list on its own |

## Building

```sh
./build.sh                 # refresh citation counts, then build all three PDFs
./build.sh --no-fetch      # build offline, from the committed citation counts
./build.sh --keep-aux      # keep build/, which holds the pdflatex logs
```

`pdflatex` and Python 3 are the only requirements; the fetcher uses nothing
outside the standard library. On Debian or Ubuntu the TeX side is

```sh
sudo apt-get install texlive-latex-recommended texlive-latex-extra \
                     texlive-fonts-recommended texlive-fonts-extra
```

`texlive-fonts-extra` is the one that is easy to miss — it carries both
Garamonds. `poppler-utils` supplies `pdftotext`, which the date-column check
below reads the built PDFs with.

## Type

Two cuts of the same French-Renaissance letterform, each with one job:

| | |
| --- | --- |
| **EB Garamond** | body text, and — via `ebgaramond-maths` — the math, so `$\sqrt{s}$` and `$\tau^+\tau^-$` in publication titles are the same letterform as the words around them |
| **Cormorant Garamond** | the name and the section headings, through `\displayface` |

Cormorant is a *display* cut: fine strokes, high contrast, drawn to be set
large. It used to set the whole CV and went thin and grey at reading size. It
now appears only where it is flattering, and `\usefont` keeps it out of
`\rmdefault` so it cannot leak back into body text.

Changing the text face means re-measuring `\datecolumn` — digit widths differ
between families, and a column a shade too narrow silently sends its widest
dates flush right. `tools/check_alignment.py` catches that.

The preamble also maps the f-ligatures back to plain letters in the PDF's
ToUnicode table. EB Garamond sets `fi`/`fl` as single glyphs, so without that
map "configuration" copies out of the PDF — and into whatever software reads a
CV — as `con<FB01>guration`, which no keyword search matches.

## External and internal editions

The internal edition carries material that is not for general circulation: the
current student and postdoc roster, thesis committee membership, individual
refereeing assignments, and student travel awards. Two commands, defined in
`LL_Preamble.tex`, select between the editions:

```latex
\internalonly{ \item Journal Referee: PRD \when{2025} }
\externalonly{ \item Journal Referee for Physical Review Letters, ... }
```

The external edition is the default. The internal one is produced by defining
`\CVinternal` ahead of the document, which is all `build.sh` does differently
between the two:

```sh
pdflatex -jobname=LL_CV_internal "\def\CVinternal{}\input{LL_CV.tex}"
```

The internal PDF also says `(internal edition)` in its PDF title, so the two
files stay distinguishable once they are detached from their filenames.

## Live citation counts

`tools/fetch_inspire.py` queries the INSPIRE-HEP API and writes
`LL_InspireData.tex`, a generated file holding nothing but declarations:

```latex
\inspiresetstat{citations}{207,000}
\inspiresetcites{2642414}{406}
```

The CV reads them back through the commands in `LL_Preamble.tex`:

| Command | Renders |
| --- | --- |
| `\inspirepub{2642414}{Towards a Muon Collider}` | the title in bold, linked to its INSPIRE-HEP record, followed by `[406 citations]` |
| `\pub{https://arxiv.org/abs/…}{Title}` | the same for an entry with no INSPIRE-HEP record |
| `\inspirestat{citations}` | one author-level figure, for the summary paragraph |

Which records to look up is discovered by scanning the sources for
`\inspirepub{…}`, so adding a publication is enough to start tracking its
citation count — there is no second list to keep in step. A count of zero
prints nothing, so a brand-new paper is simply left unannotated.

`LL_InspireData.tex` is committed, and `LL_Preamble.tex` carries a hand-checked
fallback for every figure, so the CV compiles without ever running the fetcher —
on Overleaf, or offline. Both paths degrade to slightly stale numbers rather
than to a failed build: if the API cannot be reached, the fetcher leaves the
existing file alone and exits successfully (`--strict` makes it fail loudly
instead, which is what the weekly CI run uses).

## CI

`.github/workflows/build-cv.yml` builds both editions on every push and pull
request, and weekly so the citation counts in the artifacts stay current. Each
run attaches:

- **`cv-external`** — `LL_CV.pdf` and `LL_Publications.pdf`
- **`latex-logs`** — the `pdflatex` logs, for when a build goes wrong

CI also runs `tools/check_alignment.py`, which reads the built PDFs and fails
if any date has drifted off the date column. Dates are placed by glue, so the
ways they go wrong — a stray space token beside an edition block, a `\vspace`
trapping one in a paragraph tail, a column too narrow for the text face — are
all invisible in the source and none of them are LaTeX errors.

**The internal PDF is built but deliberately not uploaded.** This repository is
public, and workflow artifacts on a public repository can be downloaded by
anyone; publishing `LL_CV_internal.pdf` there would defeat the point of having
an internal edition. CI still compiles it, so breakage is caught. Build it
locally with `./build.sh`. If this repository is ever made private, add it to
its own upload step.

## Layout

```
LL_CV.tex             the CV body
LL_Publications.tex   the publication list as a standalone document
LL_PubInclude.tex     the publication entries, shared by both of the above
LL_Preamble.tex       everything shared: packages, page layout, list styles,
                      the edition switches, the INSPIRE-HEP commands
LL_InspireData.tex    generated -- citation counts, written by the fetcher
tools/fetch_inspire.py
build.sh
```

A few conventions worth knowing before editing the body:

- `\when{2021--2026}` sets a date in the right-hand date column. Use it for
  every date in the single-line lists rather than a bare `\hfill`, so the
  column stays aligned; a date too wide for the column falls back to flush
  right instead of spilling into the margin.
- `\whenflush{2025}` sets a date flush right at its natural width. It is what
  the publication lists use: their entries are multi-line paragraphs, every
  date there is a bare year, and the empty tail of the column box would only
  push years onto lines of their own.
- `\rightnote{…}` is the right-aligned italic annotation hung under an entry.
- `$\RHD$` marks a primary editor, primary analyzer, or intellectual lead role.
- The two numbered publication lists share one sequence: the second opens with
  `\begin{enumerate}[resume]`, so the numbering continues across the
  subsection break without a hand-set counter.
- The citation tags are set small in a muted grey (`LLmuted`); `\citesmin` in
  `LL_Preamble.tex` hides counts below a threshold.
- `itemize`, `itemizetight`, `itemizetighter` and `itemizetightrightpad` are
  the four bullet-free list styles, in decreasing order of leading.
- Comment style: `%%` marks the documentation block at the top of a file;
  everything else — notes, date memos, disabled entries — uses a single `%`
  with one space on each side of the marker.
