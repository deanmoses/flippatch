#!/usr/bin/env python3
"""Emit the lineage campaign's sweep feed as an ai_corpus_sweep candidates file.

The campaign-specific adapter onto the sweep's parts-kit contract. Discovery is the
external data source layer's live ``ipdb_model_relationships_missing`` view, cut by
``lineage.sql``'s ``lineage_sweep_candidates`` -- the ``no_edge`` class minus every
model campaign 0128's sweep already judged (those route to the hand pass over
``lineage_parked_0128`` instead; see the analysis header). "What's already done" is
the layer's carriage test, so a re-run after authoring simply drops the newly edged
models; there is nothing to reconcile.

    uv run python3 emit_candidates.py     # writes sweep/candidates.jsonl
    make sweep ARGS="campaigns/0299-ipdb-relationship-lineage/sweep/candidates.jsonl --no-ai"

No ``hint`` and no ``evidence`` rows, deliberately. 0128's target guesses live only
in its regenerable candidate file, not in any adjudicated record, so there is
nothing standing to audit against; and no maker in this scope has a shipped
maker-level authorization source (0128's ``MAKER_AUTHORIZATION`` covered bootleg
copy makers, not conversion houses), so every row's evidence is its own ``ipdb:``
note -- the sweep's default.

The view is read through ``patchkit.read_view``, which runs the analysis's
``lineage_checks`` gate first: a feed whose routing partition has broken -- a model
dropped between the two routes, or 0128's record silently re-swept -- is still
well-formed JSONL, and the paid sweep it drives has no way to notice.

Read-only over the catalog; rerunnable any time (the sweep's results.json is keyed
on ipdb_id, so regenerating this file never invalidates already-judged models).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Repo root by marker, never by counting parents, so a campaign dir stays movable.
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common

import patchkit as pk  # noqa: E402

LINEAGE_SQL = HERE / "lineage.sql"
OUT = HERE / "sweep" / "candidates.jsonl"


def main() -> int:
    rows = pk.read_view(LINEAGE_SQL, "lineage_sweep_candidates", prefix="lineage")
    if not rows:
        raise SystemExit("lineage_sweep_candidates returned no rows — nothing to emit")
    OUT.parent.mkdir(exist_ok=True)
    lines = [
        json.dumps({"ipdb_id": int(str(row["ipdb_id"]))}, ensure_ascii=False)
        for row in sorted(rows, key=lambda r: int(str(r["ipdb_id"])))
    ]
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {len(lines)} candidates to {OUT.relative_to(HERE)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
