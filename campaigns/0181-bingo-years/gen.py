#!/usr/bin/env python3
"""Generate ``patches/0181-bingo-years.yaml`` — years for the year-less bingo corpus.

Matching, ambiguity detection and the gate all live in ``years.sql`` (this dir); this
script is a pure emitter over its ``year_patch_rows`` view, read from the live
flipcommons catalog via the duckdb CLI (run with cwd = the flipcommons checkout, so
the view's ``.read scripts/analysis/catalog.sql`` and its ``ATTACH`` resolve).

Every entry asserts one field — ``year`` — and cites bingo.cdyn.com's machine listing
with that machine's own table row as the verbatim quote::

    - model.acapulco-2:
        year: 2000
        cite:
          ref: https://bingo.cdyn.com/machines/index.html
          quote: '| Acapulco | unknown | six-card | 2000 |'

The cite is a URL rather than a ``scheme:id``, so bingo.cdyn.com must be seeded as a
citation source root — it already is ("Bingo Pinballs"), which is why this patch emits
no ``sources:`` block. ``make verify-quotes`` resolves the URL against pinexplore's web
scrape cache and collapses whitespace on both sides, so the pipe-delimited row verifies
as a substring of the cached page text.

**Every quote is a proposal until ``make verify-quotes`` passes.**

Run from the flippatch repo root::

    uv run python3 campaigns/0181-bingo-years/extract_cdyn.py   # refresh the TSV
    uv run python3 campaigns/0181-bingo-years/gen.py
    make validate
    make verify-quotes
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
# Repo root by marker, never by counting parents, so a campaign dir stays movable.
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common

import patchkit as pk  # noqa: E402

PATCH_PATH = pk.PATCHES_DIR / "0181-bingo-years.yaml"
YEARS_SQL = HERE / "years.sql"
CDYN_URL = "https://bingo.cdyn.com/machines/index.html"

# Admin-only and lint-capped at 80 chars; the rationale lives in README.md and this
# module's docstring, the per-row evidence in each cite quote.
DESCRIPTION = "Production years for year-less bingo machines, from bingo.cdyn.com."



def main() -> int:
    rows = pk.read_view(YEARS_SQL, "year_patch_rows", prefix="year")
    if not rows:
        raise SystemExit("year_patch_rows returned no rows — nothing to emit")

    entries: list[str] = []
    for r in sorted(rows, key=lambda r: str(r["slug"])):
        year = r.get("year")
        if not isinstance(year, int):
            raise SystemExit(f"{r['slug']}: year is not an integer ({year!r})")
        quote = pk.clean_quote(str(r["quote"]).strip())
        if not quote:
            raise SystemExit(f"{r['slug']}: quote became empty after cleaning")
        entries.append(
            pk.entry(
                f"model.{r['slug']}",
                cite={"ref": CDYN_URL, "quote": quote},
                fields={"year": year},
            )
        )

    pk.write_patch(
        PATCH_PATH,
        attribution="flipcommons-catalog",
        description=DESCRIPTION,
        entries=entries,
    )
    keys = Counter(str(r["matched_on"]) for r in rows)
    makers = Counter(str(r["manufacturer_name"]) for r in rows)
    print(
        f"wrote {PATCH_PATH.relative_to(pk.REPO_ROOT)} — {len(entries)} entries "
        f"(matched on: {', '.join(f'{n} by {k}' for k, n in sorted(keys.items()))}; "
        f"{len(makers)} makers, largest {makers.most_common(1)[0][0]} at "
        f"{makers.most_common(1)[0][1]})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
