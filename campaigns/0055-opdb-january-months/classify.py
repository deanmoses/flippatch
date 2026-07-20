"""Classify every OPDB January date as corrupt or genuine.

Run from the **pinexplore** repo root (needs the raw OPDB export and the IPDB
dump):

    uv run python ../flippatch/campaigns/0055-opdb-january-months/classify.py

OPDB stores a month-precision date ``YYYY-MM-01`` as ``YYYY-01-MM`` — month and
the default day-01 transposed — and also defaults a year-only date to
``YYYY-01-01``. Both pool into January, so OPDB's January is a mix of corrupt
and genuine values. Keyed on the raw OPDB date (for the day) and the IPDB dump
(for a reference month), this writes ``opdb-january.csv`` — one row per OPDB
January machine with its bucket and a retract/keep decision under this rule:

  RETRACT when OPDB month == January AND
    - IPDB has a date whose month is NOT January (transposed / year-default /
      disagreement — OPDB's January is wrong), or
    - no IPDB date AND OPDB day == 01 (a year-only default).
  KEEP when
    - IPDB also says January (genuine — real day-precise or agreed
      month-precision January), or
    - no IPDB date AND OPDB day > 01 (a plausibly-real day-precise January).

The decision never corrects OPDB's value — the retract simply removes a
known-bad claim so the lower-priority IPDB month resolves, or the field goes
empty where nothing better exists. gen.py (flipcommons side) reads this table
and emits the retracts for the models that actually hold the OPDB claim.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPDB_JSON = Path("ingest_sources/opdb_export_machines.json")
EXPLORE = Path("explore.duckdb")


def bucket_and_decision(opdb_day: str, ipdb_month: int | None) -> tuple[str, bool]:
    """Return (bucket, retract) for one OPDB January record."""
    if ipdb_month is not None:
        if ipdb_month == 1:
            return "C-genuine-january", False  # IPDB agrees January
        if opdb_day == "01":
            return "B-year-default", True  # OPDB defaulted a year-only date to Jan 1
        if int(opdb_day) == ipdb_month:
            return "A-transposed", True  # month sits in the day slot; == IPDB's month
        return "D-disagreement", True  # non-January per IPDB, no clean rule
    # No IPDB date to check against.
    if opdb_day == "01":
        return "E-year-default-no-ipdb", True
    return "E-day-precise-keep", False


# ChangeSet note per bucket — explains the ingest refinement (no citations).
BUCKET_NOTES = {
    "A-transposed": (
        "OPDB stored this month-precision date with the month transposed into "
        "the day position (YYYY-MM-01 as YYYY-01-MM), so its month reads as "
        "January. Retracted as an ingest refinement; the real month, recorded "
        "by IPDB, now resolves."
    ),
    "B-year-default": (
        "OPDB defaulted a year-only manufacture date to January 1, so its "
        "January carries no month information; IPDB records a real month. "
        "Retracted as an ingest refinement so that month resolves."
    ),
    "D-disagreement": (
        "OPDB's January is not credible: it disagrees with IPDB's month and "
        "fits neither a genuine January nor OPDB's month-into-day "
        "transposition. Retracted as an ingest refinement so IPDB's month "
        "resolves."
    ),
    "E-year-default-no-ipdb": (
        "OPDB defaulted a year-only manufacture date to January 1 and no other "
        "source records a month. Retracted as an ingest refinement - no month "
        "is better than an untrustworthy one."
    ),
}


def main() -> None:
    if not OPDB_JSON.exists() or not EXPLORE.exists():
        sys.exit("run from the pinexplore repo root (needs ingest_sources/ and explore.duckdb)")

    import duckdb

    con = duckdb.connect(str(EXPLORE), read_only=True)
    ipdb_month: dict[int, int] = {}
    for iid, d in con.execute(
        "SELECT IpdbId, DateOfManufacture FROM ipdb_machines WHERE DateOfManufacture IS NOT NULL"
    ).fetchall():
        if d:
            ipdb_month[int(iid)] = int(str(d)[5:7])

    opdb = json.loads(OPDB_JSON.read_text())
    rows = []
    for m in opdb:
        d = m.get("manufacture_date")
        if not d or d[5:7] != "01":  # only OPDB January records
            continue
        iid = m.get("ipdb_id")
        ipm = ipdb_month.get(int(iid)) if iid else None
        bucket, retract = bucket_and_decision(d[8:10], ipm)
        rows.append(
            {
                "opdb_id": m["opdb_id"],
                "name": m["name"],
                "opdb_date": d,
                "opdb_day": d[8:10],
                "ipdb_id": iid or "",
                "ipdb_month": ipm if ipm is not None else "",
                "bucket": bucket,
                "retract": "yes" if retract else "no",
            }
        )

    rows.sort(key=lambda r: (r["bucket"], r["opdb_date"]))
    with (HERE / "opdb-january.csv").open("w", newline="") as f:
        w = csv.DictWriter(
            f,
            lineterminator="\n",
            fieldnames=["opdb_id", "name", "opdb_date", "opdb_day", "ipdb_id", "ipdb_month", "bucket", "retract"],
        )
        w.writeheader()
        w.writerows(rows)

    from collections import Counter

    by_bucket = Counter(r["bucket"] for r in rows)
    n_retract = sum(1 for r in rows if r["retract"] == "yes")
    print(f"OPDB January records: {len(rows)}  retract: {n_retract}  keep: {len(rows) - n_retract}")
    for b, n in sorted(by_bucket.items()):
        print(f"  {b}: {n}")


if __name__ == "__main__":
    main()
