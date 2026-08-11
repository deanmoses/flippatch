"""Emit patch 0223 — the Cirqus Voltaire family: the 1997 Bally original,
American Pinball's 2026 remake, and its Ringmaster Edition.

See ../../README.md for the family split and CirqusVoltaire.md beside this
file for the evidence inventory, the catalog baseline, the traps and the
user rulings this generator encodes (2026-08-10).

SCOPE IS THE WHOLE FAMILY, three models:
  1997  Cirqus Voltaire (Bally) — seeded, enriched here
  2026  Cirqus Voltaire (Remake) — created by 0215, fleshed out here
  2026  Cirqus Voltaire (Remake Ringmaster Edition) — CREATED here

Only missing facts are asserted; the baseline table in CirqusVoltaire.md
records what each model already holds. Deliberately absent (each recorded
there): descriptions, cabinet, year on the Ringmaster Edition, Standard/LE
edition models (dead sources), system/technology_generation/month on the
remake models, the playfield-DMD display subtype.

THE REMAKE CREDIT CARRY (user ruling 2026-08-10): all creative credits —
design, art, animation, music, sound — carry from the original to the
remake, cited to the original's evidence with a note; mechanics and
software do not (the remake is re-engineered with updated code). On the
Ringmaster Edition the art slot goes to Brian Allen instead (its art
package is new), so Linda Deal's art credit carries only to the base.

THE EDITION (user ruling 2026-08-10): created from distributor evidence.
SD Amusements is the only live source naming the edition; its citation
root is a single-family root created in this patch (the Cardona pattern).

Run: uv run python campaigns/0215-frontier-2026/model-families/cirqus-voltaire/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0223-cirqus-voltaire.yaml"

# ── Models ──────────────────────────────────────────────────────────────
ORIG = "model.cirqus-voltaire"
BASE = "model.cirqus-voltaire-remake"
RING = "model.cirqus-voltaire-remake-ringmaster-edition"

# ── Sources ─────────────────────────────────────────────────────────────
AP_ANN = "https://americanpinball.com/cirqus-voltaire-announcement"
SD = "https://sdamusements.com/products/cirqus-voltaire-ringmaster-edition"
# The 1997 Williams/Bally official site survives on Planetary Pinball
# (root seeded by 0217).
PPS_RULES = "https://www.planetarypinball.com/mm5/Williams/games/cirqus/rules.html"
IPDB = "ipdb:4059"

# ── Quotes ──────────────────────────────────────────────────────────────
ANN_BACK = (
    "American Pinball is proud to announce that we are bringing the "
    "legendary Cirqus Voltaire back to life for a new generation of players"
)
ANN_REMAKING = (
    "American Pinball is remaking Cirqus Voltaire, a pinball combining "
    "magic, artistry, and gameplay that made the original a fan favorite"
)
ANN_META_LOCATOR = "in the page's meta description"
SD_COMING = (
    "Circus Voltaire is coming back and being reimagined by American "
    "Pinball. Join the interest list today with a $0 deposit and no "
    "commitment, and be among the first to receive updates on "
    "availability, preorder details, pricing, and release information."
)
SD_RING_772 = "RINGMASTER EDITION (Limited to 772 units)"
SD_ART = (
    "New Brian Allen full Art Package including Playfield, Cabinet, "
    "Plastics & Backglass"
)
SD_EQUIPMENT = (
    "New Scrolls that light up with Interactive Topper [...] Custom "
    "Shooter Rod [...] Magic Glass [...] Shaker & Knocker"
)

IPDB_FEATURE_LINE = (
    "Flippers (2), Pop bumpers (3), Slingshots (2), Stop magnets (3), "
    "Standup targets (9), Kick-out holes (2), Spinning targets (2), "
    "Speech, Playfield-mounted dot matrix display."
)
IPDB_PRODUCTION = (
    "The sample game pictured in this listing has several playfield "
    "differences from the production games that followed."
)
IPDB_MENAGERIE = (
    "The menagerie ball, a large plastic ball trapped within a cage above "
    "the left slingshot, can be hit by the ball in play and disrupts ball "
    "direction."
)
IPDB_RINGMASTER = (
    "The Ringmaster is an animated head that elevates from the underside "
    "of the playfield and makes wise cracks at the player, who tries to "
    "defeat him by hitting him with the pinball in various modes."
)
IPDB_BOOM = (
    'The "Boom Balloon" pop bumper (on the lower right side of the '
    "playfield) is a disappearing bumper, dropping down until its flat "
    "plastic top is level with the playfield."
)
IPDB_CREATIVE_CREDITS = (
    "Design by: John Popadiuk, Cameron Silver [...] Art by: Linda Deal "
    "(aka Doane) [...] Dots/Animation by: Adam Rhine, Brian Morris [...] "
    "Music by: Rob Berry, Dave Zabriskie [...] Sound by: Rob Berry"
)
IPDB_CREATIVE_CREDITS_NO_ART = (
    "Design by: John Popadiuk, Cameron Silver [...] Dots/Animation by: "
    "Adam Rhine, Brian Morris [...] Music by: Rob Berry, Dave Zabriskie "
    "[...] Sound by: Rob Berry"
)
RULES_HIGHWIRE = (
    "LOCK balls up the HIGHWIRE ramp, then start HW Multiball. [...] "
    "Rollover Buttons add VOLTAGE to CHARGE the BOOM BALLOON."
)

REMAKE_CARRY_NOTE = (
    "A remake preserves the original's creative work, so the original's "
    "creative credits — design, art, animation, music, sound — carry to "
    "the remake, as with Medieval Madness and its Chicago Gaming "
    "remake. The maker frames the remake as "
    "preserving the original's magic, artistry and gameplay. Mechanics "
    "and software credits do not carry: the remake is re-engineered."
)

CREATIVE_CREDITS: list[tuple[str, str]] = [
    ("john-popadiuk", "design"),
    ("cameron-silver", "design"),
    ("linda-deal", "art"),
    ("adam-rhine", "animation"),
    ("brian-morris", "animation"),
    ("dave-zabriskie", "music"),
    ("rob-berry", "music"),
    ("rob-berry", "sound"),
]
# The Ringmaster Edition's art package is new (Brian Allen), so Linda
# Deal's art credit carries only to the base remake.
CREATIVE_CREDITS_NO_ART = [c for c in CREATIVE_CREDITS if c[1] != "art"]


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


def main() -> None:
    sources = [
        pk.source_root(
            "San Diego Amusements",
            source_type="web",
            description=(
                "Pinball and amusement distributor in San Diego, "
                "California. Carries the only live edition listing for "
                "American Pinball's Cirqus Voltaire remake."
            ),
            links=[("https://sdamusements.com/", "San Diego Amusements", "homepage")],
        ),
    ]

    entries = [
        # ── 1997: Cirqus Voltaire (Bally) ───────────────────────────────
        pk.entry(
            ORIG,
            note=(
                "The row records production games following the pictured "
                "sample game, so the machine was produced."
            ),
            cite=cite(IPDB, IPDB_PRODUCTION),
            fields={"production_status": "produced"},
        ),
        # One changeset: format and the speech feature rest on the same
        # hardware line. Its seven counted features are already claimed by
        # the IPDB actor; Speech is in the line but not among them.
        pk.entry(
            ORIG,
            cite=cite(IPDB, IPDB_FEATURE_LINE),
            fields={"game_format": "pinball"},
            relationships={"gameplay_feature": ["speech"]},
        ),
        pk.entry(
            ORIG,
            cite=cite(PPS_RULES, RULES_HIGHWIRE),
            relationships={
                "gameplay_feature": [
                    "ball-locks",
                    "ramps",
                    "multiball",
                    "rollover-buttons",
                ]
            },
        ),
        pk.entry(
            ORIG,
            note=(
                "A ball permanently trapped in a cage that the ball in "
                "play strikes is a captive ball."
            ),
            cite=cite(IPDB, IPDB_MENAGERIE),
            relationships={"gameplay_feature": ["captive-ball"]},
        ),
        pk.entry(
            ORIG,
            note=(
                "The player defeats the elevating Ringmaster head by "
                "hitting it with the pinball, so it classifies as a bash "
                "toy."
            ),
            cite=cite(IPDB, IPDB_RINGMASTER),
            relationships={"gameplay_feature": ["bash-toys"]},
        ),
        pk.entry(
            ORIG,
            cite=cite(IPDB, IPDB_BOOM),
            relationships={"gameplay_feature": ["disappearing-bumpers"]},
        ),
        # ── 2026: Cirqus Voltaire (Remake) ──────────────────────────────
        pk.entry(
            BASE,
            note=(
                "The maker announces the machine and gathers interest; "
                "nothing is sold yet (no store listing), so announced."
            ),
            cite=cite(AP_ANN, ANN_BACK),
            fields={"production_status": "announced"},
        ),
        pk.entry(
            BASE,
            cite=[
                cite(AP_ANN, ANN_REMAKING, locator=ANN_META_LOCATOR),
                cite(AP_ANN, ANN_BACK),
            ],
            fields={"remake_of": "cirqus-voltaire"},
        ),
        pk.entry(
            BASE,
            cite=cite(AP_ANN, ANN_REMAKING, locator=ANN_META_LOCATOR),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            BASE,
            note=REMAKE_CARRY_NOTE,
            cite=[
                cite(IPDB, IPDB_CREATIVE_CREDITS),
                cite(AP_ANN, ANN_REMAKING, locator=ANN_META_LOCATOR),
            ],
            credits=CREATIVE_CREDITS,
        ),
        # ── Scaffolding: the new person ─────────────────────────────────
        pk.entry(
            "person.brian-allen",
            create=True,
            note=(
                "Pinball artist; creates the new art package for American "
                "Pinball's Cirqus Voltaire remake Ringmaster Edition — his "
                "first credit here."
            ),
            cite=cite(SD, SD_ART),
            fields={"name": "Brian Allen"},
        ),
        # ── 2026: Cirqus Voltaire (Remake Ringmaster Edition) ───────────
        pk.entry(
            RING,
            create=True,
            note=(
                "Named the way remake editions are named here, as in "
                "Medieval Madness (Remake Limited Edition). No source "
                "states a release year, so none is asserted."
            ),
            cite=cite(SD, SD_RING_772),
            fields={
                "name": "Cirqus Voltaire (Remake Ringmaster Edition)",
                "title": "cirqus-voltaire",
                "corporate_entity": "american-pinball-inc",
            },
        ),
        pk.entry(
            RING,
            note=(
                "An edition is a variant of its base model, and the base "
                "is American Pinball's remake of Bally's 1997 Cirqus "
                "Voltaire, so both relationships follow."
            ),
            cite=cite(SD, SD_COMING),
            fields={
                "variant_of": "cirqus-voltaire-remake",
                "remake_of": "cirqus-voltaire",
            },
        ),
        pk.entry(
            RING,
            note=(
                "The edition is the same machine as the base remake, so "
                "the base's themes carry."
            ),
            cite=cite(SD, SD_COMING),
            relationships={"theme": ["carnivals", "circus"]},
        ),
        pk.entry(
            RING,
            note=(
                "The distributor pre-sells interest-list deposits with no "
                "price, availability or release information, so the "
                "machine is announced, not produced."
            ),
            cite=cite(SD, SD_COMING),
            fields={"production_status": "announced"},
        ),
        pk.entry(
            RING,
            cite=cite(SD, SD_RING_772),
            fields={"production_quantity": 772},
            tags=["limited-edition"],
        ),
        pk.entry(
            RING,
            cite=cite(SD, "LCD Screen"),
            fields={"display_type": "lcd"},
        ),
        pk.entry(
            RING,
            note=(
                "Magic Glass is a branded form of anti-reflection "
                "playfield glass. The trade term custom shooter rod names the "
                "decorated shooter assembly that custom shooter knobs "
                "describes. The scrolls themselves are model-specific decor "
                "(recorded in the family notes); the interactive topper "
                "attaches as the generic topper."
            ),
            cite=cite(SD, SD_EQUIPMENT),
            relationships={
                "gameplay_feature": [
                    "toppers",
                    "custom-shooter-knobs",
                    "magic-glass",
                    "shaker-motors",
                    "knockers",
                ]
            },
        ),
        pk.entry(
            RING,
            cite=cite(SD, SD_ART),
            credits=[("brian-allen", "art")],
        ),
        pk.entry(
            RING,
            note=REMAKE_CARRY_NOTE
            + " The art credit does not carry to this edition: its art "
            "package is new (Brian Allen).",
            cite=cite(IPDB, IPDB_CREATIVE_CREDITS_NO_ART),
            credits=CREATIVE_CREDITS_NO_ART,
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="Cirqus Voltaire family: 1997 Bally original + 2026 AP remake editions",
        entries=entries,
        sources=sources,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
