"""Sweep IPDB notes for cross-references that call ANOTHER named game not-a-pinball.

The own-note signal (ipdb_non_pinball_signals.explicit_not_pinball) only sees a
game's own Notes. But entries frequently say things like
"Williams' 1981 'Hyperball' ... is Not A Pinball" inside a DIFFERENT game's note.
This finds those, resolves the quoted title to a flipcommons model, and reports
ones not already labeled by the own-note worksheet.
"""

import csv
import re

import duckdb

con = duckdb.connect("explore.duckdb", read_only=True)

with open("worksheet.csv") as _f:
    labeled = {int(r["ipdb_id"]) for r in csv.DictReader(_f)}
excluded = {25, 502, 6786}

by_name: dict[str, list[tuple[str, object, object]]] = {}
for slug, name, year, ipdb in con.execute(
    "SELECT slug,name,year,ipdb_id FROM models"
).fetchall():
    by_name.setdefault(name.lower(), []).append((slug, year, ipdb))

rows = con.execute(
    "SELECT IpdbId, Title, coalesce(Notes,'') || ' ' || coalesce(AdditionalDetails,'') FROM ipdb_machines"
).fetchall()

phrase = re.compile(
    r"not a pinball|is a gun game|is a video game|is a slot machine|is a puck bowler|is a shuffle",
    re.IGNORECASE,
)
quoted = re.compile(r"'([^'\s][^']{1,40})'|\"([^\"\s][^\"]{1,40})\"")

seen = set()
cands = []
for ipdb, title, blob in rows:
    blob = re.sub(r"\s+", " ", (blob or "").replace("\r", " ").replace("\n", " "))
    for s in re.split(r"(?<=[.!?])\s+", blob):
        if not phrase.search(s):
            continue
        for m in quoted.finditer(s):
            ref = (m.group(1) or m.group(2)).strip().lower()
            if ref == (title or "").lower():
                continue
            for slug, year, refipdb in by_name.get(ref, []):
                if refipdb in labeled or refipdb in excluded:
                    continue
                key = (slug, ipdb)
                if key in seen:
                    continue
                seen.add(key)
                cands.append((slug, refipdb, year, ipdb, title, s.strip()[:160]))

print(f"cross-ref candidates: {len(cands)}")
for slug, refipdb, year, citing, _ctitle, s in sorted(cands):
    print(
        f"  {slug:32s} own_ipdb={refipdb!s:6s} yr={year} cited_in=ipdb:{citing} | {s}"
    )
