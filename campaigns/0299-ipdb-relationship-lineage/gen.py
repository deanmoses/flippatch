#!/usr/bin/env python3
"""Emit the hand-pass patch: the 0128-parked lineage adjudications.

One entry per model from ``lineage.sql``'s ``lineage_patch_rows`` -- the
adjudication table minus any edge the catalog already carries, so a re-run after
the apply legitimately emits nothing and says so. The judgments themselves live in
``_lineage_adjudications`` beside their rationale; this module only groups rows
into entries (a model with two same-quote donors becomes one entry with two
members) and hands them to patchkit.

The quotes were each verified verbatim (``make show-source --check``) before being
recorded in the table, and ``make verify-quote-verbatim`` re-checks the emitted
patch independently.

Run from the flippatch repo root::

    uv run python3 campaigns/0299-ipdb-relationship-lineage/gen.py
    make validate
"""

from __future__ import annotations

import sys
from collections import Counter
from itertools import groupby
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Repo root by marker, never by counting parents, so a campaign dir stays movable.
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common

import patchkit as pk  # noqa: E402

PATCH_PATH = pk.PATCHES_DIR / "0299-conversion-lineage.yaml"
LINEAGE_SQL = HERE / "lineage.sql"

# The `description:` is Admin-only and lint-capped at 80 chars; the campaign's
# rationale lives in lineage.sql's adjudication table and the dir README.
DESCRIPTION = "Conversion lineage for 20 machines, from campaign 0128's parked verdicts."


def main() -> int:
    rows = pk.read_view(LINEAGE_SQL, "lineage_patch_rows", prefix="lineage")
    if not rows:
        raise SystemExit(
            "lineage_patch_rows is empty — every adjudicated edge is already in the catalog"
        )
    entries: list[str] = []
    keyed = sorted(rows, key=lambda r: (str(r["model_slug"]), str(r["quote"])))
    for (slug, quote), group in groupby(
        keyed, key=lambda r: (str(r["model_slug"]), str(r["quote"]))
    ):
        members = list(group)
        edges = []
        for r in members:
            edge: dict[str, str] = {}
            if r["target_machine"] is not None:
                edge["target_machine"] = str(r["target_machine"])
            else:
                edge["target_label"] = str(r["target_label"])
            edge["relationship_type"] = str(r["relationship_type"])
            edge["license_status"] = str(r["license_status"])
            edges.append(edge)
        entries.append(
            pk.entry(
                f"model.{slug}",
                cite={"ref": f"ipdb:{members[0]['ipdb_id']}", "quote": quote},
                model_relationship=edges,
            )
        )
    pk.write_patch(
        PATCH_PATH,
        attribution="flipcommons-catalog",
        description=DESCRIPTION,
        entries=entries,
    )
    kinds = Counter(str(r["relationship_type"]) for r in rows)
    labels = sum(1 for r in rows if r["target_machine"] is None)
    print(
        f"wrote {PATCH_PATH.relative_to(pk.REPO_ROOT)} — {len(entries)} entries, "
        f"{len(rows)} edges ({', '.join(f'{n} {k}' for k, n in sorted(kinds.items()))}; "
        f"{labels} label-target)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
