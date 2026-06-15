"""Emit patches/0031-maker-operating-status.yaml.

Two-stage authoring (DataPatchAuthoring.md): verbatim quotes come from the
pinexplore web cache; the `expect:` guards come from the live flipcommons DB.
Run from the flipcommons backend:

    cd backend && uv run python ../../pindata/patches/authoring/0031-maker-operating-status/gen.py

Prints a review table (slug | quote) and writes the patch. Re-run after tweaking
a needle in classify.py until every quote reads right.
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
from pathlib import Path

# Pinball News pages start their body with a "Date: 18th July 2024 " line that
# trafilatura folds into the first sentence — strip it so the note quotes prose.
_DATE_PREFIX = re.compile(r"^Date:\s*\d{1,2}[a-z]{0,2}\s+[A-Za-z]+,?\s+\d{4}\s+")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # patchkit
sys.path.insert(0, str(HERE))  # classify
import classify as C  # noqa: E402
import patchkit as pk  # noqa: E402

# --- live flipcommons DB (expect guards) ---------------------------------- #
sys.path.insert(0, "/Users/moses/dev/flipcommons/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()
from apps.catalog.models import MachineModel  # noqa: E402
from apps.catalog.models.manufacturer import CorporateEntity  # noqa: E402

CACHE = "/Users/moses/dev/pinexplore/ingest_sources/web/cache.sqlite"
PATCH = HERE.parent.parent / "0031-maker-operating-status.yaml"


def cached_text(url: str) -> str:
    """Extracted text for a cached page, by exact or suffix-normalized URL."""
    c = sqlite3.connect(CACHE)
    for u in (url, url.rstrip("/")):
        r = c.execute("select text from pages where url = ?", (u,)).fetchone()
        if r:
            return r[0]
    # fall back to a LIKE on the path tail (handles trailing-slash / www drift)
    tail = url.rstrip("/").split("//", 1)[-1]
    r = c.execute(
        "select text from pages where url like ?", ("%" + tail + "%",)
    ).fetchone()
    return r[0] if r else ""


def quote_for(row: dict) -> str:
    if row.get("quote"):
        return row["quote"]
    text = cached_text(row.get("cache_url", row["cite"]))
    q = pk.sentence_with(text, row["needle"])
    if not q:
        raise SystemExit(
            f"NO QUOTE for {row['slug']!r} (needle {row['needle']!r} not found)"
        )
    return pk.clean_ipdb_quote(_DATE_PREFIX.sub("", q), limit=300)


def ce_guard(slug: str) -> dict:
    ce = (
        CorporateEntity.objects.filter(slug=slug)
        .values("ipdb_manufacturer_id", "name")
        .first()
    )
    if not ce:
        raise SystemExit(f"corporate-entity {slug!r} not found in live DB")
    if ce["ipdb_manufacturer_id"] is not None:
        return {"ipdb_manufacturer_id": ce["ipdb_manufacturer_id"]}
    return {"name": ce["name"]}


def model_guard(slug: str) -> dict:
    m = (
        MachineModel.objects.filter(slug=slug)
        .values("year", "corporate_entity__slug")
        .first()
    )
    if not m:
        raise SystemExit(f"model {slug!r} not found in live DB")
    return pk.guard(m, prefer=("year", "corporate_entity"))


entries: list[str] = []
review: list[tuple[str, str]] = []

for row in C.ONGOING + C.ENDED:
    q = quote_for(row)
    review.append((row["slug"], q))
    entries.append(
        pk.entry(
            f"corporate-entity.{row['slug']}",
            expect=ce_guard(row["slug"]),
            note=pk.source_note(row["source"], q),
            cite=row["cite"],
            fields={"operating_status": "ongoing" if row in C.ONGOING else "ended"},
        )
    )

for row in C.MODEL_FIXES:
    q = quote_for(row)
    review.append((f"{row['slug']} [{row['field']}]", q))
    entries.append(
        pk.entry(
            f"model.{row['slug']}",
            expect=model_guard(row["slug"]),
            note=pk.source_note(row["source"], q),
            cite=row["cite"],
            fields={row["field"]: row["value"]},
        )
    )

sources = [
    pk.source_root(name, description=desc, links=[(home, name, "homepage")])
    for name, home, desc in C.NEW_ROOTS
]

DESC = (
    "operating_status for corporate entities with a non-variant model released since 2010 "
    "that are not on Wikipedia's current-manufacturers list. ongoing = a 2023-or-newer source "
    "shows current production; ended = defunct, a one-off, or not a pinball OEM, each cited. "
    "Plus model fixes: Pinball Tronic game_format (video-screen 'virtual pinball' -> "
    "miscellaneous), Road Trip production_status, and two aftermarket conversions. "
    f"Deferred to the ended baseline (ambiguous): {', '.join(s for s, _ in C.DEFER)}."
)

pk.write_patch(
    PATCH,
    attribution="flipcommons-catalog",
    description=DESC,
    entries=entries,
    sources=sources,
)

print(f"\nwrote {PATCH}  ({len(entries)} entries, {len(sources)} new roots)\n")
print("=== REVIEW: slug | verbatim quote ===")
for slug, q in review:
    print(f"  {slug:48} {q}")
