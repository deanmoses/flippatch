#!/usr/bin/env python3
"""Generate ``patches/0172-bingo-game-format.yaml`` — set ``game_format =
bingo-pinball`` on the catalog's bingo machines.

Candidate detection and vetting live in ``bingo.sql`` (this dir); this script is
just the emitter. It reads that file's ``bingo_patch_rows`` view from the live
flipcommons catalog via the duckdb CLI (run with cwd = the flipcommons checkout,
so the view's ``.read scripts/analysis/catalog.sql`` and its ``ATTACH`` resolve),
then writes one patch entry per candidate:

- **struct rows** — a ``note:`` reasoning from the model's own structured
  gameplay-feature data (its trap/gobble-hole count). No ``cite:``: the evidence
  IS the catalog data, so a cite would misleadingly imply the IPDB quote is the
  basis (DataPatchAuthoring.md → "skip the cite when the evidence is the entity's
  own data").
- **word rows** — a ``cite: ipdb:<id>`` carrying the verbatim "bingo" statement
  from IPDB free text. The per-row quotes are hand-authored below (the mechanical
  per-row work DataPatchKit exists for) and gated verbatim by ``make verify-quotes``.
- **flagged rows** (one-ball / word-bingo / hybrid) — a word row plus a short
  bucket ``note:`` recording the boundary call.

Run from the flippatch repo root::

    uv run python3 patches/authoring/0172-bingo-game-format/gen.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTHORING = HERE.parent  # patches/authoring/
REPO_ROOT = AUTHORING.parent.parent  # -> repo root
sys.path.insert(0, str(AUTHORING))  # patchkit
sys.path.insert(0, str(REPO_ROOT / "scripts"))  # common.related_projects

import patchkit as pk  # noqa: E402
from common.related_projects import FLIPCOMMONS_DIR, load_env  # noqa: E402

PATCH_PATH = REPO_ROOT / "patches" / "0172-bingo-game-format.yaml"
BINGO_SQL = HERE / "bingo.sql"
GAME_FORMAT = "bingo-pinball"

# Short boundary-call note for each flagged bucket (rides its cite/quote).
BUCKET_NOTES = {
    "one-ball": (
        "One-ball game built on the bingo platform (bingo cards, hole grid); "
        "a member of the bingo family, classified bingo-pinball."
    ),
    "word-bingo": (
        "Bally letter-bingo — a bingo playfield scoring words instead of "
        "numbers; classified bingo-pinball."
    ),
    "hybrid": (
        "Record describes a combination bingo machine and pinball; "
        "classified bingo-pinball."
    ),
}

# Word-detected rows whose record carries only INDIRECT bingo text (a book title;
# a same-named other game). Genuine bingos, but the quote is weak — flagged so a
# human eyeballs them. Kept as candidates; not special-cased in emission.
WEAK_EVIDENCE = {"cherry-picker", "continental-super-7"}

# Hand-authored verbatim quotes, one per word-detected candidate (keyed by slug).
# Each is an exact substring of the model's IPDB notes / notable_features; the
# " [...] " marker joins spans across an omitted stretch (verify-quotes checks
# each span verbatim). Multi-mode SIRMO/Splin machines quote their "Bingo Game"
# mode via that join, sidestepping the bullet glyph in the source.
WORD_QUOTES: dict[str, str] = {
    # -- core --
    "3-4-5": "First United Bingo game with conventional playfield",
    "3-in-line": "Bingo card in both backglass and playfield lights corresponding number earned during play.",
    "5-star": "The center star hole lights all stars on the (purchased) backglass bingo cards.",
    "apollo-ball": 'had a release (to production) date of 9-25-69 as a "6 card bingo"',
    "bingo-continental-one-ball-euro": "Three types of games: [...] Bingo Game",
    "bongo": "Bingo card in both backglass and playfield lights corresponding number earned during play.",
    "broadway-2": "Bright Lights and Broadway were Bally's first two bingo machines following a gap of many years since their very first one in 1937, Line-Up.",
    "cherry-picker": "several modified features, which are described in Jeffrey Lawton's book Bingo Pinball Machines on page 62.",
    "continental": "this solid state Continental classifies as Bally's last full production bingo game.",
    "continental-super-7": "indicating GAA made a bingo game with the same name",
    "diamond-flipper": "This is a bingo machine equipped by the manufacturer with flippers and was made for export to Italy.",
    "diamond-flipper-di-lusso": "This is a bingo machine equipped by the manufacturer with flippers and was made for export to Italy.",
    "dixieland-3": "Two different games: [...] Bingo Game",
    "euro-star": "'Euro Star' is a conversion of an unknown bingo machine made by WIMI whose logo can be seen on the coin door.",
    "flipper-bingo": "Scoring any number 1 through 9 on the playfield lights up the number on the backglass bingo card.",
    "flipperino": "This is a bingo machine equipped by the manufacturer with flippers and was made for export to Italy.",
    "galaxy-2": "This is the only 24-hole bingo built by Bally.",
    "golden-flipper": "This is a bingo machine equipped by the manufacturer with flippers and was made for export to Italy.",
    "golden-gate-3-game": "between the 1st and 4th bingo cards there is no large window",
    "golden-gate-388": "Three types of games: [...] Bingo Game",
    "golden-gate-4-game": "between the 1st and 4th bingo cards this game has a large window",
    "golden-gate-75": 'lists Model 1017 as a bingo named "Golden Gate 75"',
    "golden-gate-euro": "Four types of games: [...] Bingo Game",
    "lucky-7": "had a release (to production) date of 6-29-70 as a bingo",
    "medieval": "Unusually, this bingo machine has flippers but they may have been retrofitted.",
    "miss-florida-2": "The manual owner advised us that this game is a bingo machine.",
    "outer-space-2": "has a release (to production) date of 6-27-80 as a 6-card electronic bingo",
    "outer-space-remote": "has a release (to production) date of 6-27-80 as a 6-card electronic bingo",
    "royal-bingo": "Three modes of play: Party, Bingo, or bet Red/Black.",
    "space-game-1-card": 'Recel produced two bingo games, both named "Space Game".',
    "space-game-1-card-2": 'Petaco produced two bingo games, both named "Space Game".',
    "space-game-7-card": 'Recel produced two bingo games, both named "Space Game".',
    "space-game-7-card-2": 'Petaco produced two bingo games, both named "Space Game".',
    "spot-em": "5 balls for 10 cents for one bingo card.",
    "stars-3": "First United Bingo game with conventional cabinet",
    "super-ball": "Four different games: [...] Bingo Game",
    "super-circus-2": "Four different games: [...] Bingo Game",
    "super-flipper-2": "This is a bingo machine equipped by the manufacturer with flippers and was made for export to Italy.",
    "tahiti-4": 'identifies this Model 1030 game as a "3 Card-6 Ball Bingo"',
    "tahiti-7": 'Bally documentation lists Model 1189-E as an "electronic bingo"',
    "venus-3": "indicates model 819 'Venus' was a bingo machine not made",
    "yukon-2": "The playfield on the drawings is of a 25-hole bingo playfield and precisely matches the photographs shown here of the Model 147 Yukon bingo game.",
    # -- flagged: hybrid --
    "disk-jockey": "Combination bingo machine and pinball.",
    "four-corners": "Combines elements of a bingo machine with flipper pinball.",
    # -- flagged: one-ball --
    "jokers-ladders-one-ball": "This is a one-ball game with a small bingo-type playfield in an upright cabinet.",
    "one-ball-bonus-multiplier": "This is a one-ball game with a small bingo-type playfield in an upright cabinet.",
    "one-ball-circus": "The name of this bingo indicates one-ball play",
    "one-ball-conti": "This is a one-ball game with a small bingo-type playfield in an upright cabinet.",
    "party-games": "This is a one-ball game with a small bingo-type playfield in an upright cabinet",
    "penalty-one-ball": "This bingo is listed on the manufacturer's website as a one ball game.",
    "penalty-une-bille": "This bingo is listed on the manufacturer's website as a one ball game.",
    "president-one-ball": "clearly shows the artful red logo design of the manufacturer TSCC above the 5th bingo card.",
    "triple-joker-2": "This is a one-ball game with a small bingo-type playfield in an upright cabinet.",
    "up-n-down-one-ball": "This is a one-ball game with a small bingo-type playfield in an upright cabinet.",
    # -- flagged: word-bingo --
    "crosswords": "for placement in locations that would not accept traditional bingo machines",
    "spelling-bee-2": "for placement in locations that would not accept traditional bingo machines",
}


def struct_note(hole_feature: str | None, hole_count: int) -> str:
    """The note for a struct row — reasoning from the model's own hole feature."""
    feat = "gobble holes" if hole_feature == "gobble-holes" else "trap holes"
    return (
        f"Marking this model as a bingo because its {hole_count} {feat} form the "
        f"in-line bingo playfield: balls landing in the hole grid light numbers on "
        f"the backglass card, scored in a line."
    )


def lineage_note(lineage_via: str) -> str:
    """The note for a lineage row — reasoning from the catalog edge to a bingo.

    For converted bingos that describe themselves only via their donor (e.g. a
    repainted bingo), carrying no bingo word, hole prose or bingo-only maker. No
    cite: the model-to-model edge is the catalog's own data."""
    return f"Marking this model as a bingo because it is a {lineage_via}, a bingo."


def maker_note(maker: str) -> str:
    """The note for a maker row — reasoning from the bingo-only manufacturer.

    Used for the modern electronic six-card machines that carry no hole-count
    prose and never say "bingo": the evidence is the maker, whose entire catalog
    is in-line bingo. No cite (the maker identity is the catalog's own data)."""
    return (
        f"Marking this model as a bingo because it is a {maker} machine, and "
        f"{maker}'s catalog is entirely in-line bingo machines (multi-card gambling "
        f"pinballs built for export)."
    )


def load_rows() -> list[dict]:
    """Read bingo.sql's ``bingo_patch_rows`` view as JSON, from the flipcommons checkout."""
    load_env()
    fc = os.environ.get("FLIPCOMMONS_DIR") or str(FLIPCOMMONS_DIR)
    proc = subprocess.run(
        [
            "duckdb", "-init", str(BINGO_SQL), ":memory:",
            "COPY (FROM bingo_patch_rows) TO '/dev/stdout' (FORMAT json, ARRAY true);",
        ],
        cwd=fc, capture_output=True, text=True, check=True,
    )
    return json.loads(proc.stdout)


def main() -> None:
    rows = load_rows()
    entries: list[str] = []
    missing: list[str] = []
    for r in sorted(rows, key=lambda r: r["slug"]):
        ref = f"model.{r['slug']}"
        if r["kind"] == "struct":
            entries.append(
                pk.entry(
                    ref,
                    note=struct_note(r["hole_feature"], r["hole_count"]),
                    fields={"game_format": GAME_FORMAT},
                )
            )
        elif r["kind"] == "maker":
            entries.append(
                pk.entry(
                    ref,
                    note=maker_note(r["maker"]),
                    fields={"game_format": GAME_FORMAT},
                )
            )
        elif r["kind"] == "lineage":
            entries.append(
                pk.entry(
                    ref,
                    note=lineage_note(r["lineage_via"]),
                    fields={"game_format": GAME_FORMAT},
                )
            )
        else:  # word
            quote = WORD_QUOTES.get(r["slug"])
            if not quote:
                missing.append(r["slug"])
                continue
            entries.append(
                pk.entry(
                    ref,
                    cite={"ref": f"ipdb:{r['ipdb_id']}", "quote": quote},
                    note=BUCKET_NOTES.get(r["bucket"]),  # None for core rows
                    fields={"game_format": GAME_FORMAT},
                )
            )
    if missing:
        raise SystemExit(
            f"WORD_QUOTES missing a verbatim quote for {len(missing)} word rows: {missing}"
        )
    pk.write_patch(
        PATCH_PATH,
        attribution="flipcommons-catalog",
        description="Classify the catalog's bingo-pinball machines.",
        entries=entries,
    )
    kinds = {k: sum(1 for r in rows if r["kind"] == k) for k in ("struct", "word", "maker", "lineage")}
    print(f"wrote {PATCH_PATH.relative_to(REPO_ROOT)} — {len(entries)} entries "
          f"({kinds['struct']} struct / {kinds['word']} word / {kinds['maker']} maker / {kinds['lineage']} lineage)")
    print("weak-evidence word rows to eyeball: " + ", ".join(sorted(WEAK_EVIDENCE)))


if __name__ == "__main__":
    main()
