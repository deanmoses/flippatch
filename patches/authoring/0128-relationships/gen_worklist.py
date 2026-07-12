import duckdb, re, json
from collections import defaultdict, OrderedDict
con = duckdb.connect('explore.duckdb', read_only=True)

# ---------- patterns ----------
SELF_LIC  = r"(manufactured|made|produced|built).{0,60}under licen|under licen[cs]e (of|from)|licensed copy of|same game as .{0,60}under licen|made in.{0,40}under licen"
SELF_COPY = r"(^|\. |\.\s|this (game )?is |this is |^a |^an )\s*(a |an |the )?(1.player |single.player |2.player |4.player |near |modified |apparent|probable |licensed )*copy of"
CONV      = r"conversion kit for|conversion of |is a conversion|conversion kit (of|includes)|converted (electromechanical|em|from)"

# reference like  Maker's 1975 'Name'  /  Maker's 'Name'
REF = re.compile(r"([A-Z][A-Za-z0-9&.\-/ ]{1,40}?)'s(?:\s+(\d{4}))?\s+(?:add.a.ball |em |ss |solid.state )?'([^']{1,50})'", re.I)

MAKER_ROOT = [   # (token in note, ILIKE root, canonical)
    ('bally midway','%Bally Midway%'),('bally/midway','%Bally Midway%'),
    ('premier','%Premier%'),('d. gottlieb','%Gottlieb%'),('d gottlieb','%Gottlieb%'),
    ('gottlieb','%Gottlieb%'),('williams','%Williams%'),('stern','%Stern%'),
    ('bally','%Bally%'),('midway','%Midway%'),('zaccaria','%Zaccaria%'),
    ('bensa','%Bensa%'),('atari','%Atari%'),('game plan','%Game Plan%'),
    ('juegos populares','%Juegos Populares%'),('playbar','%Playbar%'),
]

# ---------- load seeded models + build lookup ----------
models = con.execute("select ipdb_id,slug,corporate_entity_slug,name,year from models where ipdb_id is not null").fetchall()
m_by_ipdb = {r[0]: r for r in models}
mfr_name = {}
for r in con.execute("select IpdbId,Manufacturer,DateOfManufacture,Notes from ipdb_machines").fetchall():
    mfr_name[r[0]] = (r[1], r[2], r[3])

# resolve a note reference (maker, year, name) -> model slug
def resolve_target(maker, year, name):
    maker = (maker or '').strip().lower()
    like = None
    for tok, lk in MAKER_ROOT:
        if tok in maker:
            like = lk; break
    name = name.strip()
    q = "select IpdbId from ipdb_machines where lower(Title)=lower(?)"
    params = [name]
    if like:
        q += " and Manufacturer ilike ?"; params.append(like)
    if year:
        q += " and substr(DateOfManufacture,1,4)=?"; params.append(str(year))
    rows = con.execute(q, params).fetchall()
    if not rows and year:  # relax year
        rows = con.execute("select IpdbId from ipdb_machines where lower(Title)=lower(?)"+(" and Manufacturer ilike ?" if like else ""),
                           [name]+([like] if like else [])).fetchall()
    for (ip,) in rows:
        if ip in m_by_ipdb:
            return m_by_ipdb[ip][1]  # slug
    return None

def first_target(note, self_slug):
    for mk, yr, nm in REF.findall(note):
        slug = resolve_target(mk, yr, nm)
        if slug == self_slug:   # true self-reference, keep looking
            continue
        return (mk.strip(), yr, nm.strip(), slug)
    return (None, None, None, None)

def year_of(ipdb):
    mo = m_by_ipdb.get(ipdb)
    if mo and mo[4]: return mo[4]
    d = mfr_name.get(ipdb, (None,None,None))[1]
    if d:
        try: return int(str(d)[:4])
        except: pass
    return None

# ---------- classify every seeded model ----------
EXCLUDE_MFR_ROOTS = ['Stern Electronics','Bally Midway Manufacturing','Genco Manufacturing',
    'Spooky Pinball','Global VR','The Pinball Factory','Dutch Pinball','Retro Pinball',
    'Stern Pinball','Midway Manufacturing Company, a subsidiary']  # originals / theme / video / never-made

rows = con.execute("select IpdbId,Manufacturer,Title,DateOfManufacture,Notes from ipdb_machines where Notes is not null").fetchall()
cands = []
for ipdb, mfr, title, date, notes in rows:
    if ipdb not in m_by_ipdb: continue
    n = notes.lower()
    lic  = bool(re.search(SELF_LIC, n))
    copy = bool(re.search(SELF_COPY, n))
    conv = bool(re.search(CONV, n))
    if not (lic or copy or conv): continue
    if any(mfr and mfr.startswith(x) for x in EXCLUDE_MFR_ROOTS): continue
    if lic:      cls = 'LICENSED'
    elif conv and not copy: cls = 'CONVERSION'
    elif copy and conv: cls = 'BOOTLEG+CONV'
    else:        cls = 'BOOTLEG'
    slug, ce, name, yr = m_by_ipdb[ipdb][1], m_by_ipdb[ipdb][2], m_by_ipdb[ipdb][3], year_of(ipdb)
    tmk, tyr, tnm, tslug = first_target(notes, slug)
    era = 'defer' if (yr and yr < 1965) else 'in'
    sent = re.split(r'(?<=[.\)])\s+(?=[A-Z])', notes.strip())[0][:170]
    cands.append(dict(ipdb=ipdb, slug=slug, ce=ce or 'UNKNOWN-MAKER', name=name, year=yr,
                      cls=cls, target=tslug, tref=f"{tmk} {tyr or ''} '{tnm}'".strip() if tnm else None,
                      era=era, note=sent, mfr=mfr))

json.dump(cands, open('cands.json','w'), indent=0)
inn=[c for c in cands if c['era']=='in']
print("TOTAL:", len(cands), " in-era:", len(inn), " deferred(pre-1965):", len(cands)-len(inn))
from collections import Counter
print("by class (in-era):", Counter(c['cls'] for c in inn))
res=sum(1 for c in inn if c['target']); print(f"targets resolved: {res}/{len(inn)}")
