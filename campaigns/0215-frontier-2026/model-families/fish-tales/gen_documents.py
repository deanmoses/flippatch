"""Emit patch 0230 — Williams-era documents for Fish Tales (1992).

Second documents supplement after 0228 (RULEBOOK.md → Document cites), and the
first whose copies came through the in-app browser + `web_import.py` route:
IPDB is the only holder of these files (archive.org hunts recorded on the
library docs), so the user's browser fetched them and the imports carry
`imported = 1`. FishTales.md → the 0230 supplement records the survey.

Declared documents (all under the williams root; every copy is IPDB's,
carried as `catalog` links):
  williams:fish-tales-operations-manual-1992   16-50005-101 August 1992, 148 sheets, scanned
  williams:fish-tales-flyer-1992               front + back, one work; back transcribed (text_source=manual)
  williams:fish-tales-parts-list-1992          plain text, fully gated

NOT declared: Operator's Handbook (June 1992) — cached and OCR'd, service
menus, no claim needs it; promo video (.wmv, no transport), artwork/plastics
scans, manual amendment, third-party rulesheet (stays web).

Claims are the staples IPDB's Notable Features line skips (its line names
criss-cross ramps, spinner, multiball, captive ball, autoplunger, catapult —
no jets, no slings), Video Mode from the flyer, and cabinet: floor under the
2026-08-12 ruling. Manual quotes are author transcriptions from rendered
sheets (SKIP-PDF); flyer and parts-list quotes gate verbatim.

Run: uv run python campaigns/0215-frontier-2026/model-families/fish-tales/gen_documents.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0230-fish-tales-documents.yaml"

M92 = "model.fish-tales"

MANUAL = "williams:fish-tales-operations-manual-1992"
FLYER = "williams:fish-tales-flyer-1992"
PARTS = "williams:fish-tales-parts-list-1992"

MANUAL_IPDB = (
    "https://www.ipdb.org/files/861/Williams_1992_Fish_Tales_English_Manual.pdf"
)
PARTS_IPDB = "https://www.ipdb.org/files/861/Williams_1992_Fish_Tales_Parts_List.txt"
FLYER_IPDB_FRONT = "https://www.ipdb.org/images/861/861f1.jpg"
FLYER_IPDB_BACK = "https://www.ipdb.org/images/861/861f2.jpg"

MATRIX_LOC = "in the Switch Matrix, printed page 3-4, PDF document page 98"

SOURCES = [
    pk.source_child(
        "Fish Tales Operations Manual (August 1992)",
        parent="williams",
        slug="fish-tales-operations-manual-1992",
        year=1992,
        month=8,
        description=(
            "Williams part 16-50005-101: operations & adjustments, testing & "
            "problem diagnosis, parts information, wiring diagrams & "
            "schematics."
        ),
        links=[(MANUAL_IPDB, "IPDB copy", "catalog")],
    ),
    pk.source_child(
        "Fish Tales Flyer (1992)",
        parent="williams",
        slug="fish-tales-flyer-1992",
        year=1992,
        description="Two-sided promotional flyer; the back carries the feature copy.",
        links=[
            (FLYER_IPDB_FRONT, "IPDB scan, front", "catalog"),
            (FLYER_IPDB_BACK, "IPDB scan, back", "catalog"),
        ],
    ),
    pk.source_child(
        "Fish Tales Parts List (1992)",
        parent="williams",
        slug="fish-tales-parts-list-1992",
        year=1992,
        description="Williams parts list for game 50005, plain text.",
        links=[(PARTS_IPDB, "IPDB copy", "catalog")],
    ),
]

ENTRIES = [
    pk.entry(
        M92,
        cite={
            "ref": FLYER,
            "locator": "in the VIDEO MODE panel on the flyer back",
            "quote": (
                "Video Mode allows players to torpedo speeding boats and "
                "watercraft in an overcrowded lake."
            ),
        },
        relationships={"gameplay_feature": ["video-modes"]},
    ),
    pk.entry(
        M92,
        note=(
            "Williams-era documents call pop bumpers jet bumpers: the switch "
            "matrix names three (Left/Center/Right Jet) and the parts list "
            "carries the jet bumper coil assembly with quantity 3."
        ),
        cite=[
            {
                "ref": MANUAL,
                "locator": MATRIX_LOC,
                "quote": "51 Left Jet 52 Center Jet 53 Right Jet",
            },
            {
                "ref": PARTS,
                "quote": "jet bumper coil assy-2 pin con",
            },
        ],
        relationships={"gameplay_feature": [{"pop-bumpers": 3}]},
    ),
    pk.entry(
        M92,
        note=(
            "Sling is Williams' term for the slingshot kicker; the switch "
            "matrix names a left and a right."
        ),
        cite={
            "ref": MANUAL,
            "locator": MATRIX_LOC,
            "quote": "57 Left Sling 58 Right Sling",
        },
        relationships={"gameplay_feature": [{"slingshots": 2}]},
    ),
    pk.entry(
        M92,
        note=(
            "No source names a cabinet format; classified from the manual's "
            "assembly-instructions dimensions - a 55-inch-long, 26-inch-wide, "
            "285-pound machine on legs is a standard floor-standing cabinet."
        ),
        cite={
            "ref": MANUAL,
            "locator": (
                "in Pinball Game Assembly Instructions, printed page 1-2, "
                "PDF document page 17"
            ),
            "quote": (
                'Cabinet Dimensions Approx. Length: 55"Approx. '
                'Width: 26" Approx. Height: 85" Weight: 285 lbs'
            ),
        },
        fields={"cabinet": "floor"},
    ),
]

pk.write_patch(
    OUT,
    attribution="flipcommons-catalog",
    description="Williams document cites for Fish Tales (1992).",
    entries=ENTRIES,
    sources=SOURCES,
)
print(f"wrote {OUT}")
