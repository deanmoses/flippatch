"""Emit 0010-game-formats.yaml from worksheet.csv.

The worked example for patchkit. Two-stage authoring (see DataPatchAuthoring.md):
  classify.py / xref_sweep.py  (pinexplore, read DuckDB)  -> worksheet.csv
  gen.py       (this file, run from the flipcommons backend)  -> the patch YAML

The vocab patch 0009-game-format-vocab.yaml is hand-written, not generated: it is
four static rows with no guards/notes/cites, so the generator would buy nothing
(per DataPatchAuthoring.md's "handful of static edits -> hand-write" rule).

Run from the backend so Django can read live guard values:
  cd flipcommons/backend && uv run python ../../pindata/patches/authoring/0010-game-formats/gen.py
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

# --- 0010 assignments (attribution flipcommons-catalog, cite ipdb) ---
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
    OUT / "0010-game-formats.yaml",
    # flipcommons (not IPDB) does the work of parsing IPDB's free-text notes into a
    # structured game_format value, so the claim is ours; each entry still cite:s the
    # IPDB record the evidence came from.
    attribution="flipcommons-catalog",
    description=(
        "Assign game_format to some non-pinball machines: slot-machine, video-game, "
        "gun-game, shuffle, bagatelle, miscellaneous."
    ),
    entries=entries,
)

print(
    f"wrote 0010-game-formats.yaml ({len(entries)} entries); 0009 vocab is hand-written"
)
