#!/usr/bin/env python3
r"""Extract bingo.cdyn.com's per-machine Features blocks into ``cdyn_features.tsv``.

Every cdyn machine page opens with a ``Game Parameters`` table whose last row is a
``Features`` cell — the site's own feature vocabulary applied to that one machine::

    | Features | - advancing odds/scores - colored lines - in-line scoring - section scoring |

That cell is the signal this campaign rests on: it says, per machine and in cdyn's own
words, whether the game scored lines, sections, or both. The vocabulary it draws from is
defined at https://bingo.cdyn.com/machines/features.html.

Pages are read from **pinexplore's web scrape cache**, never from the network, so the
rows extracted here and the quotes the patch cites come from the same durable blob
``make verify-quote-verbatim`` checks against — the same store
``scripts/analysis/evidence.sql`` attaches as ``ev``. Seed the cache first; the machine
URLs are the outbound links of the alpha listing::

    cd ../pinexplore
    uv run python scripts/web_scrape/web_cache.py links \
      https://bingo.cdyn.com/machines/index.html --limit 0 \
      | grep -E '^https://bingo\.cdyn\.com/machines/[a-z_]+/' | cut -f1 > /tmp/cdyn_urls.txt
    uv run python scripts/web_scrape/web_fetch.py --from-file /tmp/cdyn_urls.txt --max-age 99999

The TSV is a checked-in AUDIT ARTIFACT, not a cache: it is what ``scoring.sql`` reads and
what a reviewer diffs when cdyn edits a page. Regenerate with::

    uv run python3 campaigns/0262-bingo-scoring/extract_cdyn_features.py
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from common.paths import WEB_CACHE_DB, load_env  # noqa: E402

OUT = HERE / "cdyn_features.tsv"
URL_RE = re.compile(r"^https://bingo\.cdyn\.com/machines/([a-z_0-9]+)/([a-z_0-9]+)$")
# The parameter table is two-cell pipe rows; the title line is "Maker : Game".
ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|$")
TITLE_RE = re.compile(r"^title:\s*(.+?)\s*:\s*(.+)$")
COLUMNS = ("url", "maker_dir", "maker", "game", "number", "year", "game_type", "features_row", "features")


def parse_page(url: str, text: str) -> dict[str, str] | None:
    """One machine page -> its parameter row, or ``None`` if it carries no Features cell.

    A page with no ``Features`` row is not an error: cdyn documents some machines only
    with images. Such a page simply contributes nothing, which is the safe default — an
    unparsed page cannot produce a wrong attachment, only a missing one.
    """
    match = URL_RE.match(url)
    if not match:
        return None
    maker_dir, _slug = match.groups()

    maker = game = ""
    params: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if title := TITLE_RE.match(line):
            maker, game = title.group(1), title.group(2)
        elif line.startswith("|"):
            if row := ROW_RE.match(line):
                key, value = row.group(1), row.group(2)
                if key and key != "---" and value != "---":
                    params.setdefault(key, value)

    features_row = params.get("Features", "")
    if not features_row:
        return None
    # The cell is a run of "- feature" items on one line. Splitting on the leading
    # "- " of each item is what turns it back into a list; a feature name may itself
    # contain "/" or spaces ("advancing odds/scores", "extended/extra time/play"),
    # so nothing narrower than the item bullet is a safe delimiter.
    features = [f.strip() for f in re.split(r"(?:^|\s)-\s", features_row) if f.strip()]
    return {
        "url": url,
        "maker_dir": maker_dir,
        "maker": maker,
        "game": game,
        "number": params.get("Game Number", ""),
        "year": params.get("Manufacture Date", ""),
        "game_type": params.get("Game Type", ""),
        # The verbatim source row, kept whole: it is what the patch quotes.
        "features_row": "| Features | " + features_row + " |",
        "features": "|".join(features),
    }


def main() -> int:
    load_env()
    if not WEB_CACHE_DB.is_file():
        raise SystemExit(f"pinexplore's web cache is missing at {WEB_CACHE_DB}")
    con = sqlite3.connect(f"file:{WEB_CACHE_DB}?mode=ro", uri=True)
    try:
        pages = con.execute(
            "SELECT url, text FROM pages "
            "WHERE url LIKE 'https://bingo.cdyn.com/machines/%/%' AND text IS NOT NULL "
            "ORDER BY url"
        ).fetchall()
    finally:
        con.close()

    rows = [row for url, text in pages if (row := parse_page(url, text))]
    if not rows:
        raise SystemExit("parsed zero machine rows — the page layout changed; fix the parser")

    OUT.write_text(
        "\t".join(COLUMNS) + "\n"
        + "".join("\t".join(r[c] for c in COLUMNS) + "\n" for r in rows),
        encoding="utf-8",
    )
    makers = sorted({r["maker_dir"] for r in rows})
    print(f"wrote {len(rows)} machine rows across {len(makers)} makers -> {OUT.relative_to(REPO_ROOT)}")
    print(f"  ({len(pages)} machine pages cached, {len(pages) - len(rows)} with no Features cell)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
