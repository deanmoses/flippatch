"""Emit 0055: retract OPDB's known-bad January months (keeping the genuine ones).

Run from the **flipcommons backend**, after classify.py (pinexplore side) has
written ``opdb-january.csv``:

    cd ../flipcommons/backend && uv run python \
        ../../flippatch/campaigns/0055-opdb-january-months/gen.py

OPDB's January is a mix: month-precision dates transposed into January
(YYYY-MM-01 stored as YYYY-01-MM), year-only dates defaulted to January 1, and
genuine Januaries. classify.py classifies each against the IPDB dump and marks
the corrupt ones to retract; this reads that decision and emits a ``retract:
[month]`` for every model that actually holds an active OPDB January claim and
is marked retract. The retraction is attributed to ``opdb`` (it acts on that
source's own claim) and carries a per-bucket ChangeSet note explaining the
refinement — no citations, and no reassertion: removing OPDB's bad claim lets
the lower-priority IPDB month resolve, or leaves the field empty where nothing
better exists.

Genuine Januaries (IPDB agrees, or a day-precise January with no IPDB date) are
left untouched. Takes numbering hole 0055 (after the 0038 prod boundary).
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATCHES = pk.PATCHES_DIR

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()

# Repo root by marker, never by counting parents, so a campaign dir stays movable.
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common
import patchkit as pk  # noqa: E402

# classify.py holds the per-bucket note text (single source of truth).
sys.path.insert(0, str(HERE))
from classify import BUCKET_NOTES  # noqa: E402

from apps.catalog.models import MachineModel  # noqa: E402
from apps.provenance.models import Claim, Source  # noqa: E402
from django.contrib.contenttypes.models import ContentType  # noqa: E402


def main() -> None:
    decision = {
        r["opdb_id"]: r
        for r in csv.DictReader((HERE / "opdb-january.csv").open())
    }

    ct = ContentType.objects.get_for_model(MachineModel)
    opdb = Source.objects.get(slug="opdb")
    # Every model that actually holds an active OPDB January month claim.
    claimed_ids = Claim.objects.filter(
        content_type=ct, actor=opdb.actor, field_name="month", value=1, is_active=True
    ).values_list("object_id", flat=True)
    models = MachineModel.objects.filter(id__in=list(claimed_ids)).values("slug", "opdb_id")

    entries = []
    kept = no_decision = 0
    from collections import Counter

    bucket_counts: Counter[str] = Counter()
    for m in sorted(models, key=lambda x: x["slug"]):
        row = decision.get(m["opdb_id"])
        if row is None:
            # Holds an OPDB January claim but its opdb_id isn't in the current
            # export (OPDB drift) — leave it rather than guess.
            no_decision += 1
            continue
        if row["retract"] != "yes":
            kept += 1
            continue
        bucket_counts[row["bucket"]] += 1
        entries.append(
            pk.entry(f"model.{m['slug']}", note=BUCKET_NOTES[row["bucket"]], retract=["month"])
        )

    path = pk.write_patch(
        PATCHES / "0055-opdb-january-month-retractions.yaml",
        attribution="opdb",
        description="Retract OPDB's known-bad January months (transposed and year-only defaults).",
        entries=entries,
    )
    print(f"wrote {path.name}: {len(entries)} retractions")
    print(f"  kept (genuine January): {kept}   no decision (opdb drift): {no_decision}")
    for b, n in sorted(bucket_counts.items()):
        print(f"  retracted {b}: {n}")


if __name__ == "__main__":
    main()
