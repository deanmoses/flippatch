"""Emit 0011-game-formats.yaml from worksheet.csv.

Two-stage authoring (see DataPatchAuthoring.md):
  classify.py  (pinexplore, reads DuckDB)        -> worksheet.csv
  gen.py       (this file, run from the backend)  -> the patch YAML

0011 is assignment-only: it positively assigns game_format = pitch-and-bat,
shuffle or bagatelle to models 0010 left null, off a POSITIVE IPDB signal. No
vocab patch is needed - all three GameFormat rows already exist (0009).

Run from the backend so Django can read live guard values:
  cd flipcommons/backend && uv run python ../../pindata/patches/authoring/0011-game-formats/gen.py
"""

import csv
import os
import sys
from pathlib import Path

import django

sys.path.insert(0, os.getcwd())  # backend on path (run this from flipcommons/backend)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # for `import patchkit`
import patchkit as pk  # noqa: E402
from apps.catalog.models import MachineModel  # noqa: E402

OUT = HERE.parent.parent  # .../patches/authoring/<set>/ -> .../patches/
WORKSHEET = HERE / "worksheet.csv"

rows = list(csv.DictReader(WORKSHEET.open()))
ipdb_ids = [int(r["ipdb_id"]) for r in rows]
live = {
    m["ipdb_id"]: m
    for m in MachineModel.objects.filter(ipdb_id__in=ipdb_ids).values("slug", "ipdb_id")
}
pk.check_resolved(ipdb_ids, live)

built = []
for r in rows:
    m = live[int(r["ipdb_id"])]
    built.append(
        (
            m["slug"],
            pk.entry(
                f"model.{m['slug']}",
                expect=pk.guard(m, prefer=("ipdb_id",)),
                note=pk.source_note("IPDB", r["quote"]),
                cite=f"ipdb:{r['cite_ipdb']}",
                fields={"game_format": r["format"]},
            ),
        )
    )
entries = [e for _, e in sorted(built, key=lambda be: be[0])]  # slug-ordered

pk.write_patch(
    OUT / "0011-game-formats.yaml",
    attribution="flipcommons-catalog",
    description="Assign game_format = pitch-and-bat, shuffle or bagatelle.",
    entries=entries,
)

print(f"wrote 0011-game-formats.yaml ({len(entries)} entries)")
