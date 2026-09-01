#!/usr/bin/env python3
"""Emit the payout-machine patches: 0319 (the vocabulary) and 0320 (the sweep).

IPDB's `Payout Machine` specialty is the largest classification the comparison
layer still reports as pointing at absent vocabulary, on 434 listings, every one
of which matches a live model. The layer's worklist reads it as spanning
`cash-payout` and `merchant-paid`; reading the population says the heading is not
a parent of our specific terms at all, and that the residue cannot be sorted --
IPDB defines it by WHO DISPENSES, half the notes say nothing more than the flag,
and where they do speak they usually describe a factory ordering option. So the
heading gets a term of its own: `payout`, the machine dispensed the award.

The reasoning, the counts behind it and the gates all live in `payout.sql` beside
this file; this script is a pure emitter over its two patch-row views.

Run from the flippatch repo root::

    uv run python3 campaigns/0319-payout-machines/gen.py
    make validate
    make verify-quote-verbatim ARGS="0320"
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Repo root by marker, never by counting parents, so a campaign dir stays movable.
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common

import patchkit as pk  # noqa: E402

PAYOUT_SQL = HERE / "payout.sql"
VOCAB_PATCH = pk.PATCHES_DIR / "0319-payout-reward-type.yaml"
SWEEP_PATCH = pk.PATCHES_DIR / "0320-payout-machines.yaml"

# Admin-only and lint-capped; the rationale lives in README.md and in payout.sql,
# the per-row evidence in each cite quote.
VOCAB_DESCRIPTION = "The payout reward type, and the terms its display order displaces."
SWEEP_DESCRIPTION = "Payout reward types from IPDB's Payout Machine specialty."

# The name the trade and every source use for the machine; the catalog names the
# REWARD, so the record is `Payout` and the machine wording rides as an alias.
PAYOUT_NAME = "Payout"
PAYOUT_ALIAS = "Payout Machine"

# One note serves all four shifts: it is one reordering, and which record moved is
# already the entry it rides on.
SHIFT_NOTE = "Shifted down one place so the general payout term seats ahead of the specific ones."


def write_vocabulary() -> int:
    rows = pk.read_view(PAYOUT_SQL, "payout_vocabulary", prefix="payout")
    if not rows:
        raise SystemExit("payout_vocabulary returned no rows — nothing to emit")

    entries = []
    for r in sorted(rows, key=lambda r: int(r["new_order"])):
        slug, new_order = str(r["slug"]), int(r["new_order"])
        if r["expected_order"] is None:
            # The create. `payout.sql` gates the slug being free, so this is the
            # one entry that mints rather than moves.
            entries.append(
                pk.entry(
                    f"reward-type.{slug}",
                    create=True,
                    fields={"name": PAYOUT_NAME, "display_order": new_order},
                    relationships={"reward_type_alias": [PAYOUT_ALIAS]},
                )
            )
        else:
            entries.append(
                pk.entry(
                    f"reward-type.{slug}",
                    note=SHIFT_NOTE,
                    fields={"display_order": new_order},
                )
            )

    # `flipcommons-catalog` holds the display_order claims these supersede — the
    # same source 0266 shifted `free-play` under — and a claim supersedes within
    # its own source.
    pk.write_patch(
        VOCAB_PATCH,
        attribution="flipcommons-catalog",
        description=VOCAB_DESCRIPTION,
        entries=entries,
    )
    return len(entries)


def write_sweep() -> int:
    rows = pk.read_view(PAYOUT_SQL, "payout_patch_rows", prefix="payout")
    if not rows:
        raise SystemExit("payout_patch_rows returned no rows — nothing to emit")

    entries = []
    for r in sorted(rows, key=lambda r: str(r["slug"])):
        quote = pk.clean_quote(str(r["quote"]).strip())
        if not quote:
            raise SystemExit(f"{r['slug']}: quote became empty after cleaning")
        entries.append(
            pk.entry(
                f"model.{r['slug']}",
                cite={"ref": str(r["cite_ref"]), "quote": quote},
                relationships={"reward_type": [str(r["reward_type"])]},
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
    n_vocab = write_vocabulary()
    n_sweep = write_sweep()
    print(
        f"wrote {VOCAB_PATCH.relative_to(pk.REPO_ROOT)} — {n_vocab} vocabulary entries\n"
        f"wrote {SWEEP_PATCH.relative_to(pk.REPO_ROOT)} — {n_sweep} payout assertions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
