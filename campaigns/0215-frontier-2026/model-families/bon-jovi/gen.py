"""Emit patch 0224 — Bon Jovi (Barrels of Fun, 2026).

See ../../README.md for the family split and BonJovi.md beside this file for
the evidence inventory, the catalog baseline, the traps and the decisions this
generator encodes (2026-08-10).

SCOPE IS ONE MODEL: model.bon-jovi. Single edition, no variants, no older
siblings — BoF's other machines are separate Titles, out of scope.

Only missing facts are asserted; 0215 already set name/year/maker/title/themes.
Deliberately absent (each recorded in BonJovi.md → Not asserted):
  month, player_count, system, technology_generation, cabinet, multiball,
  EverGloss decal art, description, standup-target count.

EVIDENCE SHAPE (BonJovi.md → Traps): the maker's own reveal post carries the
credits and the 700-unit paragraph but NOT the spec blocks; those live in
Pinball News's verbatim press-release reprint (gated HTML) and on the flyer
(no text layer — quotes transcribed off the rendered sheets, 2026-08-10).

USER DECISIONS (2026-08-10): production_quantity 700 with the maker's own
final-number-TBA caveat in the note; production_status produced on the user's
criterion (for sale now = produced); patch number 0224. Person-name spelling
conflicts (van Es / Dillmann) are aliased additively, renames pending user.

Run: uv run python campaigns/0215-frontier-2026/model-families/bon-jovi/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0224-bon-jovi.yaml"

MODEL = "model.bon-jovi"

# ── Sources ─────────────────────────────────────────────────────────────
POST = (
    "https://www.barrelsoffun.com/2026/07/28/"
    "bon-jovi-pinball-is-ready-to-rock-build-the-setlist-and-play-it-loud"
)
PN = "https://www.pinballnews.com/site/2026/07/28/bon-jovi-revealed"
FLYER = "https://www.barrelsoffun.com/wp-content/uploads/2026/07/BJ-Flyer.pdf"

FLYER_P2 = "PDF document page 2 of 2; the flyer carries no printed folios"
PN_REPRINT = (
    "in the press release reprinted verbatim in the article "
    "(the maker's own words)"
)


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


def vocab(
    slug: str,
    name: str,
    *,
    parents: list[str] | None = None,
    aliases: list[str] | None = None,
) -> str:
    rel: dict[str, list[str]] = {}
    if parents:
        rel["gameplay_feature_parent"] = parents
    if aliases:
        rel["gameplay_feature_alias"] = aliases
    return pk.entry(
        f"gameplay-feature.{slug}",
        create=True,
        fields={"name": name},
        relationships=rel or None,
    )


# ── Maker reveal post quotes (gated HTML) ───────────────────────────────
POST_PINBALL = (
    "Bon Jovi Pinball brings the sound, lights, videos, concerts, and energy "
    "of one of the world's most enduring arena rock bands into a limited "
    "worldwide pinball experience."
)
POST_700 = (
    "A limited worldwide release of 700 games, plus possible Barrels Reserve "
    "member access. If the initial release sells out within the first 7 days, "
    "eligible Barrels Reserve direct customers will receive an additional "
    "7-day ordering window. After all orders are received, Barrels of Fun "
    "will announce the final edition number."
)
POST_ORDER = "Order Bon Jovi Pinball from Barrels of Fun!"

# ── Pinball News press-release-reprint quotes (gated HTML) ──────────────
PN_IN_PRODUCTION = (
    "Bon Jovi Pinball is currently in production and being manufactured by "
    "Barrels of Fun LLC., a luxury pinball manufacturing company based in "
    "Houston, TX."
)
PN_ON_SALE = (
    "The game is available for purchase now at www.barrelsoffun.com and all "
    "authorized distributor."
)
PN_GAME_FEATURES = (
    "2 Lightning Flippers, 2 Mini Flippers, 6 Balls [...] 2 Plastic Ramps, "
    "2 Metal Jump Ramps, 1 Metal Ramp, [...] 4 Chrome Wire Habitrails, "
    "1 Subway, 2 Scoops, [...] 1 Vertical Upkick, 3 Magnets, 2 Spinners, "
    "2 Diverters, [...] 2 Drop Targets, 2 Physical 3-Ball Locks, "
    "1 Captive Ball"
)
PN_ATTRACTIONS = (
    "Bon Jovi Heart & Dagger Magnetic Ball Catch & Diverter: Take a \"Shot "
    "Through the Heart\" with this versatile 3-level diverter & jump ramp "
    "that sends the ball along one of three unique paths! [...] Steel Horse "
    "3-Ball Lock: Buck up, Cowboy! A hidden magnet along the back orbit can "
    "divert the ball into a vertical upkick that feeds a physical 3-ball "
    "lock [...] Crowd Amp-Up Loop Captive Ball & Spinner: This first-ever "
    "loop-de-loop captive ball with a spinner inside is designed to pump up "
    "the crowd! [...] Backstage Access: Your pass to a variety of shots "
    "featuring 3 standup targets, a spinner, an exit ramp, hidden scoop, & "
    "magnet catch that diverts the ball to a physical 3-ball lock"
)
PN_SCULPTS = (
    "High-Fidelity Sculpts: Bon Jovi Heart & Dagger and Jon's Iconic New "
    "Jersey Guitar"
)
PN_LIGHTING = (
    "Spotlights & Trusses: Custom metal trussing along the left and back "
    "of the stage includes 3 functional spotlights [...] Horizon "
    "Atmospheric Lighting (HAL): An RGBW LED Low-Profile Inner Cabinet "
    "Lighting System for Complete Concert Experience Lighting Effects "
    "[...] All-RGBW LED Playfield Insert Lamps & General Illumination "
    "Lamps, and Playfield Apron Flood Lights"
)
PN_COSMETICS = (
    "EverGloss High-Gloss Decal Art [...] Infinity Glass (Anti-Reflective "
    "Glass) [...] Thunder From Down Under Shaker Motor [...] "
    "Factory-Installed Inner Blade Art [...] Polyester Metallic Powder "
    "Coated Cabinet Armor"
)
PN_DISPLAY = "15.6\" HD LCD Display flanked by 5-1/4\""
PN_AUDIO = (
    "Full-Range Stereo Speakers with Interactive [...] Full RGBW "
    "Illumination [...] 8\" Cabinet Subwoofer"
)

# ── Flyer transcriptions (no text layer; read off the rendered sheets) ──
FLYER_GAME_FEATURES = (
    "2 Lightning Flippers, 2 Mini Flippers, 6 Balls [...] 2 Plastic Ramps, "
    "2 Metal Jump Ramps, 1 Metal Ramp, 4 Chrome Wire Habitrails, 1 Subway, "
    "2 Scoops, 1 Vertical Upkick, 3 Magnets, 2 Spinners, 2 Diverters, "
    "2 Drop Targets, 2 Physical 3-Ball Locks, 1 Captive Ball"
)
FLYER_DISPLAY = (
    "15.6\" HD LCD Display flanked by 5-1/4\" Full-Range Stereo Speakers "
    "with Interactive Full RGBW Illumination"
)
FLYER_ART = "Featuring Amped Up Original Art by Jonathan Bergeron"

# ── Credit-block quotes (maker reveal post) ─────────────────────────────
CR_DESIGN = "Game Design: David van Es"
CR_RULES = "Rules: Phil Grimaldi Jess DeNardo"
CR_CODING = "Coding: Eric Priepke"
CR_SOUND = "Sound Design: Jeff Dodson"
CR_ART = "Artwork: Jonathan Bergeron"
CR_ANIM = "Animations: Joshua Clay Trent Armstrong"
CR_MECH = "Mechanical Engineering: Luke Underwood Paul Sulisz"
CR_ELEC = "Electrical Engineering: Parker Dillmann"

OTHER_ROLE_NOTE = (
    "has no dedicated role in the closed credit-role vocabulary, so the "
    "credit maps to the other role; the maker's block label is recorded here."
)


def main() -> None:
    entries = [
        # ── Vocabulary (parents exist; all generic or branded-child) ────
        vocab(
            "lightning-flippers",
            "Lightning Flippers",
            parents=["flippers"],
            aliases=["Lightning Flipper"],
        ),
        vocab(
            "mini-flippers",
            "Mini Flippers",
            parents=["flippers"],
            aliases=["Mini Flipper", "Mini-Flipper"],
        ),
        vocab(
            "jump-ramps",
            "Jump Ramps",
            parents=["ramps"],
            aliases=["Jump Ramp"],
        ),
        # BoF's branded anti-reflective glass — the InvisiGlass / Magic
        # Glass pattern: a branded child of the generic, created by the
        # family patch that attaches it.
        vocab(
            "infinity-glass",
            "Infinity Glass",
            parents=["anti-reflection-playfield-glass"],
        ),
        # BoF's branded interactive inner-cabinet lighting product — a maker
        # product leaf under the 0220 interactive-lighting DAG's location
        # node (the AURA shape: one product, no separate brand-family node).
        vocab(
            "horizon-atmospheric-lighting",
            "Horizon Atmospheric Lighting",
            parents=["interactive-cabinet-lighting"],
            aliases=["HAL", "Horizon Atmospheric Lighting (HAL)"],
        ),
        # ── People: the six new to the catalog ──────────────────────────
        pk.entry(
            "person.phil-grimaldi",
            create=True,
            cite=cite(POST, CR_RULES),
            fields={"name": "Phil Grimaldi"},
        ),
        pk.entry(
            "person.jess-denardo",
            create=True,
            cite=cite(POST, CR_RULES),
            fields={"name": "Jess DeNardo"},
        ),
        pk.entry(
            "person.jeff-dodson",
            create=True,
            cite=cite(POST, CR_SOUND),
            fields={"name": "Jeff Dodson"},
        ),
        pk.entry(
            "person.trent-armstrong",
            create=True,
            cite=cite(POST, CR_ANIM),
            fields={"name": "Trent Armstrong"},
        ),
        pk.entry(
            "person.luke-underwood",
            create=True,
            cite=cite(POST, CR_MECH),
            fields={"name": "Luke Underwood"},
        ),
        pk.entry(
            "person.paul-sulisz",
            create=True,
            cite=cite(POST, CR_MECH),
            fields={"name": "Paul Sulisz"},
        ),
        # ── People: maker-spelling corrections on existing people ───────
        # The maker writes "David van Es" and "Parker Dillmann" where the
        # existing people carried Pinside-era "David Van Es" / "Parker
        # Dillman". Per the GTF spelling ruling the maker's form is
        # canonical (user-approved rename, 2026-08-10) and the losing form
        # stays as an alias. Josh Clay keeps his short-form name — "Joshua"
        # is the maker's long form, aliased, not a spelling conflict.
        pk.entry(
            "person.david-van-es",
            note=(
                "The maker credits him as 'David van Es' (lowercase v, the "
                "Dutch convention); Pinside spells it 'David Van Es', kept "
                "as an alias so both forms resolve."
            ),
            cite=cite(POST, CR_DESIGN),
            fields={"name": "David van Es"},
            relationships={"person_alias": ["David Van Es"]},
        ),
        pk.entry(
            "person.josh-clay",
            cite=cite(POST, CR_ANIM),
            relationships={"person_alias": ["Joshua Clay"]},
        ),
        pk.entry(
            "person.parker-dillman",
            note=(
                "The maker credits him as 'Parker Dillmann' (two n's); "
                "Pinside spells it 'Parker Dillman', kept as an alias so "
                "both forms resolve."
            ),
            cite=cite(POST, CR_ELEC),
            fields={"name": "Parker Dillmann"},
            relationships={"person_alias": ["Parker Dillman"]},
        ),
        # ── Production ──────────────────────────────────────────────────
        pk.entry(
            MODEL,
            note=(
                "The maker states the game is in production and on sale now "
                "(its own post's order call-to-action, and the press "
                "release's purchase sentence), so the machine is produced "
                "rather than merely announced."
            ),
            cite=[
                cite(POST, POST_ORDER),
                cite(PN, PN_IN_PRODUCTION, locator=PN_REPRINT),
                cite(PN, PN_ON_SALE, locator=PN_REPRINT),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            MODEL,
            note=(
                "700 is the announced size of the limited worldwide release; "
                "the maker reserves a possible Barrels Reserve member overrun "
                "and will announce the final edition number after ordering "
                "closes, so this figure is the announced floor, not a final "
                "census."
            ),
            cite=cite(POST, POST_700),
            fields={"production_quantity": 700},
            tags=["limited-edition"],
        ),
        pk.entry(
            MODEL,
            cite=cite(POST, POST_PINBALL),
            fields={"game_format": "pinball"},
        ),
        # ── Display ─────────────────────────────────────────────────────
        pk.entry(
            MODEL,
            note=(
                "The press-release reprint's line breaks split the display "
                "sentence; the flyer carries it unbroken (transcribed off "
                "the rendered sheet — the flyer has no text layer)."
            ),
            cite=[
                cite(PN, PN_DISPLAY, locator=PN_REPRINT),
                cite(FLYER, FLYER_DISPLAY, locator=FLYER_P2),
            ],
            fields={"display_type": "lcd"},
        ),
        # ── Credits (the maker post's credit block, role by role) ───────
        pk.entry(
            MODEL,
            cite=cite(POST, CR_DESIGN),
            credits=[("david-van-es", "design")],
        ),
        pk.entry(
            MODEL,
            note="'Rules' " + OTHER_ROLE_NOTE,
            cite=cite(POST, CR_RULES),
            credits=[("phil-grimaldi", "other"), ("jess-denardo", "other")],
        ),
        pk.entry(
            MODEL,
            note="The maker's block label for the software credit is 'Coding'.",
            cite=cite(POST, CR_CODING),
            credits=[("eric-priepke", "software")],
        ),
        pk.entry(
            MODEL,
            note="The maker's block label for the sound credit is 'Sound Design'.",
            cite=cite(POST, CR_SOUND),
            credits=[("jeff-dodson", "sound")],
        ),
        pk.entry(
            MODEL,
            cite=[
                cite(POST, CR_ART),
                cite(FLYER, FLYER_ART, locator=FLYER_P2),
            ],
            credits=[("jonathan-bergeron", "art")],
        ),
        pk.entry(
            MODEL,
            note=(
                "The maker writes 'Joshua Clay'; his earlier credits use "
                "'Josh Clay'. Both forms resolve to the same person via "
                "alias."
            ),
            cite=cite(POST, CR_ANIM),
            credits=[("josh-clay", "animation"), ("trent-armstrong", "animation")],
        ),
        pk.entry(
            MODEL,
            note="The maker's block label for the mechanics credits is 'Mechanical Engineering'.",
            cite=cite(POST, CR_MECH),
            credits=[("luke-underwood", "mechanics"), ("paul-sulisz", "mechanics")],
        ),
        pk.entry(
            MODEL,
            note="'Electrical Engineering' " + OTHER_ROLE_NOTE,
            cite=cite(POST, CR_ELEC),
            credits=[("parker-dillman", "other")],
        ),
        # ── Gameplay features: the Game Features counts block ───────────
        pk.entry(
            MODEL,
            note=(
                "Counts follow the Game Features block. Ramps attach "
                "count-less: 2 plastic ramps, 1 metal ramp and 2 metal jump "
                "ramps make any single ramps count ambiguous, so only the "
                "jump-ramp subtype carries its own count. The two Physical "
                "3-Ball Locks attach as ball-locks with count 2."
            ),
            cite=[
                cite(PN, PN_GAME_FEATURES, locator=PN_REPRINT),
                cite(FLYER, FLYER_GAME_FEATURES, locator=FLYER_P2),
            ],
            relationships={
                "gameplay_feature": [
                    {"lightning-flippers": 2},
                    {"mini-flippers": 2},
                    {"balls": 6},
                    "ramps",
                    {"jump-ramps": 2},
                    {"habitrails": 4},
                    {"subways": 1},
                    {"scoops": 2},
                    {"vertical-up-kickers": 1},
                    {"magnets": 3},
                    {"spinners": 2},
                    {"diverters": 2},
                    {"drop-targets": 2},
                    {"ball-locks": 2},
                    {"captive-ball": 1},
                ]
            },
        ),
        # ── Gameplay features: the Game Attractions mechanisms ──────────
        pk.entry(
            MODEL,
            note=(
                "Classifications: the Steel Horse's hidden magnet that "
                "diverts the ball is a diverter magnet; Backstage's magnet "
                "catch is a stop magnet; the Crowd Amp-Up Loop's captive "
                "ball with a spinner inside is exactly a captive ball "
                "spinner. Standup targets attach "
                "count-less: the 3 stated are scoped to the Backstage "
                "block and the machine total is unstated."
            ),
            cite=cite(PN, PN_ATTRACTIONS, locator=PN_REPRINT),
            relationships={
                "gameplay_feature": [
                    "diverter-magnets",
                    "stop-magnets",
                    "captive-ball-spinners",
                    "standup-targets",
                ]
            },
        ),
        # ── Toys ────────────────────────────────────────────────────────
        pk.entry(
            MODEL,
            note=(
                "Toy classifications: the Heart & Dagger sculpt catches and "
                "holds the ball (magnetic ball catch), so it is a "
                "ball-holding toy; Jon's New Jersey Guitar sculpt states no "
                "motion or ball interaction, so it is a static toy."
            ),
            cite=[
                cite(PN, PN_SCULPTS, locator=PN_REPRINT),
                cite(
                    PN,
                    "Bon Jovi Heart & Dagger Magnetic Ball Catch & Diverter",
                    locator=PN_REPRINT,
                ),
            ],
            relationships={
                "gameplay_feature": ["ball-holding-toys", "static-toys"]
            },
        ),
        # ── Presentation: lighting ──────────────────────────────────────
        pk.entry(
            MODEL,
            note=(
                "HAL is the maker's branded interactive inner-cabinet "
                "lighting product (its own name for the system), attached "
                "as the branded leaf under interactive-cabinet-lighting."
            ),
            cite=cite(PN, PN_LIGHTING, locator=PN_REPRINT),
            relationships={
                "gameplay_feature": [
                    "horizon-atmospheric-lighting",
                    "led-general-illumination",
                    {"stage-spotlights": 3},
                ]
            },
        ),
        # ── Presentation: glass, armor, blades, shaker ──────────────────
        pk.entry(
            MODEL,
            note=(
                "Infinity Glass is the maker's branded anti-reflective "
                "playfield glass; 'Thunder From Down Under' is its branding "
                "for the shaker motor (recorded as a shaker motor; the "
                "branding is preserved in this quote). The press release's "
                "armor sentence continues beyond the quoted span; the "
                "cabinet armor itself is what the span establishes."
            ),
            cite=cite(PN, PN_COSMETICS, locator=PN_REPRINT),
            relationships={
                "gameplay_feature": [
                    "infinity-glass",
                    "cabinet-armor",
                    "art-blades",
                    "shaker-motors",
                ]
            },
        ),
        # ── Audio ───────────────────────────────────────────────────────
        pk.entry(
            MODEL,
            note=(
                "The reprint's line breaks split the speaker sentence into "
                "three fragments; the flyer carries it unbroken. The "
                "speakers' Interactive Full RGBW Illumination is recorded "
                "as interactive speaker lighting — the maker gives this "
                "one no product brand."
            ),
            cite=[
                cite(PN, PN_AUDIO, locator=PN_REPRINT),
                cite(FLYER, FLYER_DISPLAY, locator=FLYER_P2),
            ],
            relationships={
                "gameplay_feature": [
                    "stereo-sound",
                    "subwoofers",
                    "interactive-speaker-lighting",
                ]
            },
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="Bon Jovi (Barrels of Fun 2026): production, credits, features",
        entries=entries,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
