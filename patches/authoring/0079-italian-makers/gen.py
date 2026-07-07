"""Emit the Italian-sweep patches (one vertical patch per manufacturer).

Run from the **flipcommons backend** (needs Django for ref resolution), with
the pinexplore web cache present as a sibling checkout:

    cd ../flipcommons/backend && uv run python \
        ../../flippatch/patches/authoring/0079-italian-makers/gen.py

Reads the frozen ``reviewed.csv`` (verdicts + cache-verified quotes from
consolidate.py) and emits, starting at patch 0085:

- one patch per NEW maker: manufacturer → corporate entity → titles → models,
  dependency-ordered within the file (the 0081 CEFF pilot layout);
- one patch per EXISTING maker gaining models: titles → models;
- a final maker-less patch for the unidentified-kits section.

Every quote is re-verified verbatim against the pinexplore web cache before
being written; any miss aborts the run. Editorial row fixes applied here (and
their reasons) live in ROW_FIXES/ROW_DROPS below — the audit trail for why a
generated entry differs from its worksheet row.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
import sys
import unicodedata
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

from apps.catalog.models import CorporateEntity, MachineModel, Manufacturer, Title  # noqa: E402
from django.utils.text import slugify  # noqa: E402

TILT = "https://www.tilt.it/flipper_pinball/ipdb"
FIRST_PATCH_NUM = 83

# ---------------------------------------------------------------- new makers
# Facts and verbatim heading/city quotes per new maker (from the adjudication
# pass; quotes re-verified against the cache below). city=None → no location
# (tilt.it prints "(??)" — unknown; the rule is city-level or nothing).
NEW_MAKERS: dict[str, dict] = {
    "bontempi": {
        "manufacturer": ("bontempi", "Bontempi", []),
        "ce": ("bontempi", "Bontempi", []),
        "city": "italy/rm/rome",
        "heading_quote": "Bontempi",
        "city_quote": "(Roma, Italy)",
        "note": "The tilt.it Italian Pinball Database credits Bontempi of Rome with one pinball machine; corroborating sources were sought at authoring time and none found.",
    },
    "dalla-pria-abm": {
        "manufacturer": ("dalla-pria", "Dalla Pria", ["Dalla Pria-ABM"]),
        "ce": ("dalla-pria-abm-electronics", "Dalla Pria/ABM Electronics srl", []),
        "city": "italy/pd/piove-di-sacco",
        "heading_quote": "Dalla Pria/ABM Electronics srl",
        "city_quote": "(Piove di Sacco – PD)",
        "note": "tilt.it lists a Dalla Pria/ABM Electronics pinball conversion kit; the firm's own site describes the Dalla Pria group of Piove di Sacco as an amusement-machine producer and distributor in the game sector since 1958.",
        "extra_changesets": [
            {
                "fields": {"operating_status": "ongoing"},
                "note": "The firm's own site says it has operated in the game sector since 1958.",
                "cite": {
                    "ref": "https://www.dallapria.it/",
                    "quote": "Il Gruppo DALLA PRIA opera nel settore dei videogame dal 1958.",
                },
                "target": "corporate-entity",  # operating_status lives on the corporate entity (0049 precedent)
            }
        ],
    },
    "ferna": {
        "manufacturer": ("ferna", "Ferna", []),
        "ce": ("ferna-srl", "Ferna srl", []),
        "city": None,
        "heading_quote": "Ferna srl",
        "city_quote": None,
        "note": "The tilt.it Italian Pinball Database credits Ferna srl with one pinball machine (city unknown — tilt.it prints \"(???)\"); corroborating sources were sought at authoring time and none found.",
    },
    "italiana-biliardi": {
        "manufacturer": ("italiana-biliardi", "Italiana Biliardi", []),
        "ce": ("italiana-biliardi", "Italiana Biliardi", []),
        "city": None,
        "heading_quote": "Italiana Biliardi",
        "city_quote": None,
        "note": "The tilt.it Italian Pinball Database credits Italiana Biliardi (Sig. G. Onorato; city unknown) with one pinball machine; corroborating sources were sought at authoring time and none found.",
    },
    "pc": {
        "manufacturer": ("pc", "P.C.", []),
        "ce": ("pc", "P.C.", []),
        "city": None,
        "heading_quote": "P.C.",
        "city_quote": None,
        "note": "The tilt.it Italian Pinball Database credits P.C. (city unknown — tilt.it prints \"(??)\") with the machine Marte; the maker's mark appears on the machine's own instruction card.",
    },
    "riflip": {
        "manufacturer": ("riflip", "RIFLIP", []),
        "ce": ("riflip-organizzazione-costa", "RIFLIP – Organizzazione Costa", []),
        "city": "italy/to/turin",
        "heading_quote": "RIFLIP – Organizzazione Costa",
        "city_quote": "(Torino, Italy)",
        "note": "The tilt.it Italian Pinball Database credits RIFLIP – Organizzazione Costa of Turin with one pinball machine; corroborating sources were sought at authoring time and none found.",
    },
    "sidam": {
        "manufacturer": ("sidam", "Sidam", ["SIPEM"]),
        "ce": ("sidam", "SIDAM", ["SIPEM"]),
        "city": "italy/to/turin",
        "heading_quote": "SIDAM/SIPEM",
        "city_quote": "(Torino, Italy)",
        "note": "Turin coin-op maker, best known for video games; tilt.it lists its one pinball-style machine. Renamed SIPEM late in its arcade era, kept as an alias (one corporate entity until a source separates them).",
    },
}

# ------------------------------------------------- existing-maker CE mapping
# Per-page corporate entity for creates under existing makers. Derived from
# the page's already-matched models where unambiguous; hand-set where a page
# spans corporate eras (bell-games) or names differ (elettronolo → the firm
# the catalog holds as elettrocoin).
PAGE_CE: dict[str, str] = {
    "artigiana-ricambi": "ditta-artigiana-ricambi",
    "bell-games": "bell-coin-matics",  # the one create is 1979, the Bell Coin Matics era (ipdb window 1978-1980)
    "bem": "bigliardini-elettronici-milano",  # brand BEM = B.E.M., Bigliardini Elettronici Milano
    "bensa": "bensa-sas",
    "cea": "costruzioni-elettroniche-automatiche",
    "dama": "dama-srl",
    "elettronolo": "elettrocoin",
    "emmepi": "emmepi",
    "europlay": "europlay",
    "gl": "giuliano-lodola",
    "lori": "lori",
    "mambelli": "l-v-mambelli",
    "manilamatic": "mm-computer-games",  # brand ManilaMatic's corporate entity
    "model-racing": "model-racing",
    "pasini": "pasini",
    "rmg": "renato-montanari-giochi",  # the plain RMG era (the Skillgame d.b.a. entity is the skill-game page's)
    "skill-game-the-best": None,  # resolved from DB below (long dba slug)
    "zaccaria": "zaccaria",
}

# ------------------------------------------------------------- row-level fixes
# (page, name, tech) -> field overrides, each with a reason (audit trail).
ROW_FIXES: dict[tuple[str, str, str], dict] = {
    # tilt.it's manilamatic page year header is unreliable: the agent found
    # Joker copies Premier's 1987 Monte Carlo (a 1976 date is impossible) and
    # itmade.htm dates the page's Enada III reference to 1974, contradicting
    # the 1976 header. Years dropped for both creates; kept in notes.
    ("manilamatic", "Joker", "ss"): {"year": None, "reason": "1976 header impossible for a copy of Premier's 1987 Monte Carlo"},
    ("manilamatic", "Pool Rabbit", "ss"): {"year": None, "reason": "same unreliable 1976 header"},
}

# (page, raw_line-prefix) -> reason. Rows dropped at generation.
ROW_DROPS: dict[tuple[str, str], str] = {
    # Duplicate of the same page's main Urania row (photo-section repeat the
    # review pass marked noise under a raw_line the worksheet stored differently).
    ("bem", "Urania (testa piccola)"): "keep",  # sentinel: the OTHER Urania row is dropped
    # An unnamed modification kit for Zaccaria's Space Shuttle — no product
    # name exists to create a record under (uncertain name, like Bensa's
    # "???"); deferred with the evidence in the README.
    ("pinball-shop", "Kit di modifica"): "unnameable kit — deferred",
}

# Per-machine hedge notes for kits-page creates tilt.it comments on
# individually (everything else gets the section-membership note).
KIT_HEDGE_NOTES = {
    "Aquarium": 'tilt.it hedges the kit reading itself ("looks like an italian kit inspired from the Gottlieb\'s Aquarius")',
    "Card Trix": "tilt.it's per-machine remark distinguishes it from RMG's version rather than describing the kit; the tag rests on the section's membership",
}

# Seeded IPDB models on the same kits page that carry explicit per-machine
# "(kit for ...)" statements — tagged here so the whole section reviews as one
# unit. slug -> (quote or None, extra note or None).
SEEDED_KIT_TAGS: dict[str, tuple[str | None, str | None]] = {
    "tex-op": ("Tex-Op (kit for Gottlieb's Harmony/Troubadour)", None),
    "bowling": ('Bowling (kit for Gottlieb\'s "Harmony"/"Troubadour")', None),
    "el-viti": ("El Viti (kit for Gottlieb's Harmony/Troubadour)", None),
    "el-tigre": ("El Tigre (kit with ss scoring for em machines)", None),
    "new-city": ('New City (kit from the early seventies for Williams\' games "Hot Line" and "Big Strike"', None),
    "grand-slam-10": (
        "Grand Slam (forse kit RMG per Ice Show Gottlieb)",
        'tilt.it hedges the attribution ("forse" - maybe an RMG kit for Gottlieb\'s Ice Show), not the kit reading.',
    ),
    "lido-2": (
        'Lido (looks like a kit for a Gottlieb\'"Subway" – maybe from Dama – art by Cortez?)',
        'tilt.it hedges ("looks like a kit"); the maker guess (Dama? art by Cortez?) stays open.',
    ),
}

TECH_MAP = {"em": "electromechanical", "ss": "solid-state"}

# (page, name) -> game_format override. Default is pinball; tilt.it labels
# Sidam's Rugby "(video-pinball)" — a video game in a pinball-style cabinet,
# classified video-game per the patch-0038 convention.
GAME_FORMAT_FIXES = {("sidam", "Rugby"): "video-game"}

# Hosts whose website roots are seeded (this patch series or earlier) — a
# third-source cite outside these can't resolve and goes to the ledger instead.
SEEDED_HOSTS = (
    "tilt.it", "dallapria.it", "retrocampus.com", "zaccaria-pinball.com",
    "arcade-museum.com", "pinside.com", "vpforums.org", "recreativas.org",
    "en.wikipedia.org", "de.wikipedia.org", "pinballnews.com", "flipper-news.de",
)


def norm_text(t: str) -> str:
    for a, b in {"“": '"', "”": '"', "‘": "'", "’": "'"}.items():
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


class QuoteChecker:
    def __init__(self) -> None:
        self.db = sqlite3.connect(str(PINEXPLORE / "ingest_sources/web/cache.sqlite"))
        self.cache: dict[str, str] = {}
        self.failures: list[str] = []

    def text(self, url: str) -> str:
        key = url.rstrip("/")
        if key not in self.cache:
            # the cache strips trailing slashes except on a bare domain root
            row = self.db.execute(
                "SELECT text FROM pages WHERE url IN (?, ?)", (key, key + "/")
            ).fetchone()
            self.cache[key] = norm_text(row[0]) if row and row[0] else ""
        return self.cache[key]

    def check(self, url: str, quote: str, label: str) -> None:
        if norm_text(quote) not in self.text(url):
            self.failures.append(f"{label}: quote not verbatim in {url}: {quote[:70]}")


def main() -> None:
    rows = list(csv.DictReader((HERE / "reviewed.csv").open()))
    creates = [r for r in rows if r["verdict"] in ("create", "reassign")]

    qc = QuoteChecker()

    # Resolve the skill-game CE from the DB (slug too gnarly to hardcode).
    skill = CorporateEntity.objects.filter(slug__startswith="skillgame").first()
    if skill:
        PAGE_CE["skill-game-the-best"] = skill.slug
    missing_ce = [
        p for p, s in PAGE_CE.items() if s and not CorporateEntity.objects.filter(slug=s).exists()
    ]
    if missing_ce:
        sys.exit(f"PAGE_CE slugs not in catalog: {missing_ce}")

    # slug registries: catalog + this run
    taken_model = set(MachineModel.objects.values_list("slug", flat=True))
    taken_title = set(Title.objects.values_list("slug", flat=True))
    taken_mfr = set(Manufacturer.objects.values_list("slug", flat=True))
    taken_ce = set(CorporateEntity.objects.values_list("slug", flat=True))

    def fresh(base: str, taken: set, maker: str) -> str:
        s = base
        if s in taken:
            s = f"{base}-{maker}"
        n = 2
        while s in taken:
            s = f"{base}-{maker}-{n}"
            n += 1
        taken.add(s)
        return s

    # group creates by page
    by_page: dict[str, list[dict]] = {}
    dropped: list[str] = []
    seen_dup: set[tuple] = set()
    for r in creates:
        page, name = r["page"], r["name"]
        drop = next(
            (why for (p, pref), why in ROW_DROPS.items() if why != "keep" and p == page and r["raw_line"].startswith(pref)),
            None,
        )
        if drop:
            dropped.append(f"{page}/{name}: {drop}")
            continue
        fields = json.loads(r["agent_fields"]) if r["agent_fields"] else {}
        tech = (r["tech"] or fields.get("technology") or "").strip().lower()
        tech = tech if tech in TECH_MAP else ""  # "em (implied)" etc. → not asserted
        players = (r["players"] or str(fields.get("players") or "")).strip()
        players = players if players.isdigit() else ""
        year = (r["year"] or str(fields.get("year") or "")).strip()
        year = year if re.fullmatch(r"(19|20)\d{2}", year) else ""
        fix = ROW_FIXES.get((page, name, tech))
        if fix and "year" in fix and fix["year"] is None:
            year = ""
        kit = str(fields.get("kit", "")).strip().lower() == "true"
        month = ""
        pm = re.fullmatch(r"(\d{1,2})/(\d{2})", (r["prod"] or "").replace("?", ""))
        if pm and year and year.endswith(pm.group(2)):
            month = str(int(pm.group(1)))
        dup_key = (page, name.lower(), tech, players, year)
        if dup_key in seen_dup:
            dropped.append(f"{page}/{name}: duplicate row (same name/tech/players/year)")
            continue
        seen_dup.add(dup_key)
        by_page.setdefault(page, []).append(
            {
                "name": name,
                "verdict": r["verdict"],
                "tech": tech,
                "players": players,
                "year": year,
                "year_uncertain": r["year_uncertain"],
                "month": month,
                "kit": kit,
                "quote": r["quote"],
                "raw_line": r["raw_line"],
                "lineage": r["lineage"],
                "parens": r["parens"],
                "notes": r["notes"],
                "slug_hint": r["final_catalog_slug"],
            }
        )

    # Third-party sources found by the review pass: (page, name) -> specs.
    # A verified quote joins the entry's cite list (multi-source evidence);
    # an unverifiable or unrooted one is reported and stays ledger-only.
    third: dict[tuple[str, str], list[dict]] = {}
    third_path = HERE / "third-sources.csv"
    ledger_only: list[str] = []
    if third_path.exists():
        for t in csv.DictReader(third_path.open()):
            if t["url"] and t["quote"]:
                third.setdefault((t["page"], t["name"]), []).append(t)

    def cite_list(url: str, quote: str, page: str, name: str):
        specs: list = [{"ref": url, "quote": quote}]
        seen = {(url, pk.clean_quote(quote))}
        for t in third.get((page, name), []):
            if (t["url"], pk.clean_quote(t["quote"])) in seen:
                continue
            seen.add((t["url"], pk.clean_quote(t["quote"])))
            host = re.sub(r"^https?://(www\.)?", "", t["url"]).split("/")[0]
            if not any(host == h or host.endswith("." + h) for h in SEEDED_HOSTS):
                ledger_only.append(f"{page}/{name}: no seeded root for {t['url']}")
                continue
            if norm_text(t["quote"]) in qc.text(t["url"]):
                specs.append({"ref": t["url"], "quote": t["quote"]})
            else:
                ledger_only.append(f"{page}/{name}: quote not verbatim at {t['url']}")
        return specs if len(specs) > 1 else specs[0]

    def model_entries(page: str, machines: list[dict], ce_slug: str | None, maker_key: str) -> list[str]:
        """Title + model entries for one page's creates (titles shared by name)."""
        url = f"{TILT}/{page}"
        out: list[str] = []
        title_slug_by_name: dict[str, str] = {}
        for m in machines:
            if m["verdict"] == "reassign":
                continue
            nm = m["name"]
            if nm.lower() not in title_slug_by_name:
                tslug = fresh(slugify(nm), taken_title, maker_key)
                title_slug_by_name[nm.lower()] = tslug
                qc.check(url, m["quote"], f"title.{tslug}")
                out.append(
                    pk.entry(
                        f"title.{tslug}",
                        create=True,
                        note=f"Title for {nm}, per the tilt.it Italian Pinball Database.",
                        cite={"ref": url, "quote": m["quote"]},
                        fields={"name": nm},
                    )
                )
        for m in machines:
            url_ = url
            nm = m["name"]
            if m["verdict"] == "reassign":
                # adopt an orphaned catalog model (P.C.'s Marte)
                qc.check(url_, m["quote"], f"model-reassign {nm}")
                out.append(
                    pk.entry(
                        f"model.{m['slug_hint']}",
                        note="flipcommons previously held this with no maker (IPDB lists the manufacturer as unknown); tilt.it identifies the maker, whose mark the machine itself carries.",
                        cite={"ref": url_, "quote": m["quote"]},
                        fields={"corporate_entity": ce_slug},
                    )
                )
                continue
            mslug = fresh(slugify(nm), taken_model, maker_key)
            note_bits = []
            if not m["year"]:
                note_bits.append("tilt.it gives no year")
            elif m["year_uncertain"]:
                note_bits.append(f"tilt.it marks the {m['year']} year uncertain (\"(?)\")")
            if not m["tech"]:
                note_bits.append("no technology is stated")
            if m["lineage"]:
                note_bits.append(f"lineage per the source line: {m['lineage']}")
            if m["kit"]:
                note_bits.append("sold as a conversion kit")
            note = ("; ".join(note_bits) + "." if note_bits else None)
            fields: dict = {"name": nm, "title": title_slug_by_name[nm.lower()]}
            if ce_slug:
                fields["corporate_entity"] = ce_slug
            if m["year"]:
                fields["year"] = int(m["year"])
            if m["month"]:
                fields["month"] = int(m["month"])
            if m["tech"]:
                fields["technology_generation"] = TECH_MAP[m["tech"]]
            if m["players"]:
                fields["player_count"] = int(m["players"])
            fields["game_format"] = GAME_FORMAT_FIXES.get((page, nm), "pinball")
            qc.check(url_, m["quote"], f"model.{mslug}")
            on_kits_page = page.startswith("ipdb-flipper-kit")
            if on_kits_page and not m["kit"]:
                # The whole section is tilt.it's unidentified-Italian-kits
                # archive; a machine it files there is tagged on that
                # membership even when the page states no per-machine detail.
                m["kit"] = True
                extra = KIT_HEDGE_NOTES.get(
                    nm,
                    "tagged conversion-kit on the section's membership (tilt.it files it among the unidentified Italian kits); the page states no per-machine kit detail",
                )
                note = (note + " " if note else "") + extra.rstrip(".") + "."
            tags = ["conversion-kit"] if m["kit"] else None
            out.append(
                pk.entry(
                    f"model.{mslug}",
                    create=True,
                    note=note,
                    cite=cite_list(url_, m["quote"], page, nm),
                    fields=fields,
                    tags=tags,
                )
            )
        return out

    num = FIRST_PATCH_NUM
    written: list[str] = []

    def write(name: str, description: str, entries: list[str]) -> None:
        nonlocal num
        path = PATCHES / f"{num:04d}-{name}.yaml"
        pk.write_patch(path, attribution="flipcommons-catalog", description=description, entries=entries)
        written.append(path.name)
        num += 1

    # --- new-maker patches (alphabetical) --------------------------------
    for page in sorted(NEW_MAKERS):
        spec = NEW_MAKERS[page]
        url = f"{TILT}/{page}"
        mslug, mname, maliases = spec["manufacturer"]
        cslug, cname, caliases = spec["ce"]
        if mslug in taken_mfr or cslug in taken_ce:
            sys.exit(f"maker slug collision: {mslug}/{cslug}")
        entries = []
        qc.check(url, spec["heading_quote"], f"manufacturer.{mslug}")
        entries.append(
            pk.entry(
                f"manufacturer.{mslug}",
                create=True,
                note=spec["note"],
                cite={"ref": url, "quote": spec["heading_quote"]},
                fields={"name": mname},
                relationships={"manufacturer_alias": maliases} if maliases else None,
            )
        )
        ce_fields: dict = {"name": cname, "manufacturer": mslug}
        ce_rels = {"corporate_entity_alias": caliases} if caliases else None
        ce_changesets = []
        if spec["city"]:
            qc.check(url, spec["city_quote"], f"corporate-entity.{cslug} city")
            ce_changesets.append(
                {
                    "relationships": {"location": [spec["city"]]},
                    "cite": {"ref": url, "quote": spec["city_quote"]},
                }
            )
        entries.append(
            pk.entry(
                f"corporate-entity.{cslug}",
                create=True,
                note=f"Corporate entity of {mname}, per the tilt.it Italian Pinball Database.",
                cite={"ref": url, "quote": spec["heading_quote"]},
                fields=ce_fields,
                relationships=ce_rels,
                changesets=ce_changesets or None,
            )
        )
        for extra in spec.get("extra_changesets", []):
            qc.check(extra["cite"]["ref"], extra["cite"]["quote"], f"{mslug} extra")
            entries.append(
                pk.entry(
                    f"manufacturer.{mslug}" if extra["target"] == "manufacturer" else f"corporate-entity.{cslug}",
                    note=extra["note"],
                    cite=extra["cite"],
                    fields=extra["fields"],
                )
            )
        entries.extend(model_entries(page, by_page.get(page, []), cslug, mslug))
        write(page if page != "dalla-pria-abm" else "dalla-pria", f"{mname}: maker, corporate entity and machines, per tilt.it (IPDB.it).", entries)

    # --- existing-maker patches (alphabetical) ----------------------------
    for page in sorted(p for p in by_page if p not in NEW_MAKERS and not p.startswith("ipdb-flipper-kit")):
        ce_slug = PAGE_CE.get(page)
        if ce_slug is None and page in PAGE_CE:
            sys.exit(f"unresolved CE for page {page}")
        if page not in PAGE_CE:
            sys.exit(f"page {page} has creates but no PAGE_CE mapping")
        ce = CorporateEntity.objects.get(slug=ce_slug)
        brand = ce.manufacturer.name if ce.manufacturer_id else ce.name
        entries = model_entries(page, by_page[page], ce_slug, slugify(ce.manufacturer.slug if ce.manufacturer_id else ce_slug))
        write(f"italian-models-{page}", f"{brand}: additional machines from tilt.it (IPDB.it).", entries)

    # --- maker-less kits ---------------------------------------------------
    kits_pages = [p for p in by_page if p.startswith("ipdb-flipper-kit")]
    if kits_pages:
        entries = []
        for page in kits_pages:
            entries.extend(model_entries(page, by_page[page], None, "kit"))
        kits_url = f"{TILT}/ipdb-flipper-kit-italiani-non-identificati"
        for slug, (quote, extra) in SEEDED_KIT_TAGS.items():
            if not MachineModel.objects.filter(slug=slug).exists():
                sys.exit(f"SEEDED_KIT_TAGS slug not in catalog: {slug}")
            if quote:
                qc.check(kits_url, quote, f"kit-tag {slug}")
            entries.append(
                pk.entry(
                    f"model.{slug}",
                    note=extra,
                    cite={"ref": kits_url, "quote": quote} if quote else kits_url,
                    tags=["conversion-kit"],
                )
            )
        write(
            "italian-unidentified-kits",
            "Italian conversion kits whose makers tilt.it cannot identify.",
            entries,
        )

    if qc.failures:
        print("\nQUOTE FAILURES:")
        for f in qc.failures:
            print(" ", f)
        sys.exit(1)
    print("wrote:", *written, sep="\n  ")
    if ledger_only:
        print("third sources kept ledger-only:")
        for x in ledger_only:
            print("  ", x)
    if dropped:
        print("dropped rows:")
        for d in dropped:
            print("  ", d)


if __name__ == "__main__":
    main()
