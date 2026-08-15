"""Emit patch 0242 — the Cardona family: the maker's two pre-2026 conversion
kits, created here, and their Williams/Bally donor machines, enriched.

See ../../README.md for the campaign and Cardona.md beside this file for the
evidence inventory, the catalog baseline, the traps and the decisions this
generator encodes (2026-08-15).

SCOPE IS THE WHOLE MAKER, four models:
  2022  No Good Gofers: Battle for the Green (Kit)  (Cardona Pinball Designs, to create)
  2023  Black Rose: Skull and Bones (Kit)           (Cardona Pinball Designs, to create)
  1997  No Good Gofers  (Williams, ipdb:4338)       (donor, to enrich)
  1992  Black Rose      (Bally, ipdb:313)           (donor, to enrich)

Only missing facts are asserted; the baseline table in Cardona.md records what
each model already holds. Deliberately absent (each recorded there): Eli Curtz
and the electronics rows (Pinside-only / platform-level), kit voice actors
(nobody named), kit cabinets, descriptions, donor hardware on the kits, BR
donor cabinet (its IPDB row has no dimensions block), Demolition Time.

ALL ROOTS ALREADY RESOLVE (0225's Cardona root carries the path-scoped wsimg
tenant; Kineticist, Planetary, ipdb:, youtube: are long seeded) — this patch
declares no sources.

NO CREDITS CARRY from the donors to the kits: a conversion kit is neither a
variant nor a remake. Each kit-to-donor link is a `conversion_kit` model
relationship, `license_status: licensed`.

Run: uv run python campaigns/0215-frontier-2026/model-families/cardona/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0242-cardona.yaml"

# ── Models ──────────────────────────────────────────────────────────────
NGG_KIT = "model.no-good-gofers-battle-for-the-green-kit"
BR_KIT = "model.black-rose-skull-and-bones-kit"
NGG97 = "model.no-good-gofers"
BR92 = "model.black-rose"

# ── Sources ─────────────────────────────────────────────────────────────
SHOP_NGG = (
    "https://cardonapinball.com/shop/ols/products/"
    "no-good-gofers-battle-for-the-green-upgrade-kit"
)
SHOP_BR = (
    "https://cardonapinball.com/shop/ols/products/"
    "black-rose-skull-and-bones-20-pinball-kit"
)
LOG_NGG = (
    "https://img1.wsimg.com/blobby/go/4bd466e8-edb0-49f6-afcc-31250ba5b0f3/"
    "downloads/b8901727-49fa-4784-801d-6663cfa49dd1/NGG%20rev%20changes%202025%2006%2001.pdf"
)
LOG_BR = (
    "https://img1.wsimg.com/blobby/go/4bd466e8-edb0-49f6-afcc-31250ba5b0f3/"
    "downloads/4c1e843c-5ca2-4426-9b9a-37d3ff7ac4be/BRose%2020250610%20change%20log.pdf"
)
KINETICIST = "https://www.kineticist.com/news/james-cardona-interview"
IPDB_NGG = "ipdb:4338"
IPDB_BR = "ipdb:313"

META = "in the page's meta description"
LOG_NGG_P1 = "PDF document page 1"
LOG_BR_P1 = "PDF document page 1"

# ── Shared quotes ───────────────────────────────────────────────────────
KIN_KIT_CATEGORY = (
    "It's a 2.0 kit, a category of officially licensed products that install "
    "into classic Bally/Williams machines and turns them into a new game "
    "experience, while keeping the original intact."
)
KIN_ROLES = (
    "He writes the code, designs the games, and has brought in more "
    "professional artists and voice actors with each title, while FAST "
    "Pinball handles the hardware."
)
KIN_THREE_TIMES = (
    "You've now done this three times, from No Good Gofers to Black Rose to "
    "Fish Tales."
)
SHOP_LICENSED = (
    "Cardona Pinball Designs is licensed by Planetary Pinball Supply to "
    "create 2.0 game kits for Bally-Williams titles"
)
NOTE_PRODUCED_KIT = (
    "An official, licensed, commercially sold product, so produced rather "
    "than aftermarket (DomainModel.md defines aftermarket as not an official "
    "commercial release)."
)
NOTE_SOLID_STATE = (
    "The FAST platform is a computerized game system, so the solid-state "
    "generation follows."
)
NOTE_KIT_FORMAT = (
    "The kit installs into a pinball machine and its result is a new pinball "
    "game, so the format follows."
)


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


def main() -> None:
    entries = [
        # ── 2022: No Good Gofers: Battle for the Green (Kit) ────────────
        pk.entry(
            "title.no-good-gofers-battle-for-the-green",
            create=True,
            fields={"name": "No Good Gofers: Battle for the Green"},
        ),
        pk.entry(
            NGG_KIT,
            create=True,
            fields={
                "name": "No Good Gofers: Battle for the Green (Kit)",
                "title": "no-good-gofers-battle-for-the-green",
                "corporate_entity": "cardona-pinball-designs",
                "year": 2022,
            },
            relationships={"theme": ["golf", "sports"]},
        ),
        pk.entry(
            NGG_KIT,
            note=NOTE_PRODUCED_KIT,
            cite=[
                cite(
                    LOG_NGG,
                    "version 20221215 [...] First commercial release",
                    locator=LOG_NGG_P1,
                ),
                cite(
                    KINETICIST,
                    "when we finally released No Good Gofers: Battle For the "
                    "Green, everyone was like, \"Yeah, yesterday's news.\"",
                ),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            NGG_KIT,
            note=(
                "The maker's release history stamps each version by date — "
                "the 20250601 sibling entry shows the YYYYMMDD convention — "
                "and labels 20221215 the first commercial release. Pinside's "
                "February 2023 reads as later framing; the maker's own "
                "document wins."
            ),
            cite=cite(
                LOG_NGG,
                "version 20221215 [...] First commercial release",
                locator=LOG_NGG_P1,
            ),
            fields={"month": 12},
        ),
        pk.entry(
            NGG_KIT,
            note=NOTE_KIT_FORMAT,
            cite=cite(KINETICIST, KIN_KIT_CATEGORY),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            NGG_KIT,
            cite=[
                cite(
                    SHOP_NGG,
                    "Includes everything you need to install No Good Gofers: "
                    "Battle For The Green into a No Good Gofers Pinball "
                    "machine. [...] Cardona Pinball Designs is licensed by "
                    "Planetary Pinball Supply to create 2.0 game kits for "
                    "Bally-Williams titles",
                    locator=META,
                ),
            ],
            model_relationship=[
                {
                    "target_machine": "no-good-gofers",
                    "relationship_type": "conversion_kit",
                    "license_status": "licensed",
                }
            ],
        ),
        pk.entry(
            NGG_KIT,
            note=(
                "The industrial 15.6-inch monitor in the kit's replacement "
                "speaker panel is an LCD-class display."
            ),
            cite=cite(
                SHOP_NGG,
                'Speaker panel with (2) 4" speakers, a industrial 15.6 inch '
                "monitor, and associated cabling.",
                locator=META,
            ),
            fields={"display_type": "lcd"},
        ),
        pk.entry(
            NGG_KIT,
            note=NOTE_SOLID_STATE,
            cite=[
                cite(
                    LOG_NGG,
                    "tested with FAST firmware 2.1, mpf 0.56 dev 20",
                    locator=LOG_NGG_P1,
                ),
                cite(
                    SHOP_NGG,
                    "FAST Interface controller board (to be installed in the "
                    "removed CPU location). CPU panel that includes CPU, FAST "
                    "audio and accessory controller, and associated cabling "
                    "(to be installed in the removed audio/video board "
                    "location).",
                    locator=META,
                ),
            ],
            fields={
                "technology_generation": "solid-state",
                "system": "fast-pinball",
            },
        ),
        pk.entry(
            NGG_KIT,
            cite=[
                cite(KINETICIST, KIN_ROLES),
                cite(
                    KINETICIST,
                    "I had only written No Good Gofers: Battle For The Green "
                    "and developed the game for P-Roc hardware.",
                ),
            ],
            credits=[("james-cardona", "design"), ("james-cardona", "software")],
        ),
        pk.entry(
            NGG_KIT,
            cite=cite(
                SHOP_NGG,
                "Cart Smash - multiball mode started by enough gopher or "
                "cart hits, shoot cart or TNT",
                locator=META,
            ),
            relationships={"gameplay_feature": ["multiball"]},
        ),
        # ── 2023: Black Rose: Skull and Bones (Kit) ─────────────────────
        pk.entry(
            "title.black-rose-skull-and-bones",
            create=True,
            fields={"name": "Black Rose: Skull and Bones"},
        ),
        pk.entry(
            BR_KIT,
            create=True,
            fields={
                "name": "Black Rose: Skull and Bones (Kit)",
                "title": "black-rose-skull-and-bones",
                "corporate_entity": "cardona-pinball-designs",
                "year": 2023,
            },
            relationships={"theme": ["fantasy", "fictional", "pirates"]},
        ),
        pk.entry(
            BR_KIT,
            note=NOTE_PRODUCED_KIT,
            cite=[
                cite(
                    LOG_BR,
                    "Black Rose: Skull and Bones version 2023_06_22 [...] "
                    "1st production release",
                    locator=LOG_BR_P1,
                ),
                cite(KINETICIST, KIN_THREE_TIMES),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            BR_KIT,
            note=(
                "The maker's release history stamps each version by date and "
                "labels 2023_06_22 the 1st production release. Pinside's "
                "August 2023 reads as later framing; the maker's own document "
                "wins."
            ),
            cite=cite(
                LOG_BR,
                "Black Rose: Skull and Bones version 2023_06_22 [...] "
                "1st production release",
                locator=LOG_BR_P1,
            ),
            fields={"month": 6},
        ),
        pk.entry(
            BR_KIT,
            note=NOTE_KIT_FORMAT,
            cite=cite(KINETICIST, KIN_KIT_CATEGORY),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            BR_KIT,
            cite=cite(
                SHOP_BR,
                "Black Rose: Skull and Bones (BR:SnB) A Licensed “2.0” "
                "Upgrade Kit by Cardona Pinball Designs Includes everything "
                "you need to install Black Rose: Skull and Bones into a "
                "Black Rose Pinball machine.",
                locator=META,
            ),
            model_relationship=[
                {
                    "target_machine": "black-rose",
                    "relationship_type": "conversion_kit",
                    "license_status": "licensed",
                }
            ],
        ),
        pk.entry(
            BR_KIT,
            note=(
                "The industrial 15.6-inch monitor in the kit's display panel "
                "is an LCD-class display."
            ),
            cite=cite(
                SHOP_BR,
                "display panel with an industrial 15.6 inch monitor, and "
                "associated cabling.",
                locator=META,
            ),
            fields={"display_type": "lcd"},
        ),
        pk.entry(
            BR_KIT,
            note=NOTE_SOLID_STATE,
            cite=[
                cite(
                    LOG_BR,
                    "sound board ID: EMU FP-CPU-1060 fast controller ID: NET "
                    "FP-SBI-0095 02.5",
                    locator=LOG_BR_P1,
                ),
                cite(
                    SHOP_BR,
                    "CPU panel that includes CPU, FAST audio and accessory "
                    "controller, and associated cabling (to be installed in "
                    "the removed audio/video board location).",
                    locator=META,
                ),
            ],
            fields={
                "technology_generation": "solid-state",
                "system": "fast-pinball",
            },
        ),
        pk.entry(
            BR_KIT,
            cite=cite(KINETICIST, KIN_ROLES),
            credits=[("james-cardona", "design"), ("james-cardona", "software")],
        ),
        pk.entry(
            BR_KIT,
            cite=cite(
                KINETICIST,
                "I hired Scott Gullicks to do my Black Rose artwork and now "
                "Brian Allen for Fish Tales.",
            ),
            credits=[("scott-gullicks", "art")],
        ),
        # ── 1997: No Good Gofers (Williams) ─────────────────────────────
        pk.entry(
            NGG97,
            note=(
                "A machine produced in four figures was commercially "
                "produced; IPDB records the exact run as 2,711."
            ),
            cite=cite(IPDB_NGG, "Production: 2711"),
            fields={"production_status": "produced"},
        ),
        # One changeset: format and the missing playfield hardware rest on
        # the same Notable Features line (the 0225 older-sibling pattern).
        # Every counted mechanism in the line is already claimed by the IPDB
        # actor; only the elevating ramps attach here.
        pk.entry(
            NGG97,
            note=(
                "The ramp entrances that elevate make the ramps moving "
                "ramps."
            ),
            cite=cite(
                IPDB_NGG,
                "Flippers (3), Pop bumpers (3), Slingshots (2), Ramps (3), "
                "Spinning targets (2), Spinning disc (1), Captive ball (1), "
                "Newton ball post (1), Left outlane kickback, Dual left "
                "inlanes. Entrances to ramps elevate to allow access to bash "
                "toy targets.",
            ),
            fields={"game_format": "pinball"},
            relationships={"gameplay_feature": ["moving-ramps"]},
        ),
        pk.entry(
            NGG97,
            cite=cite(
                IPDB_NGG,
                'Height: 76" (190cm) - backbox upright [...] Width: 28.75" '
                '(73cm) [...] Depth: 51.5" (127cm) [...] Weight: 300 lbs. '
                "(136kg) - uncrated",
            ),
            fields={"cabinet": "floor"},
        ),
        pk.entry(
            NGG97,
            note=(
                "The beaver identity of the two bash toys is recorded in the "
                "family notes as a future unique feature."
            ),
            cite=cite(IPDB_NGG, "Toys: Beaver bash toys (2)"),
            relationships={"gameplay_feature": [{"bash-toys": 2}]},
        ),
        pk.entry(
            NGG97,
            cite=cite(
                IPDB_NGG,
                "Voices of Jon Hey as Bud and Vince Pontarelli as Buzz.",
            ),
            credits=[("jon-hey", "voice"), ("vince-pontarelli", "voice")],
        ),
        # ── 1992: Black Rose (Bally) ────────────────────────────────────
        pk.entry(
            BR92,
            note=(
                "A machine produced in four figures was commercially "
                "produced; IPDB records the exact run as 3,746."
            ),
            cite=cite(IPDB_BR, "Production: 3746"),
            fields={"production_status": "produced"},
        ),
        # One changeset: format and the missing playfield hardware rest on
        # the same Notable Features line. The counted staples are already
        # claimed by the IPDB actor; the mechanically raised or lowered left
        # ramp attaches as a moving ramp, the Broadside VUK as a vertical
        # up-kicker, the center habitrail as a habitrail.
        pk.entry(
            BR92,
            cite=cite(
                IPDB_BR,
                "Flippers (3), Pop bumpers (3), Ramps (3), 3-bank standup "
                "targets (3), 2- or 3-ball Multiball. Left ramp is a "
                "mechanically raised or lowered ramp which is raised at "
                "certain times to load the ball cannon. [...] The Broadside "
                "VUK kicks the ball to the center habitrail above the "
                "playfield the and sends it to the flippers.",
            ),
            fields={"game_format": "pinball"},
            relationships={
                "gameplay_feature": [
                    "moving-ramps",
                    "vertical-up-kickers",
                    "habitrails",
                ]
            },
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description=(
            "Cardona family: the two pre-2026 conversion kits and their "
            "Williams/Bally donors"
        ),
        entries=entries,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
