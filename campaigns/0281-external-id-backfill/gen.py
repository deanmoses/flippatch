#!/usr/bin/env python3
"""Generate ``patches/0281-external-id-backfill.yaml`` — external identifiers for
catalog models that already exist but carry no link to IPDB or OPDB.

Detection, the 2023+ scope line, the hand-approved edition pairs and every gate live in
``backfill.sql`` (this dir); this script is a pure emitter over its ``bf_patch_rows``
view. Three evidence kinds come out of that view, and the only thing this file decides is
how each one words its note::

    - model.dungeon-crawler-carl:
        note: 'OPDB''s API lists this machine as "Dungeon Crawler Carl" by [...]'
        opdb_id: G0lJE-MP3vX

Three things about that shape are deliberate.

**The OPDB rows carry a note and no cite.** An ``opdb:`` cite resolves to a cached
``opdb.org/machines/<id>`` page, and that URL is keyed by a numeric database id the
published export does not carry — our Group-Model-Alias identifier is not addressable
there, so there is no page to cite. The note carries the provenance instead, which is
what ``note-required`` asks for. The IPDB rows have no such problem and are cited
properly, with a verbatim quote cut from the same columns the resolver renders.

**Only the OPDB rows carry a note.** For them it is the only durable record of what the
external listing says, so it reports the listing's name, manufacturer and year and stops
there. An IPDB row carries none: its quote already reproduces those same three fields in
the source's own words, and a note restating them would be exactly the scaffolding a
quoted cite exists to replace.

**The edition rows are a human judgment, and only the analysis records that.** They are
the one population the comparison layer does not offer — it classifies them ``absent``
because ``name_norm`` cannot bridge "(CE)" to "(Collector's Edition)" — so the pairs are
approved by hand in ``bf_edition_pairs`` and gated on the two legs a machine CAN be
checked on, manufacturer and year. Their note is the same as any other OPDB row: it
quotes the listing's own name, which is precisely the fact a reader needs to see that the
two wordings differ.

Run from the flippatch repo root::

    uv run python3 campaigns/0281-external-id-backfill/gen.py
    make validate
    make verify-quote-verbatim ARGS="0281"
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Repo root by marker, never by counting parents, so a campaign dir stays movable.
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common

import patchkit as pk  # noqa: E402

PATCH_PATH = pk.PATCHES_DIR / "0281-external-id-backfill.yaml"
BACKFILL_SQL = HERE / "backfill.sql"

# Admin-only and lint-capped at 80 chars; the rationale lives in README.md and this
# module's docstring, the per-row evidence in each note.
DESCRIPTION = "IPDB and OPDB IDs for 2023+ models."

# One note for every OPDB row, stating what the listing says and nothing more. The
# identity inference the note used to spell out ("matching this model's name,
# manufacturer and year") is left to the reader, who can see both sides: it was also the
# clause most likely to be FALSE on an individual row, since the layer's year leg accepts
# a one-year gap that a flat "matching ... year" would misreport.
#
# The IPDB rows carry no note at all -- their cite quotes the listing's own name, header
# date and manufacturer, which is that same evidence in the source's own words.
OPDB_NOTE = 'OPDB\'s API lists this machine as "{name}" by {maker}, {year}'


def main() -> int:
    rows = pk.read_view(BACKFILL_SQL, "bf_patch_rows", prefix="bf")
    if not rows:
        raise SystemExit("bf_patch_rows returned no rows — nothing to emit")

    entries = []
    for r in sorted(rows, key=lambda r: (r["field_name"], r["model_slug"])):
        # The IPDB rows carry no note at all: their cite quotes the listing's own name,
        # header date and manufacturer, which IS the evidence, and a note restating it
        # would be the scaffolding `note-required` explicitly accepts a quoted cite in
        # place of. The OPDB rows have no citable page, so there the note is the record.
        note = (
            OPDB_NOTE.format(
                name=r["ext_name"], maker=r["note_maker"], year=r["ext_year"]
            )
            if r["field_name"] == "opdb_id"
            else None
        )
        # Only the IPDB rows have a citable document behind them.
        cite = (
            {"ref": r["cite_ref"], "quote": pk.clean_quote(r["quote"])}
            if r["cite_ref"]
            else None
        )
        # A claim's value is compared as JSON, so the type is load-bearing: every
        # ipdb_id already in the catalog is stored as a bare number and a string "7073"
        # would never equal the 7073 the same machine carries elsewhere. The union in
        # the analysis has to widen both id kinds to VARCHAR to stack them, so the
        # numeric one is narrowed back here, at the point of serialization.
        # `bf_checks` asserts every ipdb_id value is digits, so this cannot raise.
        value = int(r["value"]) if r["field_name"] == "ipdb_id" else r["value"]
        entries.append(
            pk.entry(
                f"model.{r['model_slug']}",
                note=note,
                cite=cite,
                fields={r["field_name"]: value},
            )
        )

    pk.write_patch(
        PATCH_PATH,
        attribution="flipcommons-catalog",
        description=DESCRIPTION,
        entries=entries,
    )
    counts = Counter(r["evidence"] for r in rows)
    print(f"wrote {PATCH_PATH.name}: {len(entries)} entries — {dict(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
