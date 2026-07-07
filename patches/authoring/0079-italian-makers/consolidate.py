"""Merge the four adjudication passes into the frozen review artifacts.

Run from the pinexplore repo root (needs the web cache for quote verification):

    uv run python ../flippatch/patches/authoring/0079-italian-makers/consolidate.py <scratch-dir>

Inputs: worksheet.csv (parser output) + the four review JSONs produced by the
adjudication agents (review-newmakers / review-bem-group / review-longtail /
review-kits) in <scratch-dir>.

Outputs, next to this script:
- reviewed.csv       — one row per worksheet machine row with the final
                       verdict (create / exists / reassign / defer / noise),
                       agent-corrected fields, lineage, conflict notes, and a
                       cache-verified verbatim quote span for every create.
- third-sources.csv  — every non-tilt.it/non-IPDB source the reviewers found,
                       keyed to the row it supports (feeds corroborations.csv
                       and the description phase).

The verdicts themselves were made row-by-row in the review pass (JSONs kept in
the session scratchpad; headline decisions in README.md). This script is the
mechanical merge; any cross-page override it applies is listed in OVERRIDES.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Cross-page conflicts resolved during consolidation (page, name) -> (verdict, why).
# Everything else comes straight from the per-row agent verdicts.
OVERRIDES: dict[tuple[str, str], tuple[str, str]] = {}

# Rows the agent passes missed (key drift or scope gap), adjudicated during
# consolidation with the same evidence standard. (page, name, players_or_"") ->
# {verdict, why, slug}. The gl page was resolved to catalog giuliano-lodola in
# the parser stage, so no agent had it in scope; the bem keys drifted on
# parenthetical suffixes; ceff was the hand-authored pilot (patch 0081).
SUPPLEMENTAL: dict[tuple[str, str], dict] = {
    ("bem", "Arabic Power"): {
        "verdict": "exists", "slug": "arabic-power",
        "why": "Catalog holds it maker-less (ipdb 5636, 'Unknown Manufacturer'); IPDB: 'purported to be BEM of Milano, Italy, but we have no information to support this' — CE assignment deferred, evidence banked.",
    },
    ("bem", "Ascot"): {
        "verdict": "exists", "slug": "ascot",
        "why": "Catalog holds it maker-less (ipdb 5965); IPDB: 'Reportedly, the manufacturer is BEM but this has not been confirmed by us' — CE assignment deferred, evidence banked.",
    },
    ("bem", "Urania"): {"verdict": "create", "why": "BEM small-head EM, tilt.it only (agent verdict, key drift)."},
    ("ceff", "Five Martians"): {"verdict": "exists", "slug": "five-martians", "why": "Created by the hand-authored pilot patch 0081."},
    ("ceff", "Joker Ball"): {"verdict": "defer", "why": "tilt.it itself is unsure it names a second model or a Five Martians feature (pilot decision, patch 0081 comment)."},
    ("dalla-pria-abm", "Stellar Airship"): {
        "verdict": "defer", "slug": "stellar-airship",
        "why": "Model-level conflict left open: catalog stellar-airship is Geiger's (ipdb 4016 notes are FIRST-PARTY from Mr. Geiger: 1979 SS conversion of Bally's Eight Ball, artist Mike Martinelli did all Geiger kits), while tilt.it shows Dalla Pria/ABM selling an EM-Gottlieb kit of the same name and artist. Possibly a rebadged/licensed Italian edition, possibly a distinct kit. No duplicate created; evidence banked. The MANUFACTURER Dalla Pria is created regardless on its own first-party evidence (dallapria.it: in games since 1958, direct producer; per user ruling first-party sites take priority).",
    },
    ("gl", "????"): {"verdict": "defer", "why": "Machine with unreadable/unknown name on the GL page — unnameable, cannot create."},
    ("gl", "Jolly Joker"): {
        "verdict": "exists", "slug": "jolly-joker-3",
        "why": "IPDB 4113 attributes the Jolly Joker kit to Mondialmatic (conversion kit for Gottlieb's 1973 Ten-Up); tilt.it lists it on the GL page too — conflict noted, no duplicate created.",
    },
    ("gl", "Diablo"): {"verdict": "create", "why": "GL (giuliano-lodola) 1980 ss 4p, tilt.it only; no IPDB entry."},
    ("gl", "Space Woman"): {
        "verdict": "exists", "slug": "space-woman",
        "why": "Catalog holds it maker-less (ipdb 5951, 'Unknown Manufacturer'); tilt.it itself hedges the maker ('GL ?') — CE assignment deferred, evidence banked.",
    },
}

SMART = {"“": '"', "”": '"', "‘": "'", "’": "'"}


def normalize(text: str) -> str:
    for a, b in SMART.items():
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text)


def canon(s: str) -> str:
    """Loose key for matching agent rows back to worksheet rows."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = normalize(s).lower()
    return re.sub(r"[^a-z0-9]+", "", s)


def main() -> None:
    scratch = Path(sys.argv[1])
    ws_rows = list(csv.DictReader((HERE / "worksheet.csv").open()))

    # --- load agent rows into a lookup -----------------------------------
    agent_rows: list[dict] = []
    for fname in (
        "review-newmakers.json",
        "review-bem-group.json",
        "review-longtail.json",
        "review-kits.json",
    ):
        d = json.loads((scratch / fname).read_text())
        rows = d["rows"]
        page_default = d.get("page", "")
        for r in rows:
            r = dict(r)
            r.setdefault("page", page_default or "ipdb-flipper-kit-italiani-non-identificati")
            agent_rows.append(r)

    by_line: dict[int, dict] = {}
    by_key: dict[tuple[str, str], dict] = {}
    for r in agent_rows:
        if isinstance(r.get("line"), int):
            by_line[r["line"]] = r
        k = (r["page"], canon(r.get("raw_line") or r.get("name") or ""))
        by_key.setdefault(k, r)
        nk = (r["page"], canon(r.get("name") or ""))
        by_key.setdefault(nk, r)

    # --- web cache for quote verification --------------------------------
    sys.path.insert(0, "scripts/web_scrape")
    import web_cache  # noqa: E402

    page_text: dict[str, str] = {}

    def cache_text(page: str) -> str:
        if page not in page_text:
            url = f"https://www.tilt.it/flipper_pinball/ipdb/{page}"
            rec = web_cache.get(url)
            page_text[page] = normalize(rec["text"]) if rec else ""
        return page_text[page]

    def find_quote(page: str, *candidates: str) -> str:
        text = cache_text(page)
        for c in candidates:
            c = normalize(c or "").strip()
            if c and c in text:
                return c
        return ""

    out_rows = []
    sources_rows = []
    unmatched = 0
    for i, w in enumerate(ws_rows, start=2):  # worksheet line numbers incl. header
        r = by_line.get(i)
        if r is None:
            r = by_key.get((w["page"], canon(w["raw_line"]))) or by_key.get(
                (w["page"], canon(w["name"]))
            )
        if r is None:
            # rows the parser already matched confidently (disposition exists,
            # no review flag) were out of the agents' scope — keep as exists
            if w["disposition"].startswith("exists") and not w["review"]:
                verdict, why, slug = "exists", "parser high-confidence match", w["catalog_slug"]
                fields, lineage, conflict = {}, "", ""
            else:
                verdict, why, slug = "UNMATCHED", "no agent verdict found", ""
                fields, lineage, conflict = {}, "", ""
                unmatched += 1
        else:
            verdict = r.get("verdict", "UNMATCHED")
            why = r.get("why") or r.get("reason") or ""
            slug = r.get("catalog_slug") or r.get("possible_catalog_slug") or ""
            fields = r.get("fields") or r.get("fields_if_created") or {}
            lineage = r.get("lineage") or fields.get("lineage") or ""
            conflict = ""
            c = r.get("conflict")
            if c:
                conflict = c if isinstance(c, str) else json.dumps(c)
            for ts in r.get("third_sources") or []:
                if isinstance(ts, str):
                    ts = {"url": ts}
                sources_rows.append(
                    {
                        "page": w["page"],
                        "name": w["name"],
                        "url": ts.get("url", ""),
                        "supports": ts.get("supports") or ts.get("fact") or "",
                        "quote": ts.get("quote") or ts.get("quote_candidate") or "",
                    }
                )

        sup = SUPPLEMENTAL.get((w["page"], w["name"]))
        if sup and verdict == "UNMATCHED":
            verdict, why = sup["verdict"], sup["why"]
            slug = sup.get("slug", slug)

        ov = OVERRIDES.get((w["page"], w["name"]))
        if ov:
            verdict, why = ov[0], f"{ov[1]} (override; agent said: {verdict})"

        quote = ""
        if verdict in ("create", "reassign"):
            quote = find_quote(w["page"], w["raw_line"], w["name"])

        out = dict(w)
        out.update(
            {
                "verdict": verdict,
                "verdict_why": why,
                "final_catalog_slug": slug,
                "agent_fields": json.dumps(fields, ensure_ascii=False) if fields else "",
                "lineage": lineage if isinstance(lineage, str) else json.dumps(lineage, ensure_ascii=False),
                "conflict": conflict,
                "quote": quote,
            }
        )
        out_rows.append(out)

    fieldnames = list(ws_rows[0].keys()) + [
        "verdict", "verdict_why", "final_catalog_slug", "agent_fields",
        "lineage", "conflict", "quote",
    ]
    with (HERE / "reviewed.csv").open("w", newline="") as f:
        wtr = csv.DictWriter(f, lineterminator="\n", fieldnames=fieldnames)
        wtr.writeheader()
        wtr.writerows(out_rows)
    with (HERE / "third-sources.csv").open("w", newline="") as f:
        wtr = csv.DictWriter(f, lineterminator="\n", fieldnames=["page", "name", "url", "supports", "quote"])
        wtr.writeheader()
        wtr.writerows(sources_rows)

    from collections import Counter
    counts = Counter(r["verdict"] for r in out_rows)
    print("verdicts:", dict(counts))
    print("unmatched:", unmatched)
    missing_quotes = [r for r in out_rows if r["verdict"] in ("create", "reassign") and not r["quote"]]
    print("creates lacking a verified quote:", len(missing_quotes))
    for r in missing_quotes[:15]:
        print("  ", r["page"], "|", r["name"], "|", r["raw_line"][:60])


if __name__ == "__main__":
    main()
