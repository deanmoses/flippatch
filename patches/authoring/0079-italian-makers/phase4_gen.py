"""Emit the Phase-4 fact patch: tilt.it facts asserted on EXISTING models.

Run from the **flipcommons backend** (Django resolution + claim inspection),
with pinexplore as a sibling checkout (quote verification):

    cd ../flipcommons/backend && uv run python \
        ../../flippatch/patches/authoring/0079-italian-makers/phase4_gen.py

Takes the frozen ``reviewed.csv`` rows whose verdict is ``exists`` and, for
each machine-line fact (year, production month, technology, player count),
classifies it against the live catalog and its claims:

- **new fact** (catalog has no value) or **stackable corroboration** (same
  value, but the flipcommons-catalog source holds no claim on the field) →
  asserted in ``0109-italian-model-facts.yaml``, the whole line as one fact
  cluster under one cite.
- **ledger** (flipcommons-catalog already claims the field — the apply
  engine rejects a same-source re-assertion as a no-op) → appended to
  ``corroborations.csv`` for the future attach-evidence pass.
- **conflict** (tilt.it's value differs from the catalog's) → written to
  ``conflicts.csv`` for adjudication; never auto-asserted. tilt.it and IPDB
  often date different events (Enada presentation vs. manufacture year), so
  a differing value is a research item, not a correction.

Photo-section repeats (same page+name, no tech/players, drifted section year)
are deduped to the primary row first — their years are parser artifacts.
"""

from __future__ import annotations

import csv
import os
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FLIPPATCH = HERE.parent.parent.parent
PATCHES = FLIPPATCH / "patches"
PINEXPLORE = FLIPPATCH.parent / "pinexplore"

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()

sys.path.insert(0, str(HERE.parent))
import patchkit as pk  # noqa: E402

from apps.catalog.models import MachineModel  # noqa: E402
from apps.provenance.models import Claim  # noqa: E402
from django.contrib.contenttypes.models import ContentType  # noqa: E402

TILT = "https://www.tilt.it/flipper_pinball/ipdb"
TECH = {"em": "electromechanical", "ss": "solid-state"}

# Conflict resolutions applied at generation (kept here so regeneration is
# stable). (model, field) -> resolution text; rows resolved in the catalog's
# favor are not asserted, just documented.
RESOLUTIONS: dict[tuple[str, str], str] = {
    ("derby-2", "year"): "resolved: catalog year stands - year means MANUFACTURE year; tilt.it dates the Enada trade-show presentation (user ruling 2026-07-07)",
    ("lucky-shot", "year"): "resolved: catalog year stands - year means MANUFACTURE year; tilt.it dates the Enada V presentation (user ruling 2026-07-07)",
}

MONTH_ARTIFACT_NOTE = (
    "the catalog's January month is OPDB's year-only date default (an unknown "
    "month encodes as January 1); tilt.it states the production month"
)

# Existing Italian models the sweep found to be conversions — a machine reworked
# into another maker's cabinet (DomainModel → Conversions). Emitted as a
# conversion-kit tag + converted_from where the donor game is named; tag only
# where tilt.it says merely "a Gottlieb cabinet". Keyed catalog slug -> spec
# (page + verbatim quote + optional donor IPDB id + note).
CONVERSIONS: dict[str, dict] = {
    "zeus": {
        "page": "centralmatic-lombarda",
        "quote": (
            'una copia, almeno nella grafica, dell\'elettronico Williams "Flash", '
            "strutturata per essere installata in un mobile Gottlieb's, funzionante "
            "elettromeccanicamente"
        ),
        "donor_ipdb": None,  # tilt.it names only "a Gottlieb cabinet", no game
        "note": (
            "tilt.it describes it as installed in a Gottlieb cabinet — a conversion, "
            "not a from-scratch bootleg — with artwork copied from Williams' Flash; the "
            "specific donor game is not named, so converted_from is left unset."
        ),
    },
}


def norm_text(t: str) -> str:
    for a, b in {"“": '"', "”": '"', "‘": "'", "’": "'"}.items():
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


def main() -> None:
    db = sqlite3.connect(str(PINEXPLORE / "ingest_sources/web/cache.sqlite"))
    page_text: dict[str, str] = {}

    def text_for(page: str) -> str:
        if page not in page_text:
            url = f"{TILT}/{page}"
            row = db.execute(
                "SELECT text FROM pages WHERE url IN (?, ?)", (url, url + "/")
            ).fetchone()
            page_text[page] = norm_text(row[0]) if row and row[0] else ""
        return page_text[page]

    rows = [
        r
        for r in csv.DictReader((HERE / "reviewed.csv").open())
        if r["verdict"] == "exists" and r["final_catalog_slug"]
    ]

    # Dedupe photo-section repeats: keep the row with data per (page, slug).
    def richness(r: dict) -> int:
        return sum(bool(r[k]) for k in ("tech", "players", "prod", "year"))

    primary: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r["page"], r["final_catalog_slug"])
        if key not in primary or richness(r) > richness(primary[key]):
            primary[key] = r

    ct = ContentType.objects.get_for_model(MachineModel)
    entries: list[str] = []
    ledger_rows: list[dict] = []
    conflict_rows: list[dict] = []
    counts = {"models": 0, "asserted-facts": 0, "ledger": 0, "conflict": 0, "no-quote": 0}

    for (page, slug), r in sorted(primary.items()):
        mm = MachineModel.objects.filter(slug=slug).first()
        if mm is None:
            continue
        quote = norm_text(r["raw_line"]).strip()
        url = f"{TILT}/{page}"
        if quote not in text_for(page):
            counts["no-quote"] += 1
            continue

        facts: list[tuple[str, object, object]] = []
        if r["year"]:
            facts.append(("year", int(r["year"]), mm.year))
        if (
            r["prod"]
            and "?" not in r["prod"]
            and r["year"]
            and r["prod"].endswith(r["year"][2:])
        ):
            facts.append(("month", int(r["prod"].split("/")[0]), mm.month))
        if r["tech"] in TECH:
            facts.append(
                (
                    "technology_generation",
                    TECH[r["tech"]],
                    mm.technology_generation.slug if mm.technology_generation else None,
                )
            )
        if r["players"]:
            facts.append(("player_count", int(r["players"]), mm.player_count))

        assertable: dict[str, object] = {}
        month_artifact = False
        for field, tilt_val, cat_val in facts:
            if (
                field == "month"
                and cat_val is not None
                and str(cat_val) == "1"
                and str(tilt_val) != "1"
            ):
                # January-default artifact (see MONTH_ARTIFACT_NOTE): tilt.it's
                # real month supersedes it (our source outranks opdb's).
                assertable[field] = tilt_val
                month_artifact = True
                continue
            if cat_val is not None and str(cat_val) != str(tilt_val):
                counts["conflict"] += 1
                conflict_rows.append(
                    {
                        "model": slug, "field": field, "tilt": tilt_val,
                        "catalog": cat_val, "page": page, "raw_line": r["raw_line"],
                        "note": r["notes"],
                        "resolution": RESOLUTIONS.get((slug, field), ""),
                    }
                )
                continue
            if cat_val is not None:
                already = Claim.objects.filter(
                    content_type=ct, object_id=mm.id, field_name=field,
                    is_active=True, actor__priority=300,
                ).exists()
                if already:
                    counts["ledger"] += 1
                    ledger_rows.append(
                        {
                            "entity_ref": f"model.{slug}", "field": field,
                            "value": tilt_val, "ref": url, "quote": pk.clean_quote(quote),
                            "note": "same value already claimed by flipcommons-catalog - banked for the attach-evidence pass",
                        }
                    )
                    continue
            assertable[field] = tilt_val

        if not assertable:
            continue
        counts["models"] += 1
        counts["asserted-facts"] += len(assertable)
        note_bits = []
        if r["year_uncertain"] and "year" in assertable:
            note_bits.append('tilt.it marks the year uncertain ("(?)")')
        if month_artifact:
            note_bits.append(MONTH_ARTIFACT_NOTE)
        note = "; ".join(note_bits) + "." if note_bits else None
        entries.append(
            pk.entry(
                f"model.{slug}",
                note=note,
                cite={"ref": url, "quote": quote},
                fields=assertable,
            )
        )

    # Conversion facts on existing Italian models (tag + converted_from), a
    # separate ChangeSet from any scalar facts on the same model above.
    for slug, c in sorted(CONVERSIONS.items()):
        mm = MachineModel.objects.filter(slug=slug).first()
        if mm is None:
            sys.exit(f"CONVERSIONS slug not in catalog: {slug}")
        url = f"{TILT}/{c['page']}"
        if norm_text(c["quote"]) not in text_for(c["page"]):
            sys.exit(f"CONVERSIONS quote not verbatim for {slug}")
        fields: dict[str, object] = {}
        if c.get("donor_ipdb"):
            donor = MachineModel.objects.filter(ipdb_id=c["donor_ipdb"]).first()
            if donor is None:
                sys.exit(f"CONVERSIONS donor ipdb {c['donor_ipdb']} not in catalog ({slug})")
            fields["converted_from"] = donor.slug
        counts["conversions"] = counts.get("conversions", 0) + 1
        entries.append(
            pk.entry(
                f"model.{slug}",
                note=c.get("note"),
                cite={"ref": url, "quote": c["quote"]},
                tags=["conversion-kit"],
                fields=fields or None,
            )
        )

    pk.write_patch(
        PATCHES / "0109-italian-model-facts.yaml",
        attribution="flipcommons-catalog",
        description="Facts from tilt.it (IPDB.it) on existing Italian models.",
        entries=entries,
    )

    with (HERE / "conflicts.csv").open("w", newline="") as f:
        w = csv.DictWriter(
            f, lineterminator="\n",
            fieldnames=["model", "field", "tilt", "catalog", "page", "raw_line", "note", "resolution"],
        )
        w.writeheader()
        w.writerows(conflict_rows)

    # Append ledger rows to corroborations.csv (dedup on entity_ref+field+ref).
    corr = HERE / "corroborations.csv"
    existing = list(csv.DictReader(corr.open()))
    seen = {(e["entity_ref"], e["field"], e["ref"]) for e in existing}
    added = 0
    for e in ledger_rows:
        if (e["entity_ref"], e["field"], e["ref"]) not in seen:
            existing.append(e)
            seen.add((e["entity_ref"], e["field"], e["ref"]))
            added += 1
    with corr.open("w", newline="") as f:
        w = csv.DictWriter(
            f, lineterminator="\n",
            fieldnames=["entity_ref", "field", "value", "ref", "quote", "note"],
        )
        w.writeheader()
        w.writerows(existing)

    print(counts, f"| corroborations.csv +{added}", f"| conflicts.csv {len(conflict_rows)}")


if __name__ == "__main__":
    main()
