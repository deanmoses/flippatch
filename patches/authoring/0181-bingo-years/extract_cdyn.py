#!/usr/bin/env python3
"""Extract bingo.cdyn.com's machine listing into ``cdyn_machines.tsv`` (this dir).

The listing is one pipe-table per manufacturer — ``Game Name | Game Number | Game
Type | Year`` — and it is the only source found that dates the late European bingo
makers (Sirmo, Splin, Wimi, Show Games, G.A.A.), whose models the catalog carries
with no year at all.

This reads the page from **pinexplore's web scrape cache**, never from the network,
so the extracted rows and the quotes the patch cites come from the same durable blob
``make verify-quotes`` checks against. Fetch it there first if it is missing::

    cd ../pinexplore
    uv run python3 scripts/web_scrape/web_fetch.py \\
      "https://bingo.cdyn.com/machines/index.html" --query "bingo machines by maker with years"

The TSV is a checked-in AUDIT ARTIFACT, not a cache: it is what ``years.sql`` reads
and what a reviewer diffs when the page changes. Regenerate with::

    uv run python3 patches/authoring/0181-bingo-years/extract_cdyn.py

A caveat that shapes the whole campaign: the **Game Number column is the literal
string "unknown" for every maker except Bally** (and one Williams row). So this page
supplies YEARS for the European makers and nothing else — the model numbers the
catalog already has for Bally come from IPDB, and no source numbers the Europeans.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from common.related_projects import PINEXPLORE_DIR, load_env  # noqa: E402

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


def main() -> int:
    load_env()
    sys.path.insert(0, str(PINEXPLORE_DIR / "scripts" / "web_scrape"))
    import web_cache  # type: ignore[import-not-found]

    page = web_cache.get(URL)
    if not page or not page.get("text"):
        raise SystemExit(
            f"{URL} is not in pinexplore's web cache — fetch it first (see this module's docstring)"
        )

    rows = rows_from_page(str(page["text"]))
    if not rows:
        raise SystemExit("parsed zero rows — the page layout changed; fix the parser")

    OUT.write_text(
        "maker\tgame\tnumber\ttype\tyear\n"
        + "".join("\t".join(r) + "\n" for r in rows),
        encoding="utf-8",
    )
    makers = sorted({r[0] for r in rows})
    print(f"wrote {len(rows)} rows across {len(makers)} makers -> {OUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
