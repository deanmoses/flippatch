#!/usr/bin/env python3
"""Emit the relationship campaign's candidates as an ai_corpus_sweep candidates file.

The campaign-specific adapter onto the sweep's parts-kit contract. Discovery is
now REPRODUCIBLE: the candidate set comes from ``relationships.sql``'s
``relationship_sweep_candidates`` view (every model with copy/conversion free-text
language and no typed edge yet), read live from the flipcommons catalog — not from
the frozen ``Worklist.md`` this script used to parse. "What's already done" is the
view's ``has_rel_edge`` filter, so a re-run after authoring simply drops the newly
edged models; there is nothing to reconcile.

Each row carries the view's resolved target guess(es) as a ``hint`` (a list); the
sweep never shows a hint to the model, it only diffs it against its own resolution,
which is how the guesses get audited instead of inherited. A few makers also get a
maker-level authorization source attached as ``evidence`` (see below).

    uv run python3 emit_candidates.py     # writes sweep/candidates.jsonl
    make sweep ARGS="campaigns/0128-relationships/sweep/candidates.jsonl --no-ai"

Read-only over the catalog; rerunnable any time (the sweep's results.json is keyed
on ipdb, so regenerating this file never invalidates already-judged models).
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]  # 0128-relationships -> authoring -> patches -> repo root

from common.paths import FLIPCOMMONS_DB, FLIPCOMMONS_DIR, load_env  # noqa: E402

RELATIONSHIPS_SQL = HERE / "relationships.sql"
OUT = HERE / "sweep" / "candidates.jsonl"

# ── Maker-level authorization sources (TOOL-NOTES DEFECT 11) ────────────────
#
# A bootleg's IPDB note establishes the COPY ("a copy of Bally's Xenon") and
# never the AUTHORIZATION — but `license_status: unlicensed` asserts exactly
# that second thing. So the authored patches carry a second cite: a maker-level
# trade history establishing that this maker's copying was unauthorized. The
# sweep only ever saw the IPDB note, so it could not reach `unlicensed` on any
# such row and reported `copy/unknown` — indicting four correct LTD edges as
# conflicts. Attaching the same source the author used lets the judge see what
# the author saw.
#
# This attaches EVIDENCE, not a verdict: no license status is defaulted per
# maker. The judge still has to find the authorization in the text and quote it
# verbatim, and the fill gate still holds a licensed/unlicensed claim to
# quote-supports-claim on both axes. A maker-level default that skipped that
# would assert authorization with no per-row evidence — the precise discipline
# these patches exist to uphold.
#
# Only makers whose SHIPPED patches already cite such a source belong here; the
# refs are copied from those patches, so the sweep and the patch rest on the
# same evidence. Adding a maker means finding its source first, not guessing.
MAKER_AUTHORIZATION: dict[str, list[str]] = {
    # 0150-ltd-do-brasil.yaml. The passage names BOTH Brazilian makers: Taito
    # "não era a única empresa a usar a Reserva de Mercado como escudo para
    # copiar impunemente … a LTD, sediada em Campinas, fazia o mesmo."
    "ltd-do-brasil": ["https://augustocampos.net/taito-brasil"],
    "taito-do-brasil": ["https://augustocampos.net/taito-brasil"],
    # 0145-petaco.yaml — Spanish trade histories covering Petaco's copying.
    "petaco": [
        "https://blogpinball.blogspot.com/2017/03/petaco-sa-procedimientos.html",
        "https://www.pinballnews.com/learn/spanishpinball/index.html",
    ],
}


def load_candidates() -> list[dict[str, Any]]:
    """Read relationships.sql's ``relationship_sweep_candidates`` view as JSON.

    Runs the duckdb CLI with cwd = the flipcommons checkout, so the view's
    ``.read scripts/analysis/catalog.sql`` and the foundation's ``ATTACH
    backend/db.sqlite3`` both resolve there (same idiom as 0172's gen.py)."""
    load_env()
    fc = os.environ.get("FLIPCOMMONS_DIR") or str(FLIPCOMMONS_DIR)
    proc = subprocess.run(
        [
            "duckdb", "-init", str(RELATIONSHIPS_SQL), ":memory:",
            "COPY (FROM relationship_sweep_candidates) TO '/dev/stdout' (FORMAT json, ARRAY true);",
        ],
        cwd=fc, capture_output=True, text=True, check=True,
    )
    rows: list[dict[str, Any]] = json.loads(proc.stdout)
    return rows


def maker_of(con: sqlite3.Connection, ipdb_id: int) -> str | None:
    """The model's Manufacturer slug — the key MAKER_AUTHORIZATION is keyed on."""
    row = con.execute(
        "SELECT mf.slug FROM catalog_machinemodel m "
        "JOIN catalog_corporateentity ce ON m.corporate_entity_id = ce.id "
        "JOIN catalog_manufacturer mf ON ce.manufacturer_id = mf.id "
        "WHERE m.ipdb_id = ?",
        (ipdb_id,),
    ).fetchone()
    return row[0] if row else None


def main() -> int:
    rows = load_candidates()
    OUT.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(f"file:{FLIPCOMMONS_DB}?mode=ro", uri=True)
    lines = []
    attached = 0
    for row in sorted(rows, key=lambda r: r["ipdb_id"]):
        ipdb = row["ipdb_id"]
        candidate: dict[str, object] = {"ipdb_id": ipdb}
        # The view's resolved target guess(es); omit an empty list.
        hints = [h for h in (row.get("hint") or []) if h]
        if hints:
            candidate["hint"] = hints
        refs = MAKER_AUTHORIZATION.get(maker_of(con, ipdb) or "")
        if refs:
            # An explicit `evidence` REPLACES the default, so the model's own
            # note has to be named alongside the maker source — it is still the
            # row's primary evidence and the only thing that names the target.
            candidate["evidence"] = [f"ipdb:{ipdb}", *refs]
            attached += 1
        lines.append(json.dumps(candidate, ensure_ascii=False))
    con.close()
    OUT.write_text("\n".join(lines) + "\n")
    print(
        f"wrote {len(lines)} candidates to {OUT.relative_to(HERE)} "
        f"({attached} with a maker-level authorization source)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
