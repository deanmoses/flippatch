"""Emit patch 0216 — the Houdini family: 100th Anniversary and its 2017 siblings.

See ../0215-frontier-2026/ENRICHMENT-PLAN.md for the family split and Houdini.md
beside this file for the evidence inventory, the catalog baseline, and the user
decisions this generator encodes (2026-08-07).

SCOPE IS THE WHOLE FAMILY: Houdini: Master of Mystery (2017), its Deluxe, and the
100th Anniversary (2026). `Houdini "Master Mystery"` (IPDB 6469) is the never-built
Popadiuk/Andrews design, NOT a sibling — leave it alone.

THE VARIANT RULE (user decision): a variant carries every credit of its base, and
the hardware of the shared design is a fact about every edition of it. So the
Deluxe and the 100th get the full 2017 team and the base hardware, cited to
`ipdb:6470` — the BASE game's row — with a `note:` saying why the value follows.
The quotable IPDB row now renders the credit/ModelNumber/MPU lines (see
scripts/quote_verify/verify_quotes.py `ipdb_row_text`), so these quotes are gated.

Only missing facts are asserted; the baseline table in Houdini.md records what
each model already holds. Deliberately absent:
  descriptions    the lint wants inline cites and TWO sources per record
                  description; a follow-up patch's job.
  month (100th)   the announcement is dated 03/19/2026 but no source states the
                  release month.
  speakers        4 (site) vs 6 (flyer + IPDB) — moot: no catalog field or
                  gameplay-feature term holds a speaker count.
  multiball count on the BASE 2017 model — `multiball` is already attached there
                  count-less; adding a count would modify an existing fact.

Run: uv run python campaigns/0215-frontier-2026/model-families/houdini/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0216-houdini.yaml"

MOM = "model.houdini-master-of-mystery"
DELUXE = "model.houdini-master-of-mystery-deluxe"
ANNIV = "model.houdini-100th-anniversary"

ANN = "https://americanpinball.com/houdini-100th-anniversary-pinball/"
SPEC = "https://americanpinball.com/houdini/"
IPDB = "ipdb:6470"

# The full 2017 team, verbatim from IPDB 6470's credit lines.
TEAM = [
    ("joe-balcer", "design"),
    ("joe-balcer", "mechanics"),
    ("jeff-busch", "art"),
    ("matt-riesterer", "art"),
    ("ish-raneses", "animation"),
    ("matt-kern", "music"),
    ("matt-kern", "sound"),
    ("josh-kugler", "software"),
]
TEAM_QUOTE = (
    "Design by: Joe Balcer [...] Art by: Jeff Busch, Matt Riesterer [...] "
    "Dots/Animation by: Ish Raneses [...] Mechanics by: Joe Balcer [...] "
    "Music by: Matt Kern [...] Sound by: Matt Kern [...] Software by: Josh Kugler"
)

# IPDB's Notable Features line — the counted base hardware of the shared design.
HARDWARE_QUOTE = (
    "Flippers (2), Pop bumpers (3), Slingshots (2), Stereo speakers (6), "
    "Magnets (3), Catapults (2), Theater spotlights (2), Multiball."
)
BASE_HARDWARE: list[str | dict[str, int]] = [
    {"flippers": 2},
    {"pop-bumpers": 3},
    {"slingshots": 2},
    {"magnets": 3},
    {"catapults": 2},
    "multiball",
]

VARIANT_NOTE = (
    "IPDB 6470 is the base Houdini: Master of Mystery row; this model is a "
    "variant of it (same game design), so the base game's value carries."
)


def cite(ref: str, quote: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote}


def main() -> None:
    entries = [
        # The vocabulary additions come first: a gameplay_feature member must resolve.
        # Neither affects ball behaviour — they are feedback and decoration — but the
        # vocabulary already carries backbox animations, lockdown-bar buttons and shaker
        # motors on the same footing, so they are consistent with it as it stands.
        pk.entry("gameplay-feature.toppers", create=True, fields={"name": "Toppers"}),
        pk.entry("gameplay-feature.knockers", create=True, fields={"name": "Knockers"}),
        # ------------------------------------------------------------------
        # Houdini: Master of Mystery (2017) — the base game.
        # ------------------------------------------------------------------
        pk.entry(
            MOM,
            cite=cite(
                IPDB,
                "The manufacturer's website stated the first game shipped 12/30/2017.",
            ),
            fields={"production_status": "produced"},
        ),
        pk.entry(
            MOM,
            cite=cite(IPDB, HARDWARE_QUOTE),
            fields={"game_format": "pinball"},
        ),
        # The spec page's Rules block is common to every Houdini edition.
        pk.entry(
            MOM,
            cite=cite(SPEC, "1 Video Mode"),
            relationships={"gameplay_feature": [{"video-modes": 1}]},
        ),
        # ------------------------------------------------------------------
        # Houdini: Master of Mystery (Deluxe) — variant_of the base (already
        # linked); nearly empty in the catalog, so the shared design's facts
        # land here via IPDB 6470 with the variant note.
        # ------------------------------------------------------------------
        pk.entry(
            DELUXE,
            note=VARIANT_NOTE,
            cite=cite(IPDB, TEAM_QUOTE),
            credits=TEAM,
        ),
        pk.entry(
            DELUXE,
            note=VARIANT_NOTE,
            cite=cite(
                IPDB,
                "The manufacturer's website stated the first game shipped 12/30/2017.",
            ),
            fields={"production_status": "produced"},
        ),
        pk.entry(
            DELUXE,
            note=VARIANT_NOTE,
            cite=cite(IPDB, HARDWARE_QUOTE),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            DELUXE,
            note=VARIANT_NOTE,
            cite=cite(IPDB, "Type: Solid State Electronic (SS)"),
            fields={"technology_generation": "solid-state"},
        ),
        pk.entry(
            DELUXE,
            note=VARIANT_NOTE,
            cite=cite(IPDB, "MPU: Multimorphic P3-ROC"),
            fields={"system": "multimorphic-p3-roc"},
        ),
        pk.entry(
            DELUXE,
            note=VARIANT_NOTE,
            cite=cite(IPDB, "Backbox has 15.6 inch color LCD monitor."),
            fields={"display_type": "lcd"},
        ),
        pk.entry(
            DELUXE,
            note=VARIANT_NOTE,
            cite=cite(IPDB, "Players: 4"),
            fields={"player_count": "4"},
        ),
        pk.entry(
            DELUXE,
            note=VARIANT_NOTE,
            cite=cite(IPDB, HARDWARE_QUOTE),
            relationships={"gameplay_feature": BASE_HARDWARE},
        ),
        # The Deluxe's own tier, from the spec page's explicitly-headed list.
        pk.entry(
            DELUXE,
            cite=cite(SPEC, "Deluxe Features [...] Shaker [...] Topper [...] Knocker"),
            relationships={"gameplay_feature": ["shaker-motors", "toppers", "knockers"]},
        ),
        pk.entry(
            DELUXE,
            cite=cite(SPEC, "1 Video Mode"),
            relationships={"gameplay_feature": [{"video-modes": 1}]},
        ),
        # ------------------------------------------------------------------
        # Houdini 100th Anniversary (2026) — a new edition of the same design.
        # ------------------------------------------------------------------
        pk.entry(
            ANNIV,
            cite=cite(
                ANN,
                "Now, American Pinball is proud to celebrate the legendary escape "
                "artist’s enduring legacy with the release of the Houdini 100th "
                "Anniversary Edition.",
            ),
            fields={"production_status": "produced"},
        ),
        pk.entry(
            ANNIV,
            cite=cite(ANN, "Introducing the Houdini 100th Anniversary Pinball Machine"),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            ANNIV,
            cite=cite(ANN, "one of the most exclusive versions of the game ever produced"),
            fields={"variant_of": "houdini-master-of-mystery"},
        ),
        # production_quantity and tag:limited-edition are NOT here — patch 0215
        # already asserts both on the 100th (user removed them 2026-08-08).
        pk.entry(
            ANNIV,
            cite=cite(
                ANN, "stunning new cabinet artwork by acclaimed artist Christopher Franchi"
            ),
            credits=[("christopher-franchi", "art")],
        ),
        pk.entry(
            ANNIV,
            note=VARIANT_NOTE,
            cite=cite(IPDB, TEAM_QUOTE),
            credits=TEAM,
        ),
        # One sentence names all three, so they share an entry.
        pk.entry(
            ANNIV,
            cite=cite(
                ANN,
                "Each game includes a custom topper, Magic Glass, shaker motor, knocker, "
                "and mirrored art blades as standard equipment.",
            ),
            relationships={"gameplay_feature": ["toppers", "knockers", "shaker-motors"]},
        ),
        pk.entry(
            ANNIV,
            note=VARIANT_NOTE,
            cite=cite(IPDB, HARDWARE_QUOTE),
            relationships={"gameplay_feature": BASE_HARDWARE},
        ),
        # The spec page's edition carousel includes the 100th, so its common
        # Rules/Cabinet blocks state these about this edition too.
        pk.entry(
            ANNIV,
            cite=cite(SPEC, "1 Video Mode"),
            relationships={"gameplay_feature": [{"video-modes": 1}]},
        ),
        pk.entry(
            ANNIV,
            cite=cite(SPEC, '15.6" Full Color LCD'),
            fields={"display_type": "lcd"},
        ),
        pk.entry(
            ANNIV,
            note=VARIANT_NOTE,
            cite=cite(IPDB, "MPU: Multimorphic P3-ROC"),
            fields={"system": "multimorphic-p3-roc"},
        ),
        pk.entry(
            ANNIV,
            note=VARIANT_NOTE,
            cite=cite(IPDB, "Type: Solid State Electronic (SS)"),
            fields={"technology_generation": "solid-state"},
        ),
        pk.entry(
            ANNIV,
            note=VARIANT_NOTE,
            cite=cite(IPDB, "Players: 4"),
            fields={"player_count": "4"},
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="Houdini family details: Master of Mystery, Deluxe, 100th Anniversary",
        entries=entries,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
