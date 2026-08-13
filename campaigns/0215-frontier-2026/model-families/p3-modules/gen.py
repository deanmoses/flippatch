"""Emit patch 0231 — the Multimorphic P3 family: 2026 pair full, platform sweep wide.

See ../../README.md for the family split and P3Modules.md beside this file for
the evidence inventory, the catalog baseline, the traps and the decisions this
generator encodes (2026-08-13).

SCOPE (user decisions, 2026-08-13):
  Full enrichment for Dungeon Crawler Carl and Ender's Game (revealed together
  2026-07-27; both `announced`, production planned late 2026), plus a
  platform-facts sweep across the older catalog Multimorphic models: system,
  cabinet, game_format, production_status, and evidenced production_quantity.
  No P3 chassis model; no creation of the catalog's missing P3 games.

THE PLATFORM CARRY: every P3 game references the EXISTING System
`multimorphic-p3-roc` (never re-created here), cited to the maker's
hardware-control-system page plus a per-model P3-membership quote. Machine
hardware facts (cabinet, display) assert only on games sold as machines
(full game kits); ADD-ON games are software running on another game's module
— the fish-tales conversion-kit rule keeps donor hardware off them, so they
get system + production_status only.

FORMAT JUDGMENT, NOT BLANKET: game_format: pinball only where a source calls
the game a pinball machine/game or it is a full-kit flipper game under the
FAQ's "real pinball machine" statement. Grand Slam Rally is the maker's own
"Pitch-and-Bat on the P3!" — it gets pitch-and-bat. Cannon Lagoon (timed
cannon lanes) and the remaining add-ons carry no stated genre and stay
format-less (P3Modules.md → Not asserted).

Deliberately absent (each recorded in P3Modules.md):
  month on the 2026 two                 year/month is the manufacture date;
                                        the July reveal date is not evidence
  player_count on the 2026 two          no primary source states it
  Heads Up! (all fields)                absent from the maker's live site
  production_status on Hoopin' It Up    free download; `produced` means sold
  descriptions                          a separate ai-desc patch's job
  DCC/EG shared-design link             no relationship type fits

Run: uv run python campaigns/0215-frontier-2026/model-families/p3-modules/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0231-p3-modules.yaml"

# ── Models ──────────────────────────────────────────────────────────────
DCC = "model.dungeon-crawler-carl"
EG = "model.enders-game"

# ── Sources ─────────────────────────────────────────────────────────────
DCC_PAGE = "https://www.multimorphic.com/dungeon-crawler-carl"
EG_PAGE = "https://www.multimorphic.com/enders-game"
DCC_KIT = "https://www.multimorphic.com/store/p3-game-kits/multimorphic-game-kits/dcc-game-kit"
EG_KIT = (
    "https://www.multimorphic.com/store/p3-game-kits/multimorphic-game-kits/enders-game-game-kit"
)
FAQ = "https://www.multimorphic.com/p3-pinball-platform/frequently-asked-questions-faq"
HW = "https://www.multimorphic.com/p3-pinball-platform/hardware-control-system"
GAMES = "https://www.multimorphic.com/p3-pinball-platform/games"
CAT_KITS = "https://www.multimorphic.com/category/p3-game-kits/multimorphic-game-kits"
CAT_ADDONS = "https://www.multimorphic.com/category/add-on-software/multimorphic-add-on-game-software"
NEWS_JUNE26 = "https://www.multimorphic.com/news/multimorphic-public-update-june-2026"
NEWS_TPB = "https://www.multimorphic.com/news/introducing-the-princess-bride-pinball-game"
NEWS_WAL = "https://www.multimorphic.com/news/weird-als-museum-of-natural-hilarity"
GSR_STORE = "https://www.multimorphic.com/store/p3-game-kits/3rd-party-game-kits/grand-slam-rally"
PN_DCC = "https://www.pinballnews.com/site/2026/07/27/dungeon-crawler-carl-revealed/"
PN_EG = "https://www.pinballnews.com/site/2026/07/27/enders-game-revealed/"
KIN_PORTAL = "https://www.kineticist.com/news/multimorphic-launches-portal-pinball"


def cite(ref: str, quote: str, **extra: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote, **extra}


# ── Shared platform quotes ──────────────────────────────────────────────
HW_P3ROC = (
    "The P3 Pinball Platform is built on top of our P3-ROC, PD-16, PD-LED, "
    "and SW-16 boards"
)
FAQ_REAL = (
    "REAL and PHYSICAL! The P3 is the same size/shape as traditional pinball "
    "machines, and it has real balls, flippers, bumpers, targets, ramps, "
    "loops, etc. The P3 replaces a traditional wooden lower playfield with a "
    "touchscreen LCD"
)
SYSTEM_NOTE = (
    "The P3-ROC is the control system of the P3 platform this game runs on, "
    "and a computer-controlled system makes the technology generation "
    "solid-state."
)
CABINET_NOTE = (
    "The cabinet classification follows from the maker's statement that the "
    "P3 is the same size and shape as traditional pinball machines — a "
    "standard full-size floor cabinet — and this game is sold installed in a "
    "P3 machine."
)
GAMES_FULLKIT_HEAD = "Full game kits with playfield modules:"
GAMES_ADDON_HEAD = "Add-on Games:"

LATE_2026 = "Production of this title begins in late 2026."
ANNOUNCED_NOTE = (
    "The store sells only non-refundable deposits and production has not "
    "begun, so the model is announced rather than produced."
)
# No month claims: a Model's year/month is the MANUFACTURE date, never the
# announcement (DataPatchAuthoring.md; user ruling 2026-08-13 — the first
# emit asserted the July reveal month and was hand-corrected). A future patch
# records the real month once production starts.

# ── Credits (both games' blocks quote the maker's own product pages; the
# irregular punctuation — "Mechanicals;" — is the pages' own) ────────────
CD_RULES_NOTE = (
    "The maker's Creative Director and Rules credits are game-creation "
    "leadership and ruleset design work, credited under the design role."
)
ART_MAP_NOTE = (
    "Cabinet Artist, Playfield Artist and Art Direction are all art-role "
    "credits: Fleitas the cabinet, Albright the playfield, Silver the "
    "direction."
)

# People created by this patch (scaffolding; the credit assignments below
# carry the same page evidence). (slug, name, ref, credit line naming them)
NEW_PEOPLE: list[tuple[str, str, str, str]] = [
    ("ian-harrower", "Ian Harrower", DCC_PAGE, "Creative Director: Stephen Silver and Ian Harrower"),
    ("wesley-johnson", "Wesley Johnson", DCC_PAGE, "Rules: Wesley Johnson"),
    ("trey-jones", "Trey Jones", DCC_PAGE, "Mechanicals; TJ Weaver and Trey Jones"),
    ("jeff-hays", "Jeff Hays", DCC_PAGE, "Voices: Jeff Hays"),
    ("luciano-fleitas", "Luciano Fleitas", DCC_PAGE, "Cabinet Artist: Luciano Fleitas"),
    ("brad-albright", "Brad Albright", DCC_PAGE, "Playfield Artist: Brad Albright"),
    (
        "davey-price",
        "Davey Price",
        PN_DCC,
        "All the sculpts in the game are produced by Davey Price of Stumblor Pinball Mods.",
    ),
    ("colin-macalpine", "Colin MacAlpine", EG_PAGE, "Rules; Colin MacAlpine"),
    ("steve-shoyer", "Steve Shoyer", EG_PAGE, "Software: Josh Kugler, Steve Shoyer, and Ian Harrower"),
    ("aaron-williams", "Aaron Williams", EG_PAGE, "Music: Aaron Williams and Paul Farrer"),
    ("paul-farrer", "Paul Farrer", EG_PAGE, "Music: Aaron Williams and Paul Farrer"),
    ("glenn-waechter", "Glenn Waechter", EG_PAGE, "Sound Design: Glenn Waechter"),
    (
        "lucas-pepke",
        "Lucas Pepke",
        EG_PAGE,
        "Voices: Glenn Waechter, Lucas Pepke, Sam Tucker, Aline Allen, Alana Johnson, "
        "Cash Bailey, Tyson and Eli Silver",
    ),
    (
        "sam-tucker",
        "Sam Tucker",
        EG_PAGE,
        "Voices: Glenn Waechter, Lucas Pepke, Sam Tucker, Aline Allen, Alana Johnson, "
        "Cash Bailey, Tyson and Eli Silver",
    ),
    (
        "aline-allen",
        "Aline Allen",
        EG_PAGE,
        "Voices: Glenn Waechter, Lucas Pepke, Sam Tucker, Aline Allen, Alana Johnson, "
        "Cash Bailey, Tyson and Eli Silver",
    ),
    (
        "alana-johnson",
        "Alana Johnson",
        EG_PAGE,
        "Voices: Glenn Waechter, Lucas Pepke, Sam Tucker, Aline Allen, Alana Johnson, "
        "Cash Bailey, Tyson and Eli Silver",
    ),
    (
        "cash-bailey",
        "Cash Bailey",
        EG_PAGE,
        "Voices: Glenn Waechter, Lucas Pepke, Sam Tucker, Aline Allen, Alana Johnson, "
        "Cash Bailey, Tyson and Eli Silver",
    ),
    (
        "tyson-silver",
        "Tyson Silver",
        EG_PAGE,
        "Voices: Glenn Waechter, Lucas Pepke, Sam Tucker, Aline Allen, Alana Johnson, "
        "Cash Bailey, Tyson and Eli Silver",
    ),
    (
        "eli-silver",
        "Eli Silver",
        EG_PAGE,
        "Voices: Glenn Waechter, Lucas Pepke, Sam Tucker, Aline Allen, Alana Johnson, "
        "Cash Bailey, Tyson and Eli Silver",
    ),
]
TYSON_ELI_NOTE = (
    'The credit line names them jointly as "Tyson and Eli Silver"; each is a '
    "distinct voice performer."
)


def person(slug: str, name: str, ref: str, line: str) -> str:
    note = TYSON_ELI_NOTE if slug in ("tyson-silver", "eli-silver") else None
    return pk.entry(
        f"person.{slug}",
        create=True,
        note=note,
        cite=cite(ref, line, locator="in the Credits section"),
        fields={"name": name},
    )


def platform_entry(
    model: str,
    membership: dict[str, str],
    *,
    machine: bool,
    fmt: str | None,
    extra_fields: dict[str, object] | None = None,
    extra_note: str = "",
) -> str:
    """The per-model platform changeset.

    membership: a cite dict quoting the maker naming this game as a P3 game.
    machine: full-kit games sold as P3 machines get cabinet (and the FAQ cite);
             add-on games are software on another game's module — the
             conversion-kit rule keeps donor hardware off them.
    fmt: game_format, or None where no source states a genre.
    """
    fields: dict[str, object] = {"system": "multimorphic-p3-roc"}
    cites = [membership, cite(HW, HW_P3ROC)]
    note = SYSTEM_NOTE
    if machine:
        cites.append(cite(FAQ, FAQ_REAL))
        fields["cabinet"] = "floor"
        note += " " + CABINET_NOTE
    if fmt:
        fields["game_format"] = fmt
    if extra_fields:
        fields.update(extra_fields)
    if extra_note:
        note += " " + extra_note
    return pk.entry(model, note=note, cite=cites, fields=fields)


def games_index_cite(head: str, name: str) -> dict[str, str]:
    return cite(
        GAMES,
        f"{head} [...] {name}",
        locator="in the games list",
    )


def cat_row_cite(ref: str, row: str) -> dict[str, str]:
    return cite(ref, row, locator="in the store category listing")


PRODUCED_STOCK_NOTE = (
    "The maker's store sells the game from stock at full price (no deposit, "
    "no pre-order), so the game is produced and commercially sold."
)

# ── The sweep: older Multimorphic models ────────────────────────────────
# (model, membership cite, machine?, format, production cite(s), production note)
FOUR_LAUNCHES = cite(
    NEWS_JUNE26,
    "our goal is always to fill all orders received from day-one through to "
    "the beginning of production within about a year of launch, and we've "
    "successfully done that with our last four game launches",
)
FOUR_LAUNCHES_NOTE = (
    "The maker's last four game launches before this June 2026 statement are "
    "Weird Al's Museum of Natural Hilarity (2022), Final Resistance (2023), "
    "The Princess Bride (2024) and Portal (2025) — all orders filled means "
    "all four were produced and shipped."
)
TPB_EDITIONS_SAME = "All editions include the same playfield module and game software."
TPB_EDITION_NOTE = (
    "This edition is a variant of The Princess Bride: the maker states all "
    "editions share the same playfield module and game software, so the "
    "shared design's platform facts and production carry from the base."
)
WAL_LE_ARTWORK = (
    "we have created two unique Weird Al's Museum of Natural Hilarity artwork "
    "packages to decorate the machine, a Standard Edition package and a "
    "Limited Edition package"
)
WAL_LE_NOTE = (
    "The Limited Edition is an artwork-and-accessories package over the same "
    "machine and game kit, so the shared design's platform facts and "
    "production carry from the base model."
)


def main() -> None:
    entries: list[str] = [
        # ── Scaffolding: the people the credit blocks name ──────────────
        *[person(*row) for row in NEW_PEOPLE],
        # ════════════════════════════════════════════════════════════════
        # Dungeon Crawler Carl (2026)
        # ════════════════════════════════════════════════════════════════
        pk.entry(
            DCC,
            note=ANNOUNCED_NOTE,
            cite=cite(DCC_KIT, LATE_2026),
            fields={"production_status": "announced"},
        ),
        pk.entry(
            DCC,
            cite=cite(
                DCC_PAGE,
                "Dungeon Crawler Carl is a pinball machine based on the Dungeon "
                "Crawler Carl book series, written by Matt Dinniman.",
            ),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            DCC,
            note=SYSTEM_NOTE,
            cite=[
                cite(DCC_KIT, "Enjoy Dungeon Crawler Carl on your P3 Pinball Platform!"),
                cite(HW, HW_P3ROC),
            ],
            fields={
                "system": "multimorphic-p3-roc",
                "technology_generation": "solid-state",
            },
        ),
        pk.entry(
            DCC,
            note=CABINET_NOTE + " The playfield display is the platform's LCD.",
            cite=cite(FAQ, FAQ_REAL),
            fields={"cabinet": "floor", "display_type": "lcd"},
        ),
        # Credits — the maker's own credits block, mapped role by role.
        pk.entry(
            DCC,
            note=CD_RULES_NOTE,
            cite=cite(
                DCC_PAGE,
                "Creative Director: Stephen Silver and Ian Harrower Rules: Wesley Johnson",
                locator="in the Credits section",
            ),
            credits=[
                ("stephen-silver", "design"),
                ("ian-harrower", "design"),
                ("wesley-johnson", "design"),
            ],
        ),
        pk.entry(
            DCC,
            cite=cite(
                DCC_PAGE,
                "Mechanicals; TJ Weaver and Trey Jones",
                locator="in the Credits section",
            ),
            credits=[("tj-weaver", "mechanics"), ("trey-jones", "mechanics")],
        ),
        pk.entry(
            DCC,
            cite=cite(DCC_PAGE, "Voices: Jeff Hays", locator="in the Credits section"),
            credits=[("jeff-hays", "voice")],
        ),
        pk.entry(
            DCC,
            cite=cite(
                DCC_PAGE,
                "Music and Sound Design: Matt Kern",
                locator="in the Credits section",
            ),
            credits=[("matt-kern", "music"), ("matt-kern", "sound")],
        ),
        pk.entry(
            DCC,
            cite=cite(
                DCC_PAGE,
                "Software: Ian Harrower, Josh Kugler, and Michael Ocean",
                locator="in the Credits section",
            ),
            credits=[
                ("ian-harrower", "software"),
                ("josh-kugler", "software"),
                ("michael-ocean", "software"),
            ],
        ),
        pk.entry(
            DCC,
            note=ART_MAP_NOTE,
            cite=cite(
                DCC_PAGE,
                "Cabinet Artist: Luciano Fleitas Playfield Artist: Brad Albright "
                "Art Direction: Stephen Silver and Brad Albright",
                locator="in the Credits section",
            ),
            credits=[
                ("luciano-fleitas", "art"),
                ("brad-albright", "art"),
                ("stephen-silver", "art"),
            ],
        ),
        pk.entry(
            DCC,
            note=(
                "The maker credits the sculpting studio; Pinball News names "
                "the person behind it. Sculpting is an art-role credit."
            ),
            cite=[
                cite(DCC_PAGE, "Sculpts: Stumblor Pinball", locator="in the Credits section"),
                cite(
                    PN_DCC,
                    "All the sculpts in the game are produced by Davey Price of "
                    "Stumblor Pinball Mods.",
                ),
            ],
            credits=[("davey-price", "art")],
        ),
        pk.entry(
            DCC,
            cite=cite(
                DCC_PAGE,
                "Animations: Stephen Silver and Ian Harrower",
                locator="in the Credits section",
            ),
            credits=[("stephen-silver", "animation"), ("ian-harrower", "animation")],
        ),
        # Gameplay features.
        pk.entry(
            DCC,
            cite=cite(
                DCC_KIT,
                "Dungeon Crawler Carl is designed as a 3-flipper game, including "
                "the two lower flippers and the Right Side-Target Flipper Assembly.",
            ),
            relationships={"gameplay_feature": [{"flippers": 3}]},
        ),
        pk.entry(
            DCC,
            note=(
                "The wireforms are habitrails (wire ball guides); the Safe Room "
                "scoop's upkicker is a vertical up-kicker; the lone drop target "
                "guarding it classifies as a solitary drop target."
            ),
            cite=cite(
                PN_DCC,
                "there is a left orbit lane which goes all the way around the "
                "back and exits into the right orbit lane. [...] The left ramp "
                "feeds onto a wireform which runs down the right side of the "
                "playfield, onto the clear plastic ball guide and into the right "
                "inlane. [...] In the very centre is a Safe Room scoop with an "
                "upkicker which is protected by a drop target and flanked by "
                "standup targets. [...] The centre right lane is a shallow ramp "
                "with a diverter",
            ),
            relationships={
                "gameplay_feature": [
                    "orbits",
                    "ramps",
                    "habitrails",
                    "scoops",
                    "vertical-up-kickers",
                    "solitary-drop-targets",
                    "standup-targets",
                    "ramp-diverters",
                ]
            },
        ),
        pk.entry(
            DCC,
            note=(
                "The disk cannon is a ball cannon; the grab/accelerator and "
                "player-controlled disruptor magnets are magnets; the inlane "
                "SlingLock blockers and the Mongo Cage lock balls, and the cage "
                "doubles as a captive ball while building toward multiball."
            ),
            cite=cite(
                PN_DCC,
                "a cannon which can be loaded and fired at playfield-level shots "
                "[...] both inlanes now incorporate blockers which can be used "
                "to lock and release balls. [...] This magnet can grab the ball "
                "when certain features, such as the boss battles, begin. [...] "
                "six round standup targets with a central player-controlled "
                "disruptor magnet [...] the Mongo Cage can also act as a captive "
                "ball, or it can become a ball lock when building towards "
                "multiball",
            ),
            relationships={
                "gameplay_feature": [
                    "ball-cannons",
                    "ball-locks",
                    "magnets",
                    "captive-ball",
                    "multiball",
                ]
            },
        ),
        pk.entry(
            DCC,
            note=(
                "The character sculpts state no motion or ball interaction, so "
                "they classify as static toys; the rotating disk mech and Mongo "
                "Cage identities stay in the family worklist as bespoke one-off "
                "mechanisms."
            ),
            cite=cite(
                PN_DCC,
                "There are four character sculpts – Carl, Samantha, Donut and "
                "Mongo, along with a giant sculpt for the dungeon.",
            ),
            relationships={"gameplay_feature": ["static-toys"]},
        ),
        # ════════════════════════════════════════════════════════════════
        # Ender's Game (2026)
        # ════════════════════════════════════════════════════════════════
        pk.entry(
            EG,
            note=ANNOUNCED_NOTE,
            cite=cite(EG_KIT, LATE_2026),
            fields={"production_status": "announced"},
        ),
        pk.entry(
            EG,
            cite=cite(
                EG_PAGE,
                "Ender's Game is a pinball machine based on the Hugo and Nebula "
                "award wining novel Ender's Game.",
            ),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            EG,
            note=SYSTEM_NOTE,
            cite=[
                cite(EG_KIT, "Enjoy Ender's Game on your P3 Pinball Platform!"),
                cite(HW, HW_P3ROC),
            ],
            fields={
                "system": "multimorphic-p3-roc",
                "technology_generation": "solid-state",
            },
        ),
        pk.entry(
            EG,
            note=CABINET_NOTE + " The playfield display is the platform's LCD.",
            cite=cite(FAQ, FAQ_REAL),
            fields={"cabinet": "floor", "display_type": "lcd"},
        ),
        # Credits.
        pk.entry(
            EG,
            note=CD_RULES_NOTE,
            cite=cite(
                EG_PAGE,
                "Creative Director: Stephen Silver and Josh Kugler Rules; Colin MacAlpine",
                locator="in the Credits section",
            ),
            credits=[
                ("stephen-silver", "design"),
                ("josh-kugler", "design"),
                ("colin-macalpine", "design"),
            ],
        ),
        pk.entry(
            EG,
            cite=cite(
                EG_PAGE,
                "Mechanicals; TJ Weaver and Trey Jones",
                locator="in the Credits section",
            ),
            credits=[("tj-weaver", "mechanics"), ("trey-jones", "mechanics")],
        ),
        pk.entry(
            EG,
            cite=cite(
                EG_PAGE,
                "Music: Aaron Williams and Paul Farrer",
                locator="in the Credits section",
            ),
            credits=[("aaron-williams", "music"), ("paul-farrer", "music")],
        ),
        pk.entry(
            EG,
            cite=cite(
                EG_PAGE,
                "Sound Design: Glenn Waechter",
                locator="in the Credits section",
            ),
            credits=[("glenn-waechter", "sound")],
        ),
        pk.entry(
            EG,
            cite=cite(
                EG_PAGE,
                "Software: Josh Kugler, Steve Shoyer, and Ian Harrower",
                locator="in the Credits section",
            ),
            credits=[
                ("josh-kugler", "software"),
                ("steve-shoyer", "software"),
                ("ian-harrower", "software"),
            ],
        ),
        pk.entry(
            EG,
            note=(
                "Artist and Technical Artist are both art-role credits; Brad "
                "Albright created the full art package, Rory Cernuda the "
                "technical art."
            ),
            cite=cite(
                EG_PAGE,
                "Artist: Brad Albright Technical Artist: Rory Cernuda",
                locator="in the Credits section",
            ),
            credits=[("brad-albright", "art"), ("rory-cernuda", "art")],
        ),
        pk.entry(
            EG,
            cite=cite(
                EG_PAGE,
                "Animations: Stephen Silver and Rory Cernuda",
                locator="in the Credits section",
            ),
            credits=[("stephen-silver", "animation"), ("rory-cernuda", "animation")],
        ),
        pk.entry(
            EG,
            note=TYSON_ELI_NOTE,
            cite=cite(
                EG_PAGE,
                "Voices: Glenn Waechter, Lucas Pepke, Sam Tucker, Aline Allen, "
                "Alana Johnson, Cash Bailey, Tyson and Eli Silver",
                locator="in the Credits section",
            ),
            credits=[
                ("glenn-waechter", "voice"),
                ("lucas-pepke", "voice"),
                ("sam-tucker", "voice"),
                ("aline-allen", "voice"),
                ("alana-johnson", "voice"),
                ("cash-bailey", "voice"),
                ("tyson-silver", "voice"),
                ("eli-silver", "voice"),
            ],
        ),
        # Gameplay features.
        pk.entry(
            EG,
            cite=cite(
                EG_PAGE,
                "Ender's Game is a 3-flipper game and therefore requires a "
                "Right Side-Target Flipper Assembly.",
            ),
            relationships={"gameplay_feature": [{"flippers": 3}]},
        ),
        pk.entry(
            EG,
            note=(
                "The captive ball balance mechanism is the maker's own naming; "
                "the balls held in it classify as captive balls."
            ),
            cite=cite(
                EG_PAGE,
                "you will need to moves balls in the captive ball balance "
                "mechanism to be aggressive, compassionate or perfectly balanced",
            ),
            relationships={"gameplay_feature": ["captive-ball"]},
        ),
        pk.entry(
            EG,
            note=(
                "The wireforms are habitrails (wire ball guides); the centre "
                "scoop's upkicker is a vertical up-kicker; the lone drop target "
                "guarding it classifies as a solitary drop target."
            ),
            cite=cite(
                PN_EG,
                "there is a left orbit lane which goes all the way around the "
                "back and exits into the right orbit lane. [...] The left ramp "
                "feeds onto a wireform which runs down the right side of the "
                "playfield, onto the clear plastic ball guide and into the right "
                "inlane. [...] In the very centre is a scoop with an upkicker "
                "which is protected by a drop target and flanked by standup "
                "targets. [...] The centre right lane is a shallow ramp which "
                "can either feeds the grab magnet on the raised ramp, or a "
                "diverter can send the ball back down the right orbit lane",
            ),
            relationships={
                "gameplay_feature": [
                    "orbits",
                    "ramps",
                    "habitrails",
                    "scoops",
                    "vertical-up-kickers",
                    "solitary-drop-targets",
                    "standup-targets",
                    "ramp-diverters",
                ]
            },
        ),
        pk.entry(
            EG,
            note=(
                "The disk cannon is a ball cannon; the grab/accelerator and "
                "player-controlled disruptor magnets are magnets; the "
                "energised-slingshot inlane blocker is a ball lock. The disk "
                "mech, Fight Ring and Valentine/Peter ball-stacker identities "
                "stay in the family worklist as bespoke one-off mechanisms."
            ),
            cite=cite(
                PN_EG,
                "This magnet can grab the ball when certain battles begin [...] "
                "six round standup targets with a central player-controlled "
                "disruptor magnet [...] Once a ball is loaded into the cannon, "
                "the disk rotates to either allow the game fire the ball towards "
                "a required shot or, at other times, allow the player to choose "
                "their shot and fire the ball themselves. [...] As long as the "
                "slingshot is energised, the ball is held in the inlane. This "
                "can be used to hold it during a mode introduction, to help the "
                "player align their shots, or longer term as a ball lock.",
            ),
            relationships={
                "gameplay_feature": ["magnets", "ball-cannons", "ball-locks"]
            },
        ),
        # ════════════════════════════════════════════════════════════════
        # The sweep: older Multimorphic models
        # ════════════════════════════════════════════════════════════════
        # ── Full game kits (machines): platform facts + production ──────
        # Lexy Lightspeed — Escape from Earth (2017)
        platform_entry(
            "model.lexy-lightspeed-escape-from-earth",
            games_index_cite(GAMES_FULLKIT_HEAD, "Lexy Lightspeed – Escape from Earth"),
            machine=True,
            fmt="pinball",
        ),
        pk.entry(
            "model.lexy-lightspeed-escape-from-earth",
            note=PRODUCED_STOCK_NOTE,
            cite=cat_row_cite(
                CAT_KITS, "Lexy Lightspeed – Escape From Earth $3,000.00 Add to cart"
            ),
            fields={"production_status": "produced"},
        ),
        # Cannon Lagoon (2017) — timed cannon-lane game: no stated genre, so
        # no game_format (P3Modules.md → Not asserted).
        platform_entry(
            "model.cannon-lagoon",
            games_index_cite(GAMES_FULLKIT_HEAD, "Cannon Lagoon"),
            machine=True,
            fmt=None,
        ),
        pk.entry(
            "model.cannon-lagoon",
            note=PRODUCED_STOCK_NOTE,
            cite=cat_row_cite(CAT_KITS, "Cannon Lagoon $1,800.00 Add to cart"),
            fields={"production_status": "produced"},
        ),
        # Cosmic Cart Racing (2018)
        platform_entry(
            "model.cosmic-cart-racing",
            games_index_cite(GAMES_FULLKIT_HEAD, "Cosmic Cart Racing"),
            machine=True,
            fmt="pinball",
        ),
        pk.entry(
            "model.cosmic-cart-racing",
            note=PRODUCED_STOCK_NOTE,
            cite=cat_row_cite(CAT_KITS, "Cosmic Cart Racing $3,000.00 Add to cart"),
            fields={"production_status": "produced"},
        ),
        # Heist (2020)
        platform_entry(
            "model.heist",
            games_index_cite(GAMES_FULLKIT_HEAD, "Heist"),
            machine=True,
            fmt="pinball",
        ),
        pk.entry(
            "model.heist",
            note=PRODUCED_STOCK_NOTE,
            cite=cat_row_cite(CAT_KITS, "Heist $3,250.00 Add to cart"),
            fields={"production_status": "produced"},
        ),
        # Weird Al's Museum of Natural Hilarity (2022)
        platform_entry(
            "model.weird-als-museum-of-natural-hilarity",
            games_index_cite(
                GAMES_FULLKIT_HEAD, "Weird Al's Museum of Natural Hilarity"
            ),
            machine=True,
            fmt="pinball",
        ),
        pk.entry(
            "model.weird-als-museum-of-natural-hilarity",
            note=PRODUCED_STOCK_NOTE,
            cite=cat_row_cite(
                CAT_KITS, "Weird Al's Museum of Natural Hilarity $3,500.00 Add to cart"
            ),
            fields={"production_status": "produced"},
        ),
        # Weird Al LE (2022) — artwork-package variant; platform facts carry.
        platform_entry(
            "model.weird-als-museum-of-natural-hilarity-limited-edition",
            cite(NEWS_WAL, WAL_LE_ARTWORK),
            machine=True,
            fmt="pinball",
            extra_fields={
                "display_type": "lcd",
                "technology_generation": "solid-state",
            },
            extra_note=WAL_LE_NOTE,
        ),
        pk.entry(
            "model.weird-als-museum-of-natural-hilarity-limited-edition",
            note=WAL_LE_NOTE,
            cite=[cite(NEWS_WAL, WAL_LE_ARTWORK), FOUR_LAUNCHES],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            "model.weird-als-museum-of-natural-hilarity-limited-edition",
            cite=cite(
                NEWS_WAL,
                "The Limited Edition package, which also includes an interactive "
                "and motorized machine topper, a printed translite autographed "
                "by Weird Al, and various game-specific accessory items, is "
                "limited to 227 copies.",
            ),
            fields={"production_quantity": 227},
        ),
        pk.entry(
            "model.weird-als-museum-of-natural-hilarity-limited-edition",
            note=(
                "The base model records a player count of 4, a fact OPDB supplies for the base edition; "
                + WAL_LE_NOTE
            ),
            cite=cite(NEWS_WAL, WAL_LE_ARTWORK),
            fields={"player_count": "4"},
        ),
        # Final Resistance (2023)
        platform_entry(
            "model.final-resistance",
            games_index_cite(GAMES_FULLKIT_HEAD, "Final Resistance"),
            machine=True,
            fmt="pinball",
        ),
        pk.entry(
            "model.final-resistance",
            note=PRODUCED_STOCK_NOTE,
            cite=cat_row_cite(CAT_KITS, "Final Resistance $3,400.00 Add to cart"),
            fields={"production_status": "produced"},
        ),
        # The Princess Bride (2024)
        platform_entry(
            "model.the-princess-bride",
            games_index_cite(GAMES_FULLKIT_HEAD, "The Princess Bride"),
            machine=True,
            fmt="pinball",
        ),
        pk.entry(
            "model.the-princess-bride",
            note=FOUR_LAUNCHES_NOTE,
            cite=[
                FOUR_LAUNCHES,
                cite(
                    KIN_PORTAL,
                    "This follows their last major release, The Princess Bride, "
                    "last year",
                ),
            ],
            fields={"production_status": "produced"},
        ),
        # TPB Collector's Edition (2024) — variant; platform facts carry.
        platform_entry(
            "model.the-princess-bride-collectors-edition",
            cite(NEWS_TPB, TPB_EDITIONS_SAME),
            machine=True,
            fmt="pinball",
            extra_fields={
                "display_type": "lcd",
                "technology_generation": "solid-state",
            },
            extra_note=TPB_EDITION_NOTE,
        ),
        pk.entry(
            "model.the-princess-bride-collectors-edition",
            note=TPB_EDITION_NOTE + " " + FOUR_LAUNCHES_NOTE,
            cite=[cite(NEWS_TPB, TPB_EDITIONS_SAME), FOUR_LAUNCHES],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            "model.the-princess-bride-collectors-edition",
            cite=cite(
                NEWS_TPB,
                "The Collector's Edition (limited to only 500 units) is the "
                "ultimate collectible for a superfan of the film",
            ),
            fields={"production_quantity": 500},
        ),
        pk.entry(
            "model.the-princess-bride-collectors-edition",
            note=(
                "The base model records a player count of 4, a fact OPDB supplies for the base edition; "
                + TPB_EDITION_NOTE
            ),
            cite=cite(NEWS_TPB, TPB_EDITIONS_SAME),
            fields={"player_count": "4"},
        ),
        # TPB Limited Edition (2024) — variant; platform facts carry.
        platform_entry(
            "model.the-princess-bride-limited-edition",
            cite(NEWS_TPB, TPB_EDITIONS_SAME),
            machine=True,
            fmt="pinball",
            extra_fields={
                "display_type": "lcd",
                "technology_generation": "solid-state",
            },
            extra_note=TPB_EDITION_NOTE,
        ),
        pk.entry(
            "model.the-princess-bride-limited-edition",
            note=TPB_EDITION_NOTE + " " + FOUR_LAUNCHES_NOTE,
            cite=[cite(NEWS_TPB, TPB_EDITIONS_SAME), FOUR_LAUNCHES],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            "model.the-princess-bride-limited-edition",
            note=(
                "The base model records a player count of 4, a fact OPDB supplies for the base edition; "
                + TPB_EDITION_NOTE
            ),
            cite=cite(NEWS_TPB, TPB_EDITIONS_SAME),
            fields={"player_count": "4"},
        ),
        # Portal Standard / Extended (2025)
        platform_entry(
            "model.portal-standard",
            cat_row_cite(CAT_KITS, "Portal Standard Game Kit (Deposit) $1,000.00"),
            machine=True,
            fmt="pinball",
        ),
        pk.entry(
            "model.portal-standard",
            cite=cite(
                NEWS_JUNE26,
                "In April, approximately 13 months after launching Portal in "
                "March 2025, we finished shipping all 2025 Portal orders.",
            ),
            fields={"production_status": "produced"},
        ),
        platform_entry(
            "model.portal-extended",
            cat_row_cite(CAT_KITS, "Portal Extended Game Kit (Deposit) $1,500.00"),
            machine=True,
            fmt="pinball",
        ),
        pk.entry(
            "model.portal-extended",
            note=(
                "Extended is an ordering option of the same Portal launch, not "
                "a separate game, so the maker's statement that all 2025 Portal "
                "orders shipped covers Extended-configuration orders."
            ),
            cite=[
                cite(
                    NEWS_JUNE26,
                    "In April, approximately 13 months after launching Portal in "
                    "March 2025, we finished shipping all 2025 Portal orders.",
                ),
                cite(
                    PN_DCC,
                    "Portal's extended option addressed this by introducing a "
                    "ramp, kickback, diverter, and a player-controlled wall "
                    "plate and inlane feeds, amongst other features.",
                ),
            ],
            fields={"production_status": "produced"},
        ),
        # ── Add-on games (software on another game's module): system +
        #    production only — the conversion-kit rule keeps donor hardware
        #    (cabinet, display) off them. ─────────────────────────────────
        # Barnyard (2017)
        platform_entry(
            "model.barnyard",
            games_index_cite(GAMES_ADDON_HEAD, "Barnyard"),
            machine=False,
            fmt=None,
        ),
        pk.entry(
            "model.barnyard",
            note=PRODUCED_STOCK_NOTE,
            cite=cat_row_cite(CAT_ADDONS, "Barnyard $149.00 Add to cart"),
            fields={"production_status": "produced"},
        ),
        # Lexy Lightspeed — Secret Agent Showdown (2017)
        platform_entry(
            "model.lexy-lightspeed-secret-agent-showdown",
            games_index_cite(
                GAMES_ADDON_HEAD, "Lexy Lightspeed – Secret Agent Showdown"
            ),
            machine=False,
            fmt=None,
        ),
        pk.entry(
            "model.lexy-lightspeed-secret-agent-showdown",
            note=PRODUCED_STOCK_NOTE,
            cite=cat_row_cite(
                CAT_ADDONS,
                "Lexy Lightspeed – Secret Agent Showdown $99.00 Add to cart",
            ),
            fields={"production_status": "produced"},
        ),
        # Grand Slam Rally (2018) — the maker's own genre: pitch-and-bat.
        pk.entry(
            "model.grand-slam-rally",
            note=(
                SYSTEM_NOTE
                + " The maker's store bills the game as pitch-and-bat, so the "
                "game format follows the maker's own genre naming."
            ),
            cite=[
                cite(
                    GSR_STORE,
                    "Pitch-and-Bat on the P3! Grand Slam Rally is a P3 mini-game "
                    "that works with the Cannon Lagoon playfield module (sold "
                    "separately).",
                ),
                cite(HW, HW_P3ROC),
            ],
            fields={
                "system": "multimorphic-p3-roc",
                "game_format": "pitch-and-bat",
            },
        ),
        pk.entry(
            "model.grand-slam-rally",
            note=PRODUCED_STOCK_NOTE,
            cite=cite(GSR_STORE, "$199.00 [...] Add to cart"),
            fields={"production_status": "produced"},
        ),
        # Hoopin' It Up (2019) — free download: production_status stays unset
        # (P3Modules.md → Not asserted); system still asserts.
        platform_entry(
            "model.hoopin-it-up",
            games_index_cite(GAMES_ADDON_HEAD, "Hoopin' It Up"),
            machine=False,
            fmt=None,
        ),
        # ROCs (2020)
        platform_entry(
            "model.rocs",
            games_index_cite(GAMES_ADDON_HEAD, "ROCs"),
            machine=False,
            fmt=None,
        ),
        pk.entry(
            "model.rocs",
            note=PRODUCED_STOCK_NOTE,
            cite=cat_row_cite(CAT_ADDONS, "ROCs $199.00 Add to cart"),
            fields={"production_status": "produced"},
        ),
        # Shoot 'n Scoot (2020)
        platform_entry(
            "model.shoot-n-scoot",
            games_index_cite(GAMES_ADDON_HEAD, "Shoot 'n Scoot"),
            machine=False,
            fmt=None,
        ),
        pk.entry(
            "model.shoot-n-scoot",
            note=PRODUCED_STOCK_NOTE,
            cite=cat_row_cite(CAT_ADDONS, "Shoot 'n Scoot $169.00 Add to cart"),
            fields={"production_status": "produced"},
        ),
        # Sorcerer's Apprentice (2021)
        platform_entry(
            "model.sorcerers-apprentice",
            games_index_cite(GAMES_ADDON_HEAD, "Sorcerer's Apprentice"),
            machine=False,
            fmt=None,
        ),
        pk.entry(
            "model.sorcerers-apprentice",
            note=PRODUCED_STOCK_NOTE,
            cite=cat_row_cite(CAT_ADDONS, "Sorcerer's Apprentice $499.00 Add to cart"),
            fields={"production_status": "produced"},
        ),
        # Heads Up! (2021): absent from the maker's live site — nothing
        # asserted (P3Modules.md → Sought and not found).
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="Multimorphic P3 family: 2026 pair enriched plus platform facts",
        entries=entries,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
