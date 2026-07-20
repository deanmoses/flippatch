"""Parse the cached tilt.it IPDB.it manufacturer pages into a gap-analysis worksheet.

Run from the **pinexplore** repo root (needs the web cache and explore.duckdb):

    uv run python ../flippatch/campaigns/0079-italian-makers/classify.py

Reads the tilt.it pages already fetched into the pinexplore web cache
(ingest_sources/web/cache.sqlite + raw blobs), parses each manufacturer page's
machine list, cross-references every machine against the flipcommons catalog
(models), the IPDB dump (ipdb_machines) and the OPDB dump (opdb_machines) in
explore.duckdb, and writes two review worksheets next to this script:

- makers.csv    — one row per tilt.it maker page: heading names, city line,
                  candidate catalog manufacturer/corporate-entity matches.
- worksheet.csv — one row per machine line: parsed fields (name, year,
                  year_uncertain, tech, players, parenthetical notes), the raw
                  source line (verbatim evidence pointer), catalog/IPDB/OPDB
                  match candidates with confidence, and a computed disposition.

The parse is deliberately conservative: anything it cannot classify with
confidence lands in the worksheet flagged ``review=yes`` rather than being
dropped. Dispositions are frozen only after the human review pass (see
README.md).
"""

from __future__ import annotations

import csv
import html
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
CACHE = Path("ingest_sources/web/cache.sqlite")
RAW = Path("ingest_sources/web/raw")
EXPLORE = Path("explore.duckdb")

BASE = "https://www.tilt.it/flipper_pinball/ipdb"

# ---------------------------------------------------------------- HTML → lines

CONTENT_START = 'class="entry-content"'
CONTENT_END = "</article>"

TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br[^>]*>", re.I)
BLOCK_RE = re.compile(r"<(h1|h2|h3|address|p|div|li)[^>]*>", re.I)
ANCHOR_IMG_RE = re.compile(r"<a\b[^>]*>\s*<img[^>]*>\s*</a>|<img[^>]*>", re.I | re.S)

# Caption / boilerplate lines that are photo credits or UI text, not data.
NOISE_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"clicca per ingrandire",
        r"click (on the images|to enlarge)",
        r"^\(?\s*collezione\b",
        r"^\(?\s*dalla collezione\b",
        r"^\(?\s*sala-?giochi\b",
        r"^\(?\s*pictures? (from|courtesy)\b",
        r"^\(?\s*foto\b",
        r"^\(?\s*photos?\b",
        r"^\(?\s*courtesy\b",
        r"^\(?\s*grazie a\b",
        r"^\(?\s*thanks to\b",
        r"^\(?\s*si ringrazia\b",
        r"^\[?translate\]?$",
        r"^\[?翻译\]?$",
        r"^condividi:",
        r"^share this:",
    )
]

YEAR_RE = re.compile(r"^[\s(–\-]*?(\?\s*)?[()\s]*((?:19|20)\d{2})\s*(\(\?\)|\?)?[\s):]*$")
# "1978-79", "1978/79" style ranges used as section headers
YEAR_RANGE_RE = re.compile(r"^\s*((?:19|20)\d{2})\s*[-–/]\s*(\d{2,4})\s*(\(\?\)|\?)?\s*$")

# Machine lines are dash-separated segments in page-dependent order:
#   "Name – em – 1p (notes)"  /  "Name – 1p – em"  /  "Name – ss – 4p – 01/80"
SEG_SPLIT_RE = re.compile(r"\s+[–—-]\s+")
TECH_SEG_RE = re.compile(r"^(?P<tech>em|ss|F)\b\s*(?P<rest>.*)$", re.I)
PLAYERS_SEG_RE = re.compile(r"^(?P<players>\d)\s*p\b\s*(?P<rest>.*)$", re.I)
PROD_SEG_RE = re.compile(r"^(?P<prod>[\d?]{1,2}/\d{2,4})$")


def extract_lines(raw_html: str) -> list[str]:
    """Reduce a tilt.it page's entry-content HTML to clean text lines."""
    i = raw_html.find(CONTENT_START)
    if i < 0:
        return []
    i = raw_html.find(">", i) + 1
    ends = [
        k
        for k in (
            raw_html.find(CONTENT_END, i),
            raw_html.find('class="sharedaddy', i),
            raw_html.find('id="jp-post-flair"', i),
        )
        if k > 0
    ]
    body = raw_html[i : min(ends) if ends else len(raw_html)]
    body = ANCHOR_IMG_RE.sub("", body)
    body = BR_RE.sub("\n", body)
    body = BLOCK_RE.sub("\n", body)
    text = TAG_RE.sub("", body)
    text = html.unescape(text)
    text = unicodedata.normalize("NFC", text)
    lines = []
    for ln in text.splitlines():
        ln = re.sub(r"\s+", " ", ln).strip()
        if ln and "<" not in ln and ">" not in ln:
            lines.append(ln)
    return lines


def is_noise(line: str) -> bool:
    return any(p.search(line) for p in NOISE_PATTERNS)


def parse_year(line: str) -> tuple[str, str] | None:
    """Return (year, uncertain) if the line is a year section marker."""
    m = YEAR_RE.match(line)
    if m:
        uncertain = "yes" if (m.group(1) or m.group(3)) else ""
        return m.group(2), uncertain
    m = YEAR_RANGE_RE.match(line)
    if m:
        return m.group(1), "yes" if m.group(3) else "range:" + m.group(0).strip()
    return None


# ------------------------------------------------------------------- matching


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    # "&" and "and" are used interchangeably across sources — drop both.
    s = s.replace("&", " ")
    s = re.sub(r"['’‘`]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\band\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


PLAYER_SUFFIX_RE = re.compile(r"\s*\((\d)\s*p\)\s*$", re.I)


def name_keys(name: str) -> list[str]:
    """Normalized lookup keys for a catalog/IPDB name — with and without a
    trailing player-variant suffix ("Wood's Queen (2P)")."""
    keys = [norm_name(name)]
    stripped = PLAYER_SUFFIX_RE.sub("", name)
    if stripped != name:
        keys.append(norm_name(stripped))
    return [k for k in keys if k]


LEGAL_SUFFIX_RE = re.compile(r"\b(s ?r ?l|s ?p ?a|s ?a ?s|s ?n ?c|co|inc|ltd|corp|company|electronics)\b")


def maker_key(s: str) -> str:
    """Normalized, suffix-stripped, space-collapsed key for maker-name matching."""
    n = LEGAL_SUFFIX_RE.sub(" ", norm_name(s))
    return n.replace(" ", "")


class Machine:
    def __init__(self, page: str, raw: str):
        self.page = page
        self.raw = raw
        self.name = ""
        self.parens: list[str] = []
        self.year = ""
        self.year_uncertain = ""
        self.tech = ""
        self.players = ""
        self.prod = ""
        self.name_uncertain = ""
        self.notes: list[str] = []
        self.review = ""


def parse_machine(line: str, page: str) -> Machine:
    m = Machine(page, line)
    # Mask parentheticals so dashes inside them don't split segments
    # ("Strike – 1p – em (home model, no coin door – sound card)").
    masked: list[str] = []

    def _mask(match: re.Match[str]) -> str:
        masked.append(match.group(0))
        return f"\x00{len(masked) - 1}\x00"

    def _unmask(s: str) -> str:
        return re.sub(r"\x00(\d+)\x00", lambda mm: masked[int(mm.group(1))], s)

    tmp = re.sub(r"\([^()]*\)", _mask, line)
    segs = [_unmask(s).strip() for s in SEG_SPLIT_RE.split(tmp)]
    head = segs[0]
    for seg in segs[1:]:
        if not seg:
            continue
        tm = TECH_SEG_RE.match(seg)
        pm = PLAYERS_SEG_RE.match(seg)
        dm = PROD_SEG_RE.match(seg)
        if tm and not m.tech:
            m.tech = tm.group("tech").lower()
            rest = tm.group("rest").strip()
            if m.tech == "f":
                m.tech = ""
                m.review = "yes"  # 'F' marker of unknown meaning
            if rest:
                # e.g. "ss (seven digit displays)" or "em ??/78"
                if PROD_SEG_RE.match(rest):
                    m.prod = rest
                else:
                    m.notes.append(rest)
        elif pm and not m.players:
            m.players = pm.group("players")
            rest = pm.group("rest").strip()
            if rest:
                m.notes.append(rest)
        elif dm and not m.prod:
            m.prod = dm.group("prod")
        else:
            m.notes.append(seg)
    # Pull trailing parentheticals off the name (may be the cloned original,
    # an artist credit, or a free-text note — humans disambiguate in review).
    while True:
        pm2 = re.match(r"^(?P<base>.+?)\s*\((?P<paren>[^()]*)\)\s*$", head)
        if not pm2:
            break
        m.parens.insert(0, pm2.group("paren").strip())
        head = pm2.group("base").strip()
    if "?" in m.parens:
        m.parens.remove("?")
        m.name_uncertain = "yes"
    # Some pages put tech/players/year inside the parenthetical instead of
    # dash segments: "Surf (1 player -em)", "Jackpot (em)", "Corsair (1976)".
    for paren in list(m.parens):
        if len(paren) > 30:
            continue
        ym = re.fullmatch(r"(19|20)\d{2}", paren)
        if ym and not m.year:
            m.year = paren
            m.parens.remove(paren)
            continue
        tm = re.search(r"\b(em|ss)\b", paren, re.I)
        pm3 = re.search(r"\b(\d)\s*p(?:layers?)?\b", paren, re.I)
        if tm and not m.tech:
            m.tech = tm.group(1).lower()
        if pm3 and not m.players:
            m.players = pm3.group(1)
        if (tm or pm3) and re.fullmatch(r"[\s\d]*p?[a-z]*\s*[-–]?\s*(em|ss)?[\s)]*", paren, re.I):
            m.parens.remove(paren)
    m.name = head
    if not m.name or len(m.name) > 60:
        m.review = "yes"
    return m


def main() -> None:
    if not CACHE.exists() or not EXPLORE.exists():
        sys.exit("run from the pinexplore repo root (needs ingest_sources/web/ and explore.duckdb)")

    db = sqlite3.connect(str(CACHE))
    pages = {
        url: sha
        for url, sha in db.execute(
            "SELECT url, content_sha FROM pages WHERE url LIKE ? AND url != ?",
            (BASE + "/%", BASE),
        )
    }
    if not pages:
        sys.exit("no tilt.it pages in the web cache — fetch them first")

    con = duckdb.connect(str(EXPLORE), read_only=True)

    # Catalog lookups, all pulled once and matched in Python (small data).
    cat_models = con.execute(
        "SELECT slug, name, corporate_entity_slug, year, ipdb_id, opdb_id FROM models"
    ).fetchall()
    cat_by_norm: dict[str, list[tuple]] = {}
    for row in cat_models:
        for k in name_keys(row[1]):
            if row not in cat_by_norm.get(k, []):
                cat_by_norm.setdefault(k, []).append(row)

    cat_by_ipdb = {row[4]: row for row in cat_models if row[4]}

    corp = con.execute("SELECT slug, name FROM corporate_entities").fetchall()
    manuf = con.execute("SELECT slug, name FROM manufacturers").fetchall()

    ipdb = con.execute(
        'SELECT IpdbId, Title, Manufacturer, DateOfManufacture, Players, TypeShortName FROM ipdb_machines'
    ).fetchall()
    ipdb_by_norm: dict[str, list[tuple]] = {}
    for row in ipdb:
        for k in name_keys(row[1] or ""):
            if row not in ipdb_by_norm.get(k, []):
                ipdb_by_norm.setdefault(k, []).append(row)

    opdb = con.execute(
        "SELECT opdb_id, name, manufacturer, manufacture_date FROM opdb_machines WHERE is_machine"
    ).fetchall()
    opdb_by_norm: dict[str, list[tuple]] = {}
    for row in opdb:
        opdb_by_norm.setdefault(norm_name(row[1] or ""), []).append(row)

    maker_rows = []
    machine_rows = []

    for url in sorted(pages):
        slug = url[len(BASE) + 1 :].strip("/")
        raw_path = RAW / f"{pages[url]}.html"
        raw_html = raw_path.read_text(errors="replace")
        tm = re.search(r"<title>([^<]*)</title>", raw_html)
        page_title = html.unescape(tm.group(1)).replace("– TILT.IT", "").strip() if tm else ""
        lines = [ln for ln in extract_lines(raw_html) if not is_noise(ln)]
        updated_line = next((ln for ln in lines if ln.lower().startswith("ultimo aggiornamento")), "")
        lines = [ln for ln in lines if ln != updated_line]
        if not lines:
            maker_rows.append({"page": slug, "heading": "", "city_line": "", "review": "EMPTY PAGE"})
            continue

        # Standard pages open with an h1 maker heading; gallery-style pages
        # (e.g. ad/) have no heading at all, so fall back to the <title>.
        tn = norm_name(page_title).replace(" ", "")
        if tn and tn in norm_name(lines[0]).replace(" ", ""):
            heading = lines[0]
            start = 1
        else:
            heading = page_title
            start = 0
        city_line = lines[start] if len(lines) > start and lines[start].startswith("(") else ""
        if city_line:
            start += 1

        # Candidate catalog makers by name overlap with any heading fragment.
        names = [n.strip() for n in re.split(r"[–—/]|(?:\s-\s)", heading) if n.strip()]
        cands = set()
        for n in names:
            nk = maker_key(n)
            if not nk:
                continue
            for cslug, cname in corp + manuf:
                ck = maker_key(cname)
                if nk == ck or (len(nk) > 3 and len(ck) > 3 and (nk in ck or ck in nk)):
                    cands.add(cslug)
        maker_rows.append(
            {
                "page": slug,
                "heading": heading,
                "city_line": city_line,
                "updated_line": updated_line,
                "catalog_candidates": " ".join(sorted(cands)),
                "review": "" if cands else "no catalog match",
            }
        )

        year = ""
        year_uncertain = ""
        current: Machine | None = None
        parsed: list[Machine] = []
        for line in lines[start:]:
            ym = parse_year(line)
            if ym:
                year, year_uncertain = ym
                current = None
                continue
            # Free-text commentary about the previous machine: parenthesized
            # lines, lines starting lowercase or with "*", and caption lines
            # ending with ":" ("sportello originale RMG:").
            if current is not None and (
                line.startswith("(") or line.startswith("*") or line[:1].islower()
            ):
                current.notes.append(line)
                continue
            if line.endswith(":"):
                continue
            mach = parse_machine(line, slug)
            # A line repeating the maker heading ("GL (Sig. Giuliano Lodola)")
            # is maker detail, not a machine.
            if maker_key(mach.name) and maker_key(mach.name) in {maker_key(n) for n in names}:
                continue
            if not mach.year:
                mach.year, mach.year_uncertain = year, year_uncertain
            current = mach
            parsed.append(mach)

        # IPDB match per machine. Confidence: "high" when the IPDB
        # manufacturer string names this page's maker; "med" when it's merely
        # an Italian manufacturer (clone-heavy makers often hit the American
        # original instead — never trust "low"/"med" without review).
        ipdb_picks: list[tuple[tuple | None, str]] = []
        for mach in parsed:
            nn = norm_name(mach.name)
            hits = ipdb_by_norm.get(nn, [])
            by_maker = [
                r for r in hits
                if any(maker_key(x) and maker_key(x) in maker_key(r[2] or "") for x in names)
            ]
            italy = [r for r in hits if "ital" in (r[2] or "").lower()]
            if by_maker:
                ipdb_picks.append((by_maker[0], "high"))
            elif italy:
                ipdb_picks.append((italy[0], "med"))
            elif hits:
                ipdb_picks.append((hits[0], "low"))
            else:
                ipdb_picks.append((None, ""))

        # Infer this page's catalog corporate entities from its confident
        # IPDB matches (keyed on ipdb_id, per the 0043 precedent) — catches
        # makers cataloged under another name (tilt.it "GL" = catalog
        # giuliano-lodola).
        ce_votes: dict[str, int] = {}
        for pick, conf in ipdb_picks:
            if pick is not None and conf == "high":
                cm = cat_by_ipdb.get(pick[0])
                if cm and cm[2]:
                    ce_votes[cm[2]] = ce_votes.get(cm[2], 0) + 1
        inferred = {ce for ce, n in ce_votes.items() if n >= 2}
        if inferred - cands:
            maker_rows[-1]["catalog_candidates"] = " ".join(sorted(cands | inferred))
            maker_rows[-1]["review"] = (maker_rows[-1]["review"] + " ipdb-inferred-ce").strip()
        cands |= inferred

        for mach, (ipdb_pick, ipdb_conf) in zip(parsed, ipdb_picks):
            nn = norm_name(mach.name)
            # Catalog match: ipdb_id-keyed when the IPDB match is confident,
            # else by normalized name.
            cat_pick, cat_conf = None, ""
            if ipdb_pick is not None and ipdb_conf == "high":
                cm = cat_by_ipdb.get(ipdb_pick[0])
                if cm:
                    cat_pick, cat_conf = cm, "high"
            if cat_pick is None:
                cat = cat_by_norm.get(nn, [])
                cat_same_maker = [r for r in cat if r[2] and r[2] in cands]
                if cat_same_maker:
                    cat_pick, cat_conf = cat_same_maker[0], "high"
                elif cat:
                    cat_pick, cat_conf = cat[0], "low"

            opdb_hits = opdb_by_norm.get(nn, [])
            opdb_pick = opdb_hits[0] if opdb_hits else None

            if cat_pick is not None and cat_conf == "high":
                dispo = "exists-orphaned" if not cat_pick[2] else "exists"
            elif cands:
                dispo = "new-model-existing-maker"
            else:
                dispo = "new-maker"

            machine_rows.append(
                {
                    "page": slug,
                    "name": mach.name,
                    "name_uncertain": mach.name_uncertain,
                    "parens": " | ".join(mach.parens),
                    "year": mach.year,
                    "year_uncertain": mach.year_uncertain,
                    "tech": mach.tech,
                    "players": mach.players,
                    "prod": mach.prod,
                    "notes": " | ".join(mach.notes),
                    "raw_line": mach.raw,
                    "disposition": dispo,
                    "catalog_slug": cat_pick[0] if cat_pick else "",
                    "catalog_conf": cat_conf,
                    "catalog_maker": cat_pick[2] if cat_pick else "",
                    "catalog_year": cat_pick[3] if cat_pick else "",
                    "ipdb_id": ipdb_pick[0] if ipdb_pick else "",
                    "ipdb_conf": ipdb_conf,
                    "ipdb_maker": ipdb_pick[2] if ipdb_pick else "",
                    "opdb_id": opdb_pick[0] if opdb_pick else "",
                    "review": mach.review or ("yes" if cat_conf == "low" or ipdb_conf == "low" else ""),
                }
            )

    with (HERE / "makers.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, lineterminator="\n", fieldnames=["page", "heading", "city_line", "updated_line", "catalog_candidates", "review"])
        w.writeheader()
        w.writerows(maker_rows)
    with (HERE / "worksheet.csv").open("w", newline="") as f:
        w = csv.DictWriter(
            f,
            lineterminator="\n",
            fieldnames=[
                "page", "name", "name_uncertain", "parens", "year", "year_uncertain",
                "tech", "players", "prod", "notes", "raw_line", "disposition",
                "catalog_slug", "catalog_conf", "catalog_maker", "catalog_year",
                "ipdb_id", "ipdb_conf", "ipdb_maker", "opdb_id", "review",
            ],
        )
        w.writeheader()
        w.writerows(machine_rows)

    total = len(machine_rows)
    by_dispo: dict[str, int] = {}
    for r in machine_rows:
        by_dispo[r["disposition"]] = by_dispo.get(r["disposition"], 0) + 1
    print(f"pages: {len(maker_rows)}  machines: {total}  dispositions: {by_dispo}")
    print(f"review-flagged: {sum(1 for r in machine_rows if r['review'])}")


if __name__ == "__main__":
    main()
