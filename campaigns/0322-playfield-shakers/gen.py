"""Emit 0323 — the playfield-shaker assertions — from `shakers.sql`.

0322 (the vocabulary) is hand-written: two creates and one DAG edge are not worth
a generator, and they must land before these assertions can resolve.

    uv run python campaigns/0322-playfield-shakers/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from patchkit import PATCHES_DIR, entry, read_view, render_patch  # noqa: E402

ANALYSIS = Path(__file__).resolve().parent / "shakers.sql"


def emit(path: Path, **kwargs: object) -> None:
    """Write only if the rendered text differs — an identical rewrite still bumps
    mtime, which `make db-patch-state` reads as a patch edited since it applied."""
    text = render_patch(**kwargs)  # type: ignore[arg-type]
    if not path.exists() or path.read_text() != text:
        path.write_text(text)
        print(f"  wrote {path.name}")
    else:
        print(f"  unchanged {path.name}")


def main() -> None:
    rows = read_view(ANALYSIS, "shk_patch_rows", prefix="shk")
    if not rows:
        raise SystemExit("shk_patch_rows is empty — nothing to emit")

    entries = []
    for r in rows:
        ref = f"ipdb:{r['ipdb_id']}"
        # Two spans off the one listing, for every member. The Specialty row is
        # what the mapping rests on; the Notable Features sentence is what the
        # machine actually does, so a reader following the footnote lands on prose
        # rather than a two-word label. On Allied's two that second span is also
        # what earns them `shaker-ball` on top of the generic term.
        cite: list[object] = [
            {"ref": ref, "quote": str(r["specialty_quote"])},
            {"ref": ref, "quote": str(r["mechanism_quote"])},
        ]
        entries.append(
            entry(
                f"model.{r['slug']}",
                cite=cite,
                relationships={"gameplay_feature": list(r["features"])},
            )
        )

    emit(
        PATCHES_DIR / "0323-playfield-shaker-machines.yaml",
        attribution="ipdb",
        description="Machines IPDB marks as having a player-shaken playfield.",
        entries=entries,
    )
    print(f"{len(entries)} entries")


if __name__ == "__main__":
    main()
