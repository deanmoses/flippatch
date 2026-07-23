#!/usr/bin/env python3
"""Generate ``patches/0187-victory-games-kits.yaml`` — the lineage edges for Victory
Games, authored as one patch.

This is PATCH ORGANIZATION, not a claim about the manufacturer. The campaign's working
convention is one patch per maker (see this dir's README), and this maker's rows are a
coherent set that reads better as its own file than as a slice of a multi-maker tranche.
Nothing here decides what those rows say: each row's ``relationship_type`` comes from
its own IPDB note in ``relationships.sql``, and each cite quotes the sentence that
establishes it. The maker is a filter, and only a filter.

``gen.py`` emits the complementary set — the same certain tier minus this maker — so
the two files cannot author the same model.

Run from the flippatch repo root::

    uv run python3 campaigns/0128-relationships/gen_victory_games.py
    make validate
    make verify-quotes
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

PATCH_PATH = pk.PATCHES_DIR / "0187-victory-games-kits.yaml"
RELATIONSHIPS_SQL = HERE / "relationships.sql"

# The maker this patch covers. gen.py excludes the same slug, so the two emitters
# partition the certain tier between them.
MAKER_SLUG = "victory-games"

# Wording is the user's, edited into the patch by hand — kept here so a regeneration
# reproduces the shipped file rather than reverting it.
DESCRIPTION = "Lineage for models by Victory Games."


def main() -> int:
    rows = [
        r
        for r in pk.read_view(
            RELATIONSHIPS_SQL, "relationship_green", prefix="relationships"
        )
        if str(r["maker_slug"]) == MAKER_SLUG
    ]
    if not rows:
        raise SystemExit(f"no {MAKER_SLUG} rows in relationship_green — nothing to emit")

    entries: list[str] = []
    for r in sorted(rows, key=lambda r: str(r["slug"])):
        quote = pk.clean_ipdb_quote(str(r["quote"]))
        if not quote:
            raise SystemExit(f"{r['slug']}: quote became empty after cleaning")
        entries.append(
            pk.entry(
                f"model.{r['slug']}",
                cite={"ref": f"ipdb:{r['ipdb_id']}", "quote": quote},
                model_relationship=[
                    {
                        "target_machine": str(r["target_machine"]),
                        "relationship_type": str(r["relationship_type"]),
                        "license_status": str(r["license_status"]),
                    }
                ],
            )
        )
    pk.write_patch(
        PATCH_PATH,
        attribution="flipcommons-catalog",
        description=DESCRIPTION,
        entries=entries,
    )
    kinds = Counter(str(r["relationship_type"]) for r in rows)
    print(
        f"wrote {PATCH_PATH.relative_to(pk.REPO_ROOT)} — {len(entries)} entries for "
        f"{MAKER_SLUG} ({', '.join(f'{n} {k}' for k, n in sorted(kinds.items()))})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
