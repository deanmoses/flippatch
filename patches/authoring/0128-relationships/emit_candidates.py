#!/usr/bin/env python3
"""Emit this campaign's Worklist rows as an ai_corpus_sweep candidates file.

The campaign-specific adapter onto the sweep's parts-kit contract. Since the
sweep judges a model's whole relationship set in one call, this emits **one
candidate per model** (keyed on the stable ``ipdb`` number), collapsing the
Worklist's licensed / bootleg / conversion buckets — which all map to the
single ``model_relationship`` field now. Each Worklist target guess rides along
as a ``hint`` (a list when a model appears under several buckets); the sweep
never shows a hint to the model, it only diffs it against its own resolution,
which is exactly how the old guesses get audited instead of inherited.

    uv run python3 emit_candidates.py     # writes sweep/candidates.jsonl
    make sweep ARGS="patches/authoring/0128-relationships/sweep/candidates.jsonl --no-ai"

Read-only over Worklist.md; rerunnable any time (the Worklist is the input of
record, the sweep's results.json is keyed on ipdb so regenerating this file
never invalidates judged models).
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from check_status import DB, parse_worklist

HERE = Path(__file__).resolve().parent
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
    rows = parse_worklist()
    OUT.parent.mkdir(exist_ok=True)
    # One candidate per model; collect its Worklist target guesses as hints
    # (deduped, order-preserving), across whatever buckets the model appears in.
    by_ipdb: dict[int, list[str]] = {}
    for _rel, _slug, ipdb, wl_tgt in rows:
        hints = by_ipdb.setdefault(ipdb, [])
        if wl_tgt and wl_tgt != "TODO" and wl_tgt not in hints:
            hints.append(wl_tgt)
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    lines = []
    attached = 0
    for ipdb, hints in by_ipdb.items():
        candidate: dict[str, object] = {"ipdb_id": ipdb}
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
