"""Emit patch 0227 — document publisher roots for the IPDB trove, plus USPTO.

Pure emitter, roots only. Every judgement (which publishers earn a root, which
catalog manufacturer each maps to, the Stern era split, Gottlieb's inclusion)
is settled in publishers.csv and README.md and gated by roots_checks; this file
turns rows into `sources:` nodes. No documents are seeded here — the roots make
`<publisher>:<document>` cite refs resolvable, and documents arrive with the
patches that cite them.

The scope decisions this encodes (regroup of 2026-08-12, recorded in README.md):

  every mapped publisher      all IPDB filename prefixes with >= 2 distinct
                              documents that map to a catalog manufacturer
  both Sterns                 the 'Stern' prefix spans stern-electronics
                              (1977-1985) and the modern stern-pinball
  Gottlieb included           zero docs on IPDB (rights holder enforces
                              copyright), but its documents exist elsewhere
  USPTO only                  the one patent-office root; ES/GB added on demand

Root slugs are the catalog manufacturer slugs verbatim (a naming convention,
never a join key — DocumentCitations.md § Naming and slugs); names are read
live from the catalog through roots.sql so a rename never drifts a root.

Run: uv run python campaigns/0227-document-publisher-roots/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import patchkit as pk  # noqa: E402

HERE = Path(__file__).resolve().parent
SQL = HERE / "roots.sql"
OUT = Path(__file__).resolve().parents[2] / "patches" / "0227-document-publisher-roots.yaml"

# The patch description maps to the Admin-only IngestRun note (80-char lint cap);
# the rationale lives in this module's docstring and the campaign README.
DESCRIPTION = "Document publisher roots for first-party manufacturer docs, plus USPTO"

# One formula for every manufacturer root, with overrides only where the name
# alone is ambiguous — the two companies that both render as "Stern" need their
# eras stated, since a picker shows nothing else to tell them apart.
DESC_OVERRIDES = {
    "stern-pinball": (
        "First-party game documentation published by the modern "
        "Stern Pinball (1999 to present)."
    ),
    "stern-electronics": (
        "First-party game documentation published by Stern Electronics "
        "(1977-1985), distinct from the modern Stern Pinball."
    ),
}


def root_description(slug: str, name: str) -> str:
    # No trailing period after a name that carries its own ("Alvin G.",
    # "SIRMO Games S.A.") — the formula would double it.
    stop = "" if name.endswith(".") else "."
    return DESC_OVERRIDES.get(
        slug, f"First-party game documentation published by {name}{stop}"
    )


def main() -> None:
    rows = pk.read_view(SQL, "roots_patch_rows", prefix="roots")
    if not rows:
        raise SystemExit("roots_patch_rows returned no rows; nothing to emit")

    # Heaviest publisher first (ties alphabetical), so the patch reads in the
    # same order as the README's evidence table; Gottlieb's 0 lands it last.
    rows.sort(key=lambda r: (-int(r["ipdb_docs"] or 0), str(r["manufacturer_slug"])))

    sources = [
        pk.source_root(
            str(r["manufacturer_name"]),
            source_type="document",
            slug=str(r["manufacturer_slug"]),
            description=root_description(
                str(r["manufacturer_slug"]), str(r["manufacturer_name"])
            ),
        )
        for r in rows
    ]

    # The one publisher root that is not a manufacturer: the patent-issuing
    # office. Not derivable from the trove's filename prefixes (those name the
    # models' makers), so it is declared here explicitly — without it no
    # uspto:<number> cite resolves (DocumentCitations.md § Patents).
    sources.append(
        pk.source_root(
            "USPTO",
            source_type="document",
            slug="uspto",
            description=(
                "The United States Patent and Trademark Office. Each document "
                "is a patent, addressed by its number."
            ),
        )
    )

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description=DESCRIPTION,
        entries=[],
        sources=sources,
    )
    print(f"wrote {OUT.relative_to(Path.cwd())} ({len(sources)} roots)")


if __name__ == "__main__":
    main()
