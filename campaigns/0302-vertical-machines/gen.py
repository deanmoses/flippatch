#!/usr/bin/env python3
"""Emit the vertical-playfield patches: 0303, 0304, 0311 and 0314.

0302 is hand-maintained -- it was generated once and then edited, so nothing here
writes it.

IPDB's `Vertical Pinball Machine` specialty describes a playfield ORIENTATION,
not a footprint: IPDB hangs it on floor uprights, counter games and wall boxes
alike, and on eleven models it sits beside `Table Top/Counter Game` on the same
listing. So the specialty lands as a tag, and each model's cabinet is a separate
per-model reading of the evidence -- which is why the table below is literal
rather than derived: there is no rule to run, only 27 sources read one by one.

    uv run python campaigns/0302-vertical-machines/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import patchkit as pk  # noqa: E402

PATCHES = Path(__file__).resolve().parents[2] / "patches"


def emit(path: Path, **kwargs: object) -> None:
    """Write only if the rendered text differs — an identical rewrite still bumps
    mtime, which `make db-patch-state` reads as a patch edited since it applied."""
    text = pk.render_patch(**kwargs)  # type: ignore[arg-type]
    if not path.exists() or path.read_text() != text:
        path.write_text(text)
        print(f"  wrote {path.name}")

PINSIDE = "https://pinside.com/pinball/forum/topic/4-in-1"
AUCTION = (
    "https://www.liveauctioneers.com/price-result/"
    "zingo-5-cent-vertical-cabinet-arcade-machine"
)
ENCYCLOPEDIA = (
    "https://www.encyclopedia.com/sports-and-everyday-life/games/"
    "games-and-hobbies/pinball"
)

FOURINONE_QUOTE = '30" tall x 22" wide x 9.25 deep. Unique bar or counter top game'
GENCO_UPRIGHT = "This is an upright game with a vertical playfield."

# slug -> IPDB id. Every model IPDB marks `Vertical Pinball Machine`.
VERTICAL: dict[str, int] = {
    "2005-world-car-racing-pinball": 6270,
    "4-in-1-pigskin-2010": 6010,
    "4-in-1-poker": 6009,
    "4-in-1-willy-at-the-bat": 6008,
    "4-in-1-willys-cup": 6011,
    "400": 934,
    "bat-a-ball": 6022,
    "boomerang-2": 6042,
    "bouncing-ball": 4837,
    "bowling-alle-neune": 6037,
    "catch-n-match": 472,
    "chuck-o-luck": 511,
    "flik-flak": 5613,
    "golden-nugget": 1054,
    "jumpin-jacks-2": 1330,
    "junior-league-bat-a-ball": 4675,
    "match-ball-wall-flipper": 7046,
    "mini-baseball": 5985,
    "pee-wee-2": 5527,
    "pickwick": 5431,
    "silver-chest": 2145,
    "sky-line": 6047,
    "still-crazy": 3730,
    "unknown-13": 5714,
    "whizz": 3544,
    "whoopee-ball": 5726,
    "zingo-2": 3578,
}

# slug -> (cabinet, cite, note). A model absent here keeps no cabinet: its
# sources describe the playfield and say nothing about how the machine stood.
CABINET: dict[str, tuple[str, object, str | None]] = {
    # --- upright: the playfield stands, and so does the machine -------------
    "400": ("upright", {"ref": "ipdb:934", "quote": GENCO_UPRIGHT}, None),
    "golden-nugget": ("upright", {"ref": "ipdb:1054", "quote": GENCO_UPRIGHT}, None),
    "jumpin-jacks-2": ("upright", {"ref": "ipdb:1330", "quote": GENCO_UPRIGHT}, None),
    "silver-chest": ("upright", {"ref": "ipdb:2145", "quote": GENCO_UPRIGHT}, None),
    "sky-line": ("upright", {"ref": "ipdb:6047", "quote": GENCO_UPRIGHT}, None),
    "bat-a-ball": (
        "upright",
        {"ref": "ipdb:6022", "quote": "This is a floor-standing upright game."},
        None,
    ),
    "boomerang-2": (
        "upright",
        {
            "ref": "ipdb:6042",
            "quote": "Cabinet measures 84 inches high, 21 inches wide, and 18 inches deep.",
        },
        None,
    ),
    "2005-world-car-racing-pinball": (
        "upright",
        {
            "ref": "ipdb:6270",
            "quote": (
                "Vertical cabinet measured 71 1/2 inches high, 22 inches wide, "
                "and 26 inches deep."
            ),
        },
        None,
    ),
    "still-crazy": (
        "upright",
        {
            "ref": "ipdb:3730",
            "quote": (
                "it was just too difficult to control the balls via the four "
                "flippers over the large vertical playfield"
            ),
        },
        "Four flippers across a playfield its own designers called large rules out "
        "a counter machine, leaving a floor-standing cabinet with the playfield "
        "turned vertical.",
    ),
    "zingo-2": (
        "upright",
        {
            "ref": AUCTION,
            "quote": (
                "Zingo 5 Cent Vertical Cabinet Arcade Machine. Chicago: Williams "
                "Mfg. Co., ca. 1944. Five cents for five balls. 86 x 22"
            ),
        },
        "At 86 inches it stands on the floor.",
    ),
    # Wall boxes: hung rather than stood, but upright all the same.
    "flik-flak": (
        "upright",
        {
            "ref": "ipdb:5613",
            "quote": "This is a wall-mounted game with a vertical playfield.",
        },
        None,
    ),
    "match-ball-wall-flipper": (
        "upright",
        {"ref": "ipdb:7046", "quote": "This game mounts onto a wall."},
        None,
    ),
    "mini-baseball": (
        "upright",
        {
            "ref": "ipdb:5985",
            "quote": "Can mount on wall or be placed on an optional console base",
        },
        None,
    ),
    "pickwick": (
        "upright",
        [
            {
                "ref": ENCYCLOPEDIA,
                "quote": (
                    "His game was called Pickwick, and was different from most of "
                    "its predecessors in that it was mounted vertically on a wall, "
                    "instead of inclined on a table."
                ),
            },
            {"ref": "ipdb:5431", "quote": "Vertical playfield bagatelle."},
        ],
        "Pickwick hung on a wall rather than lying on a table; this Gamages "
        "machine is one of the models built to that design.",
    ),
    # --- countertop: small enough to sit on a bar --------------------------
    "chuck-o-luck": (
        "countertop",
        {
            "ref": "ipdb:511",
            "quote": (
                "This is a table top game with a vertical playfield. Its height "
                "has been listed at 14 inches"
            ),
        },
        "Fourteen inches puts it among the smallest bar machines rather than "
        "among the two-to-four-foot miniatures of full-sized games.",
    ),
    "whoopee-ball": (
        "countertop",
        {
            "ref": "ipdb:5726",
            "quote": (
                "Game measures 14 1/4 inches high, 9 inches wide, 7 inches deep "
                "at the bottom"
            ),
        },
        None,
    ),
    "pee-wee-2": (
        "countertop",
        {
            "ref": "ipdb:5527",
            "quote": (
                "Game measures approximately 24 inches high, 14 inches wide, and "
                "7 inches deep."
            ),
        },
        None,
    ),
    "whizz": (
        "countertop",
        {
            "ref": "ipdb:3544",
            "quote": "The game can be detached from the pedestal to use as a counter game.",
        },
        "Sold on a 38-inch pedestal that brings it to 62 inches, but the game "
        "lifts off it and works on a counter.",
    ),
    "junior-league-bat-a-ball": (
        "countertop",
        {
            "ref": "ipdb:4675",
            "quote": "This counter game was available with a floor stand for an additional charge.",
        },
        None,
    ),
    "catch-n-match": (
        "countertop",
        {
            "ref": "ipdb:472",
            "quote": "Guide to Vintage Trade Stimulators & Counter Games, page 177",
        },
        "A penny-and-nickel machine worked by handles on its side and front, "
        "photographed in a guide to counter games rather than to floor machines.",
    ),
    "bowling-alle-neune": (
        "countertop",
        {
            "ref": "ipdb:6037",
            "quote": "Cabinet measures 28 inches high, 22 inches wide, and 9 inches deep.",
        },
        None,
    ),
    "unknown-13": (
        "countertop",
        {
            "ref": "ipdb:5714",
            "quote": (
                "Cabinet measured 23 inches high, 12 inches wide, and 10 1/2 "
                "inches deep."
            ),
        },
        None,
    ),
    "4-in-1-poker": (
        "countertop",
        {"ref": PINSIDE, "quote": FOURINONE_QUOTE},
        None,
    ),
    "4-in-1-willy-at-the-bat": (
        "countertop",
        {"ref": PINSIDE, "quote": FOURINONE_QUOTE},
        None,
    ),
    "4-in-1-pigskin-2010": (
        "countertop",
        {"ref": PINSIDE, "quote": FOURINONE_QUOTE},
        None,
    ),
    "4-in-1-willys-cup": (
        "countertop",
        {"ref": PINSIDE, "quote": FOURINONE_QUOTE},
        None,
    ),
}

unknown = set(CABINET) - set(VERTICAL)
if unknown:
    raise SystemExit(f"cabinet rows for models not in the population: {sorted(unknown)}")


def write_features() -> None:
    entries = [
        pk.entry(
            f"model.{slug}",
            cite={
                "ref": f"ipdb:{ipdb_id}",
                "quote": "Specialty: [...] Vertical Pinball Machine",
            },
            relationships={"gameplay_feature": ["vertical-playfields"]},
        )
        for slug, ipdb_id in sorted(VERTICAL.items())
    ]
    emit(
        PATCHES / "0303-vertical-playfield-machines.yaml",
        attribution="ipdb",
        description="Machines IPDB marks as having a vertical playfield.",
        entries=entries,
    )


def write_cabinets() -> None:
    entries = [
        pk.entry(
            f"model.{slug}",
            note=note,
            cite=cite,
            fields={"cabinet": cabinet},
        )
        for slug, (cabinet, cite, note) in sorted(CABINET.items())
    ]
    # This is the first patch to cite either root, so it seeds them.
    sources = [
        pk.source_root(
            "LiveAuctioneers",
            description="Auction marketplace whose sold-lot records carry cataloguers' machine descriptions and measurements.",
            links=[("https://www.liveauctioneers.com/", "LiveAuctioneers", "homepage")],
        ),
        pk.source_root(
            "Encyclopedia.com",
            description="Reference aggregator republishing encyclopedia and subject-dictionary articles.",
            links=[("https://www.encyclopedia.com/", "Encyclopedia.com", "homepage")],
        ),
    ]
    emit(
        PATCHES / "0304-vertical-playfield-cabinets.yaml",
        attribution="flipcommons-catalog",
        description="Cabinet form factors for the vertical-playfield machines.",
        entries=entries,
        sources=sources,
    )




# ── 0314-0316: the tag becomes a gameplay feature ────────────────────────────
#
# A vertical playfield is a property of the PLAYFIELD, not of the machine, which
# is why it stopped fitting a tag. An upright cabinet very often has one -- and
# not always: the Euromats hang on a wall with the playfield sloped toward the
# player. Modelling it as a feature also gives the backbox playfields somewhere
# to land, as a child: they are vertical playfields that are not the machine's
# own playing surface.

# The five IPDB states outside the Specialty field (0311's population).
FREETEXT: dict[str, tuple[int, str]] = {
    "flipper-4": (
        7040,
        "Player drops coin at top of game to fall through a small vertical "
        "playfield of pins to scoring pockets at the bottom.",
    ),
    "hi-fly": (5615, "This is a table top game with a vertical playfield."),
    "pickwick-improved": (5432, "Vertical playfield bagatelle."),
    "whiz-bowler": (5702, "10 balls for 1 cent. Vertical playfield."),
    "zipper-3": (5701, "5 balls for 1-cent. Vertical playfield."),
}

# A vertical playfield that is NOT the machine's own playing surface: a second
# one standing in the backbox, above an ordinary horizontal playfield.
BACKBOX: dict[str, tuple[int, str, str | None]] = {
    "banzai-run": (
        175,
        "A magnet on a moving vertical track lifts the ball in play to the "
        "vertical playfield in the backbox.",
        None,
    ),
    "double-action": (
        706,
        "activates a flipperless vertical playfield in the backbox where the next "
        "captive ball is mechanically lifted to the top and released to fall "
        "through pins",
        None,
    ),
    "springtime-2": (
        2326,
        "The scores from the flipperless vertical playfield carry-over to the next game.",
        "Genco's companion to Double Action of three months earlier, which states "
        "the same flipperless vertical playfield sits in the backbox.",
    ),
    "wreckn-ball": (
        6167,
        "A vertical moving track lifts the ball in play to the vertical playfield "
        "in the backbox.",
        None,
    ),
}

SPECIALTY_QUOTE = "Specialty: [...] Vertical Pinball Machine"


def write_freetext() -> None:
    """The five IPDB states outside the Specialty field."""
    entries = [
        pk.entry(
            f"model.{slug}",
            cite={"ref": f"ipdb:{ipdb_id}", "quote": quote},
            relationships={"gameplay_feature": ["vertical-playfields"]},
        )
        for slug, (ipdb_id, quote) in sorted(FREETEXT.items())
    ]
    emit(
        PATCHES / "0311-vertical-playfield-free-text.yaml",
        attribution="ipdb",
        description="Vertical playfields IPDB states outside its Specialty field.",
        entries=entries,
    )


def write_backbox() -> None:
    entries = [
        pk.entry(
            f"model.{slug}",
            note=note,
            cite={"ref": f"ipdb:{ipdb_id}", "quote": quote},
            relationships={"gameplay_feature": ["backbox-playfields"]},
        )
        for slug, (ipdb_id, quote, note) in sorted(BACKBOX.items())
    ]
    emit(
        PATCHES / "0314-backbox-playfields.yaml",
        attribution="ipdb",
        description="Machines with a vertical playfield in the backbox.",
        entries=entries,
    )


if __name__ == "__main__":
    write_features()
    write_cabinets()
    write_freetext()
    write_backbox()
    print(f"{len(VERTICAL)} tagged, {len(CABINET)} cabinets, "
          f"{len(set(VERTICAL) - set(CABINET))} left without one")
