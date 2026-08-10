"""Emit patch 0215 — the foundation rows for the 2026 frontier sweep.

Pure emitter. Every judgement (which models exist, what themes they carry, which
franchise groups them) is settled in frontier.sql + candidates.csv and gated by
frontier_checks; this file only turns rows into YAML.

FOUNDATION ONLY. It carries the fields the catalog itself leaves uncited — name,
slug, title, corporate entity, franchise, theme, year. Deliberately absent:

  production_status  91% of its claims carry a citation, and the value is not
                     quotable today: Pinside's HTML says "In production" but
                     trafilatura drops it from the extracted text that
                     `make verify-quotes` checks. Enrichment patch.
  game_format / tag  59% / 27% cited. Enrichment patch.
  month              known for 2 of 21. Enrichment patch.
  lineage            remake_of / variant_of / conversion_kit all need a source;
                     the variant_of here was derived from a name match, which is
                     exactly the kind of guess a citation exists to prevent.
  description        the lint requires inline cites and TWO sources per record
                     description. Research, not foundation.

Run: uv run python campaigns/0215-frontier-2026/model-discovery/gen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import patchkit as pk  # noqa: E402

HERE = Path(__file__).resolve().parent
SQL = HERE / "frontier.sql"
OUT = Path(__file__).resolve().parents[3] / "patches" / "0215-new-2026-models.yaml"

# The patch description maps to the Admin-only IngestRun note and is capped at 80
# chars by the lint — the rationale lives in this module's docstring and the campaign
# README, not here.
DESCRIPTION = "New models for 2026"

AP_URL = "https://americanpinball.com/houdini-100th-anniversary-pinball/"

# americanpinball.com is NOT a recognized host: the American Pinball citation root
# registers american-pinball.com (hyphenated), and citation_root_for_host() returns
# NULL for the unhyphenated one, so a cite: to it would not resolve. Recognition hosts
# are homepage ∪ domains, and the sources: block is additive get-or-create matched by
# recognition host — so declaring the root with BOTH homepages matches the existing row
# via the hyphenated host and backfills the new one.
AP_SOURCE = pk.source_root(
    "American Pinball",
    source_type="web",
    links=[
        ("https://www.american-pinball.com/", "American Pinball", "homepage"),
        ("https://americanpinball.com/", "American Pinball", "homepage"),
    ],
)

# The limited run and its size are a sourced fact, so they ride a cited companion entry
# below the create rather than the create itself. First-party, from the maker's own
# announcement.
HOUDINI_QTY_QUOTE = (
    "This limited production run of just 100 machines worldwide commemorates "
    "100 years since Harry Houdini\u2019s passing"
)


def title_name(candidate: str) -> str:
    """The Title name for a model: its name minus one trailing parenthetical."""
    return candidate.split(" (")[0].strip() if candidate.endswith(")") else candidate


def main() -> None:
    rows = pk.read_view(SQL, "frontier_patch_rows", prefix="frontier")

    entries: list[str] = []

    # 1. New makers. The manufacturer is declared first so the corporate entity below
    #    can point at it — a forward reference is not supported.
    seen_makers: set[str] = set()
    for r in rows:
        if not r["maker_action"] or r["corporate_entity_slug"] in seen_makers:
            continue
        seen_makers.add(r["corporate_entity_slug"])
        slug = r["corporate_entity_slug"]
        entries.append(
            pk.entry(f"manufacturer.{slug}", create=True, fields={"name": r["maker_name"]})
        )
        entries.append(
            pk.entry(
                f"corporate-entity.{slug}",
                create=True,
                fields={"name": r["maker_name"], "manufacturer": slug},
            )
        )

    # 2. Franchises, before the titles that reference them.
    seen_fr: set[str] = set()
    for r in rows:
        if r["franchise_action"] != "create" or r["franchise_slug"] in seen_fr:
            continue
        seen_fr.add(r["franchise_slug"])
        entries.append(
            pk.entry(
                f"franchise.{r['franchise_slug']}",
                create=True,
                fields={"name": title_name(r["candidate_name"])},
            )
        )

    # 3. Titles, before the models that reference them.
    #
    # Driven by title_exists, NOT title_action: a Title can be real and still unreachable
    # by name-matching the model (the 100th Anniversary belongs to the existing `houdini`
    # Title, which its own name does not match), and create: true against a live title
    # fails the apply as a duplicate.
    seen_titles: set[str] = set()
    for r in rows:
        if r["title_exists"] or r["title_slug"] in seen_titles:
            continue
        seen_titles.add(r["title_slug"])
        fields: dict[str, object] = {"name": title_name(r["candidate_name"])}
        if r["franchise_slug"]:
            fields["franchise"] = r["franchise_slug"]
        entries.append(pk.entry(f"title.{r['title_slug']}", create=True, fields=fields))

    # 4. The models.
    for r in rows:
        themes = [t.strip() for t in (r["themes"] or "").split(",") if t.strip()]

        fields = {
            "name": r["candidate_name"],
            "title": r["title_slug"],
            "corporate_entity": r["corporate_entity_slug"],
        }
        if r["year"] is not None:
            fields["year"] = r["year"]
        entries.append(
            pk.entry(
                f"model.{r['proposed_slug']}",
                create=True,
                fields=fields,
                relationships={"theme": themes} if themes else None,
            )
        )
        # The limited run is a sourced fact, not identity, so it rides its own entry
        # below the create with the quote that establishes it.
        if r["proposed_slug"] == "houdini-100th-anniversary":
            entries.append(
                pk.entry(
                    f"model.{r['proposed_slug']}",
                    cite={"ref": AP_URL, "quote": HOUDINI_QTY_QUOTE},
                    fields={"production_quantity": 100},
                    tags=["limited-edition"],
                )
            )

    pk.write_patch(
        OUT,
        attribution="flipcommons-catalog",
        description=DESCRIPTION,
        entries=entries,
        sources=[AP_SOURCE],
    )
    print(f"wrote {OUT} — {len(entries)} entries")


if __name__ == "__main__":
    main()
