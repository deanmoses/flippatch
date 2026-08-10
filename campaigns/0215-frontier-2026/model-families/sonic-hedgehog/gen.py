"""Emit patch 0221 — the Sonic the Hedgehog family: JJP's 2026 CE / SE / AE trio.

See ../../README.md for the family split and
SonicHedgehog.md beside this file for the evidence inventory, the catalog
baseline, the traps and the decisions this generator encodes (2026-08-10).

SCOPE IS THE WHOLE FAMILY, three models, all 2026 — no older siblings:
  Sonic the Hedgehog — Collector's Edition / Special Edition / Arcade Edition

Only missing facts are asserted; 0215 already set name, year, title,
corporate entity and themes. Deliberately absent (each recorded in
SonicHedgehog.md → Not asserted):
  month                 the reveal dates the launch, not manufacture (0220 precedent)
  player_count          no primary source states it
  system + technology_generation   no document names JJP's platform
  wider team credits    first-party and journalism name only Ritchie and Slash;
                        the Pinside roster is unusable (manufacturer PDFs exist)
  descriptions          a follow-up patch's job (inline-cite rules)
  production_quantity + tags       no quantity or limit is published

THE EDITION LADDER (user decision 2026-08-10): the Special Edition is the
base; the Collector's and Arcade Editions are its variants — the shape the
catalog's seeded JJP families use (Harry Potter 2025: Arcade + Collector's
both variant_of Wizard). The all-models evidence (flyer, collection page,
manual) covers every edition directly, so shared facts cite it on each model
without a carry note; only variant_of itself records the ladder reasoning.

PDF QUOTES ARE TRANSCRIPTIONS: the flyer and manual quotes below were read
off rendered sheets (2026-08-10) — `verify-quote-verbatim` reports PDFs
SKIP-PDF by design. HTML quotes (collection + product pages, blog) are
machine-gated.

Run: uv run python campaigns/0215-frontier-2026/model-families/sonic-hedgehog/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0221-sonic-hedgehog.yaml"

# ── Models ──────────────────────────────────────────────────────────────
CE = "model.sonic-the-hedgehog-collectors-edition"
SE = "model.sonic-the-hedgehog-special-edition"
AE = "model.sonic-the-hedgehog-arcade-edition"
SE_SLUG = "sonic-the-hedgehog-special-edition"

# ── Sources ─────────────────────────────────────────────────────────────
FLYER_ALL = (
    "https://marketing.jerseyjackpinball.com/distributors/Sonic/Flyers/"
    "73-100024-12-04%20-%20REV.%20A%20-%20SONIC%20FLYER,%20ALL%20MODELS.pdf"
)
MANUAL = "https://marketing.jerseyjackpinball.com/sonic/Sonic_Manual_10_July_2026.pdf"
COLLECTION = "https://jerseyjackpinball.com/collections/sonic-the-hedgehog-pinball-game"
PROD_CE = "https://jerseyjackpinball.com/products/sonic-collectors-edition"
PROD_SE = "https://jerseyjackpinball.com/products/sonic-special-edition"
PROD_AE = "https://jerseyjackpinball.com/products/sonic-arcade-edition"

FLYER_LOC = "PDF document page 2 of 2; the flyer carries no printed folios"


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


def flyer(quote: str) -> dict[str, str]:
    return cite(FLYER_ALL, quote, locator=FLYER_LOC)


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


# ── Shared quotes ───────────────────────────────────────────────────────
FAQ_AVAILABLE = (
    "Yes, the Sonic the Hedgehog Pinball Machine is available for purchase "
    "directly from Jersey Jack Pinball."
)
FAQ_DELIVERY = (
    "Delivery timelines vary based on production schedules, inventory "
    "availability, and your selected delivery method. If your game is in "
    "stock and you select White Glove delivery, estimated delivery is 1-2 "
    "weeks."
)
PRODUCED_NOTE = (
    "The maker sells the game now and ships it from stock — its delivery "
    "terms turn on production schedules and inventory availability — so the "
    "machine is in production, not merely announced."
)
FAQ_THREE = (
    "There are three pinball machines for Sonic: the Collector's Edition "
    "($15,000), the Special Edition ($12,000), and the Arcade Edition "
    "($9,999)."
)
FAQ_AE_SAME = (
    "And the Arcade Edition delivers the same layout, the same shots, and "
    "the same speed at an entry-level price"
)
FAQ_DESIGNED = (
    "The game was designed by Steve Ritchie — widely regarded as one of the "
    "greatest pinball designers in history with a career spanning over 40 "
    "years."
)
GOTTA_PINBALL = (
    "Sonic the Hedgehog Pinball by Jersey Jack Pinball brings the legendary "
    "speed, color, music, and energy of Sonic to life in a fast-flowing "
    "pinball adventure built for fans and players across generations."
)
MANUAL_DESIGN = (
    "Hall of Fame game designer Steve Ritchie is known for his fast-flowing "
    "games. He and his design team have created Sonic pinball."
)
HIGHLIGHTS_SLASH = (
    "amplified with exclusive guitar solos from Slash for a high-voltage edge"
)
FLYER_SLASH = (
    "Open Your Heart (Guitar Solo by Slash) [...] It Doesn't Matter "
    "(Guitar Solo by Slash)"
)
HIGHLIGHTS_SHAKER = (
    "SHAKER MOTOR WITH HAPTIC FEEDBACK (CE & SE ONLY) [...] Available on the "
    "Collector's and Special Editions"
)
BACKGLASS_27 = (
    "The 27\" high-definition backglass display brings Sonic's world to life"
)

# The flyer's GAME FEATURES - ALL MODELS block, transcribed off the rendered
# sheet 2026-08-10. Three thematic slices keep each changeset's note short.
FLYER_MECHS = (
    "4 Full-Sized Flippers [...] 9 Stand-Up Targets [...] 2 Spring Targets "
    "[...] 1 Spinner [...] 2 Up-Posts to Catch the Ball [...] Total-Control "
    "Inline 3-Bank Drop Target Lock [...] Upper Playfield Entry Drop Target "
    "[...] Bash Dash Captive Ball Lock [...] 6-Ball Multiball [...] "
    "Polycarbonate Upper Playfield [...] Stainless Steel Ramps [...] "
    "Magnetic Accelerator Loop Ramp [...] 'Superconducting' Battle Zone! "
    "Magnet"
)
MECHS_NOTE = (
    "Classifications: the Total-Control Inline 3-Bank Drop Target Lock is an "
    "in-line 3-bank that locks balls; the Upper Playfield Entry Drop Target "
    "is a single drop target, so it attaches as a solitary drop target; the "
    "Bash Dash Captive Ball Lock is a captive ball that locks; the "
    "Polycarbonate Upper Playfield attaches as a mini-playfield, the term "
    "in use for upper playfields; the Magnetic Accelerator Loop Ramp's "
    "magnet accelerates the ball, so it attaches as a thrust magnet, and the "
    "Battle Zone! magnet states no direction, so it attaches as the generic "
    "magnet."
)
FEATURES_MECHS: list[str | dict[str, int]] = [
    {"flippers": 4},
    {"standup-targets": 9},
    {"spring-targets": 2},
    {"spinners": 1},
    {"up-posts": 2},
    "3-in-line-drop-targets",
    "ball-locks",
    "solitary-drop-targets",
    "captive-ball",
    "6-ball-multiball",
    "mini-playfields",
    "ramps",
    "thrust-magnets",
    "magnets",
]
FLYER_TOYS = (
    "Interactive Dr. Eggman Bash Toy [...] Custom Sculptures of Sonic, Amy "
    "Rose & Dr. Eggman [...] Voice Callouts by Official Sonic Cast"
)
COLLECTION_EGGMAN = "Dr. Eggman Animatronic Bash Toy"
TOYS_NOTE = (
    "Toy classifications: JJP's own wording calls the Dr. Eggman toy both "
    "interactive bash toy and animatronic, so it attaches as bash and "
    "animatronic; the Sonic and Amy Rose sculptures state no motion or ball "
    "interaction, so they classify as static toys."
)
FEATURES_TOYS: list[str | dict[str, int]] = [
    "bash-toys",
    "animatronic-toys",
    "static-toys",
    "speech",
]
FLYER_EQUIP = (
    "Wi-Fi Connectivity [...] Bluetooth Audio [...] Audio Equalizer and "
    "8-inch Subwoofer [...] JJP Exclusive High-Score Player Camera [...] "
    "2,000+ individually controlled RGB LEDs [...] Custom Chaos Emerald "
    "Inserts"
)
COLLECTION_RGB_INSERTS = "Custom RGB Chaos Emerald Inserts"
EQUIP_NOTE = (
    "The collection page's playfield list states the Chaos Emerald inserts "
    "are RGB; the 2,000+ individually controlled RGB LEDs attach as LED "
    "general illumination."
)
FEATURES_EQUIP: list[str | dict[str, int]] = [
    "wifi-connectivity",
    "bluetooth-audio",
    "subwoofers",
    "player-cameras",
    "led-general-illumination",
    "rgb-playfield-inserts",
]

# ── Per-edition quotes (product pages are gated HTML; the flyer's edition
#    blocks are headed text lists, transcribed — not checkmark columns) ──
PROD_SE_LIST = (
    "'Sonic Blue' Powder Coated Armor [...] Battle Topper with Dual-Layer "
    "Acrylic LEDs [...] Shaker Motor with Haptic Feedback [...] Industry "
    "Leading JJP Invisiglass™ [...] 'Special Edition' Numbered Plaque"
)
PROD_CE_LIST = (
    "Sonic Vs. Dr. Eggman Mechanical Battle Topper with Super-Wide LCD "
    "Screen [...] 'Knuckles Red' Metallic Laser-Cut Armor [...] Gold "
    "Wireform Ramps [...] Gold Ring Shooter Knob [...] External LED "
    "Lighting Package [...] Shaker Motor with Haptic Feedback [...] "
    "Industry Leading JJP Invisiglass™ [...] 'Collector's Edition' Numbered "
    "Plaque [...] 'Jersey Jack' Guarnieri & Steve Ritchie Signature Card"
)
PROD_AE_ARMOR = "Black Armor"
COLLECTION_CE_GLOW = (
    "external lighting surrounds the cabinet in a bold, reactive glow"
)
CE_NOTE = (
    "Classifications: the Mechanical Battle Topper attaches as a topper; "
    "Gold Wireform Ramps attach as habitrails (wireform); the Gold Ring "
    "Shooter Knob is a custom shooter knob; the External LED Lighting "
    "Package reacts to gameplay per the collection page's cabinet caption, "
    "so it attaches as interactive cabinet lighting; the Guarnieri & "
    "Ritchie Signature Card attaches as designer autographs."
)
FEATURES_CE: list[str | dict[str, int]] = [
    "toppers",
    "cabinet-armor",
    "habitrails",
    "custom-shooter-knobs",
    "interactive-cabinet-lighting",
    "shaker-motors",
    "invisiglass",
    "numbered-plaques",
    "designer-autographs",
]
FEATURES_SE: list[str | dict[str, int]] = [
    "cabinet-armor",
    "toppers",
    "shaker-motors",
    "invisiglass",
    "numbered-plaques",
]
VARIANT_NOTE = (
    "Jersey Jack sells the family as one game in three trim tiers around "
    "the Special Edition, the same shape as its other multi-edition "
    "families — Harry Potter's Arcade and Collector's Editions are likewise "
    "variants of that family's mid-tier Wizard Edition."
)


def shared(model: str, prod_url: str) -> list[str]:
    """The entries every edition gets; the evidence covers all models."""
    return [
        pk.entry(
            model,
            note=PRODUCED_NOTE,
            cite=[
                cite(COLLECTION, FAQ_AVAILABLE, locator="in the Frequently Asked Questions section"),
                cite(prod_url, FAQ_DELIVERY, locator="in the DELIVERY section"),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            model,
            cite=cite(COLLECTION, GOTTA_PINBALL, locator="in the GOTTA GO FAST! section"),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            model,
            cite=[
                flyer('Industry-Leading 27" LCD Display'),
                cite(COLLECTION, BACKGLASS_27, locator="in The Backglass section"),
            ],
            fields={"display_type": "lcd"},
        ),
        pk.entry(
            model,
            cite=[
                cite(COLLECTION, FAQ_DESIGNED, locator="in the Frequently Asked Questions section"),
                flyer("Game Designer: Steve Ritchie"),
                cite(
                    MANUAL,
                    MANUAL_DESIGN,
                    locator="printed folio V, PDF document page 5",
                ),
            ],
            credits=[("steve-ritchie", "design")],
        ),
        pk.entry(
            model,
            note=(
                "Slash contributed the soundtrack's exclusive guitar solos, "
                "so he credits as music."
            ),
            cite=[
                cite(COLLECTION, HIGHLIGHTS_SLASH, locator="in The Highlights section"),
                flyer(FLYER_SLASH),
            ],
            credits=[("saul-slash-hudson", "music")],
        ),
        pk.entry(
            model,
            note=MECHS_NOTE,
            cite=flyer(FLYER_MECHS),
            relationships={"gameplay_feature": FEATURES_MECHS},
        ),
        pk.entry(
            model,
            note=TOYS_NOTE,
            cite=[
                flyer(FLYER_TOYS),
                cite(COLLECTION, COLLECTION_EGGMAN, locator="in The Playfield section"),
            ],
            relationships={"gameplay_feature": FEATURES_TOYS},
        ),
        pk.entry(
            model,
            note=EQUIP_NOTE,
            cite=[
                flyer(FLYER_EQUIP),
                cite(COLLECTION, COLLECTION_RGB_INSERTS, locator="in The Playfield section"),
            ],
            relationships={"gameplay_feature": FEATURES_EQUIP},
        ),
    ]


def main() -> None:
    entries = [
        # ── Vocabulary (all generic; identities stay in the family doc) ──
        vocab(
            "spring-targets",
            "Spring Targets",
            parents=["targets"],
            aliases=["Spring Target"],
        ),
        vocab(
            "player-cameras",
            "Player Cameras",
            aliases=["High-Score Player Camera", "Player Camera"],
        ),
        vocab("wifi-connectivity", "Wi-Fi Connectivity", aliases=["Wi-Fi"]),
        vocab("bluetooth-audio", "Bluetooth Audio"),
        vocab(
            "subwoofers",
            "Subwoofers",
            parents=["speakers"],
            aliases=["Subwoofer"],
        ),
        vocab(
            "custom-shooter-knobs",
            "Custom Shooter Knobs",
            aliases=["Custom Shooter Knob"],
        ),
        # ── Special Edition (the base) ──────────────────────────────────
        *shared(SE, PROD_SE),
        pk.entry(
            SE,
            cite=[
                cite(PROD_SE, PROD_SE_LIST),
                cite(COLLECTION, HIGHLIGHTS_SHAKER, locator="in The Highlights section"),
            ],
            relationships={"gameplay_feature": FEATURES_SE},
        ),
        # ── Collector's Edition ─────────────────────────────────────────
        *shared(CE, PROD_CE),
        pk.entry(
            CE,
            note=VARIANT_NOTE,
            cite=cite(COLLECTION, FAQ_THREE, locator="in the Frequently Asked Questions section"),
            fields={"variant_of": SE_SLUG},
        ),
        pk.entry(
            CE,
            note=CE_NOTE,
            cite=[
                cite(PROD_CE, PROD_CE_LIST),
                cite(COLLECTION, COLLECTION_CE_GLOW, locator="in The Cabinet section"),
            ],
            relationships={"gameplay_feature": FEATURES_CE},
        ),
        # ── Arcade Edition ──────────────────────────────────────────────
        *shared(AE, PROD_AE),
        pk.entry(
            AE,
            note=VARIANT_NOTE,
            cite=[
                cite(COLLECTION, FAQ_THREE, locator="in the Frequently Asked Questions section"),
                cite(COLLECTION, FAQ_AE_SAME, locator="in the Frequently Asked Questions section"),
            ],
            fields={"variant_of": SE_SLUG},
        ),
        pk.entry(
            AE,
            note=(
                "Armor is cabinet trim; the feature vocabulary includes "
                "presentation equipment, so the Black Armor attaches as "
                "cabinet armor."
            ),
            cite=cite(PROD_AE, PROD_AE_ARMOR),
            relationships={"gameplay_feature": ["cabinet-armor"]},
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="Sonic the Hedgehog family details across JJP's 2026 editions",
        entries=entries,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
