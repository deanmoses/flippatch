"""Emit patch 0236 — For Amusement Only Games: the maker and all seven titles.

See ../../README.md for the campaign and ForAmusementOnlyGames.md beside this
file for the evidence inventory, the baseline, the traps and the user rulings
this generator encodes (2026-08-13).

SCOPE IS THE WHOLE MAKER: the corporate entity's legal name and Richmond, VA
location, six existing models (Ranger in the Ruins 2020, Quest for Glory 2021,
Silver Falls 2021, Drained 2022, Flipper Foxtrot Rhythm Explosion 2022,
Drained Bite-Sized 2023) and one create (Steelbound, announced 2025 — user
ruling). All are Multimorphic P3 titles by a third-party developer, so the
platform facts (system multimorphic-p3-roc, cabinet floor, game_format)
follow 0231's convention for Multimorphic's own catalog, cited to the same
platform pages.

Only missing facts are asserted; the baseline is recorded in the family notes.
Deliberately absent (each recorded there):
  display_type + technology_generation on the six      already claimed (opdb)
  year / month / player_count on the six               already claimed; QFG year
                                                       stays 2021 (user ruling)
  production_quantity                                  kits built to order, no counts published
  descriptions                                         a follow-up patch's job (the
                                                       flipcommons-ai-desc-model attribution)
  donor-module hardware on the add-on games            the conversion-kit rule:
                                                       the donor supplies it
  Silver Falls theme                                   no vocabulary fit for a life sim
  Drained "twin ball launchers"                        no clean vocabulary fit; recorded

THE KIT EDGES (user ruling): the free-text "the Multimorphic P3 platform"
edges on Drained Bite-Sized and Flipper Foxtrot are removed and replaced with
resolved donors (drained, cannon-lagoon) from the maker's own Module Required
lines. Drained's own platform-label edge stays (it is a full module kit whose
donor is genuinely the platform), and Steelbound gets the same label shape
(module-agnostic by design). patchkit's remove= only carries string members,
so the two model_relationship removes are hand-built YAML entry strings.

THE KIT CREDIT RULE (fish-tales, 2026-08-11): no credits carry from a donor
machine to a kit, so Drained Bite-Sized does NOT inherit Molly Baldridge's art
or Charles Wolf's music even though it runs on the Drained module.

DRAINED STANDUPS (user ruling): 20 per the maker's press release; Pinball
News's own count of twenty-two is the losing value, recorded in the notes.

Run: uv run python campaigns/0215-frontier-2026/model-families/for-amusement-only-games/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0236-for-amusement-only-games.yaml"

# ── Models ──────────────────────────────────────────────────────────────
CE = "corporate-entity.for-amusement-only-games"
DRAINED = "model.drained"
DBS = "model.drained-bite-sized"
FF = "model.flipper-foxtrot-rhythm-explosion"
SF = "model.silver-falls"
RITR = "model.ranger-in-the-ruins"
QFG = "model.quest-for-glory"
SB = "model.steelbound"

# ── Sources ─────────────────────────────────────────────────────────────
HOME = "https://foramusementonlygames.com/"
OG = "https://foramusementonlygames.com/othergames.html"
DR_PAGE = "https://foramusementonlygames.com/drained.html"
QFG_PAGE = "https://foramusementonlygames.com/projects/qfg.html"
ABOUT = "https://store.foramusementonlygames.com/about"
DP = "https://drainedpinball.com/"
RITR_SITE = "https://rangerintheruins.com/"
SF_SITE = "https://silverfallsforever.com/"
PN_DR = "https://www.pinballnews.com/site/2022/11/21/drained-launched"
PN_DBS = "https://www.pinballnews.com/site/2023/10/02/drained-bite-sized"
PN_SB = "https://www.pinballnews.com/site/2025/07/01/steelbound-announced"
PS_FF = "https://pinside.com/pinball/forum/topic/p3-game-flipper-foxtrot-rhythm-explosion"
TWIP = "https://twip.kineticist.com/p/this-week-in-pinball-march-30th-2020"
MM_HW = "https://www.multimorphic.com/p3-pinball-platform/hardware-control-system"
MM_FAQ = "https://www.multimorphic.com/p3-pinball-platform/frequently-asked-questions-faq"
ST_DBS = "https://www.multimorphic.com/store/p3-game-kits/3rd-party-game-kits/drained-bite-sized"
ST_FF = "https://www.multimorphic.com/store/p3-game-kits/3rd-party-game-kits/flipper-foxtrot"
ST_SB = "https://store.foramusementonlygames.com/shop/steelbound/EYI3UAH5QNOG5S2COPV7O5EX"

PR_LOC = "in the manufacturer's press release reprinted verbatim in the article"


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


# ── Shared platform quotes (same citation base as 0231) ─────────────────
HW_BOARDS = (
    "The P3 Pinball Platform is built on top of our P3-ROC, PD-16, PD-LED, "
    "and SW-16 boards"
)
FAQ_PHYSICAL = (
    "REAL and PHYSICAL! The P3 is the same size/shape as traditional pinball "
    "machines"
)
CABINET_NOTE = (
    "The maker states the P3 platform matches traditional pinball machine "
    "dimensions, so the floor cabinet classification follows from the stated "
    "size and shape."
)


def system_entry(model: str, module_cite: dict[str, str], how: str) -> str:
    """The per-model system claim: the game's own P3 statement + the platform's
    control-system statement."""
    return pk.entry(
        model,
        note=(
            f"{how} The P3 platform is built on the maker's P3-ROC control "
            "system, so the system follows for every game running on it."
        ),
        cite=[module_cite, cite(MM_HW, HW_BOARDS)],
        fields={"system": "multimorphic-p3-roc"},
    )


def cabinet_entry(model: str) -> str:
    return pk.entry(
        model,
        note=CABINET_NOTE,
        cite=cite(MM_FAQ, FAQ_PHYSICAL),
        fields={"cabinet": "floor"},
    )


def remove_label_edge(model: str, note: str) -> str:
    """A hand-built entry removing the model's free-text platform kit edge.

    patchkit's remove= emits only string members, and a model_relationship
    remove is keyed by an explicit-key mapping (the label slot), so this one
    block is authored directly. Indentation matches patchkit's entry layout.
    """
    return "\n".join(
        [
            f"  - {model}:",
            f"      note: {pk.yamlq(note)}",
            "      remove:",
            "        model_relationship:",
            "          - target_label: the Multimorphic P3 platform",
        ]
    )


# ── Corporate entity ────────────────────────────────────────────────────
ABOUT_RICHMOND = (
    "For Amusement Only Games manufactures and distributes P³ pinball "
    "platforms and game kits, and many other items, in Richmond, VA. We are "
    "proud to be the only pinball manufacturer to have existed in Richmond!"
)
FOOTER_ADDRESS = "Address: 3301 Rosedale Ave Ste D, Richmond, VA 23230"
PR_RICHMOND = (
    "The company manufactures game kits in Richmond, Va., and ships to "
    "customers worldwide."
)
FOOTER_LLC = "Copyright © For Amusement Only Games, LLC"
PR_LLC = "the all-new game game kit from For Amusement Only Games LLC (FAOG)"

# ── People quotes ───────────────────────────────────────────────────────
PR_FIRSTKIT = (
    "The first third-party combination of a game and playfield module for "
    "the P3 pinball platform has been announced by game developer, podcaster "
    "and bingo expert, Nick Baldridge."
)
PR_OWNER = "said Nicholas Baldridge, owner of FAOG and designer of Drained"
ART_MOLLY = (
    "The physical and digital artwork is by Molly Baldridge, while the "
    "extensive soundtrack – featuring 54 unique songs composed specifically "
    "for the game – is by Charles Wolf Music."
)
SB_TEAM = (
    "Steelbound is the work of Nick and his talented team, including Jon "
    "Chad on artwork, Soliu Jamiu on character and 3D model animations, and "
    "Charles Wolf who composed and performed the soundtrack."
)
SF_CREATOR = (
    "Silver Falls is the latest game from Nick Baldridge, creator of Ranger "
    "In The Ruins, and his first collaboration with Sophia Baldridge"
)
PS_SOPHIA = (
    "Silver Falls (populate a house and complete various tasks as a custom "
    "avatar you design, with beautiful chillhop music by Scott Danesi, and "
    "co-designed with my daughter, Sophia)"
)
SF_DANESI = "A unique chillhop soundtrack, a first for pinball, by Scott Danesi."
QFG_HAXBY = "A second artist, Johnny Haxby, was hired to draw the backglass artwork."
QFG_ESTHER = (
    "I was lucky to work with a very talented artist named Esther Wijdevld "
    "for the 2D background paintings."
)
QFG_BEN = "Next, artist Ben Rittmann, was hired to draw the interaction and item icons."
QFG_BART = "The final artist, Bart Heinen, provided sprite animations."

PINSIDE_AUTHOR_NOTE = (
    "The Pinside post is the designer's own launch thread (author "
    "bingopodcast; Pinball News identifies the maker as 'game developer, "
    "podcaster and bingo expert, Nick Baldridge')."
)

# ── Drained quotes ──────────────────────────────────────────────────────
DR_STATUS = "In Production [...] Game Kit Available Now"
PR_LAYOUT = (
    "In Drained, players become unlikely vampire hunters through an "
    "original, symmetrical playfield layout that blends classic gameplay "
    "with cutting-edge pinball technology."
)
DR_REQUIRES = "Requires Base P3 Pinball Platform"
DBS_DEV = (
    "Developed by Nick Baldridge, the original Drained is a full-featured "
    "game which launched in November 2022."
)
DR_INHOUSE = (
    "Designed, engineered, and coded entirely in-house by For Amusement Only "
    "Games, Drained brings a humourous gothic atmosphere to the P3."
)
PR_CLASSIC = (
    "It also features classic pinball elements like a physical bell and "
    "mechanical knocker – and brings back a notorious pinball feature that "
    "hasn't been seen in nearly 60 years: the gobble hole."
)
PR_SPEC = (
    "Drained includes 15 unique vampires to hunt, seven target sequences, 54 "
    "unique songs, 75 sound effects, more than 1,300 voice-acted callouts "
    "from 17 actors, dual banks of sweepable drop targets, a pop bumper and "
    "20 standup targets, as well as a gorgeous pen-and-ink, hand-drawn art "
    "package."
)
DBS_MODULE = (
    "It comes with its very own retro-themed P3 playfield module featuring "
    "an array of standup targets, twin ball launchers, six drop targets, a "
    "pop bumper and a gobble hole."
)
DR_WING = "Wing Slings: The central bat plastic hides a secret - slingshot mechanisms!"
DP_MULTIBALL = (
    "A ball travelling from left to right or right to left count as separate "
    "shots, two separate series of combo shots for advanced players, a "
    "second ball can be launched into play to help battle the vampire or "
    "collect items."
)
PR_HEADLINE = "Slay silverball vampires in the new Drained pinball game"
DROP_BANK_NOTE = (
    "The six drop targets sit in dual sweepable banks per the press "
    "release. The press release's 20 standup targets wins over the article "
    "body's count of twenty-two (maker beats outlet; user ruling "
    "2026-08-13)."
)

# ── Add-on game quotes (othergames.html) ────────────────────────────────
OG_DBS_BLURB = (
    "Short on time but hungry for blood? Drained: Bite-Sized takes the core, "
    "satisfying kinetic flow of Drained and amplify the tension with "
    "speedrunning your vampire slaying, and an up to 16-ball multiball."
)
OG_DBS_MOD = "Module Required: Drained Playfield Module"
OG_FF_BLURB = (
    "Pinball meets rhythm game! Tap your flippers to the beat of more than "
    "30 songs from multiple genres."
)
OG_FF_MOD = "Module Required: Cannon Lagoon Playfield Module"
OG_SF_MOD = "Module Required: Heist! Playfield Module"
OG_RITR_BLURB = (
    "A retro-inspired, roguelike RPG pinball experience. Explore a ruined "
    "world, seeking the sum of all knowledge."
)
OG_RITR_WORLD = (
    "It takes the physical playfield you know and transforms it into an "
    "8-bit fantasy world."
)
OG_RITR_MOD = "Module Required: Cosmic Cart Racing Playfield Module"
OG_DIGITAL = (
    "Upon purchasing these For Amusement Only Games Originals, you will be "
    "able to download and install the game directly to your P3."
)
OG_PRICE_99 = "Low Price - Only $99"
OG_PRICE_149 = "Low Price - Only $149"

DBS_RULESET = (
    "Now Nick has released Drained: Bite-Sized which works with the same "
    "playfield module and has a similar look and feel, but features a "
    "completely different ruleset based around slaying fifteen vampires in "
    "the shortest time possible."
)
ST_DBS_REQ = "This game application requires the Drained P3 playfield module."

PRODUCED_NOTE = (
    "Sold from the maker's and Multimorphic's stores as an immediate digital "
    "download, so the game is commercially produced and sold."
)
STORE_LICENSE_NOTE = (
    "The donor module is Multimorphic's own product and the game is sold "
    "through Multimorphic's official store, which establishes the maker's "
    "authorization as a third-party developer on the platform."
)

# ── Silver Falls / Ranger quotes ────────────────────────────────────────
SF_SIM = "A Pinball Simulation for the Multimorphic P3 System"
RITR_ABOUT = (
    "You are a ranger, a wanderer in the crumbling cities of a civilization "
    "from the distant past."
)
RITR_HUMANS = (
    "As one of the last remaining humans, you fight to keep yourself alive, "
    "and hold out hope that you will find others willing to build a "
    "community."
)
RITR_AUTHOR = "author: Nick Baldridge"

# ── Quest for Glory quotes ──────────────────────────────────────────────
QFG_TITLE_TAG = "For Amusement Only Games - Quest for Glory (non-commercial/fan game)"
QFG_CONCEPT = (
    "When I (Nick) was 8 years old, I received a copy of the VGA version of "
    "a computer game called \"Quest For Glory I: So You Want To Be A "
    "Hero?\", and I was immediately enthralled."
)
QFG_CLASSES = (
    "There are three classes (fighter, magic user, and thief) to choose "
    "from, and that choice can impact solutions to puzzles and your ability "
    "(or lack thereof) with various skills."
)
QFG_LEXY = "I decided to use the Lexy Lightspeed playfield module."
QFG_PROG = "In order to program this game, I had to be quite organized."
QFG_RPG = "Pinball RPG/Adventure"
TWIP_QFG = "host Nick Baldridge is making his own P3 game called Quest For Glory"
SB_SIXTH = (
    "Steelbound is Nick Baldridge's sixth P3 project, following on from "
    "Quest for Glory, Ranger in the Ruins, Silver Falls, Flipper Foxtrot "
    "Rhythm Explosion and Drained (incorporating Drained: Bite Sized)."
)
QFG_ONEOFF_NOTE = (
    "A private fan rebuild of Sierra's PC game, published by the maker as a "
    "non-commercial project and never offered for sale, so it is a one-off "
    "rather than a produced or aftermarket machine."
)

# ── Steelbound quotes ───────────────────────────────────────────────────
SB_ANNOUNCED = (
    "The latest game from For Amusement Only Games for the Multimorphic P3 "
    "pinball platform has been announced, although it will be a while before "
    "it is available to purchase."
)
SB_DATE = "Date: July 1st, 2025"
SB_NOTYET = (
    "Although the game isn't expected to be released for several months, a "
    "number of Steelbound-branded items are available to purchase right now "
    "in the For Amusement Only Games store."
)
SB_RPG = (
    "They also get to pilot a giant robot to explore dungeons, collect "
    "treasure, and even unearth dangerous truths about the world of pinball."
)
SB_ANYMODULE = (
    "Although it can be played and completed with any of the existing P3 "
    "playfield modules installed, additional gameplay, characters, locations "
    "and music are made available depending on which module is fitted."
)
SB_MERCH = (
    "Merchandise for the pinball role-playing game: Steelbound from For "
    "Amusement Only Games, LLC."
)


def person(slug: str, name: str, spec, note: str | None = None, aliases: list[str] | None = None) -> str:
    return pk.entry(
        f"person.{slug}",
        create=True,
        note=note,
        cite=spec,
        fields={"name": name},
        relationships={"person_alias": aliases} if aliases else None,
    )


def main() -> None:
    sources = [
        # The FAOG root exists (foramusementonlygames.com); this node matches
        # it by recognition host and backfills the maker's per-game domains,
        # which currently resolve to no root.
        pk.source_root(
            "For Amusement Only Games",
            links=[("https://foramusementonlygames.com/", "For Amusement Only Games", "homepage")],
            domains=["drainedpinball.com", "rangerintheruins.com", "silverfallsforever.com"],
        ),
    ]
    entries = [
        # ── Corporate entity: legal name + Richmond, VA ─────────────────
        pk.entry(
            CE,
            note=(
                "The corporate entity takes the legal name from the maker's "
                "own copyright line and press release; the manufacturer keeps "
                "the trading name For Amusement Only Games (the Turner Logic "
                "precedent)."
            ),
            cite=[
                cite(HOME, FOOTER_LLC, locator="in the page footer"),
                cite(PN_DR, PR_LLC, locator=PR_LOC),
            ],
            fields={"name": "For Amusement Only Games, LLC"},
        ),
        pk.entry(
            CE,
            cite=[
                cite(ABOUT, ABOUT_RICHMOND, locator="in the About Us section"),
                cite(HOME, FOOTER_ADDRESS, locator="in the page footer"),
                cite(PN_DR, PR_RICHMOND, locator=PR_LOC),
            ],
            relationships={"location": ["usa/va/richmond"]},
        ),
        # ── People ──────────────────────────────────────────────────────
        person(
            "nick-baldridge",
            "Nick Baldridge",
            [
                cite(PN_DR, PR_FIRSTKIT),
                cite(PN_DR, PR_OWNER, locator=PR_LOC),
            ],
            note=(
                "Founder-designer of For Amusement Only Games; Nick per his "
                "own manual signature and most coverage, with the press "
                "release's formal Nicholas Baldridge as an alias."
            ),
            aliases=["Nicholas Baldridge"],
        ),
        person("molly-baldridge", "Molly Baldridge", cite(PN_DR, ART_MOLLY)),
        person(
            "sophia-baldridge",
            "Sophia Baldridge",
            [
                cite(SF_SITE, SF_CREATOR),
                cite(PS_FF, PS_SOPHIA, locator="in the topic's game list"),
            ],
            note=PINSIDE_AUTHOR_NOTE,
        ),
        person("charles-wolf", "Charles Wolf", cite(PN_SB, SB_TEAM)),
        person("johnny-haxby", "Johnny Haxby", cite(QFG_PAGE, QFG_HAXBY)),
        person(
            "esther-wijdevld",
            "Esther Wijdevld",
            cite(QFG_PAGE, QFG_ESTHER),
            note="Spelling as printed on the maker's own project page.",
        ),
        person("ben-rittmann", "Ben Rittmann", cite(QFG_PAGE, QFG_BEN)),
        person("bart-heinen", "Bart Heinen", cite(QFG_PAGE, QFG_BART)),
        person("jon-chad", "Jon Chad", cite(PN_SB, SB_TEAM)),
        person("soliu-jamiu", "Soliu Jamiu", cite(PN_SB, SB_TEAM)),
        # ── Drained (2022, the full module kit) ─────────────────────────
        pk.entry(
            DRAINED,
            cite=cite(DR_PAGE, DR_STATUS, locator="in the page header badges"),
            fields={"production_status": "produced"},
        ),
        pk.entry(
            DRAINED,
            cite=cite(PN_DR, PR_LAYOUT, locator=PR_LOC),
            fields={"game_format": "pinball"},
        ),
        system_entry(
            DRAINED,
            cite(DR_PAGE, DR_REQUIRES, locator="in the page header badges"),
            "The game is a playfield module kit for the P3 platform.",
        ),
        cabinet_entry(DRAINED),
        pk.entry(
            DRAINED,
            cite=cite(PN_DR, PR_OWNER, locator=PR_LOC),
            credits=[("nick-baldridge", "design")],
        ),
        pk.entry(
            DRAINED,
            note=(
                "The maker's page attributes the engineering and code to the "
                "company, whose developer is Nick Baldridge per the article's "
                "opening."
            ),
            cite=[
                cite(PN_DBS, DBS_DEV),
                cite(DR_PAGE, DR_INHOUSE, locator="in The Experience section"),
            ],
            credits=[("nick-baldridge", "software")],
        ),
        pk.entry(
            DRAINED,
            cite=cite(PN_DR, ART_MOLLY),
            credits=[("molly-baldridge", "art"), ("charles-wolf", "music")],
        ),
        pk.entry(
            DRAINED,
            cite=cite(PN_DR, PR_CLASSIC),
            relationships={"gameplay_feature": ["bells", "knockers", "gobble-holes"]},
        ),
        pk.entry(
            DRAINED,
            note=DROP_BANK_NOTE,
            cite=[
                cite(PN_DR, PR_SPEC, locator=PR_LOC),
                cite(PN_DBS, DBS_MODULE),
            ],
            relationships={
                "gameplay_feature": [
                    {"standup-targets": 20},
                    {"pop-bumpers": 1},
                    {"drop-targets": 6},
                ]
            },
        ),
        pk.entry(
            DRAINED,
            note=(
                "The Wing Slings are slingshot mechanisms concealed in the "
                "central bat plastic; the bespoke identity is a future unique "
                "feature, recorded in the family notes."
            ),
            cite=cite(DR_PAGE, DR_WING, locator="in the Unique Mechanisms list"),
            relationships={"gameplay_feature": ["slingshots"]},
        ),
        pk.entry(
            DRAINED,
            cite=cite(DP, DP_MULTIBALL, locator="in the Game Features section"),
            relationships={"gameplay_feature": ["orbits", "2-ball-multiball"]},
        ),
        pk.entry(
            DRAINED,
            cite=cite(PN_DR, PR_HEADLINE, locator=PR_LOC),
            relationships={"theme": ["vampires"]},
        ),
        # ── Drained Bite-Sized (2023, add-on on the Drained module) ─────
        pk.entry(
            DBS,
            note=PRODUCED_NOTE,
            cite=[
                cite(OG, OG_PRICE_99, locator="in the Drained: Bite-Sized panel"),
                cite(OG, OG_DIGITAL, locator="in the Digital Delivery section"),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            DBS,
            note=(
                "A software add-on ruleset for the Drained pinball module, so "
                "the machine format is pinball."
            ),
            cite=[
                cite(OG, OG_DBS_BLURB, locator="in the Drained: Bite-Sized panel"),
                cite(MM_FAQ, FAQ_PHYSICAL),
            ],
            fields={"game_format": "pinball"},
        ),
        system_entry(
            DBS,
            cite(OG, OG_DBS_MOD, locator="in the Drained: Bite-Sized panel"),
            "The game is a software add-on running on the Drained module on the P3 platform.",
        ),
        cabinet_entry(DBS),
        pk.entry(
            DBS,
            note=(
                "The donor module is the maker's own Drained playfield, so "
                "the conversion is the maker's own licensed use."
            ),
            cite=[
                cite(OG, OG_DBS_MOD, locator="in the Drained: Bite-Sized panel"),
                cite(ST_DBS, ST_DBS_REQ),
            ],
            model_relationship=[
                {
                    "target_machine": "drained",
                    "relationship_type": "conversion_kit",
                    "license_status": "licensed",
                }
            ],
        ),
        remove_label_edge(
            DBS,
            "The maker's own page names the Drained playfield module as the "
            "requirement, so the vague platform-wide conversion kit "
            "relationship comes off in favor of the resolved donor module "
            "relationship asserted here (user ruling 2026-08-13).",
        ),
        pk.entry(
            DBS,
            cite=cite(PN_DBS, DBS_RULESET),
            credits=[("nick-baldridge", "design")],
        ),
        pk.entry(
            DBS,
            cite=cite(OG, OG_DBS_BLURB, locator="in the Drained: Bite-Sized panel"),
            relationships={"theme": ["vampires"], "gameplay_feature": ["multiball"]},
        ),
        # ── Flipper Foxtrot Rhythm Explosion (2022, add-on) ─────────────
        pk.entry(
            FF,
            note=PRODUCED_NOTE,
            cite=[
                cite(OG, OG_PRICE_149, locator="in the Flipper Foxtrot panel"),
                cite(OG, OG_DIGITAL, locator="in the Digital Delivery section"),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            FF,
            cite=cite(OG, OG_FF_BLURB, locator="in the Flipper Foxtrot panel"),
            fields={"game_format": "pinball"},
        ),
        system_entry(
            FF,
            cite(OG, OG_FF_MOD, locator="in the Flipper Foxtrot panel"),
            "The game is a software add-on running on the Cannon Lagoon module on the P3 platform.",
        ),
        cabinet_entry(FF),
        pk.entry(
            FF,
            note=STORE_LICENSE_NOTE,
            cite=[
                cite(OG, OG_FF_MOD, locator="in the Flipper Foxtrot panel"),
                cite(ST_FF, "Rhythm action for your P3 system!"),
            ],
            model_relationship=[
                {
                    "target_machine": "cannon-lagoon",
                    "relationship_type": "conversion_kit",
                    "license_status": "licensed",
                }
            ],
        ),
        remove_label_edge(
            FF,
            "The maker's own page names the Cannon Lagoon playfield module "
            "as the requirement, so the vague platform-wide conversion kit "
            "relationship comes off in favor of the resolved donor module "
            "relationship asserted here (user ruling 2026-08-13).",
        ),
        pk.entry(
            FF,
            cite=cite(PN_SB, SB_SIXTH),
            credits=[("nick-baldridge", "design")],
        ),
        pk.entry(
            FF,
            cite=cite(OG, OG_FF_BLURB, locator="in the Flipper Foxtrot panel"),
            relationships={"theme": ["music"]},
        ),
        # ── Silver Falls (2021, add-on on the Heist module) ─────────────
        pk.entry(
            SF,
            note=PRODUCED_NOTE,
            cite=[
                cite(OG, OG_PRICE_149, locator="in the Silver Falls panel"),
                cite(OG, OG_DIGITAL, locator="in the Digital Delivery section"),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            SF,
            cite=cite(SF_SITE, SF_SIM, locator="in the page header"),
            fields={"game_format": "pinball"},
        ),
        system_entry(
            SF,
            cite(OG, OG_SF_MOD, locator="in the Silver Falls panel"),
            "The game is a software add-on running on the Heist module on the P3 platform.",
        ),
        cabinet_entry(SF),
        pk.entry(
            SF,
            note=PINSIDE_AUTHOR_NOTE,
            cite=[
                cite(SF_SITE, SF_CREATOR),
                cite(PS_FF, PS_SOPHIA, locator="in the topic's game list"),
            ],
            credits=[("nick-baldridge", "design"), ("sophia-baldridge", "design")],
        ),
        pk.entry(
            SF,
            cite=cite(SF_SITE, SF_DANESI, locator="in the Major Features list"),
            credits=[("scott-danesi", "music")],
        ),
        # ── Ranger in the Ruins (2020, add-on on the CCR module) ────────
        pk.entry(
            RITR,
            note=PRODUCED_NOTE,
            cite=[
                cite(OG, OG_PRICE_149, locator="in the Ranger in the Ruins panel"),
                cite(OG, OG_DIGITAL, locator="in the Digital Delivery section"),
            ],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            RITR,
            cite=cite(OG, OG_RITR_BLURB, locator="in the Ranger in the Ruins panel"),
            fields={"game_format": "pinball"},
        ),
        system_entry(
            RITR,
            cite(OG, OG_RITR_MOD, locator="in the Ranger in the Ruins panel"),
            "The game is a software add-on running on the Cosmic Cart Racing module on the P3 platform.",
        ),
        cabinet_entry(RITR),
        pk.entry(
            RITR,
            note=(
                "The per-game site's author meta tag names the designer; the "
                "Pinball News chronology confirms the game as his project."
            ),
            cite=[
                cite(RITR_SITE, RITR_AUTHOR, locator="in the page's author meta tag"),
                cite(PN_SB, SB_SIXTH),
            ],
            credits=[("nick-baldridge", "design")],
        ),
        pk.entry(
            RITR,
            cite=[
                cite(OG, OG_RITR_WORLD, locator="in the Ranger in the Ruins panel"),
                cite(RITR_SITE, RITR_ABOUT, locator="in the About RITR section"),
                cite(RITR_SITE, RITR_HUMANS, locator="in the About RITR section"),
            ],
            relationships={"theme": ["fantasy", "apocalyptic"]},
        ),
        # ── Quest for Glory (2021, private fan game on the Lexy module) ─
        pk.entry(
            QFG,
            note=QFG_ONEOFF_NOTE,
            cite=[
                cite(QFG_PAGE, QFG_TITLE_TAG, locator="in the page title"),
                cite(PN_SB, SB_SIXTH),
            ],
            fields={"production_status": "one-off"},
        ),
        pk.entry(
            QFG,
            cite=cite(QFG_PAGE, QFG_RPG, locator="in the header claims strip"),
            fields={"game_format": "pinball"},
        ),
        system_entry(
            QFG,
            cite(QFG_PAGE, QFG_LEXY, locator="in the Programming section"),
            "The game runs on the Lexy Lightspeed module on the P3 platform.",
        ),
        cabinet_entry(QFG),
        pk.entry(
            QFG,
            note=(
                "No statement establishes authorization either way: the P3 "
                "SDK is open to homebrew developers, while the game itself is "
                "a private non-commercial project."
            ),
            cite=cite(QFG_PAGE, QFG_LEXY, locator="in the Programming section"),
            model_relationship=[
                {
                    "target_machine": "lexy-lightspeed-escape-from-earth",
                    "relationship_type": "conversion_kit",
                    "license_status": "unknown",
                }
            ],
        ),
        pk.entry(
            QFG,
            cite=[
                cite(TWIP, TWIP_QFG),
                cite(QFG_PAGE, QFG_PROG, locator="in the Programming section"),
            ],
            credits=[("nick-baldridge", "design"), ("nick-baldridge", "software")],
        ),
        pk.entry(
            QFG,
            cite=[
                cite(QFG_PAGE, QFG_HAXBY),
                cite(QFG_PAGE, QFG_ESTHER),
                cite(QFG_PAGE, QFG_BEN),
            ],
            credits=[
                ("johnny-haxby", "art"),
                ("esther-wijdevld", "art"),
                ("ben-rittmann", "art"),
            ],
        ),
        pk.entry(
            QFG,
            cite=cite(QFG_PAGE, QFG_BART),
            credits=[("bart-heinen", "animation")],
        ),
        pk.entry(
            QFG,
            cite=[
                cite(QFG_PAGE, QFG_CONCEPT, locator="in The Concept section"),
                cite(QFG_PAGE, QFG_CLASSES, locator="in The Concept section"),
            ],
            relationships={"theme": ["fantasy", "video-games"]},
        ),
        # ── Steelbound (create; announced 2025, unreleased) ─────────────
        pk.entry("title.steelbound", create=True, fields={"name": "Steelbound"}),
        pk.entry(
            SB,
            create=True,
            cite=cite(PN_SB, SB_ANNOUNCED),
            fields={
                "name": "Steelbound",
                "title": "steelbound",
                "corporate_entity": "for-amusement-only-games",
                "year": 2025,
            },
        ),
        pk.entry(
            SB,
            note=(
                "The month is the announcement month; no release month "
                "exists yet."
            ),
            cite=cite(PN_SB, SB_DATE),
            fields={"month": 7},
        ),
        pk.entry(
            SB,
            note=(
                "Still unreleased as of August 2026: the maker's store "
                "carries only Steelbound merchandise and the game is absent "
                "from Multimorphic's games index."
            ),
            cite=[
                cite(PN_SB, SB_NOTYET),
                cite(ST_SB, SB_MERCH, locator="in the page's meta description"),
            ],
            fields={"production_status": "announced"},
        ),
        pk.entry(
            SB,
            note=(
                "The P3 is a computerized platform whose lower playfield is "
                "a touchscreen LCD, so the solid-state generation and LCD "
                "display follow for a P3 game."
            ),
            cite=[cite(MM_HW, HW_BOARDS), cite(MM_FAQ, FAQ_PHYSICAL)],
            fields={
                "technology_generation": "solid-state",
                "display_type": "lcd",
                "system": "multimorphic-p3-roc",
            },
        ),
        cabinet_entry(SB),
        pk.entry(
            SB,
            cite=cite(PN_SB, SB_ANNOUNCED),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            SB,
            cite=[cite(PN_SB, SB_SIXTH), cite(PN_SB, SB_TEAM)],
            credits=[
                ("nick-baldridge", "design"),
                ("jon-chad", "art"),
                ("soliu-jamiu", "animation"),
                ("charles-wolf", "music"),
            ],
        ),
        pk.entry(
            SB,
            note=(
                "Module-agnostic by design, so the conversion kit "
                "relationship targets the platform rather than one donor "
                "module, matching how Drained relates to the platform."
            ),
            cite=cite(PN_SB, SB_ANYMODULE),
            model_relationship=[
                {
                    "target_label": "the Multimorphic P3 platform",
                    "relationship_type": "conversion_kit",
                    "license_status": "unknown",
                }
            ],
        ),
        pk.entry(
            SB,
            cite=cite(PN_SB, SB_RPG),
            relationships={"theme": ["robots"]},
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="For Amusement Only Games: maker location and details across its P3 titles",
        entries=entries,
        sources=sources,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
