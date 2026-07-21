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

The view is read through ``patchkit.read_view``, which runs the analysis's
``relationships_checks`` gate first — the same gate ``gen.py`` emits patches behind.
A feed built on a detector that has gone dark is still well-formed JSONL, and the
paid sweep it drives has no way to notice.

Read-only over the catalog; rerunnable any time (the sweep's results.json is keyed
on ipdb, so regenerating this file never invalidates already-judged models).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Repo root by marker, never by counting parents, so a campaign dir stays movable.
# (The retired `patches/authoring/` layout made parents[2] the root; under
# `campaigns/` the same expression resolves outside the repo entirely.)
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common

import patchkit as pk  # noqa: E402

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


def main() -> int:
    # Through patchkit, so `analysis query --check relationships` gates the read: a
    # feed drawn from an analysis whose detectors have gone dark is still well-formed
    # JSONL, and nothing downstream — least of all the paid AI sweep it drives — can
    # tell. The runner also owns the cwd/path resolution the raw duckdb call used to
    # hand-roll here.
    rows = pk.read_view(
        RELATIONSHIPS_SQL, "relationship_sweep_candidates", prefix="relationships"
    )
    if not rows:
        raise SystemExit("relationship_sweep_candidates returned no rows — nothing to emit")
    OUT.parent.mkdir(exist_ok=True)
    lines = []
    attached = 0
    for row in sorted(rows, key=lambda r: int(str(r["ipdb_id"]))):
        ipdb = row["ipdb_id"]
        candidate: dict[str, object] = {"ipdb_id": ipdb}
        # The view's resolved target guess(es); omit an empty list.
        hints = [h for h in (row.get("hint") or []) if h]
        if hints:
            candidate["hint"] = hints
        # maker_slug comes off the view (models.manufacturer_slug), so it is
        # live-filtered and needs no second connection to the catalog.
        refs = MAKER_AUTHORIZATION.get(str(row.get("maker_slug") or ""))
        if refs:
            # An explicit `evidence` REPLACES the default, so the model's own
            # note has to be named alongside the maker source — it is still the
            # row's primary evidence and the only thing that names the target.
            candidate["evidence"] = [f"ipdb:{ipdb}", *refs]
            attached += 1
        lines.append(json.dumps(candidate, ensure_ascii=False))
    OUT.write_text("\n".join(lines) + "\n")
    print(
        f"wrote {len(lines)} candidates to {OUT.relative_to(HERE)} "
        f"({attached} with a maker-level authorization source)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
