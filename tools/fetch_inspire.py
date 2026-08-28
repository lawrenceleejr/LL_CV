#!/usr/bin/env python3
"""Fetch live publication metrics from INSPIRE-HEP and emit them as LaTeX.

The CV cites two kinds of number that go stale the moment they are typed:

  * the citation count of each individual paper, and
  * the author-level summary at the top of the Publications section
    (total papers, total citations, h-index).

This script reads both from the INSPIRE-HEP REST API and writes them into a
generated LaTeX file (LL_InspireData.tex by default) as a flat list of
declarations::

    \\inspiresetcites{2690093}{3}
    \\inspiresetstat{papers}{1400}

LL_Preamble.tex defines those two commands, plus the \\inspirepub and
\\inspirestat commands that the CV body uses to typeset the values.  Fallback
values live in the preamble as well, so the CV still compiles -- with the
last hand-checked numbers -- if this file was never generated.

Nothing here is required at build time: on any network or API failure the
script leaves any existing generated file untouched and exits 0, so a flaky
connection degrades to slightly stale citation counts rather than a failed
build.  Pass --strict to turn such failures into a non-zero exit instead.

Usage:
    tools/fetch_inspire.py                  # refresh LL_InspireData.tex
    tools/fetch_inspire.py --strict         # fail the build on API errors
    tools/fetch_inspire.py --print          # dump to stdout, write nothing

Only the Python standard library is used, so CI needs no pip install.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://inspirehep.net/api"
USER_AGENT = "LL_CV-inspire-fetcher/1.0 (+https://github.com/lawrenceleejr/LL_CV)"

# Records are discovered from the sources rather than listed here, so adding a
# publication to the CV is enough to start tracking its citation count.  Both
# spellings count: \inspirepub{<recid>}{...}, which is what the CV uses, and a
# bare INSPIRE-HEP URL, which is what a freshly pasted entry looks like.
RECORD_RE = re.compile(r"\\inspirepub\{(\d+)\}|inspirehep\.net/literature/(\d+)")
AUTHOR_RE = re.compile(r"inspirehep\.net/authors/(\d+)")

# Papers and citations are quoted as "over N" in the CV, so round them down to
# a figure that stays true for a while; the h-index is quoted exactly.
PAPER_ROUNDING = 100
CITATION_ROUNDING = 1000


# --------------------------------------------------------------------------
# INSPIRE-HEP API
# --------------------------------------------------------------------------

def api_get(endpoint: str, params: dict, retries: int = 3, timeout: int = 60) -> dict:
    """GET a JSON document from the INSPIRE-HEP API, retrying transient errors."""
    url = f"{API}/{endpoint}?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            # 4xx responses mean the query itself is wrong; retrying won't help.
            if isinstance(exc, urllib.error.HTTPError) and 400 <= exc.code < 500:
                raise
            if attempt == retries:
                raise
            backoff = 2 ** attempt
            print(f"  ! {exc} -- retrying in {backoff}s "
                  f"({attempt}/{retries - 1})", file=sys.stderr)
            time.sleep(backoff)
    raise AssertionError("unreachable")


def fetch_citation_counts(recids: list[str]) -> dict[str, int]:
    """Return {record id: citation count} for the given INSPIRE record ids.

    All records are requested in a single query, so the number of publications
    in the CV costs one API call rather than one call per entry.
    """
    if not recids:
        return {}
    result = api_get("literature", {
        "q": " or ".join(f"recid {recid}" for recid in recids),
        "fields": "control_number,citation_count",
        "size": str(max(len(recids), 1)),
    })
    counts = {}
    for hit in result["hits"]["hits"]:
        metadata = hit["metadata"]
        counts[str(metadata["control_number"])] = int(metadata.get("citation_count") or 0)
    missing = sorted(set(recids) - set(counts))
    if missing:
        print(f"  ! no INSPIRE record for: {', '.join(missing)}", file=sys.stderr)
    return counts


def fetch_author_summary(author_recid: str) -> dict[str, int]:
    """Return the author-level paper count, citation count and h-index.

    INSPIRE's own profile pages compute these with the ``citation-summary``
    aggregation, so asking for the same facet gives numbers that match what a
    reader sees on inspirehep.net rather than a private re-derivation.
    """
    profile = api_get(f"authors/{author_recid}", {"fields": "ids"})
    bais = [i["value"] for i in profile["metadata"].get("ids", [])
            if i.get("schema") == "INSPIRE BAI"]
    if not bais:
        raise RuntimeError(f"author {author_recid} has no INSPIRE BAI")

    facets = api_get("literature/facets", {
        "q": f"a {bais[0]}",
        "facet_name": "citation-summary",
    })
    summary = facets["aggregations"]["citation_summary"]
    return {
        # Every record attributed to the author, matching the profile page's
        # publication count.
        "papers": int(facets["hits"]["total"]["value"]),
        "citations": int(summary["citations"]["buckets"]["all"]["citations_count"]["value"]),
        "hindex": int(summary["h-index"]["value"]["all"]),
    }


# --------------------------------------------------------------------------
# LaTeX generation
# --------------------------------------------------------------------------

def floor_to(value: int, step: int) -> int:
    """Round `value` down to a multiple of `step`."""
    return (value // step) * step


def render(counts: dict[str, int], summary: dict[str, int]) -> str:
    """Render the fetched numbers as the body of LL_InspireData.tex."""
    lines = [
        "%% Publication metrics fetched from the INSPIRE-HEP API.",
        "%% GENERATED FILE -- do not edit; run tools/fetch_inspire.py instead.",
        "%%",
        "%% \\inspiresetcites{<record>}{<count>}  per-paper citation count",
        "%% \\inspiresetstat{<key>}{<value>}      author-level summary figure",
        "%% Both are defined in LL_Preamble.tex.",
        "",
        "%% Author-level summary, as shown at the top of the Publications section.",
        "%% Papers and citations are rounded down because the CV says \"over\".",
        f"\\inspiresetstat{{papers}}{{{floor_to(summary['papers'], PAPER_ROUNDING)}}}"
        f"    % exact: {summary['papers']:,}",
        f"\\inspiresetstat{{citations}}{{{floor_to(summary['citations'], CITATION_ROUNDING):,}}}"
        f"  % exact: {summary['citations']:,}",
        f"\\inspiresetstat{{hindex}}{{{summary['hindex']}}}",
        "",
        "%% Per-paper citation counts, keyed by INSPIRE record id.",
    ]
    for recid in sorted(counts, key=int, reverse=True):
        lines.append(f"\\inspiresetcites{{{recid}}}{{{counts[recid]}}}")
    return "\n".join(lines) + "\n"


def write_if_changed(path: Path, content: str) -> bool:
    """Write `content` to `path`; return True if the file actually changed.

    Leaving an unchanged file alone keeps the generated data out of `git
    status` on every build.
    """
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)
    return True


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def discover(sources: list[Path]) -> tuple[list[str], str | None]:
    """Scan the LaTeX sources for INSPIRE record and author ids."""
    text = "\n".join(p.read_text(encoding="utf-8") for p in sources)
    recids = sorted({a or b for a, b in RECORD_RE.findall(text)}, key=int)
    authors = set(AUTHOR_RE.findall(text))
    return recids, authors.pop() if len(authors) == 1 else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent,
                        help="repository root holding the LaTeX sources (default: %(default)s)")
    parser.add_argument("--output", type=Path, default=None,
                        help="generated LaTeX file (default: <root>/LL_InspireData.tex)")
    parser.add_argument("--author", default=None,
                        help="INSPIRE author record id (default: the one linked in the CV)")
    parser.add_argument("--strict", action="store_true",
                        help="exit non-zero if the API cannot be reached")
    parser.add_argument("--print", dest="to_stdout", action="store_true",
                        help="write the generated LaTeX to stdout instead of a file")
    args = parser.parse_args(argv)

    sources = sorted(p for p in args.root.glob("*.tex") if not p.name.endswith("Data.tex"))
    if not sources:
        print(f"no LaTeX sources found in {args.root}", file=sys.stderr)
        return 1

    recids, discovered_author = discover(sources)
    author = args.author or discovered_author
    if not author:
        print("could not determine the INSPIRE author id; pass --author", file=sys.stderr)
        return 1

    print(f"Fetching INSPIRE metrics for author {author} "
          f"and {len(recids)} linked records...")
    try:
        counts = fetch_citation_counts(recids)
        summary = fetch_author_summary(author)
    except Exception as exc:  # noqa: BLE001 - any failure degrades the same way
        print(f"INSPIRE-HEP lookup failed: {exc}", file=sys.stderr)
        if args.strict:
            return 1
        print("Keeping the existing citation data; the CV will still build.",
              file=sys.stderr)
        return 0

    content = render(counts, summary)
    if args.to_stdout:
        sys.stdout.write(content)
        return 0

    output = args.output or args.root / "LL_InspireData.tex"
    changed = write_if_changed(output, content)
    print(f"  {summary['papers']:,} papers, {summary['citations']:,} citations, "
          f"h-index {summary['hindex']}")
    print(f"  {len(counts)} per-paper citation counts")
    print(f"{'Updated' if changed else 'Unchanged'}: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
