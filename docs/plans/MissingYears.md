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

## Months are the one IPDB job left

**314 models have no month while IPDB's header line names one** — 307 of them where the catalog year already agrees with IPDB's. Same shape as 0268 and reusing its machinery exactly: the parse is pinexplore's `ipdb_machine_additional_details`, quoting the raw header line makes the quote verbatim by construction, and `production_month` vs `project_month` is decided the same way — by whether the listing holds a `DateOfManufacture`. No new source, no page fetching. Worth doing before the multi-site sweep below.

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
