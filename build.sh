#!/usr/bin/env bash
#
# Build every PDF in this repository:
#
#   LL_CV.pdf            the external CV, for general circulation
#   LL_CV_internal.pdf   the internal CV, with the material \internalonly hides
#   LL_Publications.pdf  the publication list on its own
#
# Citation counts are refreshed from INSPIRE-HEP before the first build; the
# fetcher leaves the existing numbers alone if the API cannot be reached, so
# this works offline too.
#
# Usage: ./build.sh [--no-fetch] [--keep-aux]
#
#   --no-fetch   build from whatever LL_InspireData.tex already holds
#   --keep-aux   leave build/ in place afterwards (it holds the pdflatex logs)

set -euo pipefail
cd "$(dirname "$0")"

BUILD_DIR=build
FETCH=1
KEEP_AUX=0

for arg in "$@"; do
  case "$arg" in
    --no-fetch)  FETCH=0 ;;
    --keep-aux)  KEEP_AUX=1 ;;
    -h|--help)   sed -n '3,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)           echo "$0: unknown option '$arg'" >&2; exit 2 ;;
  esac
done

command -v pdflatex >/dev/null || {
  echo "$0: pdflatex not found; install TeX Live (texlive-latex-extra and" >&2
  echo "    texlive-fonts-extra cover every package this CV uses)." >&2
  exit 1
}

# --------------------------------------------------------------------------
# Live citation counts
# --------------------------------------------------------------------------
if [[ $FETCH -eq 1 ]]; then
  python3 tools/fetch_inspire.py
else
  echo "Skipping the INSPIRE-HEP refresh (--no-fetch)."
fi

# --------------------------------------------------------------------------
# PDFs
# --------------------------------------------------------------------------
mkdir -p "$BUILD_DIR"

# build <jobname> <source> <prelude>
#
# pdflatex runs twice: the second pass resolves the page references and hyperref
# anchors written by the first.  Aux files stay in $BUILD_DIR, so only the PDFs
# land next to the sources.  The prelude is TeX executed ahead of the document,
# which is how the internal edition is selected.
build() {
  local jobname=$1 source=$2 prelude=$3 log pass
  printf '==> %s.pdf\n' "$jobname"
  for pass in 1 2; do
    log="$BUILD_DIR/$jobname.pass$pass.log"
    if ! pdflatex -interaction=nonstopmode -halt-on-error \
                  -output-directory="$BUILD_DIR" -jobname="$jobname" \
                  "${prelude}\\input{${source}}" >"$log" 2>&1; then
      echo "--- pdflatex failed on pass $pass; see $log ---" >&2
      grep -nE '^(!|l\.[0-9])' "$log" | head -20 >&2
      exit 1
    fi
  done
  cp "$BUILD_DIR/$jobname.pdf" .

  # Overfull and underfull boxes are the usual sign that an entry has outgrown
  # its line, so report them rather than burying them in the log.
  local boxes
  boxes=$(grep -cE '^(Overfull|Underfull)' "$BUILD_DIR/$jobname.pass2.log" || true)
  if [[ ${boxes:-0} -gt 0 ]]; then
    echo "    note: $boxes overfull/underfull box(es):"
    grep -E '^(Overfull|Underfull)' "$BUILD_DIR/$jobname.pass2.log" | sed 's/^/      /'
  fi
}

build LL_CV            LL_CV.tex           ''
build LL_CV_internal   LL_CV.tex           '\def\CVinternal{}'
build LL_Publications  LL_Publications.tex ''

# Dates are placed by glue, so a stray space token or a date column too narrow
# for the text face shifts one silently.  Check the built PDFs rather than the
# source, since that is where the evidence is.
echo
python3 tools/check_alignment.py LL_CV.pdf LL_CV_internal.pdf LL_Publications.pdf

[[ $KEEP_AUX -eq 1 ]] || rm -rf "$BUILD_DIR"

echo
echo "Done:"
for pdf in LL_CV.pdf LL_CV_internal.pdf LL_Publications.pdf; do
  printf '  %-22s %s\n' "$pdf" "$(du -h "$pdf" | cut -f1)"
done
