"""Emit 0326 (cue-game formats) and 0327 (horse-racing themes) from `cue_games.sql`.

The `cue-game` mint rides `0302-new-vocab-terms` and the description is
hand-written in 0325; neither is worth a generator, and the mint must land
before 0326 can resolve.

    uv run python campaigns/0325-cue-games/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from patchkit import PATCHES_DIR, entry, read_view, render_patch  # noqa: E402

ANALYSIS = Path(__file__).resolve().parent / "cue_games.sql"


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
    cue_rows = read_view(ANALYSIS, "cue_patch_rows", prefix="cue")
    hr_rows = read_view(ANALYSIS, "hr_patch_rows", prefix="cue")
    if not cue_rows and not hr_rows:
        raise SystemExit("both patch-row views are empty — nothing to emit")

    # Each entry cites its own listing's Specialty row. The quote names one
    # specialty and leans on the `[...]` ellipsis (scripts/quotes/sources.py): the
    # census records which specialties a listing carries, not the order the page
    # prints them, and the ellipsis absorbs whatever precedes the name, an empty
    # prefix included.
    cue_entries = [
        entry(
            f"model.{r['slug']}",
            cite={"ref": f"ipdb:{r['ipdb_id']}", "quote": str(r["specialty_quote"])},
            fields={"game_format": str(r["game_format"])},
        )
        for r in cue_rows
    ]
    hr_entries = [
        entry(
            f"model.{r['slug']}",
            cite={"ref": f"ipdb:{r['ipdb_id']}", "quote": str(r["specialty_quote"])},
            relationships={"theme": [str(r["theme"])]},
        )
        for r in hr_rows
    ]

    if cue_entries:
        emit(
            PATCHES_DIR / "0326-cue-game-machines.yaml",
            attribution="ipdb",
            description="Cue-game formats from IPDB's Cue Game specialty.",
            entries=cue_entries,
        )
    if hr_entries:
        emit(
            PATCHES_DIR / "0327-horserace-themes.yaml",
            attribution="ipdb",
            description="Horse-racing themes from IPDB's Horserace Game specialty.",
            entries=hr_entries,
        )
    print(f"{len(cue_entries)} cue-game entries, {len(hr_entries)} horse-racing entries")


if __name__ == "__main__":
    main()
