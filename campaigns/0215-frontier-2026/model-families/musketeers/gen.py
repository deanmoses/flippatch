"""Emit patch 0229 — The 3 Musketeers family (HEXA Pinball, 2026).

See ../../README.md for the family split and 3Musketeers.md beside this file
for the evidence inventory, the decisions this generator encodes, the close
calls and the sought-and-not-found record (2026-08-12).

SCOPE: two models, no older siblings —
  the-3-musketeers                    the maker's Classic Edition (renamed here, user-approved)
  the-3-musketeers-elegance-edition   200-unit numbered limited edition

Only missing facts are asserted (0215 set name/title/corporate_entity/year/
themes). Deliberately absent (each recorded in 3Musketeers.md):
  display_type / player_count / system / technology_generation   Pinside-only or unstated
  physical dimensions and weight                                 no catalog fields exist
  team credit "Hexa Pinball Engineering"                         user ruling: skipped
  pause mode / Plungr ranking / accessibility vocabulary         close calls: not created
  ~800 total production target                                   a target, not a cap

CITE STRATEGY (user ruling 2026-08-12): HEXA's product specification sheet
exists only as images reproduced in Pinball News's reveal article; the two
sheets are web-cited at their pinballnews.com URLs with hand transcriptions
filed in the cache (text_source=manual), locators naming them as HEXA's
document. The maker's own product pages are cited directly. Non-English
evidence would be quoted verbatim with a brief English gloss in the note; in
the end every asserted fact's richest carrier was English, so no French quote
appears.

The spec sheet is edition-neutral: the maker's own comparison table differs
only in cosmetic items and Kineticist states gameplay is identical across
editions, so playfield/experience features assert on both models, cited to
the same sheet.

Run: uv run python campaigns/0215-frontier-2026/model-families/musketeers/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0229-musketeers.yaml"

# ── Models ──────────────────────────────────────────────────────────────
BASE = "model.the-3-musketeers"
ELEG = "model.the-3-musketeers-elegance-edition"

# ── Sources ─────────────────────────────────────────────────────────────
PRODUCT_EN = "https://www.hexa-pinball.com/en/produit/the-3-musketeers"
PN_ARTICLE = "https://www.pinballnews.com/site/2026/03/20/the-3-musketeers-revealed"
SPEC_FRONT = (
    "https://www.pinballnews.com/site/wp-content/uploads/games/"
    "three-musketeers/024--three-musketeers.jpg"
)
SPEC_BACK = (
    "https://www.pinballnews.com/site/wp-content/uploads/games/"
    "three-musketeers/025--three-musketeers.jpg"
)
KINETICIST = "https://www.kineticist.com/news/hexa-3-musketeers-pinball"

SPEC_FRONT_LOC = (
    "front sheet of HEXA's product specification sheet, reproduced as an "
    "image in Pinball News's reveal article"
)
SPEC_BACK_LOC = (
    "back sheet of HEXA's product specification sheet, reproduced as an "
    "image in Pinball News's reveal article"
)


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


def spec_front(quote: str, section: str) -> dict[str, str]:
    return cite(SPEC_FRONT, quote, locator=f"{SPEC_FRONT_LOC}; {section}")


def spec_back(quote: str, section: str) -> dict[str, str]:
    return cite(SPEC_BACK, quote, locator=f"{SPEC_BACK_LOC}; {section}")


# ── Shared quotes ───────────────────────────────────────────────────────
KIN_TIMELINE = (
    "HEXA says first shipments are expected within three months, roughly June 2026."
)
KIN_IDENTICAL = (
    "Gameplay is identical across editions — the Elegance is a cosmetic and "
    "tactile upgrade, not a mechanical one."
)
PRODUCT_PINBALL = (
    "this pinball machine plunges you into the adventure of d'Artagnan, an "
    "ambitious young Gascon who dreams of joining the prestigious Musketeers "
    "in the service of King Louis XIII of France"
)
PN_DATELINE = "Date: March 20th, 2026"
PN_ART_MUSIC = (
    "Artwork is by Tristan Fallon, while the music comes from Hervé Coussillan."
)
SPEC_COUNTS = (
    "3 Bank Drop Target, Ramp, Diverter, Hidden Mini-Ball Shot [...] "
    "3 Balls Lock La Rochelle Harbor [...] 3 Ramps: [...] "
    "VUK Treville's Mansion Roof [...] "
    "Captive Ball of the Queen's Diamonds Studs [...] "
    "1 Spinner [...] 2 Flippers [...] 7 Balls + 1 Mini-Ball"
)
SPEC_DIVERTERS = (
    "Canon platform Diverter [...] Treville's Mansion courtyard Hidden "
    "Diverter [...] Notre Dame's Forest Hidden Diverter [...] "
    "Back board Diverter"
)
SPEC_SOUND = (
    "Speakers and Subwoofer by Pinsound [...] 2.1 Sound System with 48V amplifier"
)
SPEC_ATMOSLIGHT = (
    "Atmoslight Surrounding Sytem [...] with pattented Atmoslight Inserts "
    "[...] 400+ RGB LEDs"
)
KIN_ATMOSLIGHT = (
    "The AtmosLight inserts, resin pieces bonded to the wood with epoxy, are "
    "integrated directly into the playing surface."
)
EDITION_NEUTRAL_NOTE = (
    "The specification sheet is edition-neutral and the maker's own "
    "comparison table differs only in cosmetic items, so the playfield "
    "features are facts about both editions."
)
CREDIT_SOUGHT_NOTE = (
    "Kineticist's Design Team block is the only non-crowdsourced source "
    "naming this credit; corroborating first-party sources were sought at "
    "authoring time and none found (the maker's specification sheet credits "
    "only art, soundtracks and engineering, and no manual exists yet)."
)


def shared_entries(model: str) -> list[str]:
    """The entries both editions get, resting on edition-neutral evidence."""
    return [
        pk.entry(
            model,
            note=(
                "Announced per the vocabulary (officially revealed but not "
                "yet shipped) as of authoring, 2026-08-12: the newest "
                "timeline statement has first shipments merely expected, and "
                "no shipping-began statement was found."
            ),
            cite=[
                cite(PN_ARTICLE, "Hexa Pinball today released full details of their second title, The 3 Musketeers, based on the famed novel by Alexandre Dumas."),
                cite(KINETICIST, KIN_TIMELINE),
            ],
            fields={"production_status": "announced"},
        ),
        pk.entry(
            model,
            cite=cite(PRODUCT_EN, PRODUCT_PINBALL),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            model,
            note=(
                "Month records the announcement month (campaign convention, "
                "GTF Victory precedent): both editions were revealed "
                "March 20, 2026, in HEXA's dual Bordeaux / Texas Pinball "
                "Festival launch."
            ),
            cite=cite(PN_ARTICLE, PN_DATELINE),
            fields={"month": 3},
        ),
        pk.entry(
            model,
            cite=[
                spec_front("Exclusive Art by Tristan Fallon", "beside the machine photo"),
                cite(PN_ARTICLE, PN_ART_MUSIC),
            ],
            credits=[("tristan-fallon", "art")],
        ),
        pk.entry(
            model,
            note=(
                "The maker's own label is 'Exclusive Soundtracks by'; the "
                "music role follows."
            ),
            cite=[
                spec_front("Exclusive Soundtracks by Hervé Coussillan", "beside the machine photo"),
                cite(PN_ARTICLE, PN_ART_MUSIC),
            ],
            credits=[("herve-coussillan", "music")],
        ),
        pk.entry(
            model,
            note=(
                "Kineticist's Design Team block labels him 'Music / Sound'; "
                "the sound role follows in addition to the music credit the "
                "maker's sheet supports."
            ),
            cite=cite(KINETICIST, "Music / Sound: Hervé Coussillan"),
            credits=[("herve-coussillan", "sound")],
        ),
        pk.entry(
            model,
            note=CREDIT_SOUGHT_NOTE,
            cite=cite(KINETICIST, "Game Design: Luis Dos Santos"),
            credits=[("luis-dos-santos", "design")],
        ),
        pk.entry(
            model,
            note=(
                "'Electronic Engineering' has no dedicated role in the "
                "closed credit-role vocabulary, so the credit maps to the "
                "other role; the block label is recorded here. "
                + CREDIT_SOUGHT_NOTE
            ),
            cite=cite(KINETICIST, "Electronic Engineering: Romain Fontaine"),
            credits=[("romain-fontaine", "other")],
        ),
        pk.entry(
            model,
            note=(
                "Counts follow the sheet's PLAYFIELD FEATURES list. "
                "Balls attach as 7 with the extra mini-ball preserved in the "
                "quote (no mini-ball vocabulary; 3Musketeers.md keeps it on "
                "the future-unique-features list). Treville's Mansion's '3 "
                "Bank Drop Target' attaches as one 3-bank; the single "
                "three-ball La Rochelle Harbor lock attaches as ball-locks "
                "with count 1 (the Bon Jovi shape). Ramps attach as the "
                "sheet's own count of 3. " + EDITION_NEUTRAL_NOTE
            ),
            cite=[
                spec_back(SPEC_COUNTS, "in the PLAYFIELD FEATURES list"),
                cite(KINETICIST, KIN_IDENTICAL),
            ],
            relationships={
                "gameplay_feature": [
                    {"flippers": 2},
                    {"balls": 7},
                    {"spinners": 1},
                    {"ramps": 3},
                    {"3-bank-drop-targets": 1},
                    {"ball-locks": 1},
                    {"vertical-up-kickers": 1},
                    {"captive-ball": 1},
                ]
            },
        ),
        pk.entry(
            model,
            note=(
                "Four diverter rows on the sheet: the cannon platform, the "
                "mansion courtyard (hidden), Notre Dame's Forest (hidden) "
                "and the back board. " + EDITION_NEUTRAL_NOTE
            ),
            cite=spec_back(SPEC_DIVERTERS, "in the PLAYFIELD FEATURES list"),
            relationships={"gameplay_feature": [{"diverters": 4}]},
        ),
        pk.entry(
            model,
            note="The Milady de Winter sculpt is a repeatable bash target under the center ramp.",
            cite=[
                spec_back("Bash Toy Milady de Winter", "in the PLAYFIELD FEATURES list"),
                cite(
                    PN_ARTICLE,
                    "Both appear on the playfield with the latter represented by a bash toy under a lift ramp.",
                ),
            ],
            relationships={"gameplay_feature": [{"bash-toys": 1}]},
        ),
        pk.entry(
            model,
            note="A swinging ship of the English fleet, timed shots required.",
            cite=[
                spec_back("Swing Target ship of the English fleet", "in the PLAYFIELD FEATURES list"),
                cite(KINETICIST, "A swinging ship representing the English fleet. It moves, so you have to time your shots to connect."),
            ],
            relationships={"gameplay_feature": [{"swinging-targets": 1}]},
        ),
        pk.entry(
            model,
            note=(
                "A physical cannon that fires the ball, themed to the Battle "
                "of La Rochelle; its platform diverter is counted in the "
                "diverters entry."
            ),
            cite=[
                spec_back("Canon Mechanism Battle of La Rochelle", "in the PLAYFIELD FEATURES list"),
                cite(
                    KINETICIST,
                    "a physical cannon fires the ball from its own platform, with a dedicated diverter routing shots into it",
                ),
            ],
            relationships={"gameplay_feature": [{"ball-cannons": 1}]},
        ),
        pk.entry(
            model,
            note=(
                "Treville's Mansion is an explicitly three-level play area "
                "on an otherwise single-level playfield."
            ),
            cite=[
                spec_back("3-level play area Treville's Mansion:", "in the PLAYFIELD FEATURES list"),
                cite(
                    KINETICIST,
                    "The main playfield is single-level (unlike Space Hunt's elevated mini-playfield with its pendulum shot), so this multi-level section stands out as the mechanical showpiece.",
                ),
            ],
            relationships={"gameplay_feature": ["multi-level-playfield"]},
        ),
        pk.entry(
            model,
            cite=cite(
                KINETICIST,
                "Three-ball lock themed to the harbor, feeding into multiball.",
            ),
            relationships={"gameplay_feature": ["multiball"]},
        ),
        pk.entry(
            model,
            cite=spec_front(
                "INTEGRATED VIDEO MODES [...] Narrative sequences and interactive [...] missions displayed on screen.",
                "in the DIGITAL & GAMEPLAY FUNCTIONS list",
            ),
            relationships={"gameplay_feature": ["video-modes"]},
        ),
        pk.entry(
            model,
            note=(
                "A 2.1 system is a stereo pair plus subwoofer; the Pinsound "
                "branding stays in the quote (no equipment-brand vocabulary "
                "is created for it)."
            ),
            cite=spec_back(SPEC_SOUND, "in the EXPERIENCE FEATURES list"),
            relationships={"gameplay_feature": ["stereo-sound", "subwoofers"]},
        ),
        pk.entry(
            model,
            note=(
                "Atmoslight is HEXA's branded RGB playfield-insert lighting "
                "system (resin inserts bonded into the playing surface), "
                "attached as the branded leaf under rgb-playfield-inserts; "
                "'Sytem' and 'pattented' are the sheet's own spellings."
            ),
            cite=[
                spec_back(SPEC_ATMOSLIGHT, "in the EXPERIENCE FEATURES list"),
                cite(KINETICIST, KIN_ATMOSLIGHT),
            ],
            relationships={"gameplay_feature": ["atmoslight"]},
        ),
    ]


def main() -> None:
    entries: list[str] = []

    # ── Vocabulary: the one branded leaf this family needs ──────────────
    entries.append(
        pk.entry(
            "gameplay-feature.atmoslight",
            create=True,
            fields={"name": "Atmoslight"},
            relationships={
                "gameplay_feature_parent": ["rgb-playfield-inserts"],
                "gameplay_feature_alias": [
                    "AtmosLight",
                    "Atmoslight Inserts",
                    "Atmoslight Surrounding System",
                ],
            },
        )
    )

    # ── People (romain-fontaine already exists in the catalog) ──────────
    entries.append(
        pk.entry(
            "person.tristan-fallon",
            create=True,
            cite=spec_front("Exclusive Art by Tristan Fallon", "beside the machine photo"),
            fields={"name": "Tristan Fallon"},
        )
    )
    entries.append(
        pk.entry(
            "person.herve-coussillan",
            create=True,
            cite=spec_front("Exclusive Soundtracks by Hervé Coussillan", "beside the machine photo"),
            fields={"name": "Hervé Coussillan"},
        )
    )
    entries.append(
        pk.entry(
            "person.luis-dos-santos",
            create=True,
            note=(
                "HEXA's own site interviews him as a game designer (the "
                "Space Hunt era 'Interview with Luis Dos Santos' page); his "
                "3 Musketeers design credit is carried by Kineticist's "
                "Design Team block."
            ),
            cite=cite(KINETICIST, "Game Design: Luis Dos Santos"),
            fields={"name": "Luis Dos Santos"},
        )
    )

    # ── Base model (the maker's Classic Edition) ────────────────────────
    entries.append(
        pk.entry(
            BASE,
            note=(
                "An earlier ingest created this model under the plain title "
                "name; the maker's own materials name the two editions "
                "Classic and Elegance, so the base model takes the maker's "
                "edition name (user-approved rename, 2026-08-12)."
            ),
            cite=[
                spec_back("CLASSIC EDITION", "heading of the Classic column"),
                cite(PRODUCT_EN, "Classic Edition [...] Experience all the intensity of the game, the original epic adventure"),
            ],
            fields={"name": "The 3 Musketeers (Classic Edition)"},
        )
    )
    entries.extend(shared_entries(BASE))
    entries.append(
        pk.entry(
            BASE,
            note="The Classic Edition's armor is Musketeer's Blue powder coat.",
            cite=spec_back(
                "Musketeer's Blue Powder coated finish Armor",
                "in the CLASSIC EDITION block",
            ),
            relationships={"gameplay_feature": ["cabinet-armor"]},
        )
    )

    # ── Elegance Edition ────────────────────────────────────────────────
    entries.extend(shared_entries(ELEG))
    entries.append(
        pk.entry(
            ELEG,
            note=(
                "The two editions are one design sold in two trims; the "
                "cheaper, unlimited Classic is the base and the 200-unit "
                "Elegance is its cosmetic/tactile upgrade (the standing "
                "variant rule)."
            ),
            cite=[
                cite(KINETICIST, KIN_IDENTICAL),
                cite(PRODUCT_EN, "Elegance Edition [...] Limited to 200 numbered copies worldwide."),
            ],
            fields={"variant_of": "the-3-musketeers"},
        )
    )
    entries.append(
        pk.entry(
            ELEG,
            note=(
                "A strictly limited, individually numbered 200-unit run is a "
                "limited edition; the maker's flyer calls it 'Strictly "
                "Limited to 200 Numbered Machines Worldwide'."
            ),
            cite=cite(PRODUCT_EN, "Limited to 200 numbered copies worldwide."),
            fields={"production_quantity": 200},
            tags=["limited-edition"],
        )
    )
    entries.append(
        pk.entry(
            ELEG,
            note="Included on the Elegance; the Classic lists it only as an option, so no claim there.",
            cite=[
                spec_back("Shaker Motor by Pinsound", "in the ELEGANCE EDITION block"),
                cite(KINETICIST, "Shaker motor by Pinsound"),
            ],
            relationships={"gameplay_feature": ["shaker-motors"]},
        )
    )
    entries.append(
        pk.entry(
            ELEG,
            cite=[
                spec_back("Anti-reflection Glass", "in the ELEGANCE EDITION block"),
                cite(KINETICIST, "Anti-reflection glass (vs. standard)"),
            ],
            relationships={"gameplay_feature": ["anti-reflection-playfield-glass"]},
        )
    )
    entries.append(
        pk.entry(
            ELEG,
            note="The Elegance's armor is Brilliant Splendor Gold powder coat.",
            cite=spec_back(
                "Brilliant Splendor Gold Powder coated finish Armor",
                "in the ELEGANCE EDITION block",
            ),
            relationships={"gameplay_feature": ["cabinet-armor"]},
        )
    )

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="The 3 Musketeers (HEXA 2026): naming, production, credits, features",
        entries=entries,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
