#!/usr/bin/env python3
"""Generate ``patches/0286-opdb-model-tags.yaml`` and
``patches/0287-ipdb-model-credits.yaml`` — the non-scalar content IPDB and OPDB hold for
the models this pass linked.

The companion to ``0284-external-field-backfill``: same scope, same attribution
reasoning, for credits and tags rather than scalar fields. Detection and every gate live
in ``content.sql`` (this dir); this script is a pure emitter over its ``cb_credits`` and
``cb_tags`` views.

**Credits are cited, tags are not.** IPDB's credit block is the field's accepted
reference — a deliberate exception to preferring primary sources — and its page is
citable, so each credit rides its own changeset quoting the line that names it
("Design by: Jack Danger"). One quote, one credit, checkable on its own. OPDB has no
citable page, so the tag rows carry the same note 0284 uses.

Run from the flippatch repo root::

    uv run python3 campaigns/0286-external-content-backfill/gen.py
    make validate
    make verify-quote-verbatim ARGS="0287"
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

CONTENT_SQL = HERE / "content.sql"
TAGS_PATCH = pk.PATCHES_DIR / "0286-opdb-model-tags.yaml"
CREDITS_PATCH = pk.PATCHES_DIR / "0287-ipdb-model-credits.yaml"

# Admin-only and lint-capped at 80 chars.
TAGS_DESCRIPTION = "OPDB tags for the 2023+ models just linked."
CREDITS_DESCRIPTION = "IPDB credits for the 2023+ models just linked."

# Same note as 0284, and for the same reason: the attribution records that OPDB asserts
# this, so the note says only where it was read from — and `note-required` needs one,
# because a tag is a relationship member with no citable OPDB page behind it.
OPDB_NOTE = "From the OPDB API."


def _emit_tags() -> int:
    rows = pk.read_view(CONTENT_SQL, "cb_tags", prefix="cb")
    if not rows:
        raise SystemExit("cb_tags returned no rows — nothing to emit")

    by_model: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        by_model[str(r["model_slug"])].append(str(r["tag_slug"]))

    entries = [
        pk.entry(f"model.{slug}", note=OPDB_NOTE, tags=sorted(tags))
        for slug, tags in sorted(by_model.items())
    ]
    pk.write_patch(
        TAGS_PATCH,
        attribution="opdb",
        description=TAGS_DESCRIPTION,
        entries=entries,
    )
    print(f"wrote {TAGS_PATCH.name}: {len(entries)} models, {len(rows)} tags")
    return len(rows)


def _emit_credits() -> int:
    rows = pk.read_view(CONTENT_SQL, "cb_credits", prefix="cb")
    if not rows:
        raise SystemExit("cb_credits returned no rows — nothing to emit")

    # model -> quote -> [(person, role)]. Each credit line names exactly one credit, so
    # in practice each quote carries one pair; grouping by quote rather than assuming
    # that keeps the shape correct if IPDB ever prints two names under one label.
    by_model: dict[str, dict[str, list[tuple[str, str]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    ipdb_ids: dict[str, int] = {}
    for r in rows:
        slug = str(r["model_slug"])
        ipdb_ids[slug] = int(str(r["ipdb_id"]))
        by_model[slug][str(r["quote"])].append(
            (str(r["person_slug"]), str(r["role_slug"]))
        )

    entries = []
    for slug, by_quote in sorted(by_model.items()):
        ref = f"ipdb:{ipdb_ids[slug]}"
        changesets = [
            {
                "cite": {"ref": ref, "quote": pk.clean_quote(quote)},
                "credits": sorted(pairs),
            }
            # Sorted by quote so a regeneration is byte-stable.
            for quote, pairs in sorted(by_quote.items())
        ]
        entries.append(pk.entry(f"model.{slug}", changesets=changesets))

    pk.write_patch(
        CREDITS_PATCH,
        attribution="ipdb",
        description=CREDITS_DESCRIPTION,
        entries=entries,
    )
    print(f"wrote {CREDITS_PATCH.name}: {len(entries)} models, {len(rows)} credits")
    return len(rows)


def main() -> int:
    _emit_tags()
    _emit_credits()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
