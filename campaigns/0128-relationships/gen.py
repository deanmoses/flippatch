#!/usr/bin/env python3
"""Generate ``patches/0188-model-lineage.yaml`` — typed lineage edges for the models
whose IPDB note states the relationship outright.

TRANCHES. This generator emits one patch per RUN, not one patch for all time. Its
input view is ``relationship_green``, which is scoped to models that carry no
relationship edge YET, so every row an earlier tranche authored drops out of it the
moment that patch is applied — the view is self-limiting, and a run always emits
exactly the remaining work. Each run therefore takes a FRESH patch number and this
constant moves with it; an applied patch is immutable (the ledger fingerprints its
content and keys on the patch id), so re-pointing this at an old number would produce
a file that cannot ingest. ``0176-model-lineage.yaml`` was the first tranche (40 rows,
applied); this is the second, opened by the widened phrasebook and its same-maker
guard. Rows deliberately held out of a tranche are recorded in the analysis's
``_rel_open_question`` — never by editing this file's output.

A maker authored as its own patch is EXCLUDED here, so the two emitters partition the
tier between them and no model can be authored twice — see ``EXCLUDED_MAKERS`` below.
That is patch organization only; what each row claims is decided in the analysis.

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

    uv run python3 campaigns/0128-relationships/gen.py
    make validate
    make verify-quotes
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
# Repo root by marker, never by counting parents, so a campaign dir stays movable.
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common

import patchkit as pk  # noqa: E402

PATCH_PATH = pk.PATCHES_DIR / "0188-model-lineage.yaml"
RELATIONSHIPS_SQL = HERE / "relationships.sql"

# The `description:` is Admin-only and lint-capped at 80 chars — a single short
# summary. The campaign's rationale (why license_status defaults to unknown, how the
# certain tier is gated) lives in this module's docstring and the dir README, and the
# per-row evidence lives in each entry's cite quote.
# Filename and wording are the user's, applied to the patch by hand — kept here so a
# regeneration reproduces the shipped file rather than reverting it.
DESCRIPTION = "Model lineage - mostly conversions and copies."

# Makers authored as their own patch (the campaign's one-patch-per-maker convention),
# excluded here so the two emitters cannot author the same model. Keep in step with
# gen_victory_games.py's MAKER_SLUG.
EXCLUDED_MAKERS = {"victory-games"}



def main() -> int:
    rows = [
        r
        for r in pk.read_view(
            RELATIONSHIPS_SQL, "relationship_green", prefix="relationships"
        )
        if str(r["maker_slug"]) not in EXCLUDED_MAKERS
    ]
    if not rows:
        raise SystemExit("relationship_green had no rows outside EXCLUDED_MAKERS")
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
        f"wrote {PATCH_PATH.relative_to(pk.REPO_ROOT)} — {len(entries)} entries "
        f"({', '.join(f'{n} {k}' for k, n in sorted(kinds.items()))}; "
        f"license: {', '.join(f'{n} {k}' for k, n in sorted(lic.items()))})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
