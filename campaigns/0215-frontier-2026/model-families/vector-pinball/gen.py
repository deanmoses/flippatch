"""Emit patch 0234 — the Vector Pinball family: all five machines plus the maker.

See VectorPinball.md beside this file for the evidence inventory, the catalog
baseline, the traps and the user decisions this generator encodes (2026-08-13).

SCOPE IS THE WHOLE MAKER, five models:
  2024  Eight Ball Fury                              (exists, mostly bare)
  2024  Peter Brock KOTM — Torana / VK Commodore     (exist as 2025; year corrected here)
  2025  Holden Heritage                              (exists, bare)
  2026  Ned Kelly                                    (CREATED here)
  2025  Lost in Space                                (CREATED here, namesake of Sega 1998)

Plus the corporate entity's Brisbane location (australia/qld and
australia/qld/brisbane are CREATED here).

User decisions encoded (2026-08-13, VectorPinball.md → Decisions):
  variant structure stays as-is (both Brocks variant_of Holden Heritage)
  Peter Brock year corrected 2025 → 2024 (AUSRETROGAMER + maker About page)
  EBF "Pub Edition" not created (alternate-backglass trade dress)

Deliberately absent (each recorded in VectorPinball.md):
  per-model production_quantity on the Brocks   105 total across BOTH models; not splittable
  limited-edition tag on the Brocks             already set by 0206 — same-actor duplicate
                                                would be silently swallowed
  credits on Ned Kelly / Lost in Space          no source names anyone
  player_count everywhere                       no primary source states it (EBF has OPDB's 4)
  months everywhere                             OPDB's month=1 rows are an ingest artifact
  descriptions                                  a follow-up patch's job (inline-cite rules)
  lower rollover lanes / "Ball gate with Lift Control"   no confident vocab mapping

The maker publishes no PDFs; its "Game Rules, Features & Specs" pages are the
spec sheets, and every quote below is HTML-gated, lifted verbatim from the
web-cache extraction (typographic quotes and en dashes preserved).

Run: uv run python campaigns/0215-frontier-2026/model-families/vector-pinball/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0234-vector-pinball.yaml"

# ── Models ──────────────────────────────────────────────────────────────
EBF = "model.eight-ball-fury"
HH = "model.holden-heritage"
PB_TOR = "model.peter-brock-king-of-the-mountain-torana"
PB_VK = "model.peter-brock-king-of-the-mountain-vk-commodore"
NK = "model.ned-kelly"
LIS = "model.lost-in-space-vector-pinball"

# ── Sources (all cached in the pinexplore web cache 2026-08-13) ─────────
HOME = "https://vectorpinball.com/"
ABOUT = "https://vectorpinball.com/about"
CONTACT = "https://vectorpinball.com/contact"

EBF_SPECS = "https://vectorpinball.com/eight-ball-fury-specs"
EBF_GAL = "https://vectorpinball.com/eight-ball-fury"
EBF_RULES = "https://vectorpinball.com/eight-ball-fury-rules-features"

PB_MAIN = "https://vectorpinball.com/peter-brock-king-of-the-mountain-pinball-games"
PB_RULES = (
    "https://vectorpinball.com/peter-brock-king-of-the-mountain-game-rules-features-specs"
)

HH_MAIN = "https://vectorpinball.com/holden-pinball-games"
HH_RULES = "https://vectorpinball.com/holden-heritage-edition-game-rules"

NK_MAIN = "https://vectorpinball.com/ned-kelly"
NK_RULES = "https://vectorpinball.com/ned-kelly-pinball-game-rules-features-specs"

LIS_MAIN = "https://vectorpinball.com/lost-in-space"
LIS_RULES = (
    "https://vectorpinball.com/lost-in-space-the-pinball-game-rules-features-specs"
)

ARG = "https://ausretrogamer.com/peter-brock-king-of-the-mountain-pinball-machines"
TWIP = "https://twip.kineticist.com/p/funkatron-mix"
KIN_PBH = "https://www.kineticist.com/games/pinball/peter-brock-holden"
KIN_EBF = "https://www.kineticist.com/games/pinball/eight-ball-fury-2024"


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


# ── Shared notes ────────────────────────────────────────────────────────
CABINET_NOTE = (
    "Classified as a floor-standing cabinet from the full-size dimensions "
    "on the maker's spec sheet."
)
STATIC_NOTE = "The spec sheet's 'Static Targets' are stationary standup targets."
BALLSAVE_NOTE = (
    "A ball that drains within the owner-adjustable minimum play time is "
    "automatically returned to the player, which is a ball save."
)
TECHGEN_NOTE = (
    "Individually addressable RGB LED strings driven by field-upgradeable "
    "game software make this a computerized, solid-state game."
)
CREDITS_NOTE = (
    "The credits follow Kineticist's Design Team listing for this machine; "
    "the maker's own pages and videos carry no credit lines, and its "
    "gallery attributes the artwork only to an Australian designer."
)

# Kineticist Design Team blocks (definition-list layout — the [...] chain
# skips the colon rows so the spans survive whitespace normalization).
KIN_PBH_CREDITS = "Design [...] Jason McNally [...] Art [...] Peter Hughes, Jeremy Ham"
KIN_EBF_CREDITS = "Design [...] Jason McNally [...] Art [...] Jeremy Ham"

# The dimensions lines (GAME SPECS block on each rules page).
DIMS_210 = (
    "Dimensions (Setup) 140cm L (inc shooter) x 73cm W, 210cm H with Topper "
    "installed, 190cm High with no Topper fitted"
)
DIMS_204 = (
    "Dimensions (Setup) 140cm L (inc shooter) x 73cm W, 204cm H with Topper "
    "installed, 186cm High with no Topper fitted"
)

LED_GI = "100% LED Lighting throughout for long life, keeps game bright and inviting"
SHOOTER = "Standard Ball Shooter with Auto Shooter built in for use when required"
SHAKER = "Shaker Motor Included for extra effect"
SPEAKERS3 = "Quality 3 Speaker Sound system"
ART_BLADES = "Cabinet Inner art Blades around the playfield to help create a world under glass"
KNOCKER_CREDIT = (
    "End of Game lucky Number match, Old School Knocker built in to Alert "
    "Match Credit & Replays Awarded"
)
KNOCKER_PLAIN = (
    "End of Game lucky Number match, Old School Knocker built in to Alert "
    "Match & Replays Awarded"
)
LEDSTRINGS_139 = (
    "2 LED strings, Each RGB LED is individually addressable for incredible "
    "light shows, 57 LEDs Under the Playfield and 82 on Top, Total 139"
)
SW_UPGRADE = "Software is upgradeable as improvements and features are added"


def brock_holden_platform(
    model: str, rules: str, *, knocker: str, sheet_note: str = ""
) -> list[str]:
    """The shared Peter Brock / Holden Heritage playfield, cited to each
    model's own rules page (the two sheets carry identical hardware lines).

    sheet_note: prefixed to the hardware-counts note — the Peter Brock sheet
    covers both editions, and the note has to say so."""
    return [
        pk.entry(
            model,
            note=sheet_note or None,
            cite=cite(
                rules,
                "3 Flippers [...] 2 Sling Shots [...] 3 Pop Bumpers [...] "
                "1 Spinner [...] 1 Captive Car shot [...] 6 Static Targets",
            ),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            model,
            note=(sheet_note + " " if sheet_note else "")
            + STATIC_NOTE
            + " The Captive Car shot is a captive ball dressed as a race car.",
            cite=cite(
                rules,
                "3 Flippers [...] 2 Sling Shots [...] 3 Pop Bumpers [...] "
                "1 Spinner [...] 1 Captive Car shot [...] 6 Static Targets",
            ),
            relationships={
                "gameplay_feature": [
                    {"flippers": 3},
                    {"slingshots": 2},
                    {"pop-bumpers": 3},
                    {"spinners": 1},
                    {"captive-ball": 1},
                    {"standup-targets": 6},
                ]
            },
        ),
        pk.entry(
            model,
            cite=cite(rules, "6 Drop Targets"),
            relationships={"gameplay_feature": [{"drop-targets": 6}]},
        ),
        pk.entry(
            model,
            cite=cite(rules, "2,3 & 4 ball Multi Ball modes"),
            relationships={
                "gameplay_feature": [
                    "2-ball-multiball",
                    "3-ball-multiball",
                    "4-ball-multiball",
                ]
            },
        ),
        pk.entry(
            model,
            note="Five lettered upper rollover lanes with lane change.",
            cite=cite(
                rules,
                "Skill Shot, Extra Ball, Jackpot & Super Jackpot, Bonus Hold features",
            ),
            relationships={"gameplay_feature": ["skill-shot"]},
        ),
        pk.entry(
            model,
            note="One saucer lower on the playfield, one at the top.",
            cite=cite(
                rules,
                "Shoot the left saucer for 10,000 points [...] Shoot the top "
                "saucer to add a virtual ball",
            ),
            relationships={"gameplay_feature": [{"kick-out-saucers": 2}]},
        ),
        pk.entry(
            model,
            cite=cite(rules, "Enable the Kick Back feature and Extra ball when lit"),
            relationships={"gameplay_feature": ["kickback"]},
        ),
        pk.entry(
            model,
            note=BALLSAVE_NOTE,
            cite=cite(
                rules,
                "There is a Minimum play time (owner adjustable) from the "
                "first score on each ball, if the ball drains within that "
                "time it will be auto returned to you.",
            ),
            relationships={"gameplay_feature": ["ball-save"]},
        ),
        pk.entry(
            model,
            cite=cite(rules, SHOOTER),
            relationships={"gameplay_feature": ["plungers", "auto-launch"]},
        ),
        pk.entry(
            model,
            cite=cite(rules, ART_BLADES),
            relationships={"gameplay_feature": ["art-blades"]},
        ),
        pk.entry(
            model,
            cite=[
                cite(rules, "Topper included"),
                cite(rules, SHAKER),
                cite(rules, knocker),
            ],
            relationships={
                "gameplay_feature": ["toppers", "shaker-motors", "knockers"]
            },
        ),
        pk.entry(
            model,
            cite=[cite(rules, LED_GI), cite(rules, SPEAKERS3)],
            relationships={
                "gameplay_feature": ["led-general-illumination", {"speakers": 3}]
            },
        ),
        pk.entry(
            model,
            cite=cite(
                rules,
                "32 Digit Alpha/Numeric Score/Information display mounted "
                "close to playfield so we can maximize the backglass art and "
                "make it easy for you to keep your eye on the ball !",
            ),
            fields={"display_type": "alphanumeric"},
        ),
        pk.entry(
            model,
            note=TECHGEN_NOTE,
            cite=[cite(rules, LEDSTRINGS_139), cite(rules, SW_UPGRADE)],
            fields={"technology_generation": "solid-state"},
        ),
        pk.entry(
            model,
            note=CABINET_NOTE,
            cite=cite(rules, DIMS_210),
            fields={"cabinet": "floor"},
        ),
        pk.entry(
            model,
            note=CREDITS_NOTE,
            cite=cite(
                KIN_PBH, KIN_PBH_CREDITS, locator="in the Design Team section"
            ),
            credits=[
                ("jason-mcnally", "design"),
                ("peter-hughes", "art"),
                ("jeremy-ham", "art"),
            ],
        ),
    ]


def main() -> None:
    entries: list[str] = []

    # ── People credited on the Vector machines ──────────────────────────
    entries += [
        pk.entry("person.jason-mcnally", create=True, fields={"name": "Jason McNally"}),
        pk.entry("person.peter-hughes", create=True, fields={"name": "Peter Hughes"}),
        pk.entry("person.jeremy-ham", create=True, fields={"name": "Jeremy Ham"}),
    ]

    # ── Locations + the maker's corporate entity ────────────────────────
    entries += [
        pk.entry(
            "location.australia/qld",
            create=True,
            fields={
                "name": "Queensland",
                "slug": "qld",
                "parent": "australia",
                "location_type": "state",
            },
            note="Created to host Brisbane; Brisbane is Queensland's capital.",
        ),
        pk.entry(
            "location.australia/qld/brisbane",
            create=True,
            cite=cite(
                CONTACT,
                "We are based in Brisbane, Australia and ship to the world",
            ),
            fields={
                "name": "Brisbane",
                "slug": "brisbane",
                "parent": "australia/qld",
                "location_type": "city",
            },
        ),
        pk.entry(
            "corporate-entity.vector-pinball",
            note=(
                "The maker's own About and Contact pages give its identity "
                "and base: Vector Pinball is the pinball-manufacturing "
                "division of Vector Synergy Pty Ltd (ABN 82 660 426 344), "
                "Brisbane."
            ),
            cite=cite(
                ABOUT,
                "Vector Pinball is a division of Vector Synergy Pty Ltd ABN "
                "82 660 426 344. We are based in Brisbane, Australia.",
            ),
            relationships={"location": ["australia/qld/brisbane"]},
        ),
    ]

    # ── Eight Ball Fury (2024) ──────────────────────────────────────────
    # Baseline: display alphanumeric, tech-gen solid-state, player_count 4,
    # month 1 (OPDB artifact) already set — none re-asserted.
    entries += [
        pk.entry(
            EBF,
            note=(
                "The maker's About page states quantity production of this "
                "title, and the machine is on sale and operating on location."
            ),
            cite=[
                cite(
                    ABOUT,
                    "In 2023 we decided to move entirely over to new game "
                    "production and create our first original title, “Eight "
                    "Ball Fury” and produce these in quantity.",
                ),
                cite(
                    EBF_SPECS,
                    "Priced at $12,900 inc GST (Buyers outside Australia are "
                    "exempt from this 10% sales tax).",
                ),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            EBF,
            cite=cite(EBF_SPECS, "This limited-Edition Game (50 Units Only)"),
            fields={"production_quantity": 50},
            tags=["limited-edition"],
        ),
        pk.entry(
            EBF,
            cite=cite(
                EBF_RULES,
                "2 Flippers [...] 2 Sling Shots [...] 3 Pop Bumpers [...] "
                "Standard Pinball Tilt Bob Mech",
            ),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            EBF,
            note=CABINET_NOTE,
            cite=cite(EBF_RULES, DIMS_204),
            fields={"cabinet": "floor"},
        ),
        pk.entry(
            EBF,
            note=STATIC_NOTE,
            cite=cite(
                EBF_RULES,
                "2 Flippers [...] 2 Sling Shots [...] 3 Pop Bumpers [...] "
                "1 Spinner [...] 1 Captive Ball shot [...] 9 Static Targets",
            ),
            relationships={
                "gameplay_feature": [
                    {"flippers": 2},
                    {"slingshots": 2},
                    {"pop-bumpers": 3},
                    {"spinners": 1},
                    {"captive-ball": 1},
                    {"standup-targets": 9},
                ]
            },
        ),
        pk.entry(
            EBF,
            note=(
                "Six individual (solitary) drop targets, software-dropped, "
                "played in timed challenge modes."
            ),
            cite=[
                cite(EBF_RULES, "6 Individual Drop Targets, with Auto Drop feature"),
                cite(
                    EBF_RULES,
                    "you have 40 seconds to knock down all 6 drop targets",
                ),
            ],
            relationships={
                "gameplay_feature": [
                    {"solitary-drop-targets": 6},
                    "timed-drop-targets",
                ]
            },
        ),
        pk.entry(
            EBF,
            cite=cite(EBF_RULES, "2,3 & 4 ball Multi-Ball modes"),
            relationships={
                "gameplay_feature": [
                    "2-ball-multiball",
                    "3-ball-multiball",
                    "4-ball-multiball",
                ]
            },
        ),
        pk.entry(
            EBF,
            note="Five lettered upper rollover lanes with lane change.",
            cite=cite(
                EBF_RULES,
                "E I G H T upper lanes & B A L L Lower rollover lanes with "
                "lane change feature",
            ),
            relationships={"gameplay_feature": [{"top-lanes": 5}, "lane-change"]},
        ),
        pk.entry(
            EBF,
            cite=cite(
                EBF_RULES,
                "Skill Shot, Extra Ball, Jackpot & Super Jackpot, Bonus Hold features",
            ),
            relationships={"gameplay_feature": ["skill-shot"]},
        ),
        pk.entry(
            EBF,
            cite=cite(
                EBF_RULES,
                "Horseshoe shot in playfield centre (alternating shots to add "
                "to the challenge)",
            ),
            relationships={"gameplay_feature": ["horseshoe-lanes"]},
        ),
        pk.entry(
            EBF,
            note=BALLSAVE_NOTE,
            cite=cite(
                EBF_RULES,
                "Minimum play time is 10 seconds from the first score on each "
                "ball, if the ball drains within that time it will be auto "
                "returned to you.",
            ),
            relationships={"gameplay_feature": ["ball-save"]},
        ),
        pk.entry(
            EBF,
            cite=cite(
                EBF_RULES,
                "Standard Pinball Shooter with upgraded Chrome Rod. Auto "
                "Shooter built in for use when required",
            ),
            relationships={"gameplay_feature": ["plungers", "auto-launch"]},
        ),
        pk.entry(
            EBF,
            cite=cite(
                EBF_RULES,
                "Cabinet Inner Mirror Blades to spread the light and create "
                "an infinity effect around the playfield.",
            ),
            relationships={"gameplay_feature": ["mirror-blades"]},
        ),
        pk.entry(
            EBF,
            cite=[
                cite(
                    EBF_RULES,
                    "Eight Ball Fury, illuminated 3D Flame Topper included",
                ),
                cite(EBF_RULES, KNOCKER_PLAIN),
            ],
            relationships={"gameplay_feature": ["toppers", "knockers"]},
        ),
        pk.entry(
            EBF,
            cite=[cite(EBF_RULES, LED_GI), cite(EBF_RULES, SPEAKERS3)],
            relationships={
                "gameplay_feature": ["led-general-illumination", {"speakers": 3}]
            },
        ),
        pk.entry(
            EBF,
            note=CREDITS_NOTE,
            cite=cite(
                KIN_EBF, KIN_EBF_CREDITS, locator="in the Design Team section"
            ),
            credits=[("jason-mcnally", "design"), ("jeremy-ham", "art")],
        ),
    ]

    # ── Peter Brock KOTM — the year correction and per-model facts ──────
    YEAR_NOTE = (
        "Both Peter Brock models were on retail sale at the Australasian "
        "Gaming Expo in August 2024, and the maker's own About page dates "
        "its Australian Centric licensed titles to 2024, so the year is "
        "2024 rather than the 2025 recorded elsewhere."
    )
    ARG_AGE = (
        "Leaving a burnout at last week’s AGE – the Australasian Gaming Expo "
        "(August 13 to 15), was Vector Pinball’s Peter Brock “King Of The "
        "Mountain” pinball machines – which were the talk of the exhibition."
    )
    ARG_RETAIL = (
        "Both variations of the King Of The Mountain retail for AU$11,900 "
        "(GST inclusive)!"
    )
    ABOUT_2024 = (
        "2024 brought more new titles including some Australian Centric "
        "licensed ones."
    )
    PB_LICENCE = (
        "These pieces of playable art are limited to 105 builds total. They "
        "come with a build plate and certificate that confirms the build "
        "number and that we manufactured it under licence from Peter Brock "
        "& HDT."
    )
    PB_PRICED = (
        "Priced at $13,900 inc GST (Buyers outside Australia are exempt from "
        "this 10% sales tax)."
    )
    for model in (PB_TOR, PB_VK):
        entries += [
            pk.entry(
                model,
                note=YEAR_NOTE,
                cite=[
                    cite(ARG, ARG_AGE, locator="article dateline 20/08/2024"),
                    cite(ABOUT, ABOUT_2024),
                ],
                fields={"year": 2024},
            ),
            # The 105-build run is TOTAL ACROSS BOTH art packages, so no
            # per-model production_quantity is assertable; the limited-edition
            # tag is already set (0206) and a same-actor duplicate would be
            # silently swallowed — both recorded in VectorPinball.md.
            pk.entry(
                model,
                note=(
                    "Machines were retailing at the Australasian Gaming Expo "
                    "in August 2024 and both variations remain on sale from "
                    "the maker."
                ),
                cite=[
                    cite(PB_MAIN, PB_PRICED),
                    cite(ARG, ARG_RETAIL),
                ],
                fields={"production_status": "produced"},
            ),
            pk.entry(
                model,
                note=(
                    "The build plate confirming the build number is a "
                    "sequentially numbered plaque."
                ),
                cite=cite(PB_MAIN, PB_LICENCE),
                relationships={
                    "theme": ["licensed"],
                    "gameplay_feature": ["numbered-plaques"],
                },
            ),
            pk.entry(
                model,
                cite=cite(
                    PB_RULES,
                    "B R O C K upper lanes & K I N G Lower rollover lanes "
                    "with lane change feature",
                ),
                relationships={
                    "gameplay_feature": [{"top-lanes": 5}, "lane-change"]
                },
            ),
            pk.entry(
                model,
                cite=cite(
                    PB_RULES,
                    "Shooting the Mountain (Ramp) on right will light “Ramp” "
                    "for a period of time",
                ),
                relationships={"gameplay_feature": [{"ramps": 1}]},
            ),
        ]
        entries += brock_holden_platform(
            model,
            PB_RULES,
            knocker=KNOCKER_PLAIN,
            sheet_note=(
                "The maker publishes one Game Rules, Features & Specs sheet "
                "covering both Peter Brock editions."
            ),
        )

    # ── Holden Heritage (2025) ──────────────────────────────────────────
    entries += [
        pk.entry(
            HH,
            cite=cite(HH_MAIN, "Available Now!"),
            fields={"production_status": "produced"},
        ),
        pk.entry(
            HH,
            note=(
                "The Build Plate confirming the build number is a "
                "sequentially numbered plaque."
            ),
            cite=cite(
                HH_MAIN,
                "These pieces of playable art are limited to just 100 builds. "
                "They come with a Build Plate and certificate that confirms "
                "the build number and that we manufactured it under licence "
                "from GM Holden.",
            ),
            fields={"production_quantity": 100},
            tags=["limited-edition"],
            relationships={"gameplay_feature": ["numbered-plaques"]},
        ),
        pk.entry(
            HH,
            cite=cite(
                HH_RULES,
                "Achieve “M O T O R” upper lanes & “C A R S” Lower rollover "
                "lanes with lane change feature",
            ),
            relationships={"gameplay_feature": [{"top-lanes": 5}, "lane-change"]},
        ),
        pk.entry(
            HH,
            cite=cite(
                HH_RULES,
                "Shooting the “Hill Climb” Ramp on right will light “Ramp” "
                "for a period of time",
            ),
            relationships={"gameplay_feature": [{"ramps": 1}]},
        ),
    ]
    entries += brock_holden_platform(HH, HH_RULES, knocker=KNOCKER_CREDIT)

    # ── Ned Kelly (create) ──────────────────────────────────────────────
    # Year: first documented availability is 2026 (the page's earliest
    # Wayback capture is 2026-02-12 and it sells the game as available);
    # the maker's Game #4 numbering could put it in 2025, but no source
    # states a 2025 release — see VectorPinball.md.
    entries += [
        pk.entry(
            "title.ned-kelly",
            create=True,
            fields={"name": "Ned Kelly"},
        ),
        pk.entry(
            NK,
            create=True,
            fields={
                "name": "Ned Kelly",
                "title": "ned-kelly",
                "corporate_entity": "vector-pinball",
                "year": 2026,
            },
            relationships={"theme": ["historical-characters", "crime"]},
        ),
        pk.entry(
            NK,
            cite=cite(
                NK_MAIN,
                "This game is now available to purchase and is priced at "
                "$13,900 inc gst.",
            ),
            fields={"production_status": "produced"},
        ),
        pk.entry(
            NK,
            cite=cite(
                NK_MAIN,
                "NED KELLY “Very Limited Edition” Retro-Classic Style, "
                "Pinball Machine, the next in our Aussie Icon series (Only "
                "100 units will be made)",
            ),
            fields={"production_quantity": 100},
            tags=["limited-edition"],
        ),
        pk.entry(
            NK,
            cite=cite(
                NK_RULES,
                "2 Flippers [...] 2 Sling Shots [...] 4 Pop Bumpers [...] "
                "1 Spinner [...] 1 Captive Ball shot [...] 5 Static Targets",
            ),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            NK,
            note=STATIC_NOTE,
            cite=cite(
                NK_RULES,
                "2 Flippers [...] 2 Sling Shots [...] 4 Pop Bumpers [...] "
                "1 Spinner [...] 1 Captive Ball shot [...] 5 Static Targets",
            ),
            relationships={
                "gameplay_feature": [
                    {"flippers": 2},
                    {"slingshots": 2},
                    {"pop-bumpers": 4},
                    {"spinners": 1},
                    {"captive-ball": 1},
                    {"standup-targets": 5},
                ]
            },
        ),
        pk.entry(
            NK,
            cite=cite(NK_RULES, "6 Drop Targets"),
            relationships={"gameplay_feature": [{"drop-targets": 6}]},
        ),
        pk.entry(
            NK,
            cite=cite(NK_RULES, "2,3 & 4 ball Multi Ball modes"),
            relationships={
                "gameplay_feature": [
                    "2-ball-multiball",
                    "3-ball-multiball",
                    "4-ball-multiball",
                ]
            },
        ),
        pk.entry(
            NK,
            note="Five lettered upper rollover lanes with lane change.",
            cite=cite(
                NK_RULES,
                "Achieve “R E B E L” upper lanes & “G U N S” Lower rollover "
                "lanes with lane change feature",
            ),
            relationships={"gameplay_feature": [{"top-lanes": 5}, "lane-change"]},
        ),
        pk.entry(
            NK,
            cite=cite(
                NK_RULES,
                "Skill Shot, Extra Ball, Jackpot, Bonus Hold features",
            ),
            relationships={"gameplay_feature": ["skill-shot"]},
        ),
        pk.entry(
            NK,
            note="One saucer lower right on the playfield, one at the top.",
            cite=cite(
                NK_RULES,
                "Shoot the right lower saucer for 10,000 points [...] Shoot "
                "the top saucer to add a virtual ball",
            ),
            relationships={"gameplay_feature": [{"kick-out-saucers": 2}]},
        ),
        pk.entry(
            NK,
            cite=cite(
                NK_RULES,
                "This will enable the Kick Back feature and Extra ball (when lit)",
            ),
            relationships={"gameplay_feature": ["kickback"]},
        ),
        pk.entry(
            NK,
            note=BALLSAVE_NOTE,
            cite=cite(
                NK_RULES,
                "There is a minimum play time (owner adjustable) from the "
                "first score on each ball, if the ball drains within that "
                "time it will be automatically returned to you.",
            ),
            relationships={"gameplay_feature": ["ball-save"]},
        ),
        pk.entry(
            NK,
            note=(
                "The stock configuration ships a gun-grip shooter; a "
                "standard shooter is optional."
            ),
            cite=cite(
                NK_RULES,
                "Standard Ball Shooter with Auto Shooter built in for use "
                "when required (Gun Grip shooter is option at extra cost)",
            ),
            relationships={"gameplay_feature": ["plungers", "auto-launch"]},
        ),
        pk.entry(
            NK,
            cite=cite(NK_RULES, ART_BLADES),
            relationships={"gameplay_feature": ["art-blades"]},
        ),
        pk.entry(
            NK,
            cite=[
                cite(NK_RULES, "Plastic Topper included"),
                cite(NK_RULES, SHAKER),
                cite(NK_RULES, KNOCKER_CREDIT),
            ],
            relationships={
                "gameplay_feature": ["toppers", "shaker-motors", "knockers"]
            },
        ),
        pk.entry(
            NK,
            cite=[cite(NK_RULES, LED_GI), cite(NK_RULES, SPEAKERS3)],
            relationships={
                "gameplay_feature": ["led-general-illumination", {"speakers": 3}]
            },
        ),
        pk.entry(
            NK,
            cite=cite(
                NK_RULES,
                "32 Digit Alpha/Numeric Score/Information display mounted "
                "close to playfield so we can maximize the backglass art and "
                "make it easy for you to keep your eye on the ball !",
            ),
            fields={"display_type": "alphanumeric"},
        ),
        pk.entry(
            NK,
            note=TECHGEN_NOTE,
            cite=[cite(NK_RULES, LEDSTRINGS_139), cite(NK_RULES, SW_UPGRADE)],
            fields={"technology_generation": "solid-state"},
        ),
        pk.entry(
            NK,
            note=CABINET_NOTE,
            cite=cite(NK_RULES, DIMS_210),
            fields={"cabinet": "floor"},
        ),
    ]

    # ── Lost in Space (create; namesake of Sega's 1998 machine) ─────────
    LIS_LE = (
        "This fully licensed “Limited Edition” (Only 300 units for the "
        "world) game spans the 3 seasons of the show and is a real playable "
        "piece of art !"
    )
    entries += [
        pk.entry(
            LIS,
            create=True,
            note=(
                "A namesake of Sega's 1998 machine on the existing Lost In "
                "Space title — a different machine from a different maker, "
                "themed on the 1965 TV series rather than the 1998 film. "
                "Debuted at the Melbourne Pinball Expo, November 2025."
            ),
            cite=[
                cite(
                    TWIP,
                    "Australia’s upstart manufacturer Vector Pinball "
                    "announced an upcoming licensed title, based on the 1965 "
                    "classic sci-fi television series, Lost in Space.",
                ),
                cite(
                    TWIP,
                    "It’s based on all three seasons of the show and is set "
                    "to make its debut at the Melbourne Pinball Expo this "
                    "November.",
                ),
            ],
            fields={
                "name": "Lost in Space",
                "title": "lost-in-space",
                "corporate_entity": "vector-pinball",
                "year": 2025,
            },
            relationships={
                "theme": [
                    "licensed",
                    "outer-space",
                    "science-fiction",
                    "television-shows",
                ]
            },
        ),
        pk.entry(
            LIS,
            note=(
                "Debuted at the Melbourne Pinball Expo in November 2025; the "
                "maker's site now sells it as available and takes orders "
                "worldwide."
            ),
            cite=[
                cite(HOME, "LOST IN SPACE Is available now, ORDER YOURS !"),
                cite(LIS_MAIN, "We are now taking orders for customers worldwide."),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            LIS,
            cite=cite(LIS_MAIN, LIS_LE),
            fields={"production_quantity": 300},
            tags=["limited-edition"],
        ),
        pk.entry(
            LIS,
            cite=cite(
                LIS_RULES,
                "4 Flippers [...] 2 Sling Shots [...] 3 Pop Bumpers [...] "
                "Standard Pinball Tilt Bob Mech",
            ),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            LIS,
            note=STATIC_NOTE,
            cite=cite(
                LIS_RULES,
                "4 Flippers [...] 2 Sling Shots [...] 3 Pop Bumpers [...] "
                "3 Spinners [...] Dual Captive Ball shot [...] 14 Static Targets",
            ),
            relationships={
                "gameplay_feature": [
                    {"flippers": 4},
                    {"slingshots": 2},
                    {"pop-bumpers": 3},
                    {"spinners": 3},
                    {"captive-ball": 2},
                    {"standup-targets": 14},
                ]
            },
        ),
        pk.entry(
            LIS,
            note=(
                "One 3-bank plus three individual software-controlled "
                "('Smart') drop targets, played in 60-second timed modes."
            ),
            cite=[
                cite(LIS_RULES, "1 Triple + 3 Single “Smart” Drop Targets"),
                cite(
                    LIS_RULES,
                    "All 3 will pop up, Knock them down in any order as many "
                    "times as possible within 60 seconds",
                ),
            ],
            relationships={
                "gameplay_feature": [
                    "3-bank-drop-targets",
                    {"solitary-drop-targets": 3},
                    "timed-drop-targets",
                ]
            },
        ),
        pk.entry(
            LIS,
            cite=cite(LIS_RULES, "2,3 & 4 ball Multi Ball modes"),
            relationships={
                "gameplay_feature": [
                    "2-ball-multiball",
                    "3-ball-multiball",
                    "4-ball-multiball",
                ]
            },
        ),
        pk.entry(
            LIS,
            note="Four lettered top lanes; the lane change is dual-flipper.",
            cite=[
                cite(
                    LIS_RULES,
                    "L-O-S-T LANES [...] Completing top lanes boosts Pop "
                    "Bumper scoring",
                ),
                cite(LIS_RULES, "Dual Lane change feature"),
            ],
            relationships={"gameplay_feature": [{"top-lanes": 4}, "lane-change"]},
        ),
        pk.entry(
            LIS,
            cite=cite(
                LIS_RULES,
                "Skill Shot, Extra Ball, Jackpot, Bonus Hold features",
            ),
            relationships={"gameplay_feature": ["skill-shot"]},
        ),
        pk.entry(
            LIS,
            cite=cite(
                LIS_RULES,
                "Making orbit shots (4-left & 3-right) will light CHARIOT",
            ),
            relationships={"gameplay_feature": ["orbits"]},
        ),
        pk.entry(
            LIS,
            cite=cite(
                LIS_RULES,
                "Orbit into ramp shot then hit the flashing target",
            ),
            relationships={"gameplay_feature": ["ramps"]},
        ),
        pk.entry(
            LIS,
            note=BALLSAVE_NOTE,
            cite=cite(
                LIS_RULES,
                "Minimum play time – with auto Ball return feature (Owner Adjustable)",
            ),
            relationships={"gameplay_feature": ["ball-save"]},
        ),
        pk.entry(
            LIS,
            cite=cite(
                LIS_RULES,
                "Standard Ball Shooter with Auto Shooter built in for use when required",
            ),
            relationships={"gameplay_feature": ["plungers", "auto-launch"]},
        ),
        pk.entry(
            LIS,
            cite=cite(
                LIS_RULES,
                "Cabinet Inner art Blades around the playfield to help create "
                "a world under glass",
            ),
            relationships={"gameplay_feature": ["art-blades"]},
        ),
        pk.entry(
            LIS,
            cite=[
                cite(LIS_RULES, "3D Plastic, LED Animated lit, Topper included"),
                cite(LIS_RULES, SHAKER),
                cite(LIS_RULES, KNOCKER_CREDIT),
            ],
            relationships={
                "gameplay_feature": ["toppers", "shaker-motors", "knockers"]
            },
        ),
        pk.entry(
            LIS,
            cite=[
                cite(LIS_RULES, LED_GI),
                cite(
                    LIS_RULES,
                    "Quality 3 Speaker Sound system – 2 Mounted High in the "
                    "headbox for great effect",
                ),
            ],
            relationships={
                "gameplay_feature": ["led-general-illumination", {"speakers": 3}]
            },
        ),
        pk.entry(
            LIS,
            note=(
                "A video screen under the lower playfield showing clips from "
                "the licensed show — classified as a playfield LCD; the "
                "score display remains alphanumeric."
            ),
            cite=cite(
                LIS_RULES,
                "TV Feature Under the lower playfield, displays video "
                "snippets from the show relevant to the game play.",
            ),
            relationships={"gameplay_feature": ["playfield-lcds"]},
        ),
        pk.entry(
            LIS,
            cite=cite(
                LIS_MAIN,
                "We are lucky enough to have access to almost all the assets "
                "of the show including the music, voices, sound effects, "
                "video and are taking full advantage of that.",
            ),
            relationships={"gameplay_feature": ["speech"]},
        ),
        pk.entry(
            LIS,
            cite=cite(
                LIS_RULES,
                "32 Digit Alpha/Numeric Score/Information display mounted "
                "close to playfield so we can maximize the Backglass art and "
                "make it easy for you to keep your eye on the ball !",
            ),
            fields={"display_type": "alphanumeric"},
        ),
        pk.entry(
            LIS,
            note=TECHGEN_NOTE,
            cite=[
                cite(
                    LIS_RULES,
                    "2 LED strings, Each RGB LED is individually addressable "
                    "for incredible light shows, 55 LEDs Under the Playfield "
                    "and 84 on Top, Total 139",
                ),
                cite(
                    LIS_RULES,
                    "Backup Software is included and is upgradeable as "
                    "improvements and features are added",
                ),
            ],
            fields={"technology_generation": "solid-state"},
        ),
        pk.entry(
            LIS,
            note=CABINET_NOTE,
            cite=cite(LIS_RULES, DIMS_210),
            fields={"cabinet": "floor"},
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description=(
            "Vector Pinball: two new models and details across the maker's five machines"
        ),
        sources=[
            pk.source_root(
                "AUSRETROGAMER",
                description="Australian retro gaming and pinball news site.",
                links=[
                    ("https://ausretrogamer.com/", "AUSRETROGAMER", "homepage"),
                ],
            ),
        ],
        entries=entries,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
