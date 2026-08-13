"""Emit patch 0232 — the Turner Pinball family: Yukon Yeti, Merlin's Arcade, Ninja Eclipse.

See ../../README.md for the campaign and YukonYeti.md beside this file for the
evidence inventory, the conflicts and their resolutions, and the decisions this
generator encodes (2026-08-13).

SCOPE IS THE WHOLE MAKER (user decision 2026-08-13), five models:
  2026  Yukon Yeti — renamed to Yukon Yeti (Legendary Edition), user-approved
  2025  Merlin's Arcade — Arcade Edition (base) / Legendary Edition
  2024  Ninja Eclipse — Arcade Edition (never produced) / First Edition (100 units)

Only missing facts are asserted; the baseline survey in YukonYeti.md records
what each model already holds. Deliberately absent (each recorded there):
  display_type, player_count, cabinet, dimensions    no textual source states them
  month on Yukon Yeti                                March 2026 dates the reveal, not manufacture
  System                                             no source names Turner's platform
  shaker/topper/etc. on Yukon Yeti                   optional upgrades, not standard equipment
  Merlin's Arcade Edition production_quantity        maker: "not numbered or limited"
  Ninja Eclipse sculpt classification                types unverifiable from the evidence
  descriptions                                       a follow-up patch's job (inline-cite rules)

THE VARIANT SHAPE: Merlin's Legendary Edition gets variant_of the Arcade
Edition — the cheaper, less-limited edition is the base (user rule 2026-08-11),
matching the shape Ninja Eclipse already has in the catalog (First Edition
variant_of Arcade Edition). Merlin's credits and shared-core-game facts cite
the maker's single title page, which covers both editions natively.

NINJA ECLIPSE ARCADE EDITION WAS NEVER PRODUCED: the maker's FAQ discusses it
only as future-possible, so it takes production_status announced with the FAQ
quote; the First Edition's hardware (from the 2023 reserve-page spec sheet)
attaches to the First Edition only.

Run: uv run python campaigns/0215-frontier-2026/model-families/yukon-yeti/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0232-turner-pinball.yaml"

# ── Models ──────────────────────────────────────────────────────────────
YY = "model.yukon-yeti"
MA_ARC = "model.merlins-arcade-arcade-edition"
MA_LEG = "model.merlins-arcade-legendary-edition"
NE_ARC = "model.ninja-eclipse-arcade-edition"
NE_FIRST = "model.ninja-eclipse-first-edition"

# ── Sources ─────────────────────────────────────────────────────────────
YY_PAGE = "https://turnerpinball.com/games/yukon-yeti"
MA_PAGE = "https://turnerpinball.com/games/merlins-arcade"
NE_PAGE = "https://turnerpinball.com/games/ninja-eclipse"
ABOUT = "https://turnerpinball.com/about"
CONTACT = "https://turnerpinball.com/contact"
TL_CONTACT = "https://turnerlogic.com/contact"

# Old-era pages recovered from Wayback: ref is the original publisher URL,
# archive the id_ snapshot (four snapshots are stored gzip-compressed at
# Wayback itself and were gunzipped + re-imported by hand — see YukonYeti.md
# → Tooling feedback).
NE_RESERVE = "https://turnerpinball.com/reserve"
NE_RESERVE_AR = "https://web.archive.org/web/20231208071132id_/https://turnerpinball.com/reserve"
MA_OLD = "https://turnerpinball.com/merlins-arcade"
MA_OLD_AR = "https://web.archive.org/web/20250318224933id_/https://turnerpinball.com/merlins-arcade"
HEROES = "https://turnerpinball.com/posts/the-heroes-of-ninja-eclipse"
HEROES_AR = (
    "https://web.archive.org/web/20250318225456id_/"
    "https://turnerpinball.com/posts/the-heroes-of-ninja-eclipse"
)

PN_YY = "https://www.pinballnews.com/site/2026/03/18/yukon-yeti-revealed"
PN_MA = "https://www.pinballnews.com/site/2025/03/19/merlins-arcade-revealed"
KIN_YY = "https://www.kineticist.com/news/turner-reveals-yukon-yeti"


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


def arch(ref: str, archive: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "archive": archive, "quote": quote, **extra}


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
# Yukon Yeti maker page. The Credits block renders as a definition list, so
# each role/name pair is quoted as two spans in source order.
YY_META_DESC = (
    "Yukon Yeti™ is a gold rush pinball adventure packed with avalanches, "
    "rapids, multiballs, hidden locks, and a mischievous mountain beast."
)
YY_SHIPPING = "Yukon Yeti™ is currently expected to begin shipping in Summer 2026."
YY_500 = (
    "We will produce 500 Legendary Edition™ Yukon Yeti™ machines before "
    "moving on to our next title."
)
YY_BASE_NAME = (
    "Yukon Yeti™ Legendary Edition includes the core game with premium "
    "construction and hand-crafted detail."
)
YY_LOCK = (
    "A signature stair-step lock mech that can hold up to five balls and "
    "unleash them for Avalanche Multiball."
)
YY_RAMP = (
    "A nostalgic and playful wavy ramp that adds strong visual identity and "
    "memorable shot value."
)
YY_UPPER = (
    "The upper playfield opens access to multiple routes, including the "
    "rapids and mine cart ramps."
)
YY_HIDDEN = "A hidden lock that adds surprise and depth to the playfield progression."
YY_SCULPT = "A major playfield centerpiece featuring the Yukon Yeti himself."
YY_GRANNER = (
    "Chris Granner is joining Yukon Yeti™ to lead its sound direction"
)
YY_GUBMAN = "Adam Gubman joins the project as composer and sound designer."

KIN_FLIPPERS = (
    "The game runs four flippers total, including a mid-playfield flipper "
    "that wasn't part of the original White Water layout."
)
KIN_POPS = (
    "this sends the ball to the pop bumpers, which award nuggets per hit"
)
KIN_SPINNER = "Shoot Kate's Place spinner to light the Dawson shot for mode start."
KIN_GLACIER = "The Glacier (Newton ball) and drop target also award nuggets when lit"
KIN_TARGETS = "Completing the target bank cycles through three rewards in order"
KIN_TRAPDOOR = "On the upper playfield, a trapdoor near the Yeti serves two functions."
KIN_HIDDEN = (
    "Behind the upper-right flipper, two optos and a post create a concealed "
    "ball lock that can hold two balls for a secondary multiball."
)
PN_FINESSE = (
    "The cabinet includes secondary flipper buttons on both sides which "
    "operate the Finesse Flip function to perform a tap pass which transfers "
    "the ball from one main flipper to the other."
)

# Merlin's Arcade maker page (curly apostrophe is the page's own).
MA_PINBALL = (
    "battle your way through a lineup of arcade-inspired medieval contests "
    "in this uproarious pinball adventure"
)
MA_AVAIL = "Legendary Edition™ is available now. Arcade Edition™ is sold out."
MA_SAME_CORE = (
    "Both editions deliver the same core game. Differences are in toys, "
    "trim, presentation, and premium features."
)
MA_FAQ_500 = (
    "No more than 500 Legendary Edition™ Merlin’s Arcade™ machines will be "
    "produced. Each will be numbered and include a signed Certificate of "
    "Authenticity. Arcade Edition™ machines are not numbered or limited."
)
MA_SHIPPED = "The first customer units for Merlin's Arcade™ started going out in late summer."
MA_SCOOP = "Shoot the scoop to start and end battles."
MA_FOOSBALL = (
    "Battle Sir Dagonet in Foosball by hitting the life-sized foosball spinner."
)
MA_OLD_SPINNERS = (
    "Huge Foosball Knight Super Spinner [...] Two Additional Super Spinners"
)
MA_OLD_MULTIBALL = (
    "Special Multiball for Each Knight (Light and Dark) [...] Merlin Multiball"
)
MA_OLD_NORRIS = (
    "The playfield layout and game ruleset were both designed by renowned "
    "pinball designer Jon Norris."
)

# Ninja Eclipse.
NE_100 = "100. The full First Edition run has been sold."
NE_MAYBE = (
    "We may offer an Arcade Edition™ of Ninja Eclipse™ at some point in the future."
)
NE_DELIVERED = (
    "We delivered our first units at Chicago Pinball Expo. The show was a "
    "huge success, and the First Edition run of Ninja Eclipse™ sold out."
)
NE_PINBALL = "the vibrant world of the Ninja Eclipse pinball game"
NE_SPECS = (
    "Three Ramps [...] Three Flippers [...] Three Ball Physical Lock [...] "
    "Two Smart Drop Targets [...] Two Spinners [...] Two Diverters [...] "
    "Two Pop Bumpers [...] Two VUKs/Scoops [...] One Spinning Disk [...] "
    "One Outlane Kickback [...] One Newton Ball [...] One Magnet"
)
NE_GAMEPLAY = "One Multiball [...] Two Wizard Modes"

VARIANT_NOTE_MA = (
    "The maker sells the title as one core game in two trims, the Arcade "
    "Edition cheaper and unlimited, the Legendary numbered and capped at "
    "500 — so the Arcade Edition is the base and the Legendary Edition its "
    "variant (the cheaper, less-limited edition is the base), the same "
    "shape Ninja Eclipse's editions already have."
)


def credits_entry(
    model: str,
    people: list[tuple[str, str]],
    cites: list[dict[str, str]] | dict[str, str],
    note: str | None = None,
) -> str:
    return pk.entry(model, note=note, cite=cites, credits=people)


def main() -> None:
    entries: list[str] = [
        # ── Feature vocabulary ──────────────────────────────────────────
        # Secondary (tap-pass) flipper buttons are generic — any maker could
        # add a second button pair; Turner's branded implementation is the
        # child, the InvisiGlass pattern.
        vocab(
            "secondary-flipper-buttons",
            "Secondary Flipper Buttons",
            aliases=["Dual Flipper Buttons"],
        ),
        vocab(
            "finesse-flip",
            "Finesse Flip",
            parents=["secondary-flipper-buttons"],
            aliases=["Finesse Feature"],
        ),
        # A glass frame that removes as a unit (vs the traditional slide-out
        # glass) is generic cabinet equipment; LumaLift is Turner's branded
        # implementation, named only on the Ninja Eclipse page.
        vocab("removable-glass-frames", "Removable Glass Frames"),
        vocab("lumalift", "LumaLift", parents=["removable-glass-frames"]),
        # ── People ──────────────────────────────────────────────────────
        pk.entry(
            "person.brad-duke",
            create=True,
            cite=cite(YY_PAGE, "Art [...] Brad Duke", locator="in the Credits section"),
            fields={"name": "Brad Duke"},
        ),
        pk.entry(
            "person.quinn-johnson",
            create=True,
            cite=cite(
                YY_PAGE, "Story [...] Quinn Johnson", locator="in the Credits section"
            ),
            fields={"name": "Quinn Johnson"},
        ),
        pk.entry(
            "person.matthew-brozusky",
            create=True,
            cite=cite(
                YY_PAGE,
                "Animation [...] Matthew Brozusky",
                locator="in the Credits section",
            ),
            fields={"name": "Matthew Brozusky"},
        ),
        pk.entry(
            "person.chris-turner",
            create=True,
            cite=cite(
                YY_PAGE,
                "Programming [...] Matthew Brozusky, Chris Turner",
                locator="in the Credits section",
            ),
            fields={"name": "Chris Turner"},
        ),
        pk.entry(
            "person.gabe-hernandez",
            create=True,
            cite=cite(
                YY_PAGE,
                "Mechanical [...] Gabe Hernandez, Chris Turner, Zofia Ryan",
                locator="in the Credits section",
            ),
            fields={"name": "Gabe Hernandez"},
        ),
        pk.entry(
            "person.zofia-ryan",
            create=True,
            cite=cite(
                YY_PAGE,
                "Mechanical [...] Gabe Hernandez, Chris Turner, Zofia Ryan",
                locator="in the Credits section",
            ),
            fields={"name": "Zofia Ryan"},
        ),
        pk.entry(
            "person.jeff-dickson",
            create=True,
            cite=cite(
                NE_PAGE, "Animation [...] Jeff Dickson", locator="in the Credits section"
            ),
            fields={"name": "Jeff Dickson"},
        ),
        pk.entry(
            "person.bradlee-ching",
            create=True,
            cite=cite(
                NE_PAGE,
                "UX Design [...] Bradlee Ching, Brad Duke",
                locator="in the Credits section",
            ),
            fields={"name": "Bradlee Ching"},
        ),
        pk.entry(
            "person.mike-grover",
            create=True,
            cite=cite(
                MA_PAGE, "Animation [...] Mike Grover", locator="in the Credits section"
            ),
            fields={"name": "Mike Grover"},
        ),
        pk.entry(
            "person.matthew-armstrong",
            create=True,
            cite=cite(
                MA_PAGE,
                "Artists [...] Matthew Armstrong, Kendall Hale, Brad Duke, "
                "Johanna Taylor, Jon Snow",
                locator="in the Credits section",
            ),
            fields={"name": "Matthew Armstrong"},
        ),
        pk.entry(
            "person.kendall-hale",
            create=True,
            cite=cite(
                MA_PAGE,
                "Artists [...] Matthew Armstrong, Kendall Hale, Brad Duke, "
                "Johanna Taylor, Jon Snow",
                locator="in the Credits section",
            ),
            fields={"name": "Kendall Hale"},
        ),
        pk.entry(
            "person.johanna-taylor",
            create=True,
            cite=cite(
                MA_PAGE,
                "Artists [...] Matthew Armstrong, Kendall Hale, Brad Duke, "
                "Johanna Taylor, Jon Snow",
                locator="in the Credits section",
            ),
            fields={"name": "Johanna Taylor"},
        ),
        pk.entry(
            "person.jon-snow",
            create=True,
            cite=cite(
                MA_PAGE,
                "Artists [...] Matthew Armstrong, Kendall Hale, Brad Duke, "
                "Johanna Taylor, Jon Snow",
                locator="in the Credits section",
            ),
            fields={"name": "Jon Snow"},
        ),
        pk.entry(
            "person.tyson-van-wagoner",
            create=True,
            cite=cite(
                MA_PAGE,
                "Toys / Sculpts [...] Tyson Van Wagoner, Gabe Hernandez",
                locator="in the Credits section",
            ),
            fields={"name": "Tyson Van Wagoner"},
        ),
        # ── The company ─────────────────────────────────────────────────
        pk.entry(
            "location.usa/tx/boerne",
            create=True,
            cite=cite(
                TL_CONTACT,
                "215 West Bandera Road Ste. 114-814 Boerne, TX 78006",
                locator="in the Mailing Address block",
            ),
            fields={"slug": "boerne", "parent": "usa/tx", "name": "Boerne"},
        ),
        pk.entry(
            "corporate-entity.turner-pinball",
            note=(
                "The corporate entity takes the legal name from the maker's "
                "own copyright line; the manufacturer keeps the trading name "
                "Turner Pinball."
            ),
            cite=cite(
                YY_PAGE,
                "© 2026 Turner Logic, LLC. All rights reserved.",
                locator="in the page footer",
            ),
            fields={"name": "Turner Logic, LLC"},
        ),
        pk.entry(
            "corporate-entity.turner-pinball",
            note=(
                "Turner Pinball's legal name is Turner Logic, LLC — every "
                "turnerpinball.com footer carries its copyright — and Turner "
                "Logic's own site publishes a Boerne, TX mailing address with "
                "the same 210-901-9955 phone number turnerpinball.com's "
                "contact page lists, tying the two sites to one company. "
                "Kineticist places the manufacturing facility in the San "
                "Antonio area, which Boerne is in. The maker's own site "
                "states no street address."
            ),
            cite=[
                cite(
                    TL_CONTACT,
                    "215 West Bandera Road Ste. 114-814 Boerne, TX 78006",
                    locator="in the Mailing Address block",
                ),
                cite(TL_CONTACT, "(210) 901-9955", locator="in the Phone block"),
                cite(CONTACT, "210-901-9955", locator="in the Call Us block"),
                cite(
                    YY_PAGE,
                    "© 2026 Turner Logic, LLC. All rights reserved.",
                    locator="in the page footer",
                ),
                cite(
                    KIN_YY,
                    "Turner recently purchased approximately 17 acres near "
                    "his current location in the San Antonio area",
                ),
            ],
            relationships={"location": ["usa/tx/boerne"]},
        ),
        # ── Yukon Yeti (Legendary Edition) ──────────────────────────────
        pk.entry(
            YY,
            note=(
                "The maker sells the machine as Yukon Yeti Legendary Edition "
                "— the Legendary Edition is the base game itself, its only "
                "edition, and the All-In Package is an upgrades bundle, not "
                "an edition — so the model takes the maker's edition name, "
                "matching the naming of Merlin's Arcade (Legendary Edition)."
            ),
            cite=[
                cite(YY_PAGE, YY_BASE_NAME, locator="in the Ordering Options section"),
                cite(
                    KIN_YY,
                    "Turner is shipping one edition rather than splitting "
                    "into Pro/Premium/LE tiers — the Legendary Edition at "
                    "$9,999, capped at 500 units",
                ),
            ],
            fields={"name": "Yukon Yeti (Legendary Edition)"},
        ),
        pk.entry(
            YY,
            note="First shipments are still expected, so the machine is announced.",
            cite=cite(YY_PAGE, YY_SHIPPING, locator="in the FAQ section"),
            fields={"production_status": "announced"},
        ),
        pk.entry(
            YY,
            cite=[
                cite(YY_PAGE, YY_500, locator="in the FAQ section"),
                cite(YY_PAGE, "Limited to 500 units."),
            ],
            fields={"production_quantity": 500},
            tags=["limited-edition"],
        ),
        pk.entry(
            YY,
            cite=cite(YY_PAGE, YY_META_DESC, locator="in the page's meta description"),
            fields={"game_format": "pinball"},
        ),
        # Credits. The page's Credits block renders as a definition list, so
        # each role/name pair is quoted as spans in source order.
        credits_entry(
            YY,
            [("dennis-nordman", "design")],
            cite(
                YY_PAGE,
                "Playfield Design [...] Dennis Nordman",
                locator="in the Credits section",
            ),
        ),
        credits_entry(
            YY,
            [
                ("brad-duke", "other"),
                ("quinn-johnson", "other"),
                ("jon-norris", "other"),
            ],
            [
                cite(
                    YY_PAGE,
                    "Ruleset Design [...] Brad Duke, Quinn Johnson, Jon Norris "
                    "[...] Story [...] Quinn Johnson",
                    locator="in the Credits section",
                ),
                cite(
                    YY_PAGE,
                    "UX Design [...] Brad Duke",
                    locator="in the Credits section",
                ),
            ],
            note=(
                "Ruleset design, story and UX design are all credited under "
                "the other role, so each person carries one such credit "
                "covering those duties."
            ),
        ),
        credits_entry(
            YY,
            [("brad-duke", "art")],
            cite(YY_PAGE, "Art [...] Brad Duke", locator="in the Credits section"),
        ),
        credits_entry(
            YY,
            [("matthew-brozusky", "animation")],
            cite(
                YY_PAGE,
                "Animation [...] Matthew Brozusky",
                locator="in the Credits section",
            ),
        ),
        credits_entry(
            YY,
            [("matthew-brozusky", "software"), ("chris-turner", "software")],
            cite(
                YY_PAGE,
                "Programming [...] Matthew Brozusky, Chris Turner",
                locator="in the Credits section",
            ),
        ),
        credits_entry(
            YY,
            [
                ("gabe-hernandez", "mechanics"),
                ("chris-turner", "mechanics"),
                ("zofia-ryan", "mechanics"),
            ],
            cite(
                YY_PAGE,
                "Mechanical [...] Gabe Hernandez, Chris Turner, Zofia Ryan",
                locator="in the Credits section",
            ),
        ),
        credits_entry(
            YY,
            [("chris-granner", "sound")],
            cite(
                YY_PAGE,
                YY_GRANNER,
                locator="in the audio-team announcement section",
            ),
            note=(
                "Announced after the March reveal — the reveal-era press "
                "coverage predates this and names no dedicated sound "
                "designer, and the page's formal Credits block, which lists "
                "no audio roles at all, predates the announcement too; the "
                "maker's own announcement is the newest statement and wins "
                "on chronology."
            ),
        ),
        credits_entry(
            YY,
            [("adam-gubman", "music"), ("adam-gubman", "sound")],
            cite(
                YY_PAGE,
                YY_GUBMAN,
                locator="in the audio-team announcement section",
            ),
        ),
        # Features — the base game's standard equipment only; the All-In
        # Package and a-la-carte upgrades (topper, shaker/knocker,
        # anti-reflective glass, art blades, speaker LEDs) are optional and
        # deliberately not asserted.
        pk.entry(
            YY,
            note=(
                "Two ball locks: the five-ball stair-step Avalanche lock and "
                "the hidden Yeti lock, so ball-locks carries no count; both "
                "feed multiballs (Avalanche Multiball on the maker page, the "
                "hidden lock's secondary multiball per Kineticist)."
            ),
            cite=[
                cite(YY_PAGE, YY_LOCK, locator="in the Playfield Overview section"),
                cite(YY_PAGE, YY_HIDDEN, locator="in the Playfield Overview section"),
                cite(KIN_YY, KIN_HIDDEN),
            ],
            relationships={"gameplay_feature": ["ball-locks", "multiball"]},
        ),
        pk.entry(
            YY,
            note=(
                "Ramps carry no count: the wavy Rapids ramp, the mine cart "
                "ramp and the Avalanche ramp leave any single total "
                "unstated."
            ),
            cite=[
                cite(YY_PAGE, YY_RAMP, locator="in the Playfield Overview section"),
                cite(YY_PAGE, YY_UPPER, locator="in the Playfield Overview section"),
            ],
            relationships={"gameplay_feature": ["ramps", "mini-playfields"]},
        ),
        pk.entry(
            YY,
            cite=cite(KIN_YY, KIN_FLIPPERS),
            relationships={"gameplay_feature": [{"flippers": 4}]},
        ),
        pk.entry(
            YY,
            note=(
                "The Yeti sculpt is the playfield centerpiece and does not "
                "move (the moving Yeti lives in the optional topper), so it "
                "classifies as a static toy."
            ),
            cite=[
                cite(YY_PAGE, YY_SCULPT, locator="in the Playfield Overview section"),
                cite(
                    KIN_YY,
                    "the Yeti sculpt on the upper playfield doesn't move",
                ),
            ],
            relationships={"gameplay_feature": ["static-toys"]},
        ),
        pk.entry(
            YY,
            cite=[
                cite(KIN_YY, KIN_SPINNER),
                cite(KIN_YY, KIN_GLACIER),
                cite(KIN_YY, KIN_POPS),
                cite(KIN_YY, KIN_TARGETS),
                cite(KIN_YY, KIN_TRAPDOOR),
            ],
            note=(
                "Hardware named by Kineticist's rules walkthrough where the "
                "maker's own page stays at mode level; the target bank's "
                "type is not stated, so the generic targets feature attaches."
            ),
            relationships={
                "gameplay_feature": [
                    "spinners",
                    "newton-balls",
                    "drop-targets",
                    "pop-bumpers",
                    "targets",
                    "trap-doors",
                ]
            },
        ),
        pk.entry(
            YY,
            cite=[
                cite(
                    YY_PAGE,
                    "Removable glass frame with standard-size tempered glass",
                    locator="in the Ordering Options base-game list",
                ),
                cite(PN_YY, PN_FINESSE),
            ],
            relationships={
                "gameplay_feature": ["removable-glass-frames", "finesse-flip"]
            },
        ),
        # ── Merlin's Arcade — both editions ─────────────────────────────
        pk.entry(
            MA_LEG,
            note=VARIANT_NOTE_MA,
            cite=[
                cite(MA_PAGE, MA_SAME_CORE, locator="in the Editions section"),
                cite(MA_PAGE, MA_FAQ_500, locator="in the Reservation terms & FAQ section"),
            ],
            fields={"variant_of": "merlins-arcade-arcade-edition"},
        ),
        pk.entry(
            MA_LEG,
            cite=[
                cite(MA_PAGE, MA_AVAIL),
                cite(
                    ABOUT,
                    MA_SHIPPED,
                    locator="in the Our Journey timeline",
                ),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            MA_ARC,
            note="Sold through and out of production — the edition shipped.",
            cite=[
                cite(MA_PAGE, MA_AVAIL),
                cite(
                    ABOUT,
                    MA_SHIPPED,
                    locator="in the Our Journey timeline",
                ),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            MA_LEG,
            note=(
                "500 is the maker's announced production cap ('no more "
                "than'), matching Pinball News's 'limited run of up to 500 "
                "units'; the numbered, certificated run takes the "
                "limited-edition tag."
            ),
            cite=[
                cite(MA_PAGE, MA_FAQ_500, locator="in the Reservation terms & FAQ section"),
                cite(
                    PN_MA,
                    "The Legendary Edition is a limited run of up to 500 "
                    "units, while the Arcade Edition has no restriction on "
                    "production.",
                ),
            ],
            fields={"production_quantity": 500},
            tags=["limited-edition"],
        ),
        pk.entry(
            MA_LEG,
            cite=cite(MA_PAGE, MA_PINBALL),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            MA_ARC,
            cite=cite(MA_PAGE, MA_PINBALL),
            fields={"game_format": "pinball"},
        ),
    ]

    # Merlin's credits: the maker's single title page covers both editions
    # (one core game in two trims), so each edition cites it directly.
    ma_credit_entries = [
        (
            [("jon-norris", "design")],
            [
                cite(
                    MA_PAGE,
                    "Playfield Design [...] Jon Norris",
                    locator="in the Credits section",
                ),
                arch(MA_OLD, MA_OLD_AR, MA_OLD_NORRIS),
            ],
            None,
        ),
        (
            [("jon-norris", "other"), ("quinn-johnson", "other")],
            [
                cite(
                    MA_PAGE,
                    "Ruleset Design [...] Jon Norris, Quinn Johnson [...] "
                    "Story Writer [...] Quinn Johnson",
                    locator="in the Credits section",
                ),
            ],
            (
                "Ruleset design and story writing are both credited under "
                "the other role."
            ),
        ),
        (
            [
                ("matthew-armstrong", "art"),
                ("kendall-hale", "art"),
                ("brad-duke", "art"),
                ("johanna-taylor", "art"),
                ("jon-snow", "art"),
            ],
            [
                cite(
                    MA_PAGE,
                    "Artists [...] Matthew Armstrong, Kendall Hale, Brad "
                    "Duke, Johanna Taylor, Jon Snow",
                    locator="in the Credits section",
                ),
            ],
            None,
        ),
        (
            [("mike-grover", "animation")],
            [
                cite(
                    MA_PAGE,
                    "Animation [...] Mike Grover",
                    locator="in the Credits section",
                ),
            ],
            None,
        ),
        (
            [("matthew-brozusky", "software"), ("chris-turner", "software")],
            [
                cite(
                    MA_PAGE,
                    "Programming [...] Matthew Brozusky, Chris Turner",
                    locator="in the Credits section",
                ),
            ],
            None,
        ),
        (
            [("brad-duke", "other"), ("chris-turner", "other")],
            [
                cite(
                    MA_PAGE,
                    "User Experience Design [...] Brad Duke, Chris Turner",
                    locator="in the Credits section",
                ),
            ],
            None,
        ),
        (
            [("gabe-hernandez", "mechanics"), ("chris-turner", "mechanics")],
            [
                cite(
                    MA_PAGE,
                    "Engineering [...] Gabe Hernandez, Chris Turner",
                    locator="in the Credits section",
                ),
            ],
            None,
        ),
    ]
    for model in (MA_ARC, MA_LEG):
        for people, cites, note in ma_credit_entries:
            entries.append(credits_entry(model, people, cites, note))

    # The Toys / Sculpts credit attaches to the Legendary Edition only: the
    # Arcade Edition ships flat plastics in place of the toys and figures,
    # so the sculpt work is not part of that trim.
    entries.append(
        credits_entry(
            MA_LEG,
            [("tyson-van-wagoner", "art"), ("gabe-hernandez", "art")],
            [
                cite(
                    MA_PAGE,
                    "Toys / Sculpts [...] Tyson Van Wagoner, Gabe Hernandez",
                    locator="in the Credits section",
                ),
            ],
            (
                "Toy and sculpt work is sculptural, so it is credited as "
                "art. The credit stays off the Arcade Edition, which ships "
                "flat plastics in place of the toys and figures."
            ),
        )
    )

    entries += [
        # Merlin's shared core-game hardware — both editions, cited to the
        # page's own explicitly-headed lists and the same-core-game statement.
        *[
            pk.entry(
                model,
                note=(
                    "The super spinners count 1 + 2: the huge foosball "
                    "knight spinner plus two additional super spinners, "
                    "listed in both editions' feature lists. The scoop and "
                    "multiballs are core-game features shared by both trims."
                ),
                cite=[
                    cite(MA_PAGE, MA_SAME_CORE, locator="in the Editions section"),
                    arch(MA_OLD, MA_OLD_AR, MA_OLD_SPINNERS),
                    cite(MA_PAGE, MA_SCOOP, locator="in the Playfield Overview section"),
                    cite(MA_PAGE, MA_FOOSBALL, locator="in the Playfield Overview section"),
                    arch(MA_OLD, MA_OLD_AR, MA_OLD_MULTIBALL),
                ],
                relationships={
                    "gameplay_feature": [{"spinners": 3}, "scoops", "multiball"]
                },
            )
            for model in (MA_ARC, MA_LEG)
        ],
        *[
            pk.entry(
                model,
                cite=[
                    cite(
                        MA_PAGE,
                        "Removable glass frame with standard-size tempered glass",
                        locator="in the Editions section's Common features list",
                    ),
                    cite(
                        MA_PAGE,
                        "Dual flipper buttons with Finesse Feature™",
                        locator="in the Editions section's Common features list",
                    ),
                ],
                relationships={
                    "gameplay_feature": ["removable-glass-frames", "finesse-flip"]
                },
            )
            for model in (MA_ARC, MA_LEG)
        ],
        # Legendary-only equipment, from the explicitly-headed Legendary
        # Edition list.
        pk.entry(
            MA_LEG,
            note=(
                "The Merlin figure moves (body and arms), so it is an "
                "animatronic toy; the Mordred and Morgan figures (glowing "
                "eyes, no stated motion), the light-up arcade machine toy, "
                "the pop bumper bobble heads and the sculpted castles state "
                "no motion or ball interaction, so they classify as static "
                "toys. The barrel ball lock is physical, with a subway."
            ),
            cite=[
                cite(
                    MA_PAGE,
                    "Merlin figure with moving body and arms [...] Mordred "
                    "and Morgan figures with glowing eyes",
                    locator="in the Legendary Edition™ features list",
                ),
                cite(
                    MA_PAGE,
                    "Light-up arcade machine toy [...] Pop bumper bobble "
                    "head toys [...] Barrel physical ball lock with subway "
                    "[...] Sculpted castles and more",
                    locator="in the Legendary Edition™ features list",
                ),
            ],
            relationships={
                "gameplay_feature": [
                    "animatronic-toys",
                    "static-toys",
                    "ball-locks",
                    "subways",
                    "pop-bumpers",
                ]
            },
        ),
        pk.entry(
            MA_LEG,
            cite=cite(
                MA_PAGE,
                "Anti-reflective glass [...] Illuminated topper",
                locator="in the Legendary Edition™ features list",
            ),
            relationships={
                "gameplay_feature": [
                    "anti-reflection-playfield-glass",
                    {"toppers": 1},
                ]
            },
        ),
        pk.entry(
            MA_LEG,
            note=(
                "The numbered, certificated Legendary run carries numbered "
                "plaques per the maker's FAQ."
            ),
            cite=cite(MA_PAGE, MA_FAQ_500, locator="in the Reservation terms & FAQ section"),
            relationships={"gameplay_feature": ["numbered-plaques"]},
        ),
        # The Arcade Edition's pop bumpers ride the shared playfield (the
        # bobble-head toys are the Legendary difference, not the bumpers).
        pk.entry(
            MA_ARC,
            note=(
                "The pop bumpers are core-game playfield hardware — the "
                "Legendary difference is the bobble-head toys sitting on "
                "them, not the bumpers themselves."
            ),
            cite=[
                cite(MA_PAGE, MA_SAME_CORE, locator="in the Editions section"),
                cite(
                    MA_PAGE,
                    "A Legendary Edition™ feature with arcade knight bobble "
                    "head toys on the pop bumpers.",
                    locator="in the Playfield Overview section",
                ),
            ],
            relationships={"gameplay_feature": ["pop-bumpers"]},
        ),
    ]

    # ── Ninja Eclipse ───────────────────────────────────────────────────
    entries += [
        pk.entry(
            NE_FIRST,
            cite=[
                cite(NE_PAGE, NE_100, locator="in the FAQ section"),
                cite(ABOUT, NE_DELIVERED, locator="in the Our Journey timeline"),
            ],
            fields={"production_status": "produced", "production_quantity": 100},
        ),
        pk.entry(
            NE_ARC,
            note=(
                "Never produced: the First Edition is the only Ninja Eclipse "
                "run ever made, and the maker discusses an Arcade Edition "
                "only as a future possibility, so the edition is announced "
                "rather than produced."
            ),
            cite=cite(NE_PAGE, NE_MAYBE, locator="in the FAQ section"),
            fields={"production_status": "announced"},
        ),
        pk.entry(
            NE_FIRST,
            cite=arch(HEROES, HEROES_AR, NE_PINBALL),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            NE_ARC,
            cite=arch(HEROES, HEROES_AR, NE_PINBALL),
            fields={"game_format": "pinball"},
        ),
    ]

    # Ninja Eclipse credits — the maker's title page names the team; the
    # design describes both catalog editions, so both cite it directly.
    ne_credit_entries = [
        (
            [("brad-duke", "design")],
            cite(
                NE_PAGE,
                "Playfield Design [...] Brad Duke",
                locator="in the Credits section",
            ),
            None,
        ),
        (
            [
                ("brad-duke", "other"),
                ("quinn-johnson", "other"),
                ("jon-norris", "other"),
                ("bradlee-ching", "other"),
            ],
            cite(
                NE_PAGE,
                "Ruleset Design [...] Brad Duke, Quinn Johnson, Jon Norris "
                "[...] Story [...] Quinn Johnson [...] UX Design [...] "
                "Bradlee Ching, Brad Duke",
                locator="in the Credits section",
            ),
            (
                "Ruleset design, story and UX design are all credited under "
                "the other role; each person carries one such credit."
            ),
        ),
        (
            [("brad-duke", "art")],
            cite(NE_PAGE, "Art [...] Brad Duke", locator="in the Credits section"),
            None,
        ),
        (
            [("jeff-dickson", "animation")],
            cite(
                NE_PAGE, "Animation [...] Jeff Dickson", locator="in the Credits section"
            ),
            None,
        ),
        (
            [("matthew-brozusky", "software"), ("chris-turner", "software")],
            cite(
                NE_PAGE,
                "Programming [...] Matthew Brozusky, Chris Turner",
                locator="in the Credits section",
            ),
            None,
        ),
        (
            [("gabe-hernandez", "mechanics"), ("chris-turner", "mechanics")],
            cite(
                NE_PAGE,
                "Mechanical [...] Gabe Hernandez, Chris Turner",
                locator="in the Credits section",
            ),
            None,
        ),
    ]
    # Credits attach to the First Edition only — the Arcade Edition was
    # never produced, and the maker's page credits the game that shipped.
    for people, cites, note in ne_credit_entries:
        entries.append(credits_entry(NE_FIRST, people, cites, note))

    entries += [
        # First Edition hardware, from the 2023 reserve-page spec sheet.
        # Attaches to the First Edition only — the Arcade Edition was never
        # produced, so asserting built hardware on it would be speculative.
        pk.entry(
            NE_FIRST,
            note=(
                "The three-ball physical lock is one lock with three-ball "
                "capacity, so ball-locks carries no count; 'Two VUKs/Scoops' "
                "is the maker's own joint label for one pair of mechanisms, "
                "recorded as scoops. The five custom sculpts are not "
                "classified — the sheet states no motion or ball interaction "
                "for them."
            ),
            cite=arch(
                NE_RESERVE,
                NE_RESERVE_AR,
                NE_SPECS,
                locator="in the PLAYFIELD FEATURES list",
            ),
            relationships={
                "gameplay_feature": [
                    {"ramps": 3},
                    {"flippers": 3},
                    "ball-locks",
                    {"drop-targets": 2},
                    {"spinners": 2},
                    {"diverters": 2},
                    {"pop-bumpers": 2},
                    {"scoops": 2},
                    {"spinning-discs": 1},
                    {"kickback": 1},
                    {"newton-balls": 1},
                    {"magnets": 1},
                ]
            },
        ),
        pk.entry(
            NE_FIRST,
            note=(
                "The 2023 sheet lists one multiball; the maker's v0.76 "
                "ruleset names Ninja Storm Multiball and Spirit Multiball, "
                "so multiball attaches without a count."
            ),
            cite=[
                arch(
                    NE_RESERVE,
                    NE_RESERVE_AR,
                    NE_GAMEPLAY,
                    locator="in the GAMEPLAY FEATURES list",
                ),
                cite(
                    "https://turnerpinball.com/rulesets/Ninja_Eclipse_Ruleset_v0.76.pdf",
                    "NINJA STORM MULTIBALL [...] SPIRIT MULTIBALL",
                    locator="PDF document page 1, in the table of contents",
                ),
            ],
            relationships={"gameplay_feature": ["multiball"]},
        ),
        pk.entry(
            NE_FIRST,
            cite=[
                cite(
                    NE_PAGE,
                    "Interior art blades [...] Badged and numbered",
                    locator="in the First Edition features list",
                ),
                cite(
                    NE_PAGE,
                    "LumaLift™ glass frame with standard-size tempered glass",
                    locator="in the Editions section's Common features list",
                ),
            ],
            relationships={
                "gameplay_feature": ["art-blades", "numbered-plaques", "lumalift"]
            },
        ),
    ]

    sources = [
        # turnerlogic.com is the legal entity's own site (same company, same
        # phone number) — attached to the existing Turner Pinball root, never
        # a new one. The match keys off the homepage recognition host;
        # missing hosts are backfilled, existing fields left alone.
        pk.source_root(
            "Turner Pinball",
            links=[("https://turnerpinball.com/", "Turner Pinball", "homepage")],
            domains=["turnerlogic.com"],
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="Turner Pinball family: Yukon Yeti, Merlin's Arcade, Ninja Eclipse",
        entries=entries,
        sources=sources,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
