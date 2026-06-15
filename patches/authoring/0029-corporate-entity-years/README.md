# 0029 corporate-entity-years — authoring record

Populates `year_start` / `year_end` on twelve more significant corporate entities
that were still missing them, **extending the hand-written
`0013-corporate-entity-years.yaml`** to the next tier of makers. `year_end` is the
year the cited source gives as the last year the entity was active in pinball / in
business; for makers still trading it is left unset.

**Attribution `flipcommons-catalog`, citing Wikipedia** — same pattern as 0013.
Wikipedia has no structured year field for us to supersede, so stamping a
`year_start`/`year_end` from its prose is our own editorial reading of the source;
each entry carries `cite:` to the article that states it. The Wikipedia web root is
already seeded by `0012-citation-sources-web.yaml`, so no new `sources:` patch is
needed. Within-brand only — this does not model cross-brand mergers/successions
(no manufacturer→manufacturer link exists yet).

## Why no classify.py / worksheet-first pipeline

The 0010 game-format pipeline classifies IPDB/OPDB **free text in DuckDB**
(pinexplore), so its judgment lives in `classify.py` and feeds `worksheet.csv`.
Here the evidence is **Wikipedia article prose gathered by web research**, not a
queryable source DB — so there is no pinexplore stage. The classification lives as
`ROWS` literals in `gen.py`; `gen.py` emits `worksheet.csv` as the audit artifact
and reads the live flipcommons DB only for the `expect:` guards and a slug-drift
check. Still uses the shared `../patchkit.py` for escaping/emission.

## Pipeline

```bash
cd flipcommons/backend
uv run python ../../pindata/patches/authoring/0029-corporate-entity-years/gen.py
```

Each row is guarded on `ipdb_manufacturer_id` (the most specific guard — present
even though both year fields were null) and cited to the article URL. Notes are
verbatim Wikipedia prose with omissions marked `[...]`; en-dashes normalize to
hyphens via `patchkit.clean_text`.

## Scope + source judgment

- **Set chosen:** the twelve highest-model-count corporate entities still missing
  years **that have a citable founding/closing statement on a seeded root**
  (Wikipedia). A mix of EM coin-op (Mills, Jennings, Evans), classic solid-state
  (Rock-Ola, Game Plan, Atari, Allied Leisure), European (Playmatic, Zaccaria) and
  modern (Jersey Jack, Spooky, Chicago Gaming) makers.
- **Dead ends (dropped, not citable):** the largest missing EM firms —
  **Genco** (202 models), **Exhibit Supply** (156), **J. H. Keeney** (119) and
  **Stoner** (75) — have **no English Wikipedia article**, and arcade-museum.com's
  newer company pages give only a database-first-machine year ("released N machines
  … starting in YYYY"), not a corporate founding/closing span (the older
  `(YYYY-YYYY)`-in-title format 0013 used for Williams is gone). With no defensible
  year from a seeded source, they are left unset rather than guessed. Adding them
  later means seeding a new citation root (e.g. a pinball-history site) first.

## Per-entity editorial notes

- **Rock-Ola / Jersey Jack / Spooky / Chicago Gaming** — still in business, so
  `year_end` is left unset (only `year_start` written).
- **Rock-Ola** — `year_start` 1932 is when the **"Rock-Ola Manufacturing
  Corporation"** name began (the entity our CE is named for; founded 1927 as the
  Rock-Ola Scale Company), following 0013's entity-name-span convention.
- **Mills Novelty** — used the precise **Sept 1, 1943** corporate-name-change to
  Mills Industries (more exact than the lead's "By 1944"); `year_start` 1898 is when
  the M.B.M. Cigar Vending Company was renamed Mills Novelty Company.
- **O. D. Jennings** — 1906 (founded as Industry Novelty Company) to 1954, the
  successor boundary: Jennings & Company was incorporated and bought O. D. Jennings
  & Company's assets on March 19, 1954. `year_end` is that corporate transition, not
  Ode Jennings's 1953 death (which the lead loosely ties succession to).
- **Allied Leisure** — 1968 is the first year of the "released as Allied Leisure
  (1968–1979)" span; `year_end` 1980 is when it was renamed Centuri (the Centuri
  era is a separate entity).
- **Atari** — `year_end` 1984 is the break-up of the original Atari, Inc. (the
  remaining part renamed Atari Games Inc.). Atari left pinball ~1979, but no
  pinball-exit year is stated, so the corporate-business end is used.
- **Chicago Gaming** — `year_start` **2001**, when the Chicago Gaming Company entity
  was established as a division of Churchill Cabinet Company. This corrects a likely
  trap: the parent Churchill Cabinet dates to 1904, which is *not* this entity's
  start.
- **Spooky** — the article lead says "2016" but its History section says Charlie
  Emery "officially founded Spooky Pinball in 2013"; the explicit 2013 is used.
- **Zaccaria** — 1974–1990 per the lead; the brief "Mr. Game" tail (1988–1990) is
  folded into that span by the source. If the catalog later splits out a Mr. Game
  entity, revisit the boundary.
