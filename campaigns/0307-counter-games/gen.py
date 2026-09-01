#!/usr/bin/env python3
"""Emit the counter-game patches: 0307 (the two pin tables) and 0310 (the sweep).

IPDB's `Table Top/Counter Game` specialty is the last large classification the
comparison layer reports as pointing at absent vocabulary, on 321 listings. It was
mapped to a display string rather than a slug on the reading that it spans two of
our cabinets and needs per-model research to split them. Reading the population
says otherwise: every member is a coin-operated counter game, and the two models
the catalog already calls `tabletop` are not members at all -- they are the legged
siblings IPDB deliberately leaves out. So the heading maps to `countertop`, and
`tabletop` is retired by 0308 and 0309 (both hand-written: a description re-edit
and a delete, neither of which patchkit emits).

The reasoning, the counts behind it and the gates all live in `counter_games.sql`
beside this file; this script is a pure emitter over its two patch-row views.

Run from the flippatch repo root::

    uv run python3 campaigns/0307-counter-games/gen.py
    make validate
    make verify-quote-verbatim ARGS="0307"
    make verify-quote-verbatim ARGS="0310"
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Repo root by marker, never by counting parents, so a campaign dir stays movable.
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common

import patchkit as pk  # noqa: E402

COUNTER_SQL = HERE / "counter_games.sql"
PIN_TABLE_PATCH = pk.PATCHES_DIR / "0307-pin-table-cabinets.yaml"
SWEEP_PATCH = pk.PATCHES_DIR / "0310-countertop-games.yaml"

# Admin-only and lint-capped at 80 chars; the rationale lives in README.md and in
# counter_games.sql, the per-row evidence in each cite quote.
PIN_TABLE_DESCRIPTION = "Cabinets for two legged pin tables previously called tabletop."
SWEEP_DESCRIPTION = "Counter-game cabinets from IPDB's Table Top/Counter Game specialty."

# Why `floor` and not simply an empty slot. Both machines are positively evidenced
# as free-standing -- one on its own legs, one on the radio table it was sold
# bolted to -- and the cabinet vocabulary uses `floor` as the general counterpart
# to `countertop` in its own prose ("the countertop format gradually gave way to
# the floor cabinet"). The dimensions in `floor`'s description are the modern norm,
# not a boundary.
#
# One note serves both entries: the reading that moves them is the same reading,
# and the machine-specific evidence is already in each cite's quote.
PIN_TABLE_NOTE = "In 1930s trade usage a 'pin table' is a legged floorstanding model."


def write_pin_tables() -> int:
    rows = pk.read_view(COUNTER_SQL, "counter_pin_tables", prefix="counter")
    if not rows:
        raise SystemExit("counter_pin_tables returned no rows — nothing to emit")

    entries = []
    for r in sorted(rows, key=lambda r: str(r["slug"])):
        entries.append(
            pk.entry(
                f"model.{r['slug']}",
                note=PIN_TABLE_NOTE,
                cite={
                    "ref": f"ipdb:{int(r['ipdb_id'])}",
                    "quote": pk.clean_quote(str(r["quote"]).strip()),
                },
                fields={"cabinet": str(r["cabinet"])},
            )
        )

    # `flipcommons-catalog` holds the tabletop claim these supersede, and a claim
    # supersedes within its own source: attributing the correction anywhere else
    # would leave the wrong value winning resolution.
    pk.write_patch(
        PIN_TABLE_PATCH,
        attribution="flipcommons-catalog",
        description=PIN_TABLE_DESCRIPTION,
        entries=entries,
    )
    return len(entries)


def write_sweep() -> int:
    rows = pk.read_view(COUNTER_SQL, "counter_patch_rows", prefix="counter")
    if not rows:
        raise SystemExit("counter_patch_rows returned no rows — nothing to emit")

    entries = []
    for r in sorted(rows, key=lambda r: str(r["slug"])):
        quote = pk.clean_quote(str(r["quote"]).strip())
        if not quote:
            raise SystemExit(f"{r['slug']}: quote became empty after cleaning")
        entries.append(
            pk.entry(
                f"model.{r['slug']}",
                cite={"ref": str(r["cite_ref"]), "quote": quote},
                fields={"cabinet": str(r["cabinet"])},
            )
        )

    pk.write_patch(
        SWEEP_PATCH,
        attribution="ipdb",
        description=SWEEP_DESCRIPTION,
        entries=entries,
    )
    return len(entries)


def main() -> int:
    n_pin = write_pin_tables()
    n_sweep = write_sweep()
    print(
        f"wrote {PIN_TABLE_PATCH.relative_to(pk.REPO_ROOT)} — {n_pin} corrections\n"
        f"wrote {SWEEP_PATCH.relative_to(pk.REPO_ROOT)} — {n_sweep} countertop assertions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
