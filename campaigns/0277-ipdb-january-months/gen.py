#!/usr/bin/env python3
"""Generate ``patches/0277-ipdb-january-months.yaml`` — the production months our
baseline could not read out of IPDB's structured date field.

Detection, the production-vs-project classification and the gate all live in
``january_months.sql`` (this dir); this script is a pure emitter over its
``jm_patch_rows`` view, read from the live flipcommons catalog via the duckdb CLI.

Every entry asserts ``production_month`` alone and cites the machine listing with its own
header line as the verbatim quote::

    - model.across-the-board:
        note: 'IPDB has a date of manufacture for this model, which means [...]'
        cite:
          ref: "ipdb:12"
          quote: "IPD No. 12 / January, 1938 / 1 Player"
        production_month: 1

Three things about that shape are deliberate.

**No year is emitted.** Every target already carries a ``production_year``, asserted by
``ipdb`` from this same listing — our baseline read the year out of the structured field
and only the month was lost. Re-asserting the year would compete with a claim that
already says the same thing.

**The quote is the header line, not the date.** IPDB renders a month-precision date as
``January, 1938`` and a year-precision one as a bare ``1938``, and that difference is the
entire evidence for this campaign. Quoting the whole line keeps the distinction visible
to a reader, and keeps the quote verbatim by construction: the ``ipdb:`` resolver
reproduces that field unlabelled in the document ``make verify-quote-verbatim`` matches
against.

**The note carries the classification.** The quote shows a date but cannot say which kind
of date it is — the header line is unlabelled — so the note states the premise that puts
the month in ``production_month`` rather than ``project_month``. It is 0268's note
inverted, and for the same reason.

Run from the flippatch repo root::

    uv run python3 campaigns/0277-ipdb-january-months/gen.py
    make validate
    make verify-quote-verbatim ARGS="0277"
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

PATCH_PATH = pk.PATCHES_DIR / "0277-ipdb-january-months.yaml"
MONTHS_SQL = HERE / "january_months.sql"

# Admin-only and lint-capped at 80 chars; the rationale lives in README.md and this
# module's docstring, the per-row evidence in each cite quote.
DESCRIPTION = "Production months IPDB names that our baseline could not read."

# One note, every entry, because one fact justifies every entry: the cited listing holds
# a manufacture date, so the date its header line names is a production date. The quote
# proves the date; only this says which kind of date it is — and saying so is OUR
# inference, which is why the note states the premise it rests on rather than presenting
# the classification as something IPDB declared.
NOTE = (
    "IPDB has a date of manufacture for this model, which means the quoted header "
    "date here is a production date."
)


def main() -> int:
    rows = pk.read_view(MONTHS_SQL, "jm_patch_rows", prefix="jm")
    if not rows:
        raise SystemExit("jm_patch_rows returned no rows — nothing to emit")

    entries: list[str] = []
    for r in sorted(rows, key=lambda r: str(r["slug"])):
        slug = str(r["slug"])
        month = r.get("production_month")
        if not isinstance(month, int):
            raise SystemExit(f"{slug}: production_month is not an integer ({month!r})")
        quote = pk.clean_quote(str(r["quote"]).strip())
        if not quote:
            raise SystemExit(f"{slug}: quote became empty after cleaning")
        entries.append(
            pk.entry(
                f"model.{slug}",
                note=NOTE,
                cite={"ref": str(r["cite_ref"]), "quote": quote},
                fields={"production_month": month},
            )
        )

    pk.write_patch(
        PATCH_PATH,
        attribution="flipcommons-catalog",
        description=DESCRIPTION,
        entries=entries,
    )
    months = Counter(int(r["production_month"]) for r in rows)  # type: ignore[arg-type]
    makers = Counter(str(r["manufacturer_name"]) for r in rows)
    top, top_n = makers.most_common(1)[0]
    spread = ", ".join(f"month {m}: {n}" for m, n in sorted(months.items()))
    print(
        f"wrote {PATCH_PATH.relative_to(pk.REPO_ROOT)} — {len(entries)} entries "
        f"({spread}; {len(makers)} makers, largest {top} at {top_n})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
