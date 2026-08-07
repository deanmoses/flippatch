"""Emit patch 0216 — the Houdini family: 100th Anniversary and its 2017 siblings.
See ../0215-frontier-2026/ENRICHMENT-PLAN.md for the family split; this family owns
0216, with 0217 free should it need a second patch.

SCOPE IS THE WHOLE FAMILY, not just the 2026 model: Houdini: Master of Mystery
(2017) and its Deluxe are in scope and currently unenriched, and the 193-page AP
manual documents THEM. But `Houdini "Master Mystery"` (IPDB 6469, year NULL) is the
never-built Popadiuk/Andrews design and is NOT a sibling — leave it alone; see
../0215-frontier-2026/README.md for the error that rule exists to prevent.

PILOT SCALE, AND BEING REWRITTEN. One model, every claim hand-vetted against the
full page, so the facts sit inline here rather than in a gated CSV. This patch has
not shipped: it is due a rewrite that leans on American Pinball's PDFs (the Houdini
game manual and quick reference guide, both now cached) and drops what aggregator
dependence it has. The fan-out to the rest of Tier B needs the 0215 architecture —
a checked-in evidence CSV plus checks that verify each quote against the pinexplore
cache, resolve each cite host to a seeded citation root, and drop anything the
catalog already holds.

CITATION ROOTS. The AP manuals live on `48804760.fs1.hubspotusercontent-na1.net`
and `my.orbitgames.fun`, neither of which resolves to a citation root today, so
citing them fails the apply until this patch declares them in its own `sources:`
block. Cardona needs a root outright. See ENRICHMENT-PLAN.md.

CAREFUL. The 193-page Houdini manual on AP's site documents the 2017 machine, not
the 100th Anniversary. Mechanics may carry over; that is an assumption, not
evidence, and needs a source that says so. This is the Houdini error's own shape —
see ../0215-frontier-2026/README.md.

Every claim is first-party, from American Pinball's own pages, and rides its own
entry with the sentence that establishes it. Two source pages:

  the announcement  https://americanpinball.com/houdini-100th-anniversary-pinball/
  the spec page     https://americanpinball.com/houdini/   (JS tabs; the cached copy
                    is a headless render, which is why the 100th Anniversary panel
                    and the common Playfield/Rules blocks are in the text at all)

Deliberately absent:
  month           neither page dates the release.
  descriptions    the lint wants inline cites and TWO sources per record description.
  lineage         the announcement evidences a variant_of houdini-master-of-mystery
                  edge; lineage is its own patch, by decision.
  toppers/knockers definitions — a `description:` must be attributed
                  flipcommons-ai-desc-*, which this patch is not, so the two new
                  vocabulary terms are created with names only. Defining them (and
                  the 67 other undefined terms) is a separate, differently-attributed
                  patch.

Run: uv run python campaigns/0216-houdini/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))

import patchkit as pk  # noqa: E402

OUT = Path(__file__).resolve().parents[4] / "patches" / "0216-houdini.yaml"
MODEL = "model.houdini-100th-anniversary"

ANN = "https://americanpinball.com/houdini-100th-anniversary-pinball/"
SPEC = "https://americanpinball.com/houdini/"


def cite(ref: str, quote: str) -> dict[str, str]:
    return {"ref": ref, "quote": quote}


def main() -> None:
    entries = [
        # The vocabulary additions come first: a gameplay_feature member must resolve.
        # Neither affects ball behaviour — they are feedback and decoration — but the
        # vocabulary already carries backbox animations, lockdown-bar buttons and shaker
        # motors on the same footing, so they are consistent with it as it stands.
        pk.entry("gameplay-feature.toppers", create=True, fields={"name": "Toppers"}),
        pk.entry("gameplay-feature.knockers", create=True, fields={"name": "Knockers"}),
        pk.entry(
            MODEL,
            cite=cite(
                ANN,
                "Now, American Pinball is proud to celebrate the legendary escape "
                "artist’s enduring legacy with the release of the Houdini 100th "
                "Anniversary Edition.",
            ),
            fields={"production_status": "produced"},
        ),
        pk.entry(
            MODEL,
            cite=cite(ANN, "Introducing the Houdini 100th Anniversary Pinball Machine"),
            fields={"game_format": "pinball"},
        ),
        pk.entry(
            MODEL,
            cite=cite(
                ANN, "stunning new cabinet artwork by acclaimed artist Christopher Franchi"
            ),
            credits=[("christopher-franchi", "art")],
        ),
        # One sentence names all three, so they share an entry.
        pk.entry(
            MODEL,
            cite=cite(
                ANN,
                "Each game includes a custom topper, Magic Glass, shaker motor, knocker, "
                "and mirrored art blades as standard equipment.",
            ),
            relationships={"gameplay_feature": ["toppers", "knockers", "shaker-motors"]},
        ),
        # The spec page's Playfield / Rules blocks are common to every Houdini edition.
        pk.entry(
            MODEL,
            cite=cite(SPEC, "Three Magnets to Control Houdini's Magic"),
            relationships={"gameplay_feature": [{"magnets": 3}]},
        ),
        pk.entry(
            MODEL,
            cite=cite(SPEC, "5 Multiballs"),
            relationships={"gameplay_feature": ["multiball"]},
        ),
        pk.entry(
            MODEL,
            cite=cite(SPEC, "1 Video Mode"),
            relationships={"gameplay_feature": [{"video-modes": 1}]},
        ),
        pk.entry(
            MODEL,
            cite=cite(SPEC, "Steampunk Flippers"),
            relationships={"gameplay_feature": ["flippers"]},
        ),
    ]

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description="Houdini 100th Anniversary details",
        entries=entries,
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
