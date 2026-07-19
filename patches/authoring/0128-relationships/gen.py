#!/usr/bin/env python3
"""Generate ``patches/0176-model-lineage.yaml`` — typed lineage edges for the models
whose IPDB note states the relationship outright.

Candidate detection, vetting and the first-cut quote all live in ``relationships.sql``
(this dir); this script is just the emitter. It reads that file's
``relationship_green`` view — the CERTAIN tier — from the live flipcommons catalog
via the duckdb CLI (run with cwd = the flipcommons checkout, so the view's ``.read
scripts/analysis/catalog.sql`` and its ``ATTACH`` resolve).

Every row emitted carries:

- a **``cite:``** of ``ipdb:<id>`` with the **verbatim quote extracted from the note**
  rather than hand-typed. The SQL already normalized it the way
  ``scripts/quote_verify/verify_quotes.py`` normalizes the source side (smart quotes
  straightened, whitespace collapsed); ``clean_ipdb_quote`` then strips the two
  IPDB-specific hazards the SQL can't see — the punctuation-less header IPDB glues
  onto a first sentence, and quote-introducer framing — and bounds a run-on with a
  marked ``[...]`` omission. All of those keep the result a verbatim SUBSTRING, so it
  still verifies.
- a **``model_relationship:``** edge: ``relationship_type`` read off the note's
  phrasing, and ``license_status`` which defaults to ``unknown`` — a note establishes
  the COPY, not the AUTHORIZATION (README + TOOL-NOTES DEFECT 11), so `licensed` /
  `unlicensed` appear only where the quote itself carries the words.

The green tier already excludes component-copies, hedged claims, reverse-direction
notes, book-attributed notes and mojibake spans (see ``relationship_green_rejected``),
so nothing here needs a per-row judgement call at emit time.

**The quote is a proposal until ``make verify-quotes`` passes.** That gate checks each
span against pinexplore's ``ipdb_machines`` corpus, independently of this extraction.

Run from the flippatch repo root::

    uv run python3 patches/authoring/0128-relationships/gen.py
    make validate
    make verify-quotes
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
AUTHORING = HERE.parent  # patches/authoring/
REPO_ROOT = AUTHORING.parent.parent  # -> repo root
sys.path.insert(0, str(AUTHORING))  # patchkit
sys.path.insert(0, str(REPO_ROOT / "scripts"))  # common.related_projects

import patchkit as pk  # noqa: E402
from common.related_projects import FLIPCOMMONS_DIR, load_env  # noqa: E402

PATCH_PATH = REPO_ROOT / "patches" / "0176-model-lineage.yaml"
RELATIONSHIPS_SQL = HERE / "relationships.sql"

# The `description:` is Admin-only and lint-capped at 80 chars — a single short
# summary. The campaign's rationale (why license_status defaults to unknown, how the
# certain tier is gated) lives in this module's docstring and the dir README, and the
# per-row evidence lives in each entry's cite quote.
DESCRIPTION = "Model lineage edges for models whose IPDB note states the relationship."


def load_rows() -> list[dict[str, Any]]:
    """Read relationships.sql's ``relationship_green`` view as JSON."""
    load_env()
    fc = os.environ.get("FLIPCOMMONS_DIR") or str(FLIPCOMMONS_DIR)
    proc = subprocess.run(
        [
            "duckdb", "-init", str(RELATIONSHIPS_SQL), ":memory:",
            "COPY (FROM relationship_green) TO '/dev/stdout' (FORMAT json, ARRAY true);",
        ],
        cwd=fc, capture_output=True, text=True, check=True,
    )
    rows: list[dict[str, Any]] = json.loads(proc.stdout)
    return rows


def main() -> int:
    rows = load_rows()
    if not rows:
        raise SystemExit("relationship_green returned no rows — nothing to emit")
    entries: list[str] = []
    for r in sorted(rows, key=lambda r: str(r["slug"])):
        quote = pk.clean_ipdb_quote(str(r["quote"]))
        if not quote:
            raise SystemExit(f"{r['slug']}: quote became empty after cleaning")
        edge: dict[str, str] = {
            "target_machine": str(r["target_machine"]),
            "relationship_type": str(r["relationship_type"]),
            "license_status": str(r["license_status"]),
        }
        entries.append(
            pk.entry(
                f"model.{r['slug']}",
                cite={"ref": f"ipdb:{r['ipdb_id']}", "quote": quote},
                model_relationship=[edge],
            )
        )
    pk.write_patch(
        PATCH_PATH,
        attribution="flipcommons-catalog",
        description=DESCRIPTION,
        entries=entries,
    )
    kinds = Counter(str(r["relationship_type"]) for r in rows)
    lic = Counter(str(r["license_status"]) for r in rows)
    print(
        f"wrote {PATCH_PATH.relative_to(REPO_ROOT)} — {len(entries)} entries "
        f"({', '.join(f'{n} {k}' for k, n in sorted(kinds.items()))}; "
        f"license: {', '.join(f'{n} {k}' for k, n in sorted(lic.items()))})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
