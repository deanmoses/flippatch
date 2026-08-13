"""Emit patch 0228 — Williams-era documents for Tales of the Arabian Nights.

The document-citation pilot (RULEBOOK.md → Document cites): the first patch to
declare publisher documents under a 0227 root and cite them as
`<publisher>:<doc-slug>`. ArabianNights.md → the 0228 supplement records the
survey; 0226 recorded these documents as indexed-but-unusable when web cites
were the only form.

Declared documents (both cached from archive.org copies; IPDB carries the same
files but 403s the fetcher):
  williams:tales-of-the-arabian-nights-operations-manual-1996   16-50047-101 FINAL MAY 1996, 160 sheets, scanned
  williams:tales-of-the-arabian-nights-flyer-1996               front + back, one work (IPDB scans it as two images)

NOT declared (identified in the document library, no claim needs them):
  Operators Handbook (May 1996)   16 sheets of service menus, cached, no game fact
  Service Bulletin #91            IPDB-only; wire-dressing fix, no catalog field
  WPC-95 Schematic Manual         platform doc; document-to-System attachment is out of scope
  Parts List (.txt)               IPDB-only; nothing missing that it evidences

Claims: the two ramp features the documents newly evidence (IPDB's Notable
Features line names no ramps, so 0226 could not assert them), and cabinet:
floor classified from the flyer's specifications line (user ruling 2026-08-12:
assert cabinet on standard machines when evidence supports it). Quotes are
author transcriptions from the rendered sheets — both documents are scans, so
the verbatim gate reports SKIP-PDF and the transcription is the author's own
check (RULEBOOK.md → Citing PDF evidence).

Run: uv run python campaigns/0215-frontier-2026/model-families/arabian-nights/gen_documents.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = (
    Path(__file__).resolve().parents[4] / "patches" / "0228-arabian-nights-documents.yaml"
)

M96 = "model.tales-of-the-arabian-nights"

MANUAL = "williams:tales-of-the-arabian-nights-operations-manual-1996"
FLYER = "williams:tales-of-the-arabian-nights-flyer-1996"

# Stable archive.org download URLs, not the datanode hosts the fetch redirected
# to — the cache resolves the alias, a reader gets the durable address.
MANUAL_ARCHIVE = (
    "https://archive.org/download/Williams_Tales_of_the_Arabian_Nights_Operations_Manual/"
    "Williams_1996_Tales_of_the_Arabian_Nights_Manual.pdf"
)
MANUAL_IPDB = (
    "https://www.ipdb.org/files/3824/Williams_1996_Tales_of_the_Arabian_Nights_Manual.pdf"
)
FLYER_ARCHIVE = (
    "https://archive.org/download/arabian-nights-pinball-us-flier/"
    "Arabian%20Nights%20Pinball%20US%20Flier.pdf"
)
FLYER_IPDB_FRONT = "https://www.ipdb.org/images/3824/3824f1.jpg"
FLYER_IPDB_BACK = "https://www.ipdb.org/images/3824/3824f2.jpg"

SOURCES = [
    pk.source_child(
        "Tales of the Arabian Nights Operations Manual (May 1996)",
        parent="williams",
        slug="tales-of-the-arabian-nights-operations-manual-1996",
        year=1996,
        month=5,
        description=(
            "Williams part 16-50047-101, FINAL: operations & adjustments, "
            "testing & problem diagnosis, parts information, wiring diagrams "
            "& schematics. 160 pages."
        ),
        links=[
            (MANUAL_ARCHIVE, "Internet Archive copy", "archive"),
            (MANUAL_IPDB, "IPDB copy", "catalog"),
        ],
    ),
    pk.source_child(
        "Tales of the Arabian Nights Flyer (1996)",
        parent="williams",
        slug="tales-of-the-arabian-nights-flyer-1996",
        year=1996,
        description=(
            "Two-sided promotional flyer: playfield photography, feature "
            "copy and the specifications line."
        ),
        links=[
            (FLYER_ARCHIVE, "Internet Archive copy (both sides)", "archive"),
            (FLYER_IPDB_FRONT, "IPDB scan, front", "catalog"),
            (FLYER_IPDB_BACK, "IPDB scan, back", "catalog"),
        ],
    ),
]

ENTRIES = [
    pk.entry(
        M96,
        cite={
            "ref": FLYER,
            "locator": (
                "in The Magical Tales of Arabian Nights feature list, "
                "flyer back (PDF document page 2)"
            ),
            "quote": "Fly on the Magic Carpet Ramps around Ancient Baghdad",
        },
        relationships={"gameplay_feature": ["ramps"]},
    ),
    pk.entry(
        M96,
        note=(
            "The manual documents a diverter on the ramp with its own coil, "
            "switch and operator adjustment — the machine's ramp is diverter-"
            "equipped, hence the diverter-ramps leaf."
        ),
        cite={
            "ref": MANUAL,
            "locator": (
                "in the Error Messages section, printed page 1-43, "
                "PDF document page 69"
            ),
            "quote": (
                "The diverter on the ramp is not functioning properly. Check "
                "the Ramp Diverter coil (coil #21) as well as the Ramp Enter "
                "switch (#15) for proper adjustment."
            ),
        },
        relationships={"gameplay_feature": ["diverter-ramps"]},
    ),
    pk.entry(
        M96,
        note=(
            "No source names a cabinet format; classified from the flyer's "
            "specifications: a 76-inch-tall, 29-inch-wide, 250-pound machine "
            "is a standard floor-standing cabinet."
        ),
        cite={
            "ref": FLYER,
            "locator": (
                "the SPECIFICATIONS line at the foot of the flyer back "
                "(PDF document page 2)"
            ),
            "quote": (
                'Height...76"...193 cm Height (with backbox folded)...56"...'
                '142 cm Width...29"...74 cm Depth...55"...140 cm Weight '
                "(crated)...270 lbs...122 kg Weight (uncrated)...250 lbs...113 kg"
            ),
        },
        fields={"cabinet": "floor"},
    ),
]

pk.write_patch(
    OUT,
    attribution="flipcommons-catalog",
    description="Williams document cites for Tales of the Arabian Nights (1996).",
    entries=ENTRIES,
    sources=SOURCES,
)
print(f"wrote {OUT}")
