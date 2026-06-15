"""Emit 0029-corporate-entity-years.yaml from the curated ROWS below.

Companion to the hand-written 0013-corporate-entity-years.yaml, extending
corporate-entity active years to twelve more significant makers that were still
missing them. Same shape as 0013: attribution `flipcommons-catalog`, each row
guarded on `ipdb_manufacturer_id` and cited to a seeded web root (Wikipedia,
created in 0012-citation-sources-web.yaml).

No pinexplore/classify.py stage here: unlike the 0010 game_format work (which
classifies IPDB/OPDB free text in DuckDB), the evidence is Wikipedia article
prose gathered by web research. So the classification lives as ROWS literals in
this file; gen.py emits worksheet.csv as the audit artifact and reads the live
flipcommons DB only for the `expect:` guards and a drift check.

Run from the backend so Django can read live guard values:
  cd flipcommons/backend && \
    uv run python ../../pindata/patches/authoring/0029-corporate-entity-years/gen.py
"""

import csv
import os
import sys
from pathlib import Path

import django

sys.path.insert(0, os.getcwd())  # backend on path (run from flipcommons/backend)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # for `import patchkit`
import patchkit as pk  # noqa: E402
from apps.catalog.models import CorporateEntity  # noqa: E402

OUT = HERE.parent.parent  # .../patches/authoring/<set>/ -> .../patches/
WORKSHEET = HERE / "worksheet.csv"

# Curated rows: each keyed on the corporate entity's IPDB manufacturer id (the
# guard), with year_start / optional year_end and the verbatim Wikipedia note +
# cite. year_end is None for a maker still in business (only year_start written).
# Notes are verbatim Wikipedia prose; en-dashes normalize to hyphens via patchkit.
ROWS = [
    {
        "ipdb_manufacturer_id": 255,
        "ce_slug": "playmatic",
        "year_start": 1968,
        "year_end": 1987,
        "cite": "https://en.wikipedia.org/wiki/Playmatic",
        "note": (
            'Wikipedia says "Playmatic was a Spanish manufacturer of pinball machines, '
            'producing approximately 63 different models between 1968 and 1987."'
        ),
    },
    {
        "ipdb_manufacturer_id": 269,
        "ce_slug": "rock-ola-manufacturing-corporation",
        "year_start": 1932,
        "year_end": None,
        "cite": "https://en.wikipedia.org/wiki/Rock-Ola",
        "note": (
            'Wikipedia says "The Rock-Ola Scale Company was founded in 1927 by David Cullen '
            'Rockola [...]," and that "The name was changed to Rock-Ola Manufacturing '
            'Corporation in 1932." No end year is asserted: Rock-Ola Manufacturing '
            "Corporation remains in business."
        ),
    },
    {
        "ipdb_manufacturer_id": 356,
        "ce_slug": "zaccaria",
        "year_start": 1974,
        "year_end": 1990,
        "cite": "https://en.wikipedia.org/wiki/Zaccaria_(company)",
        "note": (
            'Wikipedia says "Zaccaria [...] was an Italian manufacturer of pinball and arcade '
            'machines that operated in Bologna from 1974 until 1990."'
        ),
    },
    {
        "ipdb_manufacturer_id": 218,
        "ce_slug": "mills-novelty-company",
        "year_start": 1898,
        "year_end": 1943,
        "cite": "https://en.wikipedia.org/wiki/Mills_Novelty_Company",
        "note": (
            'Wikipedia says "In 1898, Mortimer Mills sold a controlling interest in the company '
            "to his son, Herbert S. Mills, and the name of the company was changed from M.B.M. "
            'Cigar Vending Company to Mills Novelty Company, Incorporated," and that "The company '
            "changed its corporate name from the Mills Novelty Company to Mills Industries, "
            'Incorporated on September 1, 1943 [...]."'
        ),
    },
    {
        "ipdb_manufacturer_id": 237,
        "ce_slug": "o-d-jennings-and-company",
        "year_start": 1906,
        "year_end": 1954,
        "cite": "https://en.wikipedia.org/wiki/Jennings_%26_Company",
        # year_end is the successor boundary (asset sale), not Ode Jennings's 1953 death.
        "note": (
            'Wikipedia says the company "manufactured other coin-operated machines, including '
            'pinball machines, from 1906 to the 1980s," was "founded by Ode D. Jennings as '
            'Industry Novelty Company, Incorporated of Chicago," and that "On March 19, 1954, '
            "Jennings & Company was incorporated in Illinois and purchased the assets of O. D. "
            'Jennings & Company from his estate."'
        ),
    },
    {
        "ipdb_manufacturer_id": 634,
        "ce_slug": "jersey-jack-pinball-inc-lakewood-nj",
        "year_start": 2011,
        "year_end": None,
        "cite": "https://en.wikipedia.org/wiki/Jersey_Jack_Pinball",
        "note": (
            'Wikipedia says "Jersey Jack Pinball was founded in January 2011 by industry veteran '
            'Jack Guarnieri." No end year is asserted: the company remains in business.'
        ),
    },
    {
        "ipdb_manufacturer_id": 671,
        "ce_slug": "spooky-pinball-llc",
        "year_start": 2013,
        "year_end": None,
        "cite": "https://en.wikipedia.org/wiki/Spooky_Pinball",
        # The article lead says 2016; its History section gives 2013. Use 2013 and say so.
        "note": (
            "Wikipedia's History section says \"Charlie Emery officially founded Spooky Pinball "
            'in 2013 in Benton, Wisconsin [...]"; the article lead instead says 2016, but the '
            "detailed History account (2013) is used here. No end year is asserted: the company "
            "remains in business."
        ),
    },
    {
        "ipdb_manufacturer_id": 126,
        "ce_slug": "game-plan-incorporated",
        "year_start": 1977,
        "year_end": 1985,
        "cite": "https://en.wikipedia.org/wiki/Game_Plan_(company)",
        "note": (
            'Wikipedia says "Game Plan was founded in May of 1977 [...]," and that it "produced '
            'pinball machines, arcade video games, and slot machines from 1978 to 1985."'
        ),
    },
    {
        "ipdb_manufacturer_id": 18,
        "ce_slug": "allied-leisure-industries-incorporated",
        "year_start": 1968,
        "year_end": 1980,
        "cite": "https://en.wikipedia.org/wiki/Centuri",
        "note": (
            "Wikipedia's article on Centuri (formerly Allied Leisure) lists \"Pinball and "
            'electro-mechanical games released as Allied Leisure (1968–1979)," and states '
            "they renamed it Centuri in 1980."
        ),
    },
    {
        "ipdb_manufacturer_id": 33,
        "ce_slug": "atari-incorporated",
        "year_start": 1972,
        "year_end": 1984,
        "cite": "https://en.wikipedia.org/wiki/Atari",
        "note": (
            'Wikipedia says "The original Atari, Inc., founded in Sunnyvale, California, United '
            "States in 1972 by Nolan Bushnell and Ted Dabney, was a pioneer in arcade games, "
            'home video game consoles, and home computers," and that "In 1984, as a result of '
            "the video game crash of 1983, the assets of the home console and computer divisions "
            "of the original Atari Inc. were sold off [...], while the remaining part of Atari, "
            'Inc. was renamed Atari Games Inc."'
        ),
    },
    {
        "ipdb_manufacturer_id": 432,
        "ce_slug": "chicago-gaming-company",
        "year_start": 2001,
        "year_end": None,
        "cite": "https://en.wikipedia.org/wiki/Chicago_Gaming",
        "note": (
            'Wikipedia says "This part of the company was established as Chicago Gaming Company '
            "as a division of Churchill cabinet company in 2001 by Doug Duba, the son of Roger "
            'Duba." 2001 is when the Chicago Gaming Company entity was established, not the '
            "parent Churchill Cabinet Company (1904). No end year is asserted: still in business."
        ),
    },
    {
        "ipdb_manufacturer_id": 144,
        "ce_slug": "h-c-evans-company",
        "year_start": 1892,
        "year_end": 1955,
        "cite": "https://en.wikipedia.org/wiki/H._C._Evans",
        "note": 'Wikipedia says "It was established in 1892 and collapsed in 1955."',
    },
]

# --- live lookup for expect guards + drift check ---
ids = [r["ipdb_manufacturer_id"] for r in ROWS]
live = {
    ce["ipdb_manufacturer_id"]: ce
    for ce in CorporateEntity.objects.filter(ipdb_manufacturer_id__in=ids).values(
        "slug", "ipdb_manufacturer_id", "year_start", "year_end"
    )
}
pk.check_resolved(ids, live)

for r in ROWS:
    ce = live[r["ipdb_manufacturer_id"]]
    if ce["slug"] != r["ce_slug"]:
        raise SystemExit(
            f"slug drift for ipdb_manufacturer_id={r['ipdb_manufacturer_id']}: "
            f"worksheet {r['ce_slug']!r} != live {ce['slug']!r}"
        )
    if ce["year_start"] is not None or ce["year_end"] is not None:
        print(
            f"  note: {ce['slug']} already has years "
            f"(start={ce['year_start']}, end={ce['year_end']}); claim will supersede"
        )

# --- emit patch ---
built = []
for r in ROWS:
    fields = {"year_start": r["year_start"]}
    if r["year_end"] is not None:
        fields["year_end"] = r["year_end"]
    built.append(
        (
            r["ce_slug"],
            pk.entry(
                f"corporate-entity.{r['ce_slug']}",
                expect={"ipdb_manufacturer_id": r["ipdb_manufacturer_id"]},
                note=r["note"],
                cite=r["cite"],
                fields=fields,
            ),
        )
    )
entries = [e for _, e in sorted(built, key=lambda be: be[0])]  # slug-ordered

pk.write_patch(
    OUT / "0029-corporate-entity-years.yaml",
    attribution="flipcommons-catalog",
    description=(
        "Populate corporate-entity active years for twelve more significant makers, "
        "extending 0013: Playmatic, Rock-Ola Mfg., Zaccaria, Mills Novelty, O.D. "
        "Jennings, Jersey Jack, Spooky, Game Plan, Allied Leisure, Atari, Chicago "
        "Gaming and H.C. Evans. Years from Wikipedia (cited per entry); year_end left "
        "unset for makers still in business."
    ),
    entries=entries,
)

# --- audit artifact: worksheet.csv (the realized rows + extracted quotes) ---
with WORKSHEET.open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(
        ["ipdb_manufacturer_id", "ce_slug", "year_start", "year_end", "cite", "note"]
    )
    for r in ROWS:
        w.writerow(
            [
                r["ipdb_manufacturer_id"],
                r["ce_slug"],
                r["year_start"],
                "" if r["year_end"] is None else r["year_end"],
                r["cite"],
                r["note"],
            ]
        )

print(
    f"wrote 0029-corporate-entity-years.yaml ({len(entries)} entries) + worksheet.csv"
)
