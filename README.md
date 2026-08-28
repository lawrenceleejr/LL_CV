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

`texlive-fonts-extra` is the one that is easy to miss — it carries Cormorant
Garamond, the CV's typeface.

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
  every date rather than a bare `\hfill`, so the column stays aligned; a date
  too wide for the column falls back to flush right instead of spilling into
  the margin.
- `\rightnote{…}` is the right-aligned italic annotation hung under an entry.
- `$\RHD$` marks a primary editor, primary analyzer, or intellectual lead role.
- `itemize`, `itemizetight`, `itemizetighter` and `itemizetightrightpad` are
  the four bullet-free list styles, in decreasing order of leading.
