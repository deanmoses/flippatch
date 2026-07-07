"""Emit 0056: retract flipcommons-catalog's OPDB-derived bad January months.

Run from the **flipcommons backend**, after 0055's classify.py has written
``opdb-january.csv``:

    cd ../flipcommons/backend && uv run python \
        ../../flippatch/patches/authoring/0056-flipcommons-catalog-january-months/gen.py

The seed derived its ``month`` from OPDB's manufacture dates and inherited
OPDB's January corruption (month-precision dates transposed into January, plus
year-only defaults), stamping it with the ``flipcommons-catalog`` attribution
at the highest priority — so it overrides IPDB's real month. 703 of the 724
flipcommons-catalog January claims coincide exactly with OPDB's January set,
confirming the shared origin.

This retracts flipcommons-catalog's month claim for every model whose OPDB
January was classified corrupt in ``opdb-january.csv`` (the same per-model
decision drives both retractions). Genuine Januaries are kept. Stragglers whose
flipcommons-catalog January has no OPDB counterpart are reported and kept
(conservative — no retraction without evidence). Retract-only, no reassertion:
removing our bad claim (and OPDB's, in 0055) lets IPDB's month resolve.

Takes numbering hole 0056 (after the 0038 prod boundary).
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATCHES = HERE.parent.parent
OPDB_CSV = HERE.parent / "0055-opdb-january-months" / "opdb-january.csv"

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()

sys.path.insert(0, str(HERE.parent))
import patchkit as pk  # noqa: E402

from apps.catalog.models import MachineModel  # noqa: E402
from apps.provenance.models import Claim, Source  # noqa: E402
from django.contrib.contenttypes.models import ContentType  # noqa: E402

# The month came from OPDB's date, so the explanation names that origin.
FC_NOTES = {
    "A-transposed": (
        "The seed derived this month from OPDB's manufacture date, which stored "
        "a month-precision date with the month transposed into the day position "
        "(reading as January). Retracted as an ingest refinement; the real "
        "month, recorded by IPDB, now resolves."
    ),
    "B-year-default": (
        "The seed derived this month from OPDB's manufacture date, which "
        "defaulted a year-only date to January 1. Retracted as an ingest "
        "refinement so IPDB's real month resolves."
    ),
    "D-disagreement": (
        "The seed derived this January from OPDB's manufacture date, which is "
        "not credible - it disagrees with IPDB and fits neither a genuine "
        "January nor OPDB's month-into-day transposition. Retracted as an "
        "ingest refinement so IPDB's month resolves."
    ),
    "E-year-default-no-ipdb": (
        "The seed derived this month from OPDB's manufacture date, a year-only "
        "date defaulted to January 1, with no other source recording a month. "
        "Retracted as an ingest refinement - no month is better than an "
        "untrustworthy one."
    ),
}


def main() -> None:
    decision = {r["opdb_id"]: r for r in csv.DictReader(OPDB_CSV.open())}

    ct = ContentType.objects.get_for_model(MachineModel)
    fc = Source.objects.get(slug="flipcommons-catalog")
    claimed_ids = Claim.objects.filter(
        content_type=ct, actor=fc.actor, field_name="month", value=1, is_active=True
    ).values_list("object_id", flat=True)
    models = MachineModel.objects.filter(id__in=list(claimed_ids)).values("slug", "opdb_id")

    from collections import Counter

    entries, stragglers = [], []
    kept = 0
    bucket_counts: Counter[str] = Counter()
    for m in sorted(models, key=lambda x: x["slug"]):
        row = decision.get(m["opdb_id"]) if m["opdb_id"] else None
        if row is None:
            stragglers.append(m["slug"])  # fc-January with no OPDB counterpart
            continue
        if row["retract"] != "yes":
            kept += 1
            continue
        bucket_counts[row["bucket"]] += 1
        entries.append(
            pk.entry(f"model.{m['slug']}", note=FC_NOTES[row["bucket"]], retract=["month"])
        )

    path = pk.write_patch(
        PATCHES / "0056-flipcommons-catalog-january-month-retractions.yaml",
        attribution="flipcommons-catalog",
        description="Retract flipcommons-catalog's OPDB-derived bad January months.",
        entries=entries,
    )
    print(f"wrote {path.name}: {len(entries)} retractions")
    print(f"  kept (genuine January): {kept}   stragglers kept (no OPDB counterpart): {len(stragglers)}")
    for b, n in sorted(bucket_counts.items()):
        print(f"  retracted {b}: {n}")
    if stragglers:
        print("  straggler slugs:", ", ".join(stragglers))


if __name__ == "__main__":
    main()
