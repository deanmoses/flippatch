#!/usr/bin/env python3
"""Generate ``patches/0268-ipdb-project-dates.yaml`` — IPDB project dates for the models
the catalog holds no date for at all.

Detection, the project-vs-manufacture classification and the gate all live in
``project_dates.sql`` (this dir); this script is a pure emitter over its
``pd_patch_rows`` view, read from the live flipcommons catalog via the duckdb CLI.

Every entry asserts ``project_year`` — plus ``project_month`` where IPDB names a month —
and cites the machine listing with its own header line as the verbatim quote::

    - model.ice-castle:
        note: 'IPDB has no date of manufacture for this model, which means [...]'
        cite:
          ref: "ipdb:3711"
          quote: "IPD No. 3711 / May, 1989 / 4 Players"
        project_year: 1989
        project_month: 5

Two things about that shape are deliberate.

**The quote carries IPDB's day.** 90 of these dates name a day (``December 09, 1935``)
and the catalog stores year and month only. Quoting the whole header line keeps the day
in the evidence rather than discarding it, and keeps the quote verbatim by construction:
the ``ipdb:`` resolver reproduces that field unlabelled in the document
``make verify-quote-verbatim`` matches against.

**The note carries the classification.** The quote shows a date but cannot say which
kind of date it is, and that is the entire question this campaign answers — so the note
is the one thing standing between the evidence and the field it lands in.

Run from the flippatch repo root::

    uv run python3 campaigns/0268-ipdb-project-dates/gen.py
    make validate
    make verify-quote-verbatim
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

PATCH_PATH = pk.PATCHES_DIR / "0268-ipdb-project-dates.yaml"
DATES_SQL = HERE / "project_dates.sql"

# Admin-only and lint-capped at 80 chars; the rationale lives in README.md and this
# module's docstring, the per-row evidence in each cite quote.
DESCRIPTION = "Project dates from IPDB for models carrying no date at all."

# One note, every entry, because one fact justifies every entry: the cited listing holds
# a date and no manufacture date. The quote proves the date; only this says which kind of
# date it is — and saying so is OUR inference, which is why the note states the premise
# it rests on rather than presenting the classification as something IPDB declared.
NOTE = (
    "IPDB has no date of manufacture for this model, which means the quoted header "
    "date here is a project date."
)


def main() -> int:
    rows = pk.read_view(DATES_SQL, "pd_patch_rows", prefix="pd")
    if not rows:
        raise SystemExit("pd_patch_rows returned no rows — nothing to emit")

    entries: list[str] = []
    for r in sorted(rows, key=lambda r: str(r["slug"])):
        slug = str(r["slug"])
        year, month = r.get("project_year"), r.get("project_month")
        if not isinstance(year, int):
            raise SystemExit(f"{slug}: project_year is not an integer ({year!r})")
        if month is not None and not isinstance(month, int):
            raise SystemExit(f"{slug}: project_month is not an integer ({month!r})")
        quote = pk.clean_quote(str(r["quote"]).strip())
        if not quote:
            raise SystemExit(f"{slug}: quote became empty after cleaning")
        fields: dict[str, object] = {"project_year": year}
        if month is not None:
            fields["project_month"] = month
        entries.append(
            pk.entry(
                f"model.{slug}",
                note=NOTE,
                cite={"ref": str(r["cite_ref"]), "quote": quote},
                fields=fields,
            )
        )

    pk.write_patch(
        PATCH_PATH,
        attribution="flipcommons-catalog",
        description=DESCRIPTION,
        entries=entries,
    )
    months = sum(1 for r in rows if r.get("project_month") is not None)
    days = sum(1 for r in rows if r.get("ipdb_day") is not None)
    makers = Counter(str(r["manufacturer_name"]) for r in rows)
    top, top_n = makers.most_common(1)[0]
    print(
        f"wrote {PATCH_PATH.relative_to(pk.REPO_ROOT)} — {len(entries)} entries "
        f"({months} with a month, {days} quoting a day-precision date; "
        f"{len(makers)} makers, largest {top} at {top_n})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
