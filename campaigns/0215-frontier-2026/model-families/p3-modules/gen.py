"""Generator for patch 0231 — the Multimorphic P3 family: 2026 pair full, platform sweep wide.

See ../../README.md for the family split and P3Modules.md beside this file for
the evidence inventory, the catalog baseline, the traps and the decisions this
generator encodes (2026-08-13).

STATUS: patches/0231-p3-modules.yaml was hand-restructured by the user after
the first emit and IS THE AUTHORITATIVE ARTIFACT. This file has been synced to
reproduce that final shape, but the patch must not be regenerated over the
hand-edited file without diffing the result first.

The 2026-08-13 restructure encodes two rules (now RULEBOOK.md → Asserting
claims):
  - ONE ASSERTION PER CHANGESET: system / technology_generation / cabinet /
    game_format / display_type each get their own changeset, as do credits
    that assert different things (a Creative Director credit vs a Rules
    credit), each carrying only the cite span(s) that support it.
  - DELETE EVERY NOTE THE CITATION ALREADY CARRIES: the only notes that
    remain are reasoning no quote states — the wireform→habitrail mapping,
    static-toy classification-by-absence, the four-launches produced ladder,
    the OPDB-supplied base player count, and Portal Extended being an
    ordering option of the one Portal launch.

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
     (do NOT run over the hand-edited patch without diffing — see STATUS)
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


def credits_cite(ref: str, line: str) -> dict[str, str]:
    return cite(ref, line, locator="in the Credits section")


# ── Shared platform quotes ──────────────────────────────────────────────
HW_P3ROC = (
    "The P3 Pinball Platform is built on top of our P3-ROC, PD-16, PD-LED, "
    "and SW-16 boards"
)
# The FAQ's one answer, split so each fact carries only its own span.
FAQ_REAL_FULL = (
    "REAL and PHYSICAL! The P3 is the same size/shape as traditional pinball "
    "machines, and it has real balls, flippers, bumpers, targets, ramps, "
    "loops, etc. The P3 replaces a traditional wooden lower playfield with a "
    "touchscreen LCD"
)
FAQ_CABINET = (
    "REAL and PHYSICAL! The P3 is the same size/shape as traditional pinball "
    "machines, and it has real balls, flippers, bumpers, targets, ramps, "
    "loops, etc."
)
FAQ_FORMAT = "Is the P3 a real pinball machine or a virtual pinball machine? REAL and PHYSICAL!"
FAQ_DISPLAY = "The P3 replaces a traditional wooden lower playfield with a touchscreen LCD"

GAMES_FULLKIT_HEAD = "Full game kits with playfield modules:"
GAMES_ADDON_HEAD = "Add-on Games:"
LATE_2026 = "Production of this title begins in late 2026."

# ── The notes that survived the golden rule (reasoning no quote states) ──
HABITRAIL_NOTE = "The wireforms are habitrails (wire ball guides)."
STATIC_TOYS_NOTE = (
    "The character sculpts state no motion or ball interaction, so they "
    "classify as static toys."
)
FOUR_LAUNCHES_BASE_NOTE = (
    "The maker's last four game launches before this June 2026 statement are "
    "Weird Al's Museum of Natural Hilarity (2022), Final Resistance (2023), "
    "The Princess Bride (2024) and Portal (2025) - all orders filled means "
    "all four were produced and shipped."
)
FOUR_LAUNCHES_TPB_EDITION_NOTE = (
    "The maker's last four game launches before this June 2026 statement are "
    "Weird Al's Museum of Natural Hilarity (2022), Final Resistance (2023), "
    "The Princess Bride (2024) and Portal (2025); the editions share one "
    "production run, so this edition's orders shipped with the base's."
)
FOUR_LAUNCHES_WAL_LE_NOTE = (
    "The maker's last four game launches before this June 2026 statement are "
    "Weird Al's Museum of Natural Hilarity (2022), Final Resistance (2023), "
    "The Princess Bride (2024) and Portal (2025); the Limited Edition is an "
    "artwork package over the same machine, so its orders shipped with the "
    "base's."
)
PORTAL_EXT_NOTE = (
    "Extended is an ordering option of the same Portal launch, not a separate "
    "game, so the maker's statement that all 2025 Portal orders shipped "
    "covers Extended-configuration orders."
)
TPB_PLAYERS_NOTE = "OPDB supplies the base model's player count of 4."
WAL_LE_PLAYERS_NOTE = (
    "OPDB supplies the base model's player count of 4; the Limited Edition is "
    "an artwork package over the same machine."
)

FOUR_LAUNCHES = cite(
    NEWS_JUNE26,
    "our goal is always to fill all orders received from day-one through to "
    "the beginning of production within about a year of launch, and we've "
    "successfully done that with our last four game launches",
)
TPB_EDITIONS_SAME = "All editions include the same playfield module and game software."
WAL_LE_ARTWORK = (
    "we have created two unique Weird Al's Museum of Natural Hilarity artwork "
    "packages to decorate the machine, a Standard Edition package and a "
    "Limited Edition package"
)
PORTAL_SHIPPED = (
    "In April, approximately 13 months after launching Portal in March 2025, "
    "we finished shipping all 2025 Portal orders."
)

# People created by this patch (scaffolding; the credit assignments below
# carry the same page evidence). (slug, name, ref, credit line naming them)
EG_VOICES_LINE = (
    "Voices: Glenn Waechter, Lucas Pepke, Sam Tucker, Aline Allen, Alana Johnson, "
    "Cash Bailey, Tyson and Eli Silver"
)
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
    ("lucas-pepke", "Lucas Pepke", EG_PAGE, EG_VOICES_LINE),
    ("sam-tucker", "Sam Tucker", EG_PAGE, EG_VOICES_LINE),
    ("aline-allen", "Aline Allen", EG_PAGE, EG_VOICES_LINE),
    ("alana-johnson", "Alana Johnson", EG_PAGE, EG_VOICES_LINE),
    ("cash-bailey", "Cash Bailey", EG_PAGE, EG_VOICES_LINE),
    ("tyson-silver", "Tyson Silver", EG_PAGE, EG_VOICES_LINE),
    ("eli-silver", "Eli Silver", EG_PAGE, EG_VOICES_LINE),
]


def person(slug: str, name: str, ref: str, line: str) -> str:
    return pk.entry(
        f"person.{slug}",
        create=True,
        cite=credits_cite(ref, line),
        fields={"name": name},
    )


def game_2026(
    model: str,
    kit: str,
    membership_quote: str,
    format_quote: str,
    page: str,
    *,
    cabinet_quote: str,
    display_quote: str,
) -> list[str]:
    """The 2026 pair's shared field ladder: announced, format, tech, system,
    cabinet, display — one assertion per changeset."""
    p3 = [cite(kit, membership_quote), cite(HW, HW_P3ROC)]
    return [
        pk.entry(model, cite=cite(kit, LATE_2026), fields={"production_status": "announced"}),
        pk.entry(model, cite=cite(page, format_quote), fields={"game_format": "pinball"}),
        pk.entry(model, cite=p3, fields={"technology_generation": "solid-state"}),
        pk.entry(model, cite=p3, fields={"system": "multimorphic-p3-roc"}),
        pk.entry(model, cite=cite(FAQ, cabinet_quote), fields={"cabinet": "floor"}),
        pk.entry(model, cite=cite(FAQ, display_quote), fields={"display_type": "lcd"}),
    ]


def sweep_platform(
    model: str,
    membership: dict[str, str],
    *,
    machine: bool,
    fmt: bool = False,
    tech: bool = False,
    display: bool = False,
) -> list[str]:
    """The sweep's per-field platform changesets: each fact rides the
    membership quote plus only the span that supports it."""
    out = [
        pk.entry(
            model,
            cite=[membership, cite(HW, HW_P3ROC)],
            fields={"system": "multimorphic-p3-roc"},
        )
    ]
    if tech:
        out.append(
            pk.entry(
                model,
                cite=[membership, cite(HW, HW_P3ROC)],
                fields={"technology_generation": "solid-state"},
            )
        )
    if machine:
        out.append(
            pk.entry(
                model,
                cite=[membership, cite(FAQ, FAQ_CABINET)],
                fields={"cabinet": "floor"},
            )
        )
    if fmt:
        out.append(
            pk.entry(
                model,
                cite=[membership, cite(FAQ, FAQ_FORMAT)],
                fields={"game_format": "pinball"},
            )
        )
    if display:
        out.append(
            pk.entry(
                model,
                cite=[membership, cite(FAQ, FAQ_DISPLAY)],
                fields={"display_type": "lcd"},
            )
        )
    return out


def games_index_cite(head: str, name: str) -> dict[str, str]:
    return cite(GAMES, f"{head} [...] {name}", locator="in the games list")


def cat_row_cite(ref: str, row: str) -> dict[str, str]:
    return cite(ref, row, locator="in the store category listing")


def sold_from_stock(model: str, ref: str, row: str) -> str:
    return pk.entry(
        model,
        cite=cat_row_cite(ref, row),
        fields={"production_status": "produced"},
    )


def main() -> None:
    entries: list[str] = [
        # ── Scaffolding: the people the credit blocks name ──────────────
        *[person(*row) for row in NEW_PEOPLE],
        # ════════════════════════════════════════════════════════════════
        # Dungeon Crawler Carl (2026)
        # ════════════════════════════════════════════════════════════════
        *game_2026(
            DCC,
            DCC_KIT,
            "Enjoy Dungeon Crawler Carl on your P3 Pinball Platform!",
            "Dungeon Crawler Carl is a pinball machine based on the Dungeon "
            "Crawler Carl book series, written by Matt Dinniman.",
            DCC_PAGE,
            cabinet_quote=FAQ_CABINET,
            display_quote=FAQ_DISPLAY,
        ),
        # Credits — one credit line per changeset.
        pk.entry(
            DCC,
            cite=credits_cite(DCC_PAGE, "Creative Director: Stephen Silver and Ian Harrower"),
            credits=[("stephen-silver", "design"), ("ian-harrower", "design")],
        ),
        pk.entry(
            DCC,
            cite=credits_cite(DCC_PAGE, "Rules: Wesley Johnson"),
            credits=[("wesley-johnson", "design")],
        ),
        pk.entry(
            DCC,
            cite=credits_cite(DCC_PAGE, "Mechanicals; TJ Weaver and Trey Jones"),
            credits=[("tj-weaver", "mechanics"), ("trey-jones", "mechanics")],
        ),
        pk.entry(
            DCC,
            cite=credits_cite(DCC_PAGE, "Voices: Jeff Hays"),
            credits=[("jeff-hays", "voice")],
        ),
        pk.entry(
            DCC,
            cite=credits_cite(DCC_PAGE, "Music and Sound Design: Matt Kern"),
            credits=[("matt-kern", "music"), ("matt-kern", "sound")],
        ),
        pk.entry(
            DCC,
            cite=credits_cite(DCC_PAGE, "Software: Ian Harrower, Josh Kugler, and Michael Ocean"),
            credits=[
                ("ian-harrower", "software"),
                ("josh-kugler", "software"),
                ("michael-ocean", "software"),
            ],
        ),
        pk.entry(
            DCC,
            cite=credits_cite(
                DCC_PAGE,
                "Cabinet Artist: Luciano Fleitas Playfield Artist: Brad Albright "
                "Art Direction: Stephen Silver and Brad Albright",
            ),
            credits=[
                ("luciano-fleitas", "art"),
                ("brad-albright", "art"),
                ("stephen-silver", "art"),
            ],
        ),
        pk.entry(
            DCC,
            cite=[
                credits_cite(DCC_PAGE, "Sculpts: Stumblor Pinball"),
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
            cite=credits_cite(DCC_PAGE, "Animations: Stephen Silver and Ian Harrower"),
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
            note=HABITRAIL_NOTE,
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
            note=STATIC_TOYS_NOTE,
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
        *game_2026(
            EG,
            EG_KIT,
            "Enjoy Ender's Game on your P3 Pinball Platform!",
            "Ender's Game is a pinball machine based on the Hugo and Nebula "
            "award wining novel Ender's Game.",
            EG_PAGE,
            cabinet_quote=FAQ_REAL_FULL,
            display_quote=FAQ_REAL_FULL,
        ),
        # Credits.
        pk.entry(
            EG,
            cite=credits_cite(EG_PAGE, "Creative Director: Stephen Silver and Josh Kugler"),
            credits=[("stephen-silver", "design"), ("josh-kugler", "design")],
        ),
        pk.entry(
            EG,
            cite=credits_cite(EG_PAGE, "Rules; Colin MacAlpine"),
            credits=[("colin-macalpine", "design")],
        ),
        pk.entry(
            EG,
            cite=credits_cite(EG_PAGE, "Mechanicals; TJ Weaver and Trey Jones"),
            credits=[("tj-weaver", "mechanics"), ("trey-jones", "mechanics")],
        ),
        pk.entry(
            EG,
            cite=credits_cite(EG_PAGE, "Music: Aaron Williams and Paul Farrer"),
            credits=[("aaron-williams", "music"), ("paul-farrer", "music")],
        ),
        pk.entry(
            EG,
            cite=credits_cite(EG_PAGE, "Sound Design: Glenn Waechter"),
            credits=[("glenn-waechter", "sound")],
        ),
        pk.entry(
            EG,
            cite=credits_cite(EG_PAGE, "Software: Josh Kugler, Steve Shoyer, and Ian Harrower"),
            credits=[
                ("josh-kugler", "software"),
                ("steve-shoyer", "software"),
                ("ian-harrower", "software"),
            ],
        ),
        pk.entry(
            EG,
            cite=credits_cite(EG_PAGE, "Artist: Brad Albright Technical Artist: Rory Cernuda"),
            credits=[("brad-albright", "art"), ("rory-cernuda", "art")],
        ),
        pk.entry(
            EG,
            cite=credits_cite(EG_PAGE, "Animations: Stephen Silver and Rory Cernuda"),
            credits=[("stephen-silver", "animation"), ("rory-cernuda", "animation")],
        ),
        pk.entry(
            EG,
            cite=credits_cite(EG_PAGE, EG_VOICES_LINE),
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
            cite=cite(
                EG_PAGE,
                "you will need to moves balls in the captive ball balance "
                "mechanism to be aggressive, compassionate or perfectly balanced",
            ),
            relationships={"gameplay_feature": ["captive-ball"]},
        ),
        pk.entry(
            EG,
            note=HABITRAIL_NOTE,
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
        # ── Full game kits (machines) ───────────────────────────────────
        *sweep_platform(
            "model.lexy-lightspeed-escape-from-earth",
            games_index_cite(GAMES_FULLKIT_HEAD, "Lexy Lightspeed – Escape from Earth"),
            machine=True,
            fmt=True,
        ),
        sold_from_stock(
            "model.lexy-lightspeed-escape-from-earth",
            CAT_KITS,
            "Lexy Lightspeed – Escape From Earth $3,000.00 Add to cart",
        ),
        # Cannon Lagoon: timed cannon-lane game — no stated genre, no format.
        *sweep_platform(
            "model.cannon-lagoon",
            games_index_cite(GAMES_FULLKIT_HEAD, "Cannon Lagoon"),
            machine=True,
        ),
        sold_from_stock("model.cannon-lagoon", CAT_KITS, "Cannon Lagoon $1,800.00 Add to cart"),
        *sweep_platform(
            "model.cosmic-cart-racing",
            games_index_cite(GAMES_FULLKIT_HEAD, "Cosmic Cart Racing"),
            machine=True,
            fmt=True,
        ),
        sold_from_stock(
            "model.cosmic-cart-racing", CAT_KITS, "Cosmic Cart Racing $3,000.00 Add to cart"
        ),
        *sweep_platform(
            "model.heist",
            games_index_cite(GAMES_FULLKIT_HEAD, "Heist"),
            machine=True,
            fmt=True,
        ),
        sold_from_stock("model.heist", CAT_KITS, "Heist $3,250.00 Add to cart"),
        *sweep_platform(
            "model.weird-als-museum-of-natural-hilarity",
            games_index_cite(GAMES_FULLKIT_HEAD, "Weird Al's Museum of Natural Hilarity"),
            machine=True,
            fmt=True,
        ),
        sold_from_stock(
            "model.weird-als-museum-of-natural-hilarity",
            CAT_KITS,
            "Weird Al's Museum of Natural Hilarity $3,500.00 Add to cart",
        ),
        # Weird Al LE — artwork-package variant; platform facts carry.
        *sweep_platform(
            "model.weird-als-museum-of-natural-hilarity-limited-edition",
            cite(NEWS_WAL, WAL_LE_ARTWORK),
            machine=True,
            fmt=True,
            tech=True,
            display=True,
        ),
        pk.entry(
            "model.weird-als-museum-of-natural-hilarity-limited-edition",
            note=FOUR_LAUNCHES_WAL_LE_NOTE,
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
            note=WAL_LE_PLAYERS_NOTE,
            cite=cite(NEWS_WAL, WAL_LE_ARTWORK),
            fields={"player_count": "4"},
        ),
        *sweep_platform(
            "model.final-resistance",
            games_index_cite(GAMES_FULLKIT_HEAD, "Final Resistance"),
            machine=True,
            fmt=True,
        ),
        sold_from_stock(
            "model.final-resistance", CAT_KITS, "Final Resistance $3,400.00 Add to cart"
        ),
        *sweep_platform(
            "model.the-princess-bride",
            games_index_cite(GAMES_FULLKIT_HEAD, "The Princess Bride"),
            machine=True,
            fmt=True,
        ),
        pk.entry(
            "model.the-princess-bride",
            note=FOUR_LAUNCHES_BASE_NOTE,
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
        # TPB Collector's Edition — variant; platform facts carry.
        *sweep_platform(
            "model.the-princess-bride-collectors-edition",
            cite(NEWS_TPB, TPB_EDITIONS_SAME),
            machine=True,
            fmt=True,
            tech=True,
            display=True,
        ),
        pk.entry(
            "model.the-princess-bride-collectors-edition",
            note=FOUR_LAUNCHES_TPB_EDITION_NOTE,
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
            note=TPB_PLAYERS_NOTE,
            cite=cite(NEWS_TPB, TPB_EDITIONS_SAME),
            fields={"player_count": "4"},
        ),
        # TPB Limited Edition — variant; platform facts carry.
        *sweep_platform(
            "model.the-princess-bride-limited-edition",
            cite(NEWS_TPB, TPB_EDITIONS_SAME),
            machine=True,
            fmt=True,
            tech=True,
            display=True,
        ),
        pk.entry(
            "model.the-princess-bride-limited-edition",
            note=FOUR_LAUNCHES_TPB_EDITION_NOTE,
            cite=[cite(NEWS_TPB, TPB_EDITIONS_SAME), FOUR_LAUNCHES],
            fields={"production_status": "produced"},
        ),
        pk.entry(
            "model.the-princess-bride-limited-edition",
            note=TPB_PLAYERS_NOTE,
            cite=cite(NEWS_TPB, TPB_EDITIONS_SAME),
            fields={"player_count": "4"},
        ),
        # Portal Standard / Extended (2025)
        *sweep_platform(
            "model.portal-standard",
            cat_row_cite(CAT_KITS, "Portal Standard Game Kit (Deposit) $1,000.00"),
            machine=True,
            fmt=True,
        ),
        pk.entry(
            "model.portal-standard",
            cite=cite(NEWS_JUNE26, PORTAL_SHIPPED),
            fields={"production_status": "produced"},
        ),
        *sweep_platform(
            "model.portal-extended",
            cat_row_cite(CAT_KITS, "Portal Extended Game Kit (Deposit) $1,500.00"),
            machine=True,
            fmt=True,
        ),
        pk.entry(
            "model.portal-extended",
            note=PORTAL_EXT_NOTE,
            cite=[
                cite(NEWS_JUNE26, PORTAL_SHIPPED),
                cite(
                    PN_DCC,
                    "Portal's extended option addressed this by introducing a "
                    "ramp, kickback, diverter, and a player-controlled wall "
                    "plate and inlane feeds, amongst other features.",
                ),
            ],
            fields={"production_status": "produced"},
        ),
        # ── Add-on games: software on another game's module — system +
        #    production only (conversion-kit rule). ──────────────────────
        *sweep_platform(
            "model.barnyard",
            games_index_cite(GAMES_ADDON_HEAD, "Barnyard"),
            machine=False,
        ),
        sold_from_stock("model.barnyard", CAT_ADDONS, "Barnyard $149.00 Add to cart"),
        *sweep_platform(
            "model.lexy-lightspeed-secret-agent-showdown",
            games_index_cite(GAMES_ADDON_HEAD, "Lexy Lightspeed – Secret Agent Showdown"),
            machine=False,
        ),
        sold_from_stock(
            "model.lexy-lightspeed-secret-agent-showdown",
            CAT_ADDONS,
            "Lexy Lightspeed – Secret Agent Showdown $99.00 Add to cart",
        ),
        # Grand Slam Rally — the maker's own genre: pitch-and-bat.
        pk.entry(
            "model.grand-slam-rally",
            cite=[
                cite(
                    GSR_STORE,
                    "Grand Slam Rally is a P3 mini-game that works with the "
                    "Cannon Lagoon playfield module (sold separately).",
                ),
                cite(HW, HW_P3ROC),
            ],
            fields={"system": "multimorphic-p3-roc"},
        ),
        pk.entry(
            "model.grand-slam-rally",
            cite=cite(
                GSR_STORE,
                "Pitch-and-Bat on the P3! Grand Slam Rally is a P3 mini-game "
                "that works with the Cannon Lagoon playfield module (sold "
                "separately).",
            ),
            fields={"game_format": "pitch-and-bat"},
        ),
        pk.entry(
            "model.grand-slam-rally",
            cite=cite(GSR_STORE, "$199.00 [...] Add to cart"),
            fields={"production_status": "produced"},
        ),
        # Hoopin' It Up — free download: production_status stays unset.
        *sweep_platform(
            "model.hoopin-it-up",
            games_index_cite(GAMES_ADDON_HEAD, "Hoopin' It Up"),
            machine=False,
        ),
        *sweep_platform(
            "model.rocs",
            games_index_cite(GAMES_ADDON_HEAD, "ROCs"),
            machine=False,
        ),
        sold_from_stock("model.rocs", CAT_ADDONS, "ROCs $199.00 Add to cart"),
        *sweep_platform(
            "model.shoot-n-scoot",
            games_index_cite(GAMES_ADDON_HEAD, "Shoot 'n Scoot"),
            machine=False,
        ),
        sold_from_stock("model.shoot-n-scoot", CAT_ADDONS, "Shoot 'n Scoot $169.00 Add to cart"),
        *sweep_platform(
            "model.sorcerers-apprentice",
            games_index_cite(GAMES_ADDON_HEAD, "Sorcerer's Apprentice"),
            machine=False,
        ),
        sold_from_stock(
            "model.sorcerers-apprentice", CAT_ADDONS, "Sorcerer's Apprentice $499.00 Add to cart"
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
