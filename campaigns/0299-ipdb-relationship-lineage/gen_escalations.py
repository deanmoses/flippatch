#!/usr/bin/env python3
"""Emit the escalation patch: the adjudicated review tier of the 0299 sweep run.

One entry per model from ``lineage.sql``'s ``lineage_escalation_patch_rows`` -- the
escalation adjudication table minus any edge the catalog already carries, so a re-run
after the apply legitimately emits nothing and says so. The adjudication rules and
their rationale live beside the table in ``lineage.sql``; the escalation ledger there
ties every review-tier model to this table or a recorded dismissal, both directions.

``license_status`` is ``unknown`` on every emitted member — no note in this tier
establishes authorization. Quotes were each ``--check``-verified before being
recorded, and ``make verify-quote-verbatim`` re-checks the emitted patch.

Run from the flippatch repo root::

    uv run python3 campaigns/0299-ipdb-relationship-lineage/gen_escalations.py
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

PATCH_PATH = pk.PATCHES_DIR / "0301-conversion-lineage-escalations.yaml"
LINEAGE_SQL = HERE / "lineage.sql"

DESCRIPTION = "Conversion lineage for 58 machines, adjudicated from the 0299 sweep review."


def main() -> int:
    rows = pk.read_view(LINEAGE_SQL, "lineage_escalation_patch_rows", prefix="lineage")
    if not rows:
        raise SystemExit(
            "lineage_escalation_patch_rows is empty — every vetted fill edge is already in the catalog"
        )
    entries: list[str] = []
    keyed = sorted(rows, key=lambda r: (str(r["model_slug"]), str(r["target_machine"])))
    for slug, group in groupby(keyed, key=lambda r: str(r["model_slug"])):
        members = list(group)
        quotes = {str(r["quote"]) for r in members}
        if len(quotes) != 1:  # the analysis checks this too; fail loudly, never choose
            raise SystemExit(f"{slug}: members disagree on the entry quote")
        edges = []
        for r in members:
            edge: dict[str, str] = {}
            if r["target_machine"] is not None:
                edge["target_machine"] = str(r["target_machine"])
            else:
                edge["target_label"] = str(r["target_label"])
            edge["relationship_type"] = str(r["relationship_type"])
            edge["license_status"] = "unknown"
            edges.append(edge)
        entries.append(
            pk.entry(
                f"model.{slug}",
                cite={"ref": f"ipdb:{members[0]['ipdb_id']}", "quote": quotes.pop()},
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
