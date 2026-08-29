#!/usr/bin/env python3
"""Generate ``patches/0288-ipdb-venom-variants.yaml`` — IPDB's testimony on the two
Venom variants the 2023+ sweep's scope rule left out.

Why these two are a justified exception, and how the checks enforce that, is in
``venom.sql`` (this dir); this script is a pure emitter over its ``venom_rows`` view.
Fields and credits ride one patch because they share one attribution.

**The month is a deliberate disagreement, not a correction.** OPDB claims July for both
and IPDB says August. ``opdb`` outranks ``ipdb``, so July keeps resolving and nothing a
reader sees changes — what changes is that IPDB's August is on the record rather than
invisible. Recording it is the whole point of a source-attributed claim.

Run from the flippatch repo root::

    uv run python3 campaigns/0288-venom-variants-ipdb/gen.py
    make validate
    make verify-quote-verbatim ARGS="0288"
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

VENOM_SQL = HERE / "venom.sql"
PATCH_PATH = pk.PATCHES_DIR / "0288-ipdb-venom-variants.yaml"

# Admin-only and lint-capped at 80 chars.
DESCRIPTION = "IPDB field values and credits for the two Venom variants."


def main() -> int:
    rows = pk.read_view(VENOM_SQL, "venom_rows", prefix="venom")
    if not rows:
        raise SystemExit("venom_rows returned no rows — nothing to emit")

    # model -> quote -> the changeset that quote supports. Grouping by quote is what
    # keeps one quote behind one fact; the date header carries year and month together
    # because it states both in a single line.
    by_model: dict[str, dict[str, dict[str, object]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    ipdb_ids: dict[str, int] = {}
    for r in rows:
        slug = str(r["model_slug"])
        ipdb_ids[slug] = int(str(r["ipdb_id"]))
        bucket = by_model[slug][str(r["quote"])]
        if r["kind"] == "credit":
            # (person, role) — the emitter's credit shape.
            bucket.setdefault("credits", []).append(  # type: ignore[union-attr]
                (str(r["value"]), str(r["name"]))
            )
        else:
            # A claim's value is compared as JSON, so an int field must not arrive as a
            # string; `venom_checks` asserts every numeric one is digits.
            value = int(str(r["value"])) if r["numeric_value"] else r["value"]
            bucket.setdefault("fields", {})[str(r["name"])] = value  # type: ignore[index]

    entries = []
    for slug, by_quote in sorted(by_model.items()):
        ref = f"ipdb:{ipdb_ids[slug]}"
        changesets = []
        # Sorted by quote so a regeneration is byte-stable.
        for quote, bucket in sorted(by_quote.items()):
            cs: dict[str, object] = {"cite": {"ref": ref, "quote": pk.clean_quote(quote)}}
            if "fields" in bucket:
                cs["fields"] = bucket["fields"]
            if "credits" in bucket:
                cs["credits"] = sorted(bucket["credits"])  # type: ignore[arg-type]
            changesets.append(cs)
        entries.append(pk.entry(f"model.{slug}", changesets=changesets))

    pk.write_patch(
        PATCH_PATH,
        attribution="ipdb",
        description=DESCRIPTION,
        entries=entries,
    )
    n_credits = sum(1 for r in rows if r["kind"] == "credit")
    print(
        f"wrote {PATCH_PATH.name}: {len(entries)} models, "
        f"{len(rows) - n_credits} fields, {n_credits} credits"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
