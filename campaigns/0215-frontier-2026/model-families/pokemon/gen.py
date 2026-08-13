"""Emit patch 0237 — the Pokémon family: Stern's 2026 Pro / Premium / Limited Edition.

See ../../README.md for the family split and Pokemon.md beside this file for
the evidence inventory, the catalog baseline, the traps and the decisions this
generator encodes (2026-08-13).

SCOPE IS THE WHOLE FAMILY, three models, no older siblings:
  2026  Pokémon — Pro / Premium / Limited Edition

Only missing facts are asserted; the baseline table in Pokemon.md records what
each model already holds. Deliberately absent (each recorded there):
  year / month / themes / abbreviations        already claimed (opdb, 0204, moses)
  LE tag + LE variant_of                       already claimed (0206, catalog)
  Premium -> Pro lineage                       Stern convention: no edge
  player_count                                 no source states it (Pro's 4 is opdb's)
  art person credit                            all art from The Pokemon Company
  descriptions                                 a follow-up patch's job

THE MATRIX IS MARKS, MOSTLY: a feature row's column membership is a visual
checkmark, so per-edition attaches cite the matrix quote-less (ref + locator +
note recording the checked rows) — RULEBOOK.md → Citing PDF evidence. Rows and
blocks that name their own subject (the LE ONLY block, the SPIKE 3 row, the
autograph row) are quoted normally (SKIP-PDF, author-checked). Wherever an
edition's own gated HTML page states the per-edition fact, that page is the
primary cite and the matrix corroborates.

Run: uv run python campaigns/0215-frontier-2026/model-families/pokemon/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0237-pokemon.yaml"

# ── Models ──────────────────────────────────────────────────────────────
PRO = "model.pokemon-pro"
PREM = "model.pokemon-premium"
LE = "model.pokemon-limited-edition"

# ── Sources ─────────────────────────────────────────────────────────────
PR = (
    "https://www.sternpinball.com/2026/02/13/"
    "become-a-top-pokemon-trainer-with-stern-pinballs-newest-line-of-machines"
)
# The matrix filename carries the game's internal dev codename "PANTS" (per
# Kineticist) and a © that must stay percent-encoded, exactly as cached.
MATRIX = "https://wp.sternpinball.com/wp-content/uploads/2026/02/PANTS-Matrix-added-%C2%A9_021226.pdf"
PAGE_PRO = "https://www.sternpinball.com/game/pokemon/pro"
PAGE_PREM = "https://www.sternpinball.com/game/pokemon/premium"
PAGE_LE = "https://www.sternpinball.com/game/pokemon/limited-edition"
MANUAL_PRO = "https://wp.sternpinball.com/wp-content/uploads/2026/04/Pokemon_Pro_web.pdf"
MANUAL_LEPRE = "https://wp.sternpinball.com/wp-content/uploads/2026/04/Pokemon_LE_Pre_web.pdf"
KIN = "https://www.kineticist.com/news/stern-pinball-reveals-pokemon-pinball"
AH = "https://arcadeheroes.com/2026/02/13/gotta-catch-em-all-stern-pinball-officially-unveils-pokemon"

MATRIX_LOCATOR = "PDF document page 1"
MATRIX_MARK_CITE = {"ref": MATRIX, "locator": MATRIX_LOCATOR}
TEAM_LOCATOR = "in the Design Team section"


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


def mark_note(column: str, rows: str) -> str:
    """The entry note for a quote-less matrix mark cite (a checkmark is a
    mark, not text — RULEBOOK.md → Citing PDF evidence)."""
    return f"On the feature matrix sheet, the {column} column carries a checkmark for the rows: {rows}"


# ── Press-release quotes (HTML, machine-gated) ──────────────────────────
PR_RELEASED = "revealed and released a new pinball machine – Pokémon by Stern Pinball"
PR_AVAILABLE = (
    "Pokémon by Stern Pinball is available now in Pro, Premium, and Limited "
    "Edition (LE) models."
)
PR_SPIKE = (
    "Powered by Stern’s SPIKE 3 technology, this dynamic machine brings the "
    "thrill of catching, battling rivals and training Pokémon in the "
    "silverball arena for the very first time."
)
PR_MEOWTH = (
    "The interactive Meowth Balloon toy swoops down onto the battle arena to "
    "challenge the Trainer."
)
PR_MAGNET = (
    "Premium and Limited Edition games include an interactive electromagnet "
    "that adds chaos to the battle arena."
)
PR_VOICE = (
    "Bringing the experience to life even further, custom voiceovers for "
    "Pikachu and the notorious Team Rocket leader, Giovanni, captures the "
    "spirit and humor that fans know and love."
)
PR_LE_EQUIPMENT = (
    "Trainers looking for an elevated experience will be able to enjoy the "
    "highly collectible Limited Edition model, limited to 750 games globally, "
    "which includes the updated Expression Lighting System™ and Speaker "
    "Expression Lighting System with Pokémon-themed game effects, a "
    "full-color mirrored backglass, full-color high-definition cabinet "
    "decals, a custom LE Pokémon pinball armor, a custom designer-autographed "
    "bottom arch, upgraded audio system, anti-reflection pinball playfield "
    "glass, shaker motor, a sequentially numbered plaque, a signed "
    "Certificate of Authenticity, and a digital Insider Connected LE owner’s "
    "badge on registration."
)

# ── Matrix quotes (PDF text layer; author-checked, SKIP-PDF) ────────────
MX_SPIKE = (
    "This one-of-a-kind pinball experience is powered by Stern’s "
    "next-generation technology with the new SPIKE 3 platform."
)
MX_DISPLAY = "Custom animations on larger, 18.5” full HD display."
MX_AUTOGRAPH = "Individually Autographed by Game Designers Jack Danger and George Gomez."
MX_750 = "Production limited to 750 machines."

# ── Kineticist quotes (HTML, machine-gated) ─────────────────────────────
KIN_DESIGN = "Design: Jack Danger, George Gomez"
KIN_CODE = "Code: Tanio Klyce, Andrew Wilkening, Josh Henderson"
KIN_PROD_PRO = (
    "Stern is prioritizing on-location Pro models first, with production "
    "starting late February through early March."
)
KIN_PROD_PREMLE = (
    "Limited Edition builds follow shortly after, with Premium models "
    "scheduled to begin production later in March."
)
KIN_PIKACHU_PREMLE = (
    "Premium/LE upgrades to a fully animatronic Pikachu with movement and "
    "custom speech."
)
KIN_WHIRLPOOL = (
    "Premium/LE adds the Squirtle Whirlpool spinning bowl that charges water "
    "energy."
)
KIN_PSYDUCK_PRO = "Psyduck: Pro gets a stand up target."
KIN_MEOWTH = (
    "An interactive Meowth Balloon descends to the playfield arena during "
    "battle sequences — Team Rocket's signature Meowth as a physical target "
    "to bash."
)

AH_DESIGNED = "this was designed by Jack Danger and George Gomez"

# All-editions matrix rows, per section (grid transcribed off the rendered
# sheet 2026-08-13; readings recorded here). Row lists inside a note stay
# verbatim row labels.
ROWS_COMMON_GF = (
    "Hit Pokédex captive ball to scan Pokémon; Town themed right scoop "
    "starts Rival Battles and other features; Complete B-A-T-T-L-E targets "
    "to advance in game and start Team Rocket Multiball; Bulbasaur outer "
    "left orbit leads to the back ramp and returns the ball to the right "
    "flipper; Right ramp encircles Pikachu toy to advance to Pikachu "
    "multiball. Feeds wire ramp back to right flipper; Charmander optical "
    "spinning target enters Tall Grass themed pop bumper area of playfield "
    "where players can discover Pokémon; 2 flippers; 2 lit pop bumpers; "
    "Full-spectrum RGB LED playfield arrow inserts"
)
FEATURES_COMMON_GF: list[str | dict[str, int]] = [
    "captive-ball",
    "scoops",
    "targets",
    "multiball",
    "orbits",
    "ramps",
    "optical-spinners",
    {"flippers": 2},
    {"pop-bumpers": 2},
    "rgb-playfield-inserts",
]
ROWS_HW_PROPREM = (
    "Powder-coated black wrinkle finish hand guard side armor, hinges, front "
    "lockdown molding and legs; Multifunction Action Button on lockdown bar"
)
ROWS_HW_LE = "Multifunction Action Button on lockdown bar"
ROWS_GENERAL = "6 pinballs; Stereo sound system with 3-channel amplifier"

CABINET_NOTE = (
    "The classification to a standard floor cabinet follows from the "
    "documented full-size dimensions."
)
LEPRE_MANUAL_NOTE = (
    "The manual covers the Limited Edition and the Premium in one document — "
    "its title sheet lists both model numbers."
)


def manual_specs_cite(ref: str, folio: str) -> dict[str, str]:
    return {
        "ref": ref,
        "quote": "Weight 210 lbs [...] Max dimensions, leg levelers extended (h, w, d) 78 x 27.75 x 57 in",
        "locator": f"printed page {folio}, PDF document page {folio}, in the SPECIFICATIONS, MECHANICAL, GAME SETUP table",
    }


def shared(model: str, column: str, prod_cite: dict[str, str]) -> list[str]:
    """The entries every edition gets; *column* names its matrix column."""
    return [
        pk.entry(
            model,
            cite=[cite(PR, PR_AVAILABLE), prod_cite],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            model,
            cite=cite(PR, PR_RELEASED),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            model,
            cite=[
                cite(PR, PR_SPIKE),
                cite(MATRIX, MX_SPIKE, locator=MATRIX_LOCATOR),
            ],
            fields={"system": "stern-spike-3"},
        ),
        pk.entry(
            model,
            cite=[
                cite(MATRIX, MX_AUTOGRAPH, locator=MATRIX_LOCATOR),
                cite(KIN, KIN_DESIGN, locator=TEAM_LOCATOR),
                cite(AH, AH_DESIGNED),
            ],
            credits=[("jack-danger", "design")],
        ),
        pk.entry(
            model,
            cite=[
                cite(MATRIX, MX_AUTOGRAPH, locator=MATRIX_LOCATOR),
                cite(KIN, KIN_DESIGN, locator=TEAM_LOCATOR),
                cite(AH, AH_DESIGNED),
            ],
            credits=[("george-gomez", "design")],
        ),
        pk.entry(
            model,
            cite=cite(KIN, KIN_CODE, locator=TEAM_LOCATOR),
            credits=[("tanio-klyce", "software")],
        ),
        pk.entry(
            model,
            cite=cite(KIN, KIN_CODE, locator=TEAM_LOCATOR),
            credits=[("andrew-wilkening", "software")],
        ),
        pk.entry(
            model,
            cite=cite(KIN, KIN_CODE, locator=TEAM_LOCATOR),
            credits=[("josh-henderson", "software")],
        ),
        pk.entry(
            model,
            note=mark_note(column, ROWS_COMMON_GF),
            cite=MATRIX_MARK_CITE,
            relationships={"gameplay_feature": FEATURES_COMMON_GF},
        ),
        pk.entry(
            model,
            cite=[cite(PR, PR_MEOWTH), cite(KIN, KIN_MEOWTH)],
            relationships={"gameplay_feature": ["bash-toys"]},
        ),
        pk.entry(
            model,
            cite=cite(PR, PR_VOICE),
            relationships={"gameplay_feature": ["speech"]},
        ),
        pk.entry(
            model,
            note=mark_note(column, ROWS_HW_LE if column == "LE" else ROWS_HW_PROPREM),
            cite=MATRIX_MARK_CITE,
            relationships={
                "gameplay_feature": (
                    ["lockdown-bar-buttons"]
                    if column == "LE"
                    else ["side-armor", "lockdown-bar-buttons"]
                )
            },
        ),
        pk.entry(
            model,
            note=mark_note(column, ROWS_GENERAL),
            cite=MATRIX_MARK_CITE,
            relationships={"gameplay_feature": [{"balls": 6}, "stereo-sound"]},
        ),
    ]


def main() -> None:
    entries = [
        # ── Scaffolding: the two people new to the catalog ──────────────
        pk.entry(
            "person.andrew-wilkening",
            create=True,
            cite=cite(KIN, KIN_CODE, locator=TEAM_LOCATOR),
            fields={"name": "Andrew Wilkening"},
        ),
        pk.entry(
            "person.josh-henderson",
            create=True,
            cite=cite(KIN, KIN_CODE, locator=TEAM_LOCATOR),
            fields={"name": "Josh Henderson"},
            relationships={"person_alias": ["Joshua Henderson"]},
        ),
        # ── Pokémon (Pro) ───────────────────────────────────────────────
        *shared(PRO, "PRO", cite(KIN, KIN_PROD_PRO, locator="in the Production Timeline section")),
        pk.entry(
            PRO,
            cite=[
                cite(PAGE_PRO, "Pikachu static toy with custom recorded speech."),
                cite(PAGE_PRO, "RGB illuminated static Poké Ball includes ball stop post on left ramp."),
            ],
            relationships={"gameplay_feature": ["static-toys"]},
        ),
        pk.entry(
            PRO,
            note=mark_note("PRO", "Psyduck stand up target"),
            cite=[
                cite(KIN, KIN_PSYDUCK_PRO, locator="in the Edition Comparison section"),
                MATRIX_MARK_CITE,
            ],
            relationships={"gameplay_feature": ["standup-targets"]},
        ),
        pk.entry(
            PRO,
            cite=cite(
                MANUAL_PRO,
                "POKÉMON PRO #500-55AG-01",
                locator="PDF document page 1, the title sheet",
            ),
            fields={"manufacturer_model_identifier": "500-55AG-01"},
        ),
        pk.entry(
            PRO,
            note=CABINET_NOTE,
            cite=manual_specs_cite(MANUAL_PRO, "67"),
            fields={"cabinet": "floor"},
        ),
        # ── Pokémon (Premium) ───────────────────────────────────────────
        *shared(
            PREM,
            "PREM",
            cite(KIN, KIN_PROD_PREMLE, locator="in the Production Timeline section"),
        ),
        pk.entry(
            PREM,
            note=(
                "SPIKE 3 is Stern's computerized game platform, so the "
                "solid-state generation follows."
            ),
            cite=cite(PR, PR_SPIKE),
            fields={"technology_generation": "solid-state"},
        ),
        pk.entry(
            PREM,
            note=mark_note("PREM", "Custom animations on larger, 18.5” full HD display"),
            cite=cite(MATRIX, MX_DISPLAY, locator=MATRIX_LOCATOR),
            fields={"display_type": "lcd"},
        ),
        pk.entry(
            PREM,
            cite=[
                cite(PAGE_PREM, "Pikachu animatronic toy reacts to playfield action with movement and custom recorded speech."),
                cite(PAGE_PREM, "Animatronic Poké Ball ball-lock with RGB illumination at the Left Ramp."),
            ],
            relationships={"gameplay_feature": ["animatronic-toys"]},
        ),
        pk.entry(
            PREM,
            cite=cite(PAGE_PREM, "Animatronic Poké Ball ball-lock with RGB illumination at the Left Ramp."),
            relationships={"gameplay_feature": ["ball-locks", "ball-holding-toys"]},
        ),
        pk.entry(
            PREM,
            cite=cite(PR, PR_MAGNET),
            relationships={"gameplay_feature": ["magnets"]},
        ),
        pk.entry(
            PREM,
            note=mark_note(
                "PREM",
                "Left ramp feeds the Squirtle Whirlpool bowl for spinning "
                "ball action. When qualified, the Squirtle Whirlpool charges "
                "up water energy",
            ),
            cite=[
                cite(KIN, KIN_WHIRLPOOL, locator="in the Edition Comparison section"),
                MATRIX_MARK_CITE,
            ],
            relationships={"gameplay_feature": ["whirlpools"]},
        ),
        pk.entry(
            PREM,
            cite=cite(
                MANUAL_LEPRE,
                "POKÉMON PREMIUM #500-55AH-01",
                locator="PDF document page 1, the title sheet",
            ),
            fields={"manufacturer_model_identifier": "500-55AH-01"},
        ),
        pk.entry(
            PREM,
            note=LEPRE_MANUAL_NOTE + " " + CABINET_NOTE,
            cite=manual_specs_cite(MANUAL_LEPRE, "72"),
            fields={"cabinet": "floor"},
        ),
        # ── Pokémon (Limited Edition) ───────────────────────────────────
        *shared(
            LE,
            "LE",
            cite(KIN, KIN_PROD_PREMLE, locator="in the Production Timeline section"),
        ),
        pk.entry(
            LE,
            note=(
                "SPIKE 3 is Stern's computerized game platform, so the "
                "solid-state generation follows."
            ),
            cite=cite(PR, PR_SPIKE),
            fields={"technology_generation": "solid-state"},
        ),
        pk.entry(
            LE,
            note=mark_note("LE", "Custom animations on larger, 18.5” full HD display"),
            cite=cite(MATRIX, MX_DISPLAY, locator=MATRIX_LOCATOR),
            fields={"display_type": "lcd"},
        ),
        pk.entry(
            LE,
            cite=[
                cite(PAGE_LE, "Animatronic Poké Ball ball-lock with RGB illumination at the Left Ramp."),
                cite(KIN, KIN_PIKACHU_PREMLE, locator="in the Edition Comparison section"),
            ],
            relationships={"gameplay_feature": ["animatronic-toys"]},
        ),
        pk.entry(
            LE,
            cite=cite(PAGE_LE, "Animatronic Poké Ball ball-lock with RGB illumination at the Left Ramp."),
            relationships={"gameplay_feature": ["ball-locks", "ball-holding-toys"]},
        ),
        pk.entry(
            LE,
            cite=[
                cite(PR, PR_MAGNET),
                cite(PAGE_LE, "The interactive Meowth Balloon Arena magnet provides kinetic action and excitement."),
            ],
            relationships={"gameplay_feature": ["magnets"]},
        ),
        pk.entry(
            LE,
            cite=cite(PAGE_LE, "Left ramp feeds the Squirtle Whirlpool bowl for spinning ball action."),
            relationships={"gameplay_feature": ["whirlpools"]},
        ),
        pk.entry(
            LE,
            cite=[
                cite(PR, "limited to 750 games globally"),
                cite(MATRIX, MX_750, locator=MATRIX_LOCATOR),
            ],
            fields={"production_quantity": 750},
        ),
        pk.entry(
            LE,
            cite=cite(PR, PR_LE_EQUIPMENT),
            relationships={
                "gameplay_feature": [
                    "cabinet-expression-lighting",
                    "speaker-expression-lighting",
                    "mirrored-backglasses",
                    "cabinet-armor",
                    "designer-autographs",
                    "anti-reflection-playfield-glass",
                    "shaker-motors",
                    "numbered-plaques",
                ]
            },
        ),
        pk.entry(
            LE,
            cite=cite(
                MANUAL_LEPRE,
                "POKÉMON LE #500-55AJ-01",
                locator="PDF document page 1, the title sheet",
            ),
            fields={"manufacturer_model_identifier": "500-55AJ-01"},
        ),
        pk.entry(
            LE,
            note=CABINET_NOTE,
            cite=manual_specs_cite(MANUAL_LEPRE, "72"),
            fields={"cabinet": "floor"},
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="Pokémon family details across Stern's Pro, Premium and Limited Edition",
        entries=entries,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
