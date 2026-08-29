#!/usr/bin/env python3
"""Generate ``patches/0284-opdb-model-fields.yaml`` and
``patches/0285-ipdb-model-fields.yaml`` — what IPDB and OPDB say about the models this
pass linked, recorded as each source's own claims.

Detection, the scope and every gate live in ``fields.sql`` (this dir); this script is a
pure emitter over its ``fb_opdb_rows`` and ``fb_ipdb_rows`` views. Two patches because a
patch carries one attribution, and these values belong to the sources, not to us.

**Attributed to the source, not to Flipcommons.** The identity links in 0281/0283 were
Flipcommons work — we decided which catalog record is which external record. These field
values are not: the source supplies them directly and there is no judgment of ours to
own. ``flipcommons-catalog`` outranks both sources, so nothing a reader sees changes;
what changes is that the catalog now records what each source says, agreement and
disagreement alike.

**The OPDB patch carries a note and no cite; the IPDB patch the reverse.** An ``opdb:``
cite resolves to a cached opdb.org machine page keyed by a numeric database id the
published export does not carry, so there is no page to point at and the note carries
the provenance. An IPDB listing is citable, so each field there rides a changeset whose
quote is the line of the rendered row stating that field — one quote, one fact, checkable
on its own by ``verify-quote-verbatim``. The date header states year and month together,
so those two share a changeset; that is why the emitter groups by QUOTE rather than by
field name.

Run from the flippatch repo root::

    uv run python3 campaigns/0284-external-field-backfill/gen.py
    make validate
    make verify-quote-verbatim ARGS="0285"
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Repo root by marker, never by counting parents, so a campaign dir stays movable.
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common

import patchkit as pk  # noqa: E402

FIELDS_SQL = HERE / "fields.sql"
OPDB_PATCH = pk.PATCHES_DIR / "0284-opdb-model-fields.yaml"
IPDB_PATCH = pk.PATCHES_DIR / "0285-ipdb-model-fields.yaml"

# Admin-only and lint-capped at 80 chars.
OPDB_DESCRIPTION = "OPDB field values for the 2023+ models just linked."
IPDB_DESCRIPTION = "IPDB field values for the 2023+ models just linked."

# The attribution already records that OPDB asserts these, so the note says only where
# the values were read from. It exists because `note-required` needs a note or a quoted
# cite, and OPDB listings have no citable page.
OPDB_NOTE = "From the OPDB API."


def _value(row: dict[str, object]) -> object:
    """The row's value, narrowed to an int where the field holds one.

    A claim's value is compared as JSON, so a string "4" would never equal the 4 the
    same fact carries elsewhere. The analysis widens every value to VARCHAR to stack
    the fields into one relation, and `fb_checks` asserts each numeric one is digits,
    so this cannot raise.
    """
    return int(str(row["value"])) if row["numeric_value"] else row["value"]


def _emit_opdb() -> int:
    rows = pk.read_view(FIELDS_SQL, "fb_opdb_rows", prefix="fb")
    if not rows:
        raise SystemExit("fb_opdb_rows returned no rows — nothing to emit")

    by_model: dict[str, dict[str, object]] = defaultdict(dict)
    for r in rows:
        by_model[str(r["model_slug"])][str(r["field_name"])] = _value(r)

    entries = [
        pk.entry(f"model.{slug}", note=OPDB_NOTE, fields=fields)
        for slug, fields in sorted(by_model.items())
    ]
    pk.write_patch(
        OPDB_PATCH,
        attribution="opdb",
        description=OPDB_DESCRIPTION,
        entries=entries,
    )
    print(f"wrote {OPDB_PATCH.name}: {len(entries)} models, {len(rows)} claims")
    return len(rows)


def _emit_ipdb() -> int:
    rows = pk.read_view(FIELDS_SQL, "fb_ipdb_rows", prefix="fb")
    if not rows:
        raise SystemExit("fb_ipdb_rows returned no rows — nothing to emit")

    # model -> quote -> {field: value}. Grouping by the quote is what makes each
    # changeset one statement supporting one fact; the date header covers two fields
    # because it states both in a single line.
    by_model: dict[str, dict[str, dict[str, object]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    ipdb_ids: dict[str, int] = {}
    for r in rows:
        slug = str(r["model_slug"])
        ipdb_ids[slug] = int(str(r["ipdb_id"]))
        by_model[slug][str(r["quote"])][str(r["field_name"])] = _value(r)

    entries = []
    for slug, by_quote in sorted(by_model.items()):
        ref = f"ipdb:{ipdb_ids[slug]}"
        changesets = [
            {
                "cite": {"ref": ref, "quote": pk.clean_quote(quote)},
                "fields": fields,
            }
            # Sorted by the quote so a regeneration is byte-stable.
            for quote, fields in sorted(by_quote.items())
        ]
        entries.append(pk.entry(f"model.{slug}", changesets=changesets))

    pk.write_patch(
        IPDB_PATCH,
        attribution="ipdb",
        description=IPDB_DESCRIPTION,
        entries=entries,
    )
    print(f"wrote {IPDB_PATCH.name}: {len(entries)} models, {len(rows)} claims")
    return len(rows)


def main() -> int:
    _emit_opdb()
    _emit_ipdb()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
