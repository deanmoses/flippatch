# Missing years

We have a lot of models that are missing years. This is a very basic and important piece of identifying a model: `Godzilla (Stern 2021)`. You basically triangulate on name, mfr, year.

We need years for as many machines as possible and I'm okay mining catalog sites.

## IPDB is exhausted for years

Checked 2026-08-19 against the dev DB at patch 0269 (6,941 live models, 974 undated), joined to pinexplore's `ipdb_machines` + `ipdb_machine_additional_details`. Of the **944** undated models carrying an IPDB ID:

|                                                           | count |
| --------------------------------------------------------- | ----: |
| IPDB ID absent from the dump                              |     0 |
| in the dump, but the dump holds no date in either carrier |   942 |
| in the dump, and the dump holds a year we lack            |     2 |

So IPDB has nothing left to give us on years — 942 of the 944 are models IPDB itself cannot date. Everything below is the only remaining lever.

The 2 stragglers are not misses by patch 0268. pinexplore's `ipdb_machines` unions two snapshots, and both records were **dateless** in the 2025-02-01 Xantari dump and gained a date in the 2026-04-11 snapshot, which landed after 0268 was generated:

| snapshot   | IPDB | title            | `DateOfManufacture` | `AdditionalDetails`               |
| ---------- | ---: | ---------------- | ------------------- | --------------------------------- |
| 2025-02-01 | 4386 | 1963 A. L. Twins | —                   | `IPD No. 4386 / 1 Player`         |
| 2026-04-11 | 4386 | 1963 A. L. Twins | `1963-01-01`        | `IPD No. 4386 / 1963 / 1 Player`  |
| 2025-02-01 | 6543 | Alien Space      | —                   | `IPD No. 6543 / 4 Players`        |
| 2026-04-11 | 6543 | Alien Space      | —                   | `IPD No. 6543 / 1979 / 4 Players` |

Patch `0270-ipdb-refreshed-snapshot-dates` fills both, under 0268's classification rule: `project_year: 1979` for `alien-space` (no date of manufacture, so the header date is a project date) and `production_year: 1963` for `1963-a-l-twins` (IPDB does hold a date of manufacture). Caveat carried in that patch's note: IPDB's own prose says the conversion date is unknown, so 1963 is really the donor game's year, Williams' 1963 Major League.

The other direction is clean too — exactly one record (3239 _Sixty-Two Baseball_) is dated only in the _older_ snapshot, and the catalog already has it as 1962.

## Months were the one IPDB job left — done in 0277 and 0278

IPDB's header line names a month for models the catalog has none for, and 0268's classifier splits them cleanly: `DateOfManufacture` present means the header date is a **production** date, absent means a **project** date. That is not one job but two, with different causes, different target fields and different value.

|                            | IPDB kind  | emitted | target field                     | shape                        |
| -------------------------- | ---------- | ------: | -------------------------------- | ---------------------------- |
| `0277-ipdb-january-months` | production | **217** | `production_month`               | every row is January         |
| `0278-ipdb-project-months` | project    | **113** | `project_year` + `project_month` | 110 Bally, 111 day-precision |

**0277 recovers 217 lost Januaries.** `DateOfManufacture` is a full timestamp, so a year-only IPDB date arrives padded to `1938-01-01` — indistinguishable in that field from a machine genuinely dated January 1938. Our baseline read `-01-01` as year-only precision, the only safe call there, and every genuine January without a day lost its month. The header line has no such ambiguity: it renders `January, 1938` for month precision and a bare `1990` for year precision. The shortfall table proves the mechanism — across every IPDB listing with a manufacture date naming a month, the catalog holds that month on **100% of all eleven other months**, and on January holds 156 of 374. Nothing about January is special to pinball, only to a padding rule. One row is held back: `asteroid-killer`, where the catalog says 1979 and IPDB says January, 1980 — a year dispute, not a month gap.

**0278 is 0268 re-run over the population its scope test could not see.** 0268 scoped on `models.year IS NULL` — the derived fallback — so it never saw a model that already carries a production year from another source. Scoping on the field, `project_year IS NULL`, finds 115 more. Their existing production years come from `0181-bingo-years` (85), OPDB and the baseline (38) and a handful of later patches, so this is not one date filed twice: it is a production date from one source and a project date from another, for the same machine. Two rows are held back where IPDB's project date **postdates** our production year (`blue-chip-2`, `dixieland-2`) — a game cannot be designed after it is built, and which of the two dates is wrong is a review, not a fill.

Worth knowing before measuring 0278 by the wrong yardstick: it changes **nothing a reader sees**. `production_year` wins the derivation, so the site goes on showing the production date. Its value is that the catalog stops being silent about a date IPDB holds.

### By-catch: 254 month conflicts

Falling out of the same join, and **not** addressed by either patch: **254 models already hold a `production_month` that disagrees with IPDB's header month**, 205 of them where the year agrees — so a genuine month-level conflict between IPDB and whatever source we took the month from, not two different dates. That is an audit, not a fill, and it wants its own pass.

## Catalog site sweep options

Options to sweep missing data from catalog sites. This is unfinished.

## Option 1: Table

Build a CSV or SQLite DB or DuckDB with data from multiple sites. Maybe a table with columns something like

model_id ⬅️ Flipcommons ID
model_slug ⬅️ Flipcommons model slug
year ⬅️ Flipcommons year
month ⬅️ Flipcommons month
manufacturer ⬅️ Flipcommons manufacturer

pinside month
pinside year
pinside ID ⬅️ ID or slug or path, but definitely NOT full URL

arcade-museum.com month
arcade-museum.com year
arcade-museum.com ID ⬅️ ID or slug or path, but definitely NOT full URL

kineticist month
kineticist year
kineticist ID ⬅️ ID or slug or path, but definitely NOT full URL

I forget if there's other catalog sites we should be looking at.

I would actually like to get the IDs/slugs for these catalog sites into our system along with IPDB and OPDB IDs. Not only would this help us with data gathering, we could link to those site from the appropriate model pages.
