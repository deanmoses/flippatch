#!/usr/bin/env python3
"""Extract bingo.cdyn.com's machine listing into ``cdyn_machines.tsv`` (this dir).

The listing is one pipe-table per manufacturer — ``Game Name | Game Number | Game
Type | Year`` — and it is the only source found that dates the late European bingo
makers (Sirmo, Splin, Wimi, Show Games, G.A.A.), whose models the catalog carries
with no year at all.

This reads the page from **pinexplore's web scrape cache**, never from the network,
so the extracted rows and the quotes the patch cites come from the same durable blob
``make verify-quotes`` checks against. The cache is located through this repo's own
``common.paths.WEB_CACHE_DB`` and read as plain SQLite — the same store
``scripts/analysis/evidence.sql`` attaches as ``ev``, which is what lets ``years.sql``
check this file back against the live page (see its drift and quote checks). Fetch the
page there first if it is missing::

    cd ../pinexplore
    uv run python3 scripts/web_scrape/web_fetch.py \\
      "https://bingo.cdyn.com/machines/index.html" --query "bingo machines by maker with years"

The TSV is a checked-in AUDIT ARTIFACT, not a cache: it is what ``years.sql`` reads
and what a reviewer diffs when the page changes. Regenerate with::

    uv run python3 campaigns/0181-bingo-years/extract_cdyn.py

A caveat that shapes the whole campaign: the **Game Number column is the literal
string "unknown" for every maker except Bally** (and one Williams row). So this page
supplies YEARS for the European makers and nothing else — the model numbers the
catalog already has for Bally come from IPDB, and no source numbers the Europeans.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]

from common.paths import WEB_CACHE_DB, load_env  # noqa: E402

URL = "https://bingo.cdyn.com/machines/index.html"
OUT = HERE / "cdyn_machines.tsv"


def rows_from_page(text: str) -> list[tuple[str, str, str, str, str]]:
    """Parse the extracted page text into (maker, game, number, type, year) rows.

    Structure: a one-cell row is a manufacturer heading and sets the current maker;
    a four-cell row is a machine. The header row repeats per section and is skipped
    by name. Anything else on the page is not a table row and is ignored.
    """
    maker: str | None = None
    out: list[tuple[str, str, str, str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|") if c.strip()]
        if len(cells) == 1:
            maker = cells[0]
        elif len(cells) == 4 and cells[0] != "Game Name":
            if maker is None:
                raise SystemExit(f"machine row before any maker heading: {line!r}")
            out.append((maker, *cells))  # type: ignore[arg-type]
    return out


def cached_text(url: str) -> str | None:
    """The cached extracted text for ``url``, or ``None`` if it isn't cached.

    Reads ``pages`` straight out of the cache SQLite rather than importing
    pinexplore's ``web_cache`` module, so this campaign depends on the store's shape —
    which ``evidence.sql`` already attaches — and not on a sibling repo's internal
    Python layout. ``pages.url`` holds the NORMALIZED url, so the constant above must
    be written in normalized form; a mismatch surfaces as "not in the cache" rather
    than as wrong rows.
    """
    if not WEB_CACHE_DB.is_file():
        raise SystemExit(f"pinexplore's web cache is missing at {WEB_CACHE_DB}")
    con = sqlite3.connect(f"file:{WEB_CACHE_DB}?mode=ro", uri=True)
    try:
        row = con.execute("SELECT text FROM pages WHERE url = ?", (url,)).fetchone()
    finally:
        con.close()
    return row[0] if row and row[0] else None


def main() -> int:
    load_env()
    text = cached_text(URL)
    if not text:
        raise SystemExit(
            f"{URL} is not in pinexplore's web cache — fetch it first (see this module's docstring)"
        )

    rows = rows_from_page(text)
    if not rows:
        raise SystemExit("parsed zero rows — the page layout changed; fix the parser")

    OUT.write_text(
        "maker\tgame\tnumber\ttype\tyear\n"
        + "".join("\t".join(r) + "\n" for r in rows),
        encoding="utf-8",
    )
    makers = sorted({r[0] for r in rows})
    print(f"wrote {len(rows)} rows across {len(makers)} makers -> {OUT.relative_to(pk.REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
