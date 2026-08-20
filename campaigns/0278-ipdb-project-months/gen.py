#!/usr/bin/env python3
"""Generate ``patches/0278-ipdb-project-months.yaml`` — IPDB project dates for models the
catalog already dates from another source.

Detection, the project-vs-manufacture classification and the gate all live in
``project_months.sql`` (this dir); this script is a pure emitter over its
``pm_patch_rows`` view, read from the live flipcommons catalog via the duckdb CLI.

Every entry asserts ``project_year`` and ``project_month`` and cites the machine listing
with its own header line as the verbatim quote::

    - model.baby-pac-man:
        note: 'IPDB has no date of manufacture for this model, which means [...]'
        cite:
          ref: "ipdb:125"
          quote: "IPD No. 125 / October 11, 1982 / 2 Players"
        project_year: 1982
        project_month: 10

This is 0268 run again over the population its scope test excluded. 0268 scoped on
``models.year IS NULL`` — the DERIVED fallback, "this model reads as undated on the
site" — which was right for the question it asked and invisible to a model that already
carries a production year from somewhere else. Scoping on ``project_year IS NULL``, the
field itself, finds them.

Both fields are always emitted. ``project_month`` alone would violate the model's own
month-needs-a-year constraint, and the year it needs is the project year — not the
production year the record already holds, which came from a different source and dates a
different event.

The note and the classification are 0268's, unchanged: the quote shows a date but cannot
say which kind of date it is, and that is the whole question. The quote is likewise the
raw header line, which is what preserves IPDB's day precision — 111 of these dates name
a day and the catalog stores year and month only.

Run from the flippatch repo root::

    uv run python3 campaigns/0278-ipdb-project-months/gen.py
    make validate
    make verify-quote-verbatim ARGS="0278"
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Repo root by marker, never by counting parents, so a campaign dir stays movable.
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common

import patchkit as pk  # noqa: E402

PATCH_PATH = pk.PATCHES_DIR / "0278-ipdb-project-months.yaml"
DATES_SQL = HERE / "project_months.sql"

# Admin-only and lint-capped at 80 chars; the rationale lives in README.md and this
# module's docstring, the per-row evidence in each cite quote.
DESCRIPTION = "IPDB project dates for models already dated from another source."

# 0268's note, verbatim, because it is the same claim about the same kind of evidence:
# the cited listing holds a date and no manufacture date. The quote proves the date; only
# this says which kind of date it is — and saying so is OUR inference, which is why the
# note states the premise it rests on rather than presenting the classification as
# something IPDB declared.
NOTE = (
    "IPDB has no date of manufacture for this model, which means the quoted header "
    "date here is a project date."
)


def main() -> int:
    rows = pk.read_view(DATES_SQL, "pm_patch_rows", prefix="pm")
    if not rows:
        raise SystemExit("pm_patch_rows returned no rows — nothing to emit")

    entries: list[str] = []
    for r in sorted(rows, key=lambda r: str(r["slug"])):
        slug = str(r["slug"])
        year, month = r.get("project_year"), r.get("project_month")
        if not isinstance(year, int):
            raise SystemExit(f"{slug}: project_year is not an integer ({year!r})")
        if not isinstance(month, int):
            raise SystemExit(f"{slug}: project_month is not an integer ({month!r})")
        quote = pk.clean_quote(str(r["quote"]).strip())
        if not quote:
            raise SystemExit(f"{slug}: quote became empty after cleaning")
        entries.append(
            pk.entry(
                f"model.{slug}",
                note=NOTE,
                cite={"ref": str(r["cite_ref"]), "quote": quote},
                fields={"project_year": year, "project_month": month},
            )
        )

    pk.write_patch(
        PATCH_PATH,
        attribution="flipcommons-catalog",
        description=DESCRIPTION,
        entries=entries,
    )
    days = sum(1 for r in rows if r.get("ipdb_day") is not None)
    same = sum(1 for r in rows if r.get("project_year") == r.get("production_year"))
    makers = Counter(str(r["manufacturer_name"]) for r in rows)
    top, top_n = makers.most_common(1)[0]
    print(
        f"wrote {PATCH_PATH.relative_to(pk.REPO_ROOT)} — {len(entries)} entries "
        f"({days} quoting a day-precision date, {same} whose project year matches the "
        f"production year already on record; {len(makers)} makers, largest {top} at "
        f"{top_n})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
