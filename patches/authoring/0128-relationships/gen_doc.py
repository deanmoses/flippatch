"""Render Worklist.md from cands.json — PURE TABLES, no hand-authored content.

All prose, judgment, per-maker notes and open questions live in README.md (hand-
maintained). This script only mechanically groups the classified candidates and
prints tables, so re-running it can never clobber or invent editorial content.
Run from the pinexplore repo root after gen_worklist.py has written cands.json.
"""
import json, re
from collections import defaultdict, Counter

cands = json.load(open('cands.json'))

def country(mfr):
    if not mfr: return '?'
    m = re.search(r',\s*of\s+(.+)', mfr)
    if not m: return '?'
    tail = re.split(r'\s*[(\[]', m.group(1))[0].strip().rstrip('.')
    segs = [s.strip() for s in tail.split(',') if s.strip()]
    return segs[-1] if segs else '?'

DONE = {'bally-wulff'}  # authored in 0124
inn = [c for c in cands if c['era'] == 'in' and c['ce'] not in DONE]
by = defaultdict(list)
for c in inn:
    by[c['ce']].append(c)

def prim(rows):
    return Counter(r['cls'].split('+')[0] for r in rows).most_common(1)[0][0]

buckets = {'LICENSED': [], 'BOOTLEG': [], 'CONVERSION': []}
for ce, rows in by.items():
    buckets[prim(rows)].append((ce, rows))
for b in buckets:
    buckets[b].sort(key=lambda x: -len(x[1]))

REL = {'LICENSED': 'licensed_build_of / licensed-build',
       'BOOTLEG': 'bootleg_of / bootleg',
       'CONVERSION': 'converted_from'}
TAG = {'LICENSED': 'licensed', 'BOOTLEG': 'bootleg', 'CONVERSION': 'conversion'}

def maker_section(ce, rows):
    cc = Counter(r['cls'].split('+')[0] for r in rows)
    split = ' '.join(f"{k}={v}" for k, v in cc.items())
    out = [f"\n### `{ce}` — {country(rows[0]['mfr'])}  ({split})\n"]
    out.append("| rel | model slug | ipdb | → target slug | yr | IPDB note (verbatim, vet before use) |")
    out.append("|-----|-----------|------|---------------|----|--------------------------------------|")
    for r in sorted(rows, key=lambda r: (r['cls'], r['slug'])):
        tgt = f"`{r['target']}`" if r['target'] else "**TODO** " + (r['tref'] or '?')
        note = r['note'].replace('|', chr(92) + '|')
        out.append(f"| {TAG[r['cls'].split('+')[0]]} | `{r['slug']}` | {r['ipdb']} | {tgt} | {r['year'] or '?'} | {note} |")
    return "\n".join(out)

doc = ["# Worklist — bootleg / licensed-build / conversion candidates",
       "",
       "**Generated file — do not hand-edit.** Produced by `gen_doc.py` from `cands.json`; edits here are lost on regeneration. All judgment, per-maker notes and open questions live in [README.md](README.md). Confirm every `→ target slug` and re-read the full IPDB note before authoring.",
       ""]
for b in ['LICENSED', 'BOOTLEG', 'CONVERSION']:
    nmk = len(buckets[b]); nmo = sum(len(r) for _, r in buckets[b])
    doc.append(f"\n## {b.title()} — {nmk} makers / {nmo} models  ({REL[b]})")
    for ce, rows in buckets[b]:
        doc.append(maker_section(ce, rows))

deferred = Counter(c['ce'] for c in cands if c['era'] == 'defer')
ndef = sum(deferred.values())
doc.append(f"\n---\n\n## Deferred — pre-1965 ({ndef} models / {len(deferred)} makers)\n")
doc.append("Not in scope now (1930s–50s copies, wartime conversions). Listed for a later campaign.\n")
for ce, n in deferred.most_common():
    doc.append(f"- `{ce}` — {n}")

open('Worklist.md', 'w').write("\n".join(doc) + "\n")
print(f"Worklist.md: {sum(len(r) for b in buckets for _, r in buckets[b])} in-era rows, {ndef} deferred")
