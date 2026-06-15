"""Emit 0042-japanese-maker-years.yaml — assert production years on early-Japanese
models flipcommons carries with a null or placeholder (1900) year.

Years come from the eremeka catalog (thetastates.com) and its companion blog
(earlyarcadesjapan.blogspot.com), seeded as citation roots in 0041. We derive the
structured `year` field from that research, so the attribution is flipcommons-catalog
with a cite to the eremeka page (the blog post where one exists, else the tag
listing). All seven models carry an IPDB id, so we guard on ipdb_id — the most
specific guard, present even where year is null.

Approximate eremeka dates (marked ~) are asserted with the uncertainty recorded in
the note, since the model has no "approximate" flag (per the authoring decision:
assert, note approximate).

Run from the backend so Django can read live guard values:
  cd flipcommons/backend && \
    uv run python ../../pindata/patches/authoring/0042-japanese-makers/gen.py
"""

import csv
import os
import sys
from pathlib import Path

import django

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # for `import patchkit`
import patchkit as pk  # noqa: E402
from apps.catalog.models import MachineModel  # noqa: E402

OUT = HERE.parent.parent  # .../patches/

LISTING = (
    "https://thetastates.com/eremeka/eremekaDisplay.php"
    "?mentionOnly=1&search=yes&tag=yokomono+~+flipper+pinball"
)

# Curated year fixes. `note` is grounded in the cited page; blog posts are quoted
# where the wording adds dating evidence. approximate=True rows record the ~ in the
# note. ipdb_id is the live guard (filled in below); year is the asserted value.
ROWS = [
    {
        "slug": "apollo-moon",
        "ipdb_id": 6812,
        "year": 1972,
        "approximate": False,
        "game_format": "pinball",
        "cite": LISTING,
        "note": 'The eremeka catalog lists "1972 Apollo Moon by Sankyo".',
    },
    {
        "slug": "the-world-series",
        "ipdb_id": 6069,
        "year": 1972,
        "approximate": False,
        "game_format": "pinball",
        "cite": "https://earlyarcadesjapan.blogspot.com/2022/06/the-world-series-by-sankyo.html",
        "note": 'Early Arcades Japan says "The earliest mention I can find of The World Series is in 1972 [...] The World Series appears in the 1973 machine directory." (A 1976 re-release was sold as New World Series.)',
    },
    {
        "slug": "new-big-race",
        "ipdb_id": 6070,
        "year": 1972,
        "approximate": False,
        "game_format": "pinball",
        "cite": "https://earlyarcadesjapan.blogspot.com/2025/09/new-big-race-by-sankyo.html",
        "note": 'Early Arcades Japan says "New Big Race appears in the 1973 game directory, which was printed in late 1972 [...] The 1972 print date of the machine directory is the only date we have, and the one we will use for the time being."',
    },
    {
        "slug": "asteroid-killer",
        "ipdb_id": 3810,
        "year": 1979,
        "approximate": False,
        "game_format": "pinball",
        "cite": "https://earlyarcadesjapan.blogspot.com/2026/05/1979-asteroid-killer-by-universal.html",
        "note": 'The eremeka catalog and Early Arcades Japan date this "1979 Asteroid Killer by Universal" (flipcommons previously had 1980).',
    },
    {
        "slug": "indy-game",
        "ipdb_id": 6774,
        "year": 1967,
        "approximate": True,
        "game_format": "pinball",
        "cite": LISTING,
        "note": 'The eremeka catalog dates this to approximately 1967 (marked ~, "~1967 Indy Game by Komaya").',
    },
    {
        "slug": "lets-go-moon",
        "ipdb_id": 6773,
        "year": 1968,
        "approximate": True,
        "game_format": "pinball",
        "cite": LISTING,
        "note": 'The eremeka catalog dates this to approximately 1968 (marked ~, "~1968 Let\'s Go Moon! by Komaya").',
    },
    {
        "slug": "ultra-attack",
        "ipdb_id": 6068,
        "year": 1972,
        "approximate": True,
        "game_format": "pinball",
        "cite": "https://earlyarcadesjapan.blogspot.com/2024/03/1972-ultra-attack-by-nihon-gorakuki.html",
        "note": "The eremeka catalog dates this to approximately 1972 (marked ~), co-credited to Nihon Gorakuki and Nihon Tenbo.",
    },
]

# --- live lookup: guard + drift checks ---
ids = [r["ipdb_id"] for r in ROWS]
live = {
    m["ipdb_id"]: m
    for m in MachineModel.objects.filter(ipdb_id__in=ids).values(
        "slug", "ipdb_id", "year"
    )
}
pk.check_resolved(ids, live)
for r in ROWS:
    m = live[r["ipdb_id"]]
    if m["slug"] != r["slug"]:
        raise SystemExit(
            f"slug drift ipdb_id={r['ipdb_id']}: worksheet {r['slug']!r} != live {m['slug']!r}"
        )
    if m["year"] == r["year"]:
        print(
            f"  note: {r['slug']} already year={r['year']}; entry will diff as unchanged"
        )

# --- build entries (slug-ordered) ---
built = []
for r in ROWS:
    built.append(
        (
            r["slug"],
            pk.entry(
                f"model.{r['slug']}",
                expect={"ipdb_id": r["ipdb_id"]},
                note=r["note"],
                cite=r["cite"],
                fields={"year": r["year"], "game_format": r["game_format"]},
            ),
        )
    )
entries = [e for _, e in sorted(built, key=lambda be: be[0])]

DESCRIPTION = (
    "Assert production years on seven early-Japanese models flipcommons carried with a "
    "null or placeholder (1900) year, from the eremeka catalog research (thetastates.com / "
    "earlyarcadesjapan.blogspot.com, seeded in 0041). Sankyo: Apollo Moon, The World Series "
    "(was 1900), New Big Race; Universal: Asteroid Killer (was 1980); Komaya: Indy Game, "
    "Let's Go Moon!; Nihon Gorakuki: Ultra Attack. Approximate eremeka dates are asserted "
    "with the uncertainty noted. Guarded on ipdb_id."
)
pk.write_patch(
    OUT / "0042-japanese-maker-years.yaml",
    attribution="flipcommons-catalog",
    description=DESCRIPTION,
    entries=entries,
)

# --- audit artifact ---
with (HERE / "worksheet.csv").open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["slug", "ipdb_id", "year", "approximate", "cite", "note"])
    for r in ROWS:
        w.writerow(
            [r["slug"], r["ipdb_id"], r["year"], r["approximate"], r["cite"], r["note"]]
        )

print(f"wrote 0042-japanese-maker-years.yaml ({len(entries)} entries) + worksheet.csv")
