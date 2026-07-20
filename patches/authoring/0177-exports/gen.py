#!/usr/bin/env python3
"""Generate ``patches/0177-exports.yaml`` — export editions and their destination
markets, for the models whose source states the fact outright.

Candidate detection, the false-positive gate and the first-cut quote all live in
``exports.sql`` (this dir); this script is just the emitter. It reads that file's
``export_patch_rows`` view — the tiers safe to author without a per-row source read —
from the live flipcommons catalog via the duckdb CLI (run with cwd = the flipcommons
checkout, so the view's ``.read scripts/analysis/catalog.sql`` and its ``ATTACH``
resolve).

Two INDEPENDENT facts ride each entry (flipcommons' DataPatchAuthoring.md → Export
editions and markets), and most rows carry only the second:

- **``export_edition_of:``** — a scalar FK to the domestic original, emitted only when
  the CITED SENTENCE names one that resolves uniquely: IPDB's formulaic paired-brand
  sentence (``twin``), or a "version of <Maker>'s <year> '<Name>'" reference
  (``notes``, via ``_origin_ref``). The target is parsed, never guessed — the
  campaign's title-mate and orphan buckets stay human worklists, because "do not infer
  the original from a shared Title" is about a Title being a *lead*, whereas here the
  source states the original in the very sentence the claim cites.
- **``export_market:``** — one ModelExportMarket shape per model, never a mix:
  ``target_market_location`` rows for parsed countries, else a ``target_market_label``
  region, else the ``- {}`` unknown-destination row. `patchkit` re-checks the
  mutual exclusion, because ingest does **not** — an illegal mix applies silently.

The three tiers differ only in what they cite:

- **twin** — ``cite: ipdb:<id>`` carrying two spans joined by a marked ``[...]``
  omission: the independent "<Brand> is the name used for export games" sentence that
  states this model's own role, then the sentence naming the domestic counterpart.
  `verify_quotes` checks each span separately, and requires them in SOURCE order.
- **notes** — ``cite: ipdb:<id>`` with the verbatim export sentence, gated in the SQL
  by a self-subject anchor (in this corpus "… made for export to Italy" is a floating
  participle that attaches to whichever noun the sentence is *about*).
- **suffix** — no cite of its own. The evidence is the model's catalog name ending in
  "(Country)", so a cite to IPDB would misleadingly imply a quote is the basis; the
  reasoning goes in a ``note:`` instead (the call ../0172-bingo-game-format/gen.py
  makes for its struct rows).
- **reciprocal** — no usable note of its own; the ORIGINAL's record names it as the
  export ("The add-a-ball version for export to Italy is Gottlieb's 1969 'Western'.").
  Cites that record.

Any row may additionally carry RECIPROCAL cites — the original's record corroborating
the export from the other end. They ride the SAME entry as extra ``cite:`` list members,
never a second entry: a cite list attaches every citation to every claim, and two entries
targeting one record must assert disjoint claim keys, so splitting would be an error.

**Every quote is a proposal until ``make verify-quotes`` passes.** That gate checks
each span against pinexplore's ``ipdb_machines`` corpus, independently of this
extraction.

Run from the flippatch repo root::

    uv run python3 patches/authoring/0177-exports/gen.py
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

PATCH_PATH = REPO_ROOT / "patches" / "0177-exports.yaml"
EXPORTS_SQL = HERE / "exports.sql"

# The `description:` is Admin-only and lint-capped at 80 chars. The campaign rationale
# (how a target gets parsed, why the OPDB flag is not a tier) lives in this module's
# docstring and README.md; the per-row evidence lives in each cite quote.
DESCRIPTION = "Export editions and destination markets stated outright by the source."


def suffix_note(country: str) -> str:
    """The note for a `suffix` row — reasoning from the model's own catalog name.

    No cite: the evidence is the entity's own data, not a source quote
    (DataPatchAuthoring.md, "skip the cite when the evidence is the entity's own
    data"). The catalog distinguishes these market editions from their domestic
    original by the name suffix alone, which is exactly the fact being structured.
    """
    return (
        f"Recording this model as built for export to {country} because the catalog "
        f"name carries a '({country})' market suffix, distinguishing it from the "
        f"same maker's domestic edition of the same game."
    )


def load_rows() -> list[dict[str, Any]]:
    """Read exports.sql's ``export_patch_rows`` view as JSON."""
    load_env()
    fc = os.environ.get("FLIPCOMMONS_DIR") or str(FLIPCOMMONS_DIR)
    proc = subprocess.run(
        [
            "duckdb", "-init", str(EXPORTS_SQL), ":memory:",
            "COPY (FROM export_patch_rows) TO '/dev/stdout' (FORMAT json, ARRAY true);",
        ],
        cwd=fc, capture_output=True, text=True, check=True,
    )
    rows: list[dict[str, Any]] = json.loads(proc.stdout)
    return rows


def market_rows(row: dict[str, Any]) -> list[dict[str, str]]:
    """The `export_market:` members for one row — exactly one of the three shapes.

    Country rows win over a label, and an empty result is the `- {}` unknown row
    rather than "no claim": every row here HAS established that the model was built
    for export, which is precisely what the targetless row records.
    """
    countries = row.get("market_countries") or []
    if countries:
        return [{"target_market_location": str(c)} for c in countries]
    if row.get("market_label"):
        return [{"target_market_label": str(row["market_label"])}]
    return [{}]


def build_quote(row: dict[str, Any]) -> str:
    """The verbatim cite quote: one span, or two joined by a marked omission.

    The role sentence comes FIRST — IPDB writes "Recel is the name used for export
    games." ahead of the "The same company made a domestic version as ..." sentence,
    and `verify_quotes` requires joined spans in SOURCE order. It also reads better
    that way: the model's own role, then the counterpart it is the export edition of.
    """
    spans = [s for s in (row.get("role_quote"), row["quote"]) if s]
    quote = " [...] ".join(pk.clean_quote(s.strip()) for s in spans if s and s.strip())
    if not quote:
        raise SystemExit(f"{row['slug']}: quote became empty after cleaning")
    return quote


def build_cites(row: dict[str, Any]) -> list[dict[str, str]]:
    """Every source backing this entry, as a `cite:` LIST.

    The model's own record first (when it has a usable quote), then each RECIPROCAL
    statement — the original's record naming this model as its export. All of them ride
    ONE entry: DataPatches.md attaches every citation in a list to every claim the entry
    asserts, and entries targeting the same record must assert disjoint claim keys, so
    splitting these across entries would be an error rather than a stylistic choice.

    A reciprocal source is always a different model, so its ipdb ref cannot collide with
    this row's own — which matters, because a repeated ref+locator+quote is a hard error.
    Duplicates are still filtered defensively, since two sources can quote one sentence.
    """
    cites: list[dict[str, str]] = []
    if row["kind"] in ("twin", "notes"):
        cites.append({"ref": f"ipdb:{row['ipdb_id']}", "quote": build_quote(row)})
    for rc in row.get("recip_cites") or []:
        quote = pk.clean_quote(str(rc["quote"]).strip())
        if not quote:
            continue
        cites.append({"ref": f"ipdb:{rc['ipdb_id']}", "quote": quote})
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for c in cites:
        key = (c["ref"], c["quote"])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def main() -> int:
    rows = load_rows()
    if not rows:
        raise SystemExit("export_patch_rows returned no rows — nothing to emit")
    entries: list[str] = []
    for r in sorted(rows, key=lambda r: str(r["slug"])):
        kind = str(r["kind"])
        fields: dict[str, object] = {}
        if r.get("export_edition_of"):
            fields["export_edition_of"] = str(r["export_edition_of"])
        cites = build_cites(r)
        # A `suffix` row reasons from the model's own name, so it carries a note; it
        # only gains a cite if a reciprocal note also corroborates it.
        note = None
        if kind == "suffix":
            countries = r.get("market_countries") or []
            if len(countries) != 1:
                raise SystemExit(
                    f"{r['slug']}: a suffix row must parse exactly one country from its "
                    f"name, got {countries!r}"
                )
            note = suffix_note(str(countries[0]).replace("-", " ").title())
        elif not cites:
            raise SystemExit(f"{r['slug']}: {kind} row has no citable evidence")
        entries.append(
            pk.entry(
                f"model.{r['slug']}",
                note=note,
                # one cite stays a mapping; several become the list form
                cite=(cites[0] if len(cites) == 1 else cites) if cites else None,
                fields=fields or None,
                export_market=market_rows(r),
            )
        )
    pk.write_patch(
        PATCH_PATH,
        attribution="flipcommons-catalog",
        description=DESCRIPTION,
        entries=entries,
    )
    kinds = Counter(str(r["kind"]) for r in rows)
    multi = sum(1 for r in rows if len(r.get("recip_cites") or []) > 0)
    shapes = Counter(
        "country" if (r.get("market_countries") or [])
        else "label" if r.get("market_label")
        else "unknown"
        for r in rows
    )
    fks = sum(1 for r in rows if r.get("export_edition_of"))
    print(
        f"wrote {PATCH_PATH.relative_to(REPO_ROOT)} — {len(entries)} entries "
        f"({', '.join(f'{n} {k}' for k, n in sorted(kinds.items()))}; "
        f"markets: {', '.join(f'{n} {k}' for k, n in sorted(shapes.items()))}; "
        f"{fks} export_edition_of; {multi} with a reciprocal cite)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
