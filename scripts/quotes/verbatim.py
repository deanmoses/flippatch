#!/usr/bin/env python3
"""Verify every ``cite:`` quote in the patches is verbatim in its source.

A ``quote:`` is trustworthy only if a reviewer could follow the citation and
ctrl-F find it, so every span must be an exact verbatim substring of the source
text, in source order. Matching allows only the normalizations
DataPatchAuthoring.md sanctions — smart quotes straightened and whitespace
collapsed (text extraction hard-wraps prose that renders as spaces) — applied to
the SOURCE side; the quote itself must already be in normalized form (straight
quotes, ``[...]`` ellipses).

A PDF quote is reported ``SKIP-PDF`` and left to the author, for the reason
:class:`quotes.sources.SourceStatus` gives. What that does **not** change is
what counts as a quote. The test is whether the evidence is *text*, not whether
extraction caught it: outlined flyer type and a manual with no text layer are
words on the sheet and are quotable once read, while a checkmark in a
feature-matrix column is a mark and never becomes text by being looked at — it
stays a quote-less cite (``ref`` + ``locator`` + ``note``). Quoting a feature's
row label to establish an edition column remains the forgery both rules exist to
stop.

Run via ``make verify-quote-verbatim``. Exits non-zero on any non-verbatim quote
or any quote whose source is missing from the cache (an unverifiable quote is
not a verified one — ``make pull`` in pinexplore refreshes the cache). A missing
document is a failure, never a skip: a PDF the cache does not hold is one a
session could not have read.

A run may be scoped to patch ids (``make verify-quote-verbatim ARGS="0223"``);
the summary stamps the scope, so a partial run cannot read as a clean full pass.
:mod:`quotes.show` is the same resolution aimed at one ref, for previewing a
source or settling a draft quote before it is written into a patch.
"""

from __future__ import annotations

import argparse
import re
import sys
from typing import TYPE_CHECKING

from common.patch_files import patch_paths, unmatched_scope_error
from common.paths import PATCHES_DIR

from quotes.sources import Sources, SourceStatus, require_pinexplore

if TYPE_CHECKING:
    from collections.abc import Iterator

_SMART = {"“": '"', "”": '"', "‘": "'", "’": "'"}


def normalize(text: str) -> str:
    """Straighten smart quotes and collapse whitespace runs to single spaces."""
    for smart, straight in _SMART.items():
        text = text.replace(smart, straight)
    return re.sub(r"\s+", " ", text)


def check_quote(quote: str, source: str) -> str | None:
    """Why *quote* fails to verify against *source*, or None if it verifies.

    Each ``[...]``-separated span must appear verbatim in the normalized
    source, and spans must appear in source order. A quote leaving no spans at
    all fails: every span would verify vacuously, so ellipses alone would carry
    a claim while resting on nothing.
    """
    spans = [s.strip() for s in quote.split("[...]") if s.strip()]
    if not spans:
        return f"quote has no text to verify: {quote[:60]!r}"
    src = normalize(source)
    pos = 0
    for span in spans:
        found = src.find(normalize(span), pos)
        if found == -1:
            if src.find(normalize(span)) != -1:
                return f"span out of source order: {span[:60]!r}"
            return f"span not verbatim in source: {span[:60]!r}"
        pos = found + len(normalize(span))
    return None


def _quote_units(body: dict[str, object]) -> Iterator[tuple[str, str | None, str]]:
    """Every (ref, archive, quote) triple in an entry: header plus changesets.

    Walks the entry-level ``cite:`` mapping and each inline ``cites:`` entry
    carrying a quote, so inline footnote quotes are verified against their
    source exactly like entry-level ones.
    """
    changesets = body.get("changesets")
    units: list[object] = [body]
    if isinstance(changesets, list):
        units.extend(changesets)
    for unit in units:
        if not isinstance(unit, dict):
            continue
        cite = unit.get("cite")
        specs = cite if isinstance(cite, list) else [cite]
        for spec in specs:
            if isinstance(spec, dict) and spec.get("quote"):
                archive = spec.get("archive")
                yield (
                    str(spec["ref"]),
                    str(archive) if archive else None,
                    str(spec["quote"]),
                )
        cites = unit.get("cites")
        if isinstance(cites, dict):
            for value in cites.values():
                if isinstance(value, dict) and value.get("quote"):
                    archive = value.get("archive")
                    yield (
                        str(value["ref"]),
                        str(archive) if archive else None,
                        str(value["quote"]),
                    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="verify-quote-verbatim",
        description=(
            "Verify every cite: quote in the patches is verbatim in its cached "
            "source text. Bare covers every patch; patch ids scope the run."
        ),
    )
    parser.add_argument(
        "patch_ids",
        nargs="*",
        help="patch numbers/stems to verify (default: every patch)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    import yaml

    args = _parse_args(argv)
    error = unmatched_scope_error(PATCHES_DIR, args.patch_ids)
    if error is not None:
        print(f"error: {error}", file=sys.stderr)
        return 2
    patches = patch_paths(PATCHES_DIR, args.patch_ids)

    require_pinexplore()
    sources = Sources()
    ok = failed = skipped = 0
    for patch in patches:
        doc = yaml.safe_load(patch.read_text())
        for claim in doc.get("claims", []):
            ((entity, body),) = claim.items()
            for ref, archive, quote in _quote_units(body):
                resolved = sources.resolve_cite(ref, archive)
                if resolved.status is SourceStatus.PDF:
                    # Name each one so the run never reads as covering what it did not.
                    skipped += 1
                    print(f"SKIP-PDF  {patch.name} {entity} — {ref[:70]}")
                    continue
                if resolved.text is None:
                    failed += 1
                    print(
                        f"NO-SOURCE {patch.name} {entity} — {ref[:70]} "
                        f"(not in the pinexplore cache; `make pull` there?)"
                    )
                    continue
                problem = check_quote(quote, resolved.text)
                if problem is None:
                    ok += 1
                else:
                    failed += 1
                    print(f"FAIL      {patch.name} {entity} — {problem}")
    tail = f", {skipped} skipped (PDF — author-checked)" if skipped else ""
    scope = f" (scope: {' '.join(args.patch_ids)})" if args.patch_ids else ""
    print(f"\nverify-quote-verbatim{scope}: {ok} verified, {failed} failed{tail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
