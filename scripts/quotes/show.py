#!/usr/bin/env python3
"""Print the source text one ``cite:`` resolves to, or check a draft quote against it.

The authoring counterpart to :mod:`quotes.verbatim` — the same resolution and the
same substring check, aimed at one ref before the quote is written rather than at
patches already authored.

Sharing :meth:`quotes.sources.Sources.resolve_cite` is the point, most of all for
an ``ipdb:`` ref, whose quotable text is a reconstruction of the IPDB page
(:func:`quotes.sources.ipdb_row_text`) that exists nowhere on disk to open. Not to
be confused with ``make extract-page``'s view, which narrows an IPDB row to editor
prose: a legitimate quote of a ``Model Number:`` row is absent from it.

Run via ``make show-source``::

    make show-source ARGS="ipdb:4059"
    make show-source ARGS="https://example.com/page --check 'the first ever'"

Source text goes to stdout and the header to stderr, so a preview pipes cleanly.
Exits 1 when a ``--check`` quote does not verify, 2 when the cite resolves to no
readable text — uncached, or a PDF, which the gate leaves to the author for the
reason :class:`quotes.sources.SourceStatus` gives.
"""

from __future__ import annotations

import argparse
import sys

from quotes.sources import Sources, SourceStatus, require_pinexplore
from quotes.verbatim import check_quote


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="show-source",
        description=(
            "Print the cached source text a cite: ref resolves to — the exact "
            "document `make verify-quote-verbatim` matches quotes against — or "
            "check a draft quote against it with --check."
        ),
    )
    parser.add_argument(
        "ref",
        help="cite ref: an http(s) URL, or ipdb:<id> / opdb:<id> / youtube:<id>",
    )
    parser.add_argument(
        "--archive",
        default=None,
        help="the cite's Wayback snapshot, tried as a fallback like the gate does",
    )
    parser.add_argument(
        "--check",
        default=None,
        metavar="QUOTE",
        help=(
            "verify a draft quote against the resolved text instead of printing "
            "it — the verdict the gate would give, in its wording"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    require_pinexplore()
    resolved = Sources().resolve_cite(args.ref, args.archive)

    if resolved.status is SourceStatus.PDF:
        print(
            f"SKIP-PDF  {args.ref} — cached as a PDF. Extraction reorders and "
            f"drops text, so the gate does not judge PDF quotes and neither "
            f"does this; read the sheet and transcribe.",
            file=sys.stderr,
        )
        return 2
    if resolved.text is None:
        print(
            f"NO-SOURCE {args.ref} — not in the pinexplore stores. Check the "
            f"ref, then fetch or refresh: `web_fetch.py <url>` for a page, "
            f"`make pull` / `make explore` in pinexplore for the stores.",
            file=sys.stderr,
        )
        return 2

    if args.check is None:
        print(f"resolved  {args.ref} — {len(resolved.text)} chars", file=sys.stderr)
        print(resolved.text)
        return 0

    problem = check_quote(args.check, resolved.text)
    if problem is None:
        print(f"OK        verbatim in {args.ref}")
        return 0
    print(f"FAIL      {args.ref} — {problem}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
