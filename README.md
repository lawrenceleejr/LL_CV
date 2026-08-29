# LL_CV

The LaTeX source for Lawrence Lee's CV. One source tree produces three PDFs,
and the citation counts in them are read from
[INSPIRE-HEP](https://inspirehep.net/authors/1071846) rather than typed by hand.

| PDF | Contents |
| --- | --- |
| `LL_CV.pdf` | the external CV, for general circulation |
| `LL_CV_internal.pdf` | the same, plus the internal-only material described below |
| `LL_Publications.pdf` | the publication list on its own |

## Everyday use

**To edit and preview:** compile `LL_CV.tex` however you normally do — `pdflatex`,
`latexmk`, your editor's build button, Overleaf. That gives you the external CV,
and the citation figures come from `LL_InspireData.tex` as committed.

**To build everything, with fresh figures:**

```sh
./build.sh
```

That refreshes the INSPIRE numbers, builds all three PDFs, and checks the date
column. Options:

```sh
./build.sh --no-fetch    # build offline, from the committed figures
./build.sh --keep-aux    # keep build/, which holds the pdflatex logs
```

### Does a normal compile fetch from INSPIRE?

**No.** Only `./build.sh` and CI run the fetcher. A plain `pdflatex`, an editor,
or Overleaf never touches the network — it typesets whatever
`LL_InspireData.tex` holds at the time.

That is deliberate: the CV has to compile on a machine with no network, and on
Overleaf, where running a Python script isn't an option. The cost is that the
figures can go quietly stale, so the fetcher records the date it last confirmed
them and the preamble turns that into an ordinary LaTeX warning once it is more
than `\citesmaxage` (120) days old:

```
Package LL_CV Warning: The INSPIRE figures date from 2026-02-10 (roughly 205 days ago).
Run ./build.sh to refresh them -- a plain pdflatex does not.
```

The build still succeeds; it just tells you. Run `./build.sh` — or
`python3 tools/fetch_inspire.py` on its own — and commit the regenerated
`LL_InspireData.tex`.

## Adding an entry

Six commands cover nearly everything. All are defined in `LL_Preamble.tex`.

| Command | Use |
| --- | --- |
| `\when{2021--26}` | a date in the right-hand column, for the single-line lists |
| `\whenflush{2025}` | a date flush right, used by the publication lists |
| `\inspirepub{2642414}{Title}` | a publication title, linked to its INSPIRE record and annotated with its live citation count |
| `\pub{https://…}{Title}` | the same for an entry with no INSPIRE record: an arXiv-only preprint, a CDS or CERN note |
| `\internalonly{…}` | material for the internal edition only |
| `\externalonly{…}` | material for the external edition only |

Conventions the existing entries follow, worth matching:

- **Newest first**, ordered by the *start* year. Entries sharing a start year
  are in no fixed order.
- **Closed ranges take a two-digit end year** — `2021--26`, not `2021--2026`.
- `$\RHD$` marks a primary editor, primary analyzer, or intellectual lead role.
- Journal names are spelled out (`Phys. Rev. D`), except JHEP and JINST, which
  go by their initialisms. Volume and page are separated by a comma for the APS
  and EPJ journals.
- Comments: `%%` heads the block at the top of a file; everything else is a
  single `%` with a space on each side.

## The two editions

The internal edition carries material that is not for general circulation: the
current student and postdoc roster, thesis committee membership, individual
refereeing assignments, and student travel awards.

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
files stay distinguishable once detached from their filenames.

## Live figures from INSPIRE-HEP

`tools/fetch_inspire.py` queries the INSPIRE-HEP API and writes
`LL_InspireData.tex`, a generated file holding nothing but declarations:

```latex
\inspiresetstat{citations}{207,000}
\inspiresetcites{2642414}{406}
\inspiresetfetched{2026-08-29}{739767}
```

`\inspirepub` and `\inspirestat` read them back. Which records to look up is
discovered by scanning the sources for `\inspirepub{…}`, so adding a publication
is enough to start tracking its citations — there is no second list to keep in
step. A count of zero prints nothing, so a brand-new paper is left unannotated;
`\citesmin` in the preamble raises that threshold.

The script uses only the Python standard library, so nothing needs installing.

```sh
python3 tools/fetch_inspire.py            # refresh LL_InspireData.tex
python3 tools/fetch_inspire.py --print    # dump to stdout, write nothing
python3 tools/fetch_inspire.py --strict   # fail loudly if the API is unreachable
```

Without `--strict` a failed lookup leaves the existing file alone and exits 0,
so a flaky connection costs you slightly stale figures rather than a failed
build. `LL_Preamble.tex` also carries a hand-checked fallback for every figure,
so the CV compiles even with `LL_InspireData.tex` deleted entirely.

## CI

`.github/workflows/build-cv.yml` builds both editions on every push and pull
request, and weekly, so the figures in the artifacts stay current. Each run
attaches:

- **`cv-external`** — `LL_CV.pdf` and `LL_Publications.pdf`
- **`latex-logs`** — the `pdflatex` logs, for when a build goes wrong

**The internal PDF is built but deliberately not uploaded.** This repository is
public, and workflow artifacts on a public repository can be downloaded by
anyone; publishing `LL_CV_internal.pdf` there would defeat the point of having
an internal edition. CI still compiles it, so breakage is caught. Build it
locally with `./build.sh`. If this repository is ever made private, add it to
its own upload step.

The weekly run uses `--strict`: a scheduled build exists to refresh the figures,
so a failed lookup should be visible. Pushes do not, since a push should not
fail because inspirehep.net blinked.

## Checks

`tools/check_alignment.py` reads the built PDFs and fails if any date has
drifted off the date column. `build.sh` runs it, and so does CI.

```sh
python3 tools/check_alignment.py LL_CV.pdf LL_CV_internal.pdf LL_Publications.pdf
```

It exists because dates are placed by glue, and the ways they go wrong are all
invisible in the source and none of them are LaTeX errors: a stray space token
beside an edition block, a `\vspace` trapping one in a paragraph tail, a column
too narrow for the text face's digits. Both reference positions — the column
edge and the right margin — are measured from the document itself, so the check
survives changes to the font, the margins, or the column width.

`build.sh` also reports any overfull or underfull boxes rather than leaving them
in the log. The CV currently builds with none.

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

Figures are **oldstyle** throughout (`[oldstyle]`, and the `-OsF` family for the
display cut): they sit at x-height with their own ascenders and descenders, so a
year reads as a word inside a line of prose rather than as a row of capitals.
The name is set at 28pt against 11pt body text — its own size, not one of the
document's steps.

The document is deliberately unornamented: no rules, no colour beyond the muted
grey of the citation tags. Hierarchy is carried by size, weight, space and small
caps alone.

Two things to know before changing any of that:

- Changing the text face **or the figure style** means re-measuring
  `\datecolumn`. Digit widths differ between both, and a column a shade too
  narrow silently sends its widest dates flush right, which
  `check_alignment.py` accepts as legitimate. It is 3.7em for the current face
  and the two-digit range convention.
- `sectsty` is loaded after `titlesec` and wins, so `\titleformat` and
  `\titlespacing` have no effect as things stand. Moving to `titlesec` means
  dropping `sectsty` in the same edit, or the headings silently revert to bold.

The preamble also maps the f-ligatures back to plain letters in the PDF's
ToUnicode table. EB Garamond sets `fi`/`fl` as single glyphs, so without that
map "configuration" copies out of the PDF — and into whatever software reads a
CV — as `con<FB01>guration`, which no keyword search matches.

## Requirements

`pdflatex` and Python 3. The fetcher uses nothing outside the standard library.
On Debian or Ubuntu:

```sh
sudo apt-get install texlive-latex-recommended texlive-latex-extra \
                     texlive-fonts-recommended texlive-fonts-extra \
                     poppler-utils
```

`texlive-fonts-extra` is the one that is easy to miss — it carries both
Garamonds. `poppler-utils` supplies `pdftotext`, which the alignment check reads
the built PDFs with.

## Files

```
LL_CV.tex               the CV body
LL_Publications.tex     the publication list as a standalone document
LL_PubInclude.tex       the publication entries, shared by both of the above
LL_Preamble.tex         everything shared: packages, page layout, list styles,
                        the edition switches, the INSPIRE-HEP commands
LL_InspireData.tex      generated -- citation counts, written by the fetcher
tools/fetch_inspire.py  reads INSPIRE-HEP, writes LL_InspireData.tex
tools/check_alignment.py  checks the date column in the built PDFs
build.sh                fetch, build all three PDFs, check
```

`LL_InspireData.tex` is committed so that a fresh checkout — or Overleaf —
builds with real figures. Its fetch date changes whenever the fetcher runs, so
expect that one line to show up in `git status` after a `./build.sh`; commit it
or discard it, either is fine.
