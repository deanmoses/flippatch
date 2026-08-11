"""Emit patch 0222 — the Galactic Tank Force family: 2023 quartet + 2026 Victory Edition.

See ../../README.md for the family split and GalacticTankForce.md beside this
file for the evidence inventory, the catalog baseline, the traps and the
decisions this generator encodes (2026-08-10).

SCOPE IS THE WHOLE FAMILY, five models:
  2023  Galactic Tank Force — Classic / Deluxe / Limited Edition / Signature
  2026  Galactic Tank Force (Victory Edition), created bare by 0215

Only missing facts are asserted; the baseline table in GalacticTankForce.md
records what each model already holds. Deliberately absent (each recorded
there):
  themes                         user ruling 2026-08-10: leave untouched
  system / display / player_count / tech generation   no citable source
  production_status on Classic   no shipping evidence for the base edition
  LE production quantity + LE per-edition features    no clean source
  cabinet: floor                 not stated quotably; 0216/0220/0221 precedent
  magnets count                  QRG/code notes suggest ≥2 vs seeded 1; parked
  descriptions                   out of campaign scope

USER RULINGS (2026-08-10, recorded in GalacticTankForce.md → Decisions):
  actors credited with role `other` (no performer role in the taxonomy),
  plus Nordman's Nord-Man 3000 `voice` credit; the actor's surname is
  Pollitt (AP's cast post + Pinball News launch article) with Politt kept
  as an alias; Victory is `announced` (shipping merely *begins* Aug 2026);
  skill-shot ×2 and multiball ×3 counts supersede the uncounted seed
  attachments, per the manual's own rules-chapter headings.

THE LE/SIGNATURE TRAP: the live 2026 product page's "Limited" panel carries
Signature content (its add-ons block is literally headed "Signature Add
Ons"), so nothing per-edition is cited from that panel; the 2023-era
archived pages and AP's Signature announcement carry the 2023 editions.

Run: uv run python campaigns/0215-frontier-2026/model-families/galactic-tank-force/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0222-galactic-tank-force.yaml"

# ── Models ──────────────────────────────────────────────────────────────
CLASSIC = "model.galactic-tank-force-classic"
DELUXE = "model.galactic-tank-force-deluxe"
LE = "model.galactic-tank-force-limited-edition"
SIG = "model.galactic-tank-force-signature"
VIC = "model.galactic-tank-force-victory-edition"

# ── Sources ─────────────────────────────────────────────────────────────
LIVE = "https://americanpinball.com/galactic-tank-force"
VICPAGE = "https://americanpinball.com/galactic-tank-force-victory-edition"

# The 2023-era site lives on the old american-pinball.com domain, dead pages
# recovered via Wayback id_ snapshots: ref is the original publisher URL,
# archive the snapshot (RULEBOOK.md → Citation roots → archive).
PAGE23 = "https://www.american-pinball.com/games/galactic-tank-force/"
PAGE23_AR = (
    "https://web.archive.org/web/20230606065409id_/"
    "https://www.american-pinball.com/games/galactic-tank-force"
)
SLAMTILT = (
    "https://www.american-pinball.com/news/"
    "slam-tilt-podcast-interviews-the-galactic-tank-fo"
)
SLAMTILT_AR = (
    "https://web.archive.org/web/20231002204904id_/"
    "https://www.american-pinball.com/news/"
    "slam-tilt-podcast-interviews-the-galactic-tank-fo"
)
CAST = (
    "https://www.american-pinball.com/news/"
    "american-pinball-inc-with-the-stars-of-galactic-t"
)
CAST_AR = (
    "https://web.archive.org/web/20231129091706id_/"
    "https://www.american-pinball.com/news/"
    "american-pinball-inc-with-the-stars-of-galactic-t"
)
SIGANN = "https://www.american-pinball.com/news/galactic-tank-force-signature-edition"
SIGANN_AR = (
    "https://web.archive.org/web/20240229215015id_/"
    "https://www.american-pinball.com/news/galactic-tank-force-signature-edition"
)
LEGAME = (
    "https://www.american-pinball.com/news/"
    "galactic-tank-force-le-gameplay-by-flip-n-out-pin"
)
LEGAME_AR = (
    "https://web.archive.org/web/20231002201859id_/"
    "https://www.american-pinball.com/news/"
    "galactic-tank-force-le-gameplay-by-flip-n-out-pin"
)
# The GTK M13 playfield-callout flyer (JPG). Its hand transcription is filed
# in the evidence cache via web_import.py --text-file (2026-08-10), so its
# quotes verify like any text; the playfield photo includes the machine's
# printed CREDITS panel beside the shooter lane — the family's only
# first-party source naming the code, animation, engineering and audio team.
FLYER = "https://www.american-pinball.com/games/galactic-tank-force/img/GTK_M13_Flyer.jpg"
FLYER_AR = (
    "https://web.archive.org/web/20250920035317id_/"
    "https://www.american-pinball.com/games/galactic-tank-force/img/GTK_M13_Flyer.jpg"
)
FLYER_CREDITS_LOC = "the CREDITS panel printed beside the shooter lane in the playfield photo"
MANUAL = (
    "https://48804760.fs1.hubspotusercontent-na1.net/hubfs/48804760/"
    "Support%20Files/Game%20Manuals/Galactic%20Tank%20Force%20-%20Game%20Manual.pdf"
)
MANUAL_LOC = "printed page 44, PDF document page 54"
PN = "https://www.pinballnews.com/site/2023/03/22/galactic-tank-force-promo-released"
AH_SIG = (
    "https://arcadeheroes.com/2024/02/19/"
    "galactic-tank-force-signature-edition-package-now-available-from-american-pinball"
)


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
LIVE_PINBALL = (
    "Galactic Tank Force is a sci-fi pinball machine featuring a fun "
    "storyline where you must protect the cows and save the ice cream!"
)
TEAM_QUOTE = (
    "There to tell them more about the game and the process of creating it "
    "were Dennis Nordman (Design), Paul Reno (Design), Jack Haeger (Art "
    "Director), Christopher Franchi (Artist), and Steve Bowden (Rules)"
)
TEAM_NOTE = (
    "American Pinball's own team announcement. Role mappings: Art Director "
    "maps to the art role; Rules maps to the design role (rules design is "
    "game design). The team is stated for the game itself, so every edition "
    "carries the credits."
)
NORDMAN_VOICE_QUOTE = (
    "game designer Dennis Nordman appears in the game as the voice of the "
    "Nord-Man 3000 robot"
)
NORDMAN_VOICE_NOTE = (
    "Journalism (Pinball News launch coverage); no first-party statement of "
    "the robot voice was found. The voice is in the game every edition "
    "shares."
)
ACTORS_QUOTE_23 = (
    "groundbreaking live-action performances from four talented actors: "
    "Kerri Hoskins, Jeff Hoover, Mitchell Politt, and Clementine Morfoot"
)
ACTORS_QUOTE_CAST = (
    "the talented cast: (L to R) Kerri Hoskins, Jeff Hoover, Mitchell "
    "Pollitt, and Clementine Morfoot"
)
ACTORS_NOTE = (
    "The four actors perform the game's live-action display characters "
    "(Empress Annoya, Professor Plotnik, Duke Moonwalker, Captain Kyan); "
    "the credit-role taxonomy has no performer role, so the role is "
    "recorded as other (user ruling 2026-08-10). The display cast is in "
    "the game every edition shares. AP's own sources split the surname "
    "spelling; Pollitt follows AP's cast announcement (user ruling "
    "2026-08-10), with Politt kept as an alias."
)
TANK_TOY_QUOTE = (
    "It retains the signature motorized action while adding 3 embedded "
    "interactive LEDs that react during game modes and attacks."
)
TANK_TOY_NOTE = (
    "The interactive tank sculpt is the game's central toy on every "
    "edition, and American Pinball's Victory upgrade copy states the "
    "standard sculpt's signature motorized action — a toy that moves "
    "under motor power during gameplay, which is what the animatronic "
    "toy classification records (the same classification as Stern's "
    "motorized animatronic Megatron). Its bespoke identity (Model 375A "
    "battle tank) stays in the family doc's future-unique-features list."
)
DIVERTER_NOTE = (
    "The core playfield is shared by every edition. The maker's own "
    "playfield-callout flyer names both mechanisms; Pinball News' launch "
    "photo caption corroborates the player-operated diverter."
)
FLYER_CREDITS_QUOTE = (
    "Dennis Nordman & Paul Reno ... GAME DESIGN [...] Zofia Bil Ryan ... "
    "DIRECTOR OF MECH. ENGINEERING [...] Jessica Durbala & Bobby Llereza "
    "... 2D+VIDEO ART [...] Joe Schober, Casey Butler & Steve Bowden ... "
    "GAME CODE [...] Mitesh Pithva ... ENGINEERING [...] Matt Kern ... "
    "AUDIO ENGINEER"
)
FLYER_CREDITS_NOTE = (
    "The flyer's playfield photo shows the machine's printed credits "
    "panel, transcribed by hand into the evidence cache. Role mappings: "
    "GAME CODE maps to software; 2D+VIDEO ART to the animation role; "
    "DIRECTOR OF MECH. ENGINEERING and ENGINEERING to mechanics; AUDIO "
    "ENGINEER to sound. Steve Bowden thus carries both design (Rules, per "
    "the team announcement) and software (GAME CODE). The panel's "
    "remaining line, David Fix ... EXECUTIVE VICE PRESIDENT, is a "
    "corporate title with no credit role and is recorded in the family "
    "doc. The credits are printed on the game every edition shares."
)
COUNTS_QUOTE = "SKILL SHOTS (2) [...] MULTIBALL MODES (3)"
COUNTS_NOTE = (
    "The manual's rules chapter documents the game every edition shares. "
    "Supersedes an earlier ingest's uncounted skill shot and multiball "
    "attachments (user-approved 2026-08-10). The skill shot section teases "
    "further undocumented skill shots ('There are more skill shots. Can "
    "you find them all?'); the count follows the maker's own heading."
)
DELUXE_FIVE_QUOTE = (
    "Interior Side Art [...] Shaker [...] AURA Lighting [...] Magic Glass "
    "[...] Knocker"
)
DELUXE_FIVE_NOTE = (
    "The live product page's explicitly-headed Deluxe Features block. "
    "Wording mappings: Interior Side Art attaches as art blades (playfield "
    "side wall art); Shaker as shaker motor; Knocker as knocker; AURA "
    "Lighting is American Pinball's branded interactive lighting product; "
    "Magic Glass is American Pinball's branded anti-reflection playfield "
    "glass."
)
VIC_FIVE_QUOTE = (
    "Standard equipment includes interior side art, a shaker motor, AURA "
    "Lighting, Magic Glass, and a physical knocker."
)
VIC_CARRY_QUOTE = (
    "The cabinet artwork, translite, and core playfield feature the same "
    "setup of the now-retired Deluxe Edition."
)
VIC_CARRY_NOTE = (
    "American Pinball states the Victory Edition's core playfield is the "
    "Deluxe's, and the Deluxe shares the family's common playfield, so the "
    "feature set an earlier ingest recorded for the 2023 editions carries "
    "with its counts (the variant rule)."
)
# The family's seeded feature set, minus skill-shot and multiball (asserted
# with their manual counts in the shared counts entry).
VIC_CARRY_FEATURES: list[str | dict[str, int]] = [
    "auto-launch",
    {"ball-locks": 3},
    {"flippers": 2},
    {"magnets": 1},
    {"orbits": 2},
    {"pop-bumpers": 3},
    "ramps",
    "rollovers",
    {"slingshots": 2},
    {"spinners": 2},
    "standup-targets",
    {"up-posts": 1},
    {"vertical-up-kickers": 2},
]
SIG_FEATURES_QUOTE = (
    "this one-of-a-kind space tank features custom painted 'Glow Tech' toys "
    "that shift colors with the playfield lighting, Radiant Rubber Reactive "
    "Bands from TITAN, retro green powder coated metal, retro-SciFi Diamond "
    "Coated Playfield Artwork by Christopher Franchi, and a 3-Dimension "
    "Lenticular Backglass!"
)
SIG_FEATURES_NOTE = (
    "Powder coated metal attaches as cabinet armor and the 3-Dimension "
    "Lenticular Backglass as a lenticular backglass. The Glow Tech "
    "color-shifting toys and TITAN reactive bands are branded finishes "
    "recorded in the family doc's future-unique-features list, not "
    "vocabulary; the Fold-n-Fight Tank Turret cabinet is a unique feature "
    "recorded there too."
)


def family_shared(model: str, edition_note: str) -> list[str]:
    """The entries every edition gets; *edition_note* says why the value carries."""
    return [
        pk.entry(
            model,
            note=edition_note,
            cite=cite(LIVE, LIVE_PINBALL, locator="the page's meta description"),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            model,
            note=TEAM_NOTE,
            cite=arch(SLAMTILT, SLAMTILT_AR, TEAM_QUOTE),
            credits=[
                ("dennis-nordman", "design"),
                ("paul-reno", "design"),
                ("jack-haeger", "art"),
                ("christopher-franchi", "art"),
                ("steve-bowden", "design"),
            ],
        ),
        pk.entry(
            model,
            note=NORDMAN_VOICE_NOTE,
            cite=cite(PN, NORDMAN_VOICE_QUOTE),
            credits=[("dennis-nordman", "voice")],
        ),
        pk.entry(
            model,
            note=ACTORS_NOTE,
            cite=[
                arch(PAGE23, PAGE23_AR, ACTORS_QUOTE_23),
                arch(CAST, CAST_AR, ACTORS_QUOTE_CAST),
            ],
            credits=[
                ("kerri-hoskins", "other"),
                ("jeff-hoover", "other"),
                ("mitchell-pollitt", "other"),
                ("clementine-morfoot", "other"),
            ],
        ),
        pk.entry(
            model,
            note=TANK_TOY_NOTE,
            cite=cite(VICPAGE, TANK_TOY_QUOTE),
            relationships={"gameplay_feature": ["animatronic-toys"]},
        ),
        pk.entry(
            model,
            note=DIVERTER_NOTE,
            cite=[
                arch(
                    FLYER,
                    FLYER_AR,
                    "Controlled Diverter Use the third flipper button to "
                    "divert ramp shots.",
                ),
                arch(
                    FLYER,
                    FLYER_AR,
                    "UFO Moving Target Stop cows from being abducted!",
                ),
                cite(
                    PN,
                    "The player-operated ball diverter",
                    locator="photo caption in the playfield section",
                ),
            ],
            relationships={"gameplay_feature": ["diverters", "moving-targets"]},
        ),
        pk.entry(
            model,
            note=FLYER_CREDITS_NOTE,
            cite=arch(
                FLYER, FLYER_AR, FLYER_CREDITS_QUOTE, locator=FLYER_CREDITS_LOC
            ),
            credits=[
                ("joe-schober", "software"),
                ("casey-butler", "software"),
                ("steve-bowden", "software"),
                ("jessica-durbala", "animation"),
                ("bobby-llereza", "animation"),
                ("zofia-bil-ryan", "mechanics"),
                ("mitesh-pithva", "mechanics"),
                ("matt-kern", "sound"),
            ],
        ),
        pk.entry(
            model,
            note=COUNTS_NOTE,
            cite=cite(MANUAL, COUNTS_QUOTE, locator=MANUAL_LOC),
            relationships={"gameplay_feature": [{"skill-shot": 2}, {"multiball": 3}]},
        ),
    ]


EDITION_CARRY = (
    "The statement covers the game itself rather than one edition, so the "
    "value holds for this edition."
)


def main() -> None:
    entries = [
        # ── Vocabulary ──────────────────────────────────────────────────
        # AURA is American Pinball's branded interactive lighting product
        # (its store sells it as "AURA Lighting-Code Controlled" for Hot
        # Wheels, Barry O's BBQ and GTF) — the InvisiGlass pattern: a branded
        # child of the generic node, created by the family patch that
        # attaches it. No source states where on the machine AURA lives, so
        # it hangs off interactive-lighting alone rather than a location-axis
        # node (unlike Stern's cabinet/speaker Expression leaves).
        vocab("aura-lighting", "AURA Lighting", parents=["interactive-lighting"]),
        # Generic: lenticular 3D backglasses appear across makers (the
        # mirrored-backglasses analogy); AP's "3-Dimension Lenticular
        # Backglass" attaches it.
        vocab(
            "lenticular-backglasses",
            "Lenticular Backglasses",
            aliases=["Lenticular Backglass", "3D Backglass"],
        ),
        # ── People (the team post and the cast post name them) ──────────
        pk.entry(
            "person.jack-haeger",
            create=True,
            cite=arch(SLAMTILT, SLAMTILT_AR, TEAM_QUOTE),
            fields={"name": "Jack Haeger"},
        ),
        pk.entry(
            "person.steve-bowden",
            create=True,
            cite=arch(SLAMTILT, SLAMTILT_AR, TEAM_QUOTE),
            fields={"name": "Steve Bowden"},
        ),
        pk.entry(
            "person.kerri-hoskins",
            create=True,
            cite=arch(CAST, CAST_AR, ACTORS_QUOTE_CAST),
            fields={"name": "Kerri Hoskins"},
        ),
        pk.entry(
            "person.jeff-hoover",
            create=True,
            cite=arch(CAST, CAST_AR, ACTORS_QUOTE_CAST),
            fields={"name": "Jeff Hoover"},
        ),
        pk.entry(
            "person.mitchell-pollitt",
            create=True,
            note=(
                "AP's own sources split the surname: the cast announcement "
                "and Pinball News' launch article spell Pollitt, the "
                "product-page prose Politt. Pollitt per the user ruling "
                "2026-08-10; Politt kept as an alias."
            ),
            cite=arch(CAST, CAST_AR, ACTORS_QUOTE_CAST),
            fields={"name": "Mitchell Pollitt"},
            relationships={"person_alias": ["Mitchell Politt"]},
        ),
        pk.entry(
            "person.clementine-morfoot",
            create=True,
            cite=arch(CAST, CAST_AR, ACTORS_QUOTE_CAST),
            fields={"name": "Clementine Morfoot"},
        ),
        # The flyer's printed credits panel names the rest of the team.
        pk.entry(
            "person.casey-butler",
            create=True,
            cite=arch(
                FLYER,
                FLYER_AR,
                "Joe Schober, Casey Butler & Steve Bowden ... GAME CODE",
                locator=FLYER_CREDITS_LOC,
            ),
            fields={"name": "Casey Butler"},
        ),
        pk.entry(
            "person.jessica-durbala",
            create=True,
            cite=arch(
                FLYER,
                FLYER_AR,
                "Jessica Durbala & Bobby Llereza ... 2D+VIDEO ART",
                locator=FLYER_CREDITS_LOC,
            ),
            fields={"name": "Jessica Durbala"},
        ),
        pk.entry(
            "person.bobby-llereza",
            create=True,
            note=(
                "The panel's cursive print is small; the surname reading is "
                "corroborated by coverage of American Pinball's animation "
                "team pairing Jessica Durbala with Bobby Llereza."
            ),
            cite=arch(
                FLYER,
                FLYER_AR,
                "Jessica Durbala & Bobby Llereza ... 2D+VIDEO ART",
                locator=FLYER_CREDITS_LOC,
            ),
            fields={"name": "Bobby Llereza"},
        ),
        pk.entry(
            "person.zofia-bil-ryan",
            create=True,
            note=(
                "Zofia per the machine's printed credits and Pinball News' "
                "launch coverage; the Sofia spelling appears in Pinball "
                "News' Expo 2023 report and is kept as an alias."
            ),
            cite=arch(
                FLYER,
                FLYER_AR,
                "Zofia Bil Ryan ... DIRECTOR OF MECH. ENGINEERING",
                locator=FLYER_CREDITS_LOC,
            ),
            fields={"name": "Zofia Bil Ryan"},
            relationships={"person_alias": ["Sofia Bil Ryan"]},
        ),
        pk.entry(
            "person.mitesh-pithva",
            create=True,
            note=(
                "The panel's cursive print is small; the name reading is "
                "corroborated by staff listings of American Pinball's "
                "engineering team."
            ),
            cite=arch(
                FLYER,
                FLYER_AR,
                "Mitesh Pithva ... ENGINEERING",
                locator=FLYER_CREDITS_LOC,
            ),
            fields={"name": "Mitesh Pithva"},
        ),
        # ── Classic ─────────────────────────────────────────────────────
        # No production_status: no source evidences the base edition itself
        # shipping (see GalacticTankForce.md → Sought and not found).
        *family_shared(CLASSIC, EDITION_CARRY),
        # ── Deluxe ──────────────────────────────────────────────────────
        *family_shared(DELUXE, EDITION_CARRY),
        pk.entry(
            DELUXE,
            note=(
                "American Pinball's RETIRED badge and 'now-retired' wording "
                "mean the edition was produced and sold and is no longer "
                "made; a retired machine records as produced."
            ),
            cite=cite(VICPAGE, VIC_CARRY_QUOTE),
            fields={"production_status": "produced"},
        ),
        pk.entry(
            DELUXE,
            note=DELUXE_FIVE_NOTE,
            cite=cite(LIVE, DELUXE_FIVE_QUOTE, locator="the Deluxe Features block"),
            relationships={
                "gameplay_feature": [
                    "art-blades",
                    "shaker-motors",
                    "aura-lighting",
                    "magic-glass",
                    "knockers",
                ]
            },
        ),
        # ── Limited Edition ─────────────────────────────────────────────
        # Per-edition LE features (tank cabinet, treads) are unique features
        # recorded in the family doc; no clean source separates LE's extras
        # from Signature's (the live page merges the two panels).
        *family_shared(LE, EDITION_CARRY),
        pk.entry(
            LE,
            note=(
                "American Pinball's own news post (September 2023) shows "
                "gameplay of the newly released LE, so the edition was "
                "produced and sold."
            ),
            cite=arch(
                LEGAME,
                LEGAME_AR,
                "Zach shows off gameplay of the newly released Galactic "
                "Tank Force LE pinball machine",
            ),
            fields={"production_status": "produced"},
        ),
        # ── Signature ───────────────────────────────────────────────────
        *family_shared(SIG, EDITION_CARRY),
        pk.entry(
            SIG,
            note="Journalism states Signature Edition shipping began February 2024.",
            cite=cite(
                AH_SIG,
                "they have begun shipping the Signature Edition (SE) of "
                "their most recent pinball design, Galactic Tank Force",
            ),
            fields={"production_status": "produced"},
        ),
        pk.entry(
            SIG,
            cite=[
                arch(
                    SIGANN,
                    SIGANN_AR,
                    "With an exclusive production rollout of ONLY 200 units",
                ),
                cite(AH_SIG, "There are only 200 of these being made"),
            ],
            fields={"production_quantity": 200},
        ),
        pk.entry(
            SIG,
            note=SIG_FEATURES_NOTE,
            cite=arch(SIGANN, SIGANN_AR, SIG_FEATURES_QUOTE),
            relationships={
                "gameplay_feature": ["cabinet-armor", "lenticular-backglasses"]
            },
        ),
        # ── Victory Edition ─────────────────────────────────────────────
        *family_shared(VIC, EDITION_CARRY),
        pk.entry(
            VIC,
            note=(
                "The family's 2023 editions point at Classic as their base, "
                "but American Pinball states the Victory Edition's cabinet "
                "art, translite and core playfield are the Deluxe's, so its "
                "base is the Deluxe."
            ),
            cite=cite(VICPAGE, VIC_CARRY_QUOTE),
            fields={"variant_of": "galactic-tank-force-deluxe"},
        ),
        pk.entry(
            VIC,
            note=(
                "Announced per the vocabulary (officially announced but not "
                "yet shipped) as of authoring, 2026-08-10: the maker states "
                "shipping merely begins August 2026 (user ruling "
                "2026-08-10)."
            ),
            cite=cite(VICPAGE, "Shipping Begins August 2026"),
            fields={"production_status": "announced"},
        ),
        pk.entry(
            VIC,
            note=(
                "Month records the announcement/launch month, matching the "
                "2023 editions' month 3 (unveiled March 22, 2023): the "
                "Victory Edition was announced July 30, 2026."
            ),
            cite=cite(VICPAGE, "Posted 07/30/2026"),
            fields={"month": 7},
        ),
        pk.entry(
            VIC,
            note=(
                "A 100-unit individually numbered final run is a limited "
                "edition; the tag matches the family's LE and Signature "
                "editions."
            ),
            cite=cite(
                VICPAGE,
                "Just 100 units will be available and each will be "
                "individually numbered.",
            ),
            fields={"production_quantity": 100},
            tags=["limited-edition"],
        ),
        pk.entry(
            VIC,
            note=VIC_CARRY_NOTE,
            cite=cite(VICPAGE, VIC_CARRY_QUOTE),
            relationships={"gameplay_feature": VIC_CARRY_FEATURES},
        ),
        pk.entry(
            VIC,
            note=DELUXE_FIVE_NOTE.replace(
                "The live product page's explicitly-headed Deluxe Features "
                "block. ",
                "",
            ),
            cite=cite(VICPAGE, VIC_FIVE_QUOTE),
            relationships={
                "gameplay_feature": [
                    "art-blades",
                    "shaker-motors",
                    "aura-lighting",
                    "magic-glass",
                    "knockers",
                ]
            },
        ),
        pk.entry(
            VIC,
            note=(
                "The armor package attaches as cabinet armor and the lit "
                "Captain Kyan topper as a topper; the topper's identity "
                "(dual-panel acrylic, Franchi art, numbered apron) stays in "
                "the family doc's future-unique-features list."
            ),
            cite=[
                cite(
                    VICPAGE,
                    "Features an exclusive Galactic Blue armor package, "
                    "complemented by new custom blue apron and shooter lane "
                    "decals.",
                ),
                cite(
                    VICPAGE,
                    "this dual-panel acrylic topper features Captain Kyan "
                    "lit by a dedicated LED strip",
                ),
            ],
            relationships={"gameplay_feature": ["cabinet-armor", "toppers"]},
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="Galactic Tank Force family details across the American Pinball editions",
        entries=entries,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
