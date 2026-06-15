"""Emit 0030-em-firm-years.yaml — corporate-entity years for four early Chicago-era
firms (Genco, Exhibit Supply, J. H. Keeney, Stoner) that 0029 left unset because
they have no English Wikipedia article.

Casting a wider net (per the data-notes follow-up): two are covered by Wikipedia's
"List of pinball manufacturers" (an already-seeded en.wikipedia.org page); the
other two need new citation roots, which this patch creates in its own `sources:`
block (the same mechanism 0012 used) — American Jukebox History for Keeney and the
Aurora Historical Society for Stoner.

Each maker is a single entry with one cite (one source supports both its years):
no per-field cite split was needed. patchkit.write_patch can't emit a `sources:`
block, so this generator composes the file itself — patchkit.entry() for the
escaped/guarded claim blocks, a literal header + sources prologue around them.

Run from the backend so Django can read live guard values:
  cd flipcommons/backend && \
    uv run python ../../pindata/patches/authoring/0030-em-firm-years/gen.py
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

# New citation roots this patch seeds (Wikipedia already seeded by 0012). The cite
# URL on each claim must share a domain with one of these homepages.
SOURCES_BLOCK = """\
sources:
  - name: American Jukebox History
    source_type: web
    description: Reference site on American coin-operated music and amusement makers, including company factory histories (e.g. J. H. Keeney & Co.).
    links:
      - { url: "https://www.jukeboxhistory.info/", label: American Jukebox History, link_type: homepage }
  - name: Aurora Historical Society
    source_type: web
    description: Local-history museum for Aurora, Illinois; publishes histories of Aurora manufacturers including Stoner Manufacturing Corporation.
    links:
      - { url: "https://aurorahistory.org/", label: Aurora Historical Society, link_type: homepage }
"""

# Curated rows. One cite per row (the source supports both years). Notes are
# verbatim source prose with omissions marked [...]; en-dashes normalize to hyphens.
ROWS = [
    {
        "ipdb_manufacturer_id": 130,
        "ce_slug": "genco-manufacturing-company",
        "year_start": 1931,
        "year_end": 1958,
        "cite": "https://en.wikipedia.org/wiki/List_of_pinball_manufacturers",
        "note": 'Wikipedia\'s "List of pinball manufacturers" lists "Genco (1931-1958)."',
    },
    {
        "ipdb_manufacturer_id": 117,
        "ce_slug": "exhibit-supply-company",
        "year_start": 1901,
        "year_end": 1979,
        "cite": "https://en.wikipedia.org/wiki/List_of_pinball_manufacturers",
        # Corporate span (1901-1979); the note preserves the pinball sub-span (1932-1957),
        # which is the range of this entity's machines in our catalog.
        "note": (
            'Wikipedia\'s "List of pinball manufacturers" lists "Exhibit Supply Company '
            '(1901-1979; pinball manufacturing 1932-1957)."'
        ),
    },
    {
        "ipdb_manufacturer_id": 162,
        "ce_slug": "j-h-keeney-and-company-incorporated",
        "year_start": 1934,
        "year_end": 1964,
        "cite": "https://www.jukeboxhistory.info/keeney/history.html",
        "note": (
            'American Jukebox History says "The firm of Keeney and Sons was terminated in '
            "November, 1933, and in January, 1934, Jack Keeney organized his own company [...] "
            'as J.H. Keeney and Company," and that "The last pin game by J.H. Keeney & Co. was '
            "the Keeney's 1964 'Arrowhead' which was first and only listed on August 29, 1964.\""
        ),
    },
    {
        "ipdb_manufacturer_id": 304,
        "ce_slug": "stoner-manufacturing-company",
        "year_start": 1931,
        "year_end": 1941,
        "cite": "https://aurorahistory.org/made-in-aurora-davy-jones-pinball-machine/",
        # Pinball era 1931-1941: founded 1931, left amusement production at the 1941 war
        # retooling (matching this entity's last catalog model, 1941); became a vendor after.
        "note": (
            'Aurora Historical Society says "The family-operated Stoner Manufacturing '
            "Corporation began in 1931 as a maker of pinball machines, producing nearly 100 "
            'different models throughout the decade," that "In 1941, they retooled and produced '
            'munitions for the war effort during World War II," and that "After the war, Stoner '
            'became a leading producer of coin-operated vending machines [...]."'
        ),
    },
]

# --- live lookup for expect guards + drift checks ---
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
        print(f"  note: {ce['slug']} already has years; claim will supersede")

# --- build claim entries (slug-ordered) ---
built = []
for r in ROWS:
    built.append(
        (
            r["ce_slug"],
            pk.entry(
                f"corporate-entity.{r['ce_slug']}",
                expect={"ipdb_manufacturer_id": r["ipdb_manufacturer_id"]},
                note=r["note"],
                cite=r["cite"],
                fields={"year_start": r["year_start"], "year_end": r["year_end"]},
            ),
        )
    )
entries = [e for _, e in sorted(built, key=lambda be: be[0])]

# --- compose the file (header + sources prologue + claims) ---
DESCRIPTION = (
    "Populate corporate-entity active years for four early Chicago-era makers 0029 "
    "left unset (no English Wikipedia article): Genco, Exhibit Supply, J. H. Keeney "
    "and Stoner. Genco/Exhibit cite Wikipedia's List of pinball manufacturers; Keeney "
    "and Stoner cite two new roots created below (American Jukebox History, Aurora "
    "Historical Society)."
)
header = ["attribution: flipcommons-catalog", "description: >"]
header += [f"  {line}" for line in pk._fold(DESCRIPTION)]
text = (
    "\n".join(header) + "\n" + SOURCES_BLOCK + "claims:\n" + "\n".join(entries) + "\n"
)
(OUT / "0030-em-firm-years.yaml").write_text(text)

# --- audit artifact ---
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
                r["year_end"],
                r["cite"],
                r["note"],
            ]
        )

print(f"wrote 0030-em-firm-years.yaml ({len(entries)} entries) + worksheet.csv")
