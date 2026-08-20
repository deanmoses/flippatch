#!/usr/bin/env python3
"""Generate ``patches/0269-ipdb-never-produced.yaml`` — IPDB's `Never Produced` status
for models the catalog files as unknown.

Detection, the dump-wins safety gate and the vocabulary mapping all live in
``never_produced.sql`` (this dir); this script is a pure emitter over its
``np_patch_rows`` view, read from the live flipcommons catalog via the duckdb CLI.

Every entry asserts ``production_status: unreleased`` and cites the machine listing with
its own ``Production:`` row as the verbatim quote::

    - model.ice-castle:
        cite:
          ref: "ipdb:3711"
          quote: "Production: Never Produced"
        production_status: unreleased

Two things about that shape are worth knowing.

**The quote resolves through a page, not the dump.** The IPDB dump types production as an
integer, so the words `Never Produced` are absent from all 6,664 records. flippatch's
``ipdb:`` resolver tops a dump row up from the cached machine page for the few labels the
dump has no column for — and only where the dump rendered no line under that label, so
this quote cannot verify against a machine the dump credits with a production run.

**No note.** The quote is the whole justification: IPDB recorded no production for this
machine. Mapping that onto `unreleased` rather than `one-off` is a vocabulary decision
made once for the whole population, not a per-record rationale, so it belongs in
README.md — repeating one boilerplate sentence on 36 records tells a reader nothing the
citation did not already carry.

Run from the flippatch repo root::

    uv run python3 campaigns/0269-ipdb-never-produced/gen.py
    make validate
    make verify-quote-verbatim
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Repo root by marker, never by counting parents, so a campaign dir stays movable.
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common

import patchkit as pk  # noqa: E402

PATCH_PATH = pk.PATCHES_DIR / "0269-ipdb-never-produced.yaml"
STATUS_SQL = HERE / "never_produced.sql"

# Admin-only and lint-capped at 80 chars; the rationale lives in README.md and this
# module's docstring, the per-row evidence in each cite quote.
DESCRIPTION = "Cancelled projects IPDB records as never produced."

# The status every row asserts. Named here so the emitter can refuse a row the analysis
# ever classifies differently, instead of writing whatever string arrives.
STATUS = "unreleased"


def main() -> int:
    rows = pk.read_view(STATUS_SQL, "np_patch_rows", prefix="np")
    if not rows:
        raise SystemExit("np_patch_rows returned no rows — nothing to emit")

    entries: list[str] = []
    for r in sorted(rows, key=lambda r: str(r["slug"])):
        slug = str(r["slug"])
        status = str(r["production_status"])
        if status != STATUS:
            raise SystemExit(f"{slug}: unexpected production_status {status!r}")
        quote = pk.clean_quote(str(r["quote"]).strip())
        if not quote:
            raise SystemExit(f"{slug}: quote became empty after cleaning")
        entries.append(
            pk.entry(
                f"model.{slug}",
                cite={"ref": str(r["cite_ref"]), "quote": quote},
                fields={"production_status": status},
            )
        )

    pk.write_patch(
        PATCH_PATH,
        attribution="flipcommons-catalog",
        description=DESCRIPTION,
        entries=entries,
    )
    dated = sum(1 for r in rows if r.get("project_year") is not None)
    makers = Counter(str(r["manufacturer_name"]) for r in rows)
    top, top_n = makers.most_common(1)[0]
    print(
        f"wrote {PATCH_PATH.relative_to(pk.REPO_ROOT)} — {len(entries)} entries "
        f"({dated} carrying a project date; "
        f"{len(makers)} makers, largest {top} at {top_n})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
