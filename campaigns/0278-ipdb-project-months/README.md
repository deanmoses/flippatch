# 0278 — IPDB project months

Fills `project_year` and `project_month` for **113 models the catalog already dates from another source**. This is 0268 run again over the population its scope test could not see.

- `project_months.sql` — the analysis: the classification, the gate, the anchors.
- `gen.py` — the emitter, one entry per `pm_patch_rows` row.
- `patches/0278-ipdb-project-months.yaml` — 113 entries, attribution `flipcommons-catalog`.

## What 0268 left behind

0268 recovered IPDB project dates under a scope test of `models.year IS NULL` — "this model reads as undated on the site". That was right for the question it asked, and it silently excluded a second population: a model IPDB holds a project date for, which the catalog **already dates from a different source**. Those models read as dated, so 0268 never saw them.

The classification is 0268's, unchanged and in its own words:

> `DateOfManufacture IS NULL` **and** a parsed header date `IS NOT NULL` **is** the definition of "IPDB holds only a project date."

Only the scope test differs: `project_year IS NULL` — the field itself is empty — rather than `year IS NULL`, the derived fallback. `models.year` coalesces production over project and `models.month` prefers the production month wholesale, so a model here reads as fully dated on the site while the project field behind it is blank.

That derived-vs-field distinction is worth stating precisely, because measuring through the derived column undercounts this population: scoping on `models.month IS NULL` finds 96 of these, and scoping on the field finds **115**. The 19 it misses are models that already carry a production month, so the derived column is populated while `project_year`/`project_month` are still empty.

## The existing date is not this date

Every candidate carries a `production_year`, and the claim record names where each came from:

| source | patch | n |
| --- | --- | ---: |
| flipcommons-catalog | `0181-bingo-years` | 85 |
| opdb | baseline | 20 |
| flipcommons-catalog | baseline | 18 |
| flipcommons-catalog | `0240-one-ball-game-formats` | 3 |
| flipcommons-catalog | `0239-turf-king-champion-one-ball` | 2 |
| flipcommons-catalog | `0241-rolldown-game-formats` | 2 |
| flipcommons-catalog | `0263-harvest-model-dates` | 2 |
| flipcommons-catalog | `0109-italian-model-facts` | 1 |

None of them could have come from the header line this patch reads, because our baseline never read that field — which is 0268's entire finding. So this is not one date filed twice. It is a production date from one source and a project date from another, for the same machine, and IPDB's own listing is the evidence that they are different kinds of date: it holds the project date and no manufacture date at all.

`pm_existing_year_provenance` prints that breakdown live.

## Totals

From `pm_summary`, against the dev DB at `0276-big-lebowski-first-model-date` (6,942 live models):

| metric | value |
| --- | ---: |
| ipdb_project_dates_naming_a_month | 250 |
| models_with_a_project_year | 188 |
| candidates | 115 |
| **patch_rows** | **113** |
| patch_rows_ipdb_day_precision | 111 |
| patch_rows_already_holding_a_production_year | 113 |
| patch_rows_where_the_two_years_agree | 109 |
| rejected | 2 |

**110 of the 113 are Bally**, plus one each from Williams, Zaccaria and Stern, spanning 1935 to 2009. That concentration is 0268's finding restated: the big makers whose internal project logs IPDB holds. `baby-pac-man` is here — the worked example 0268 used to show a project date is not a never-produced marker, carrying a project date of October 11, 1982 *and* 7,000 confirmed units.

**109 of 113 project years equal the production year already on record**, which is the expected shape for a machine designed and built inside one year, and a quiet corroboration that the two dates describe the same machine. The remaining 4 have a project date one or two years earlier — `bigfoot` (produced 1978, project April 29, 1977), `malibu-beach` (1980, December 28, 1978), `tahiti-3` (1979, October 09, 1978), `tramway` (1974, February 03, 1973).

## Why this patch changes nothing a reader sees

Worth naming before anyone measures it by the wrong yardstick. `models.year` coalesces production over project and `models.month` prefers the production month wholesale, so every model here goes on displaying exactly the date it displays today. The value is that the catalog stops being silent about a date IPDB holds, and that the two dates become separately attributable — not a visible fix.

## The two rejections

`blue-chip-2` (Bally, produced 1974, IPDB project date September 11, **1975**) and `dixieland-2` (Bally, produced 1978, project date March 06, **1979**).

A project date is the design milestone that *precedes* manufacture, so a project year later than the production year is a contradiction on its face, and writing one would leave the record stating that the game was designed after it was built. Which of the two dates is wrong is an open question — our production year comes from another source and may well be the mistaken one — but they cannot both stand unexamined. That is a review, not a fill. `pm_checks` asserts no emitted row can carry one.

## Judgment calls

**Both fields are emitted, always.** `project_month` alone would violate the model's own month-needs-a-year constraint, and the year it needs is the *project* year — not the production year the record already holds, which came from a different source and dates a different event.

**A month is required, and a year-only project date is out of scope.** 0268's leftovers include models whose listing carries a project date with no month. That is a thinner claim on an already-dated model and a different judgment; it is not in this patch.

**Day precision goes in the evidence, not in prose.** 111 of the 113 dates name a day (`October 11, 1982`) and the catalog stores year and month only. Each entry quotes the whole header line, so the day is preserved in the citation a reader can follow — and the quote is verbatim by construction, since the `ipdb:` resolver reproduces `AdditionalDetails` unlabelled in the document `make verify-quote-verbatim` matches against.

**The note is 0268's, verbatim.** Same claim, same kind of evidence, same reason a quote-bearing cite still needs a note here — the quote proves a date but cannot say which kind of date, and that is the entire question:

> IPDB has no date of manufacture for this model, which means the quoted header date here is a project date.

**Attribution is `flipcommons-catalog`, not `ipdb`**, on 0268's argument unchanged: IPDB never labels the header line, and the classification is read out of an unlabelled string plus the absence of a second field, under a rule we apply on IPDB's behalf.

## Anchors, and why they don't point at the patch

The emitted set drains to zero the moment this patch applies, so anchoring on `pm_patch_rows` could not tell "the campaign finished" from "the grammar rotted":

- **`anchor_day_precision_project_date`** — IPDB 125 must still parse `October 11, 1982` onto `baby-pac-man` with no manufacture date. The shape this campaign reads.
- **`anchor_manufacture_dates_excluded`** — a listing holding a manufacture date must never reach the candidates, however its header line reads. The exclusion that defines the scope, and the boundary against 0277.

Verified after apply: `pm_summary` gives `patch_rows: 0` with `candidates: 2` (the two held-back rows) and `models_with_a_project_year` up from 188 to 301, `pm_checks` still clean.

## Reaching the parse

`project_months.sql` opens with `ATTACH '../pinexplore/explore.duckdb'`, as 0268 does and for the same reason: `AdditionalDetails` never became catalog data, so it is absent from `models.extra_data` and every foundation column, and flippatch's `scripts/analysis/evidence.sql` bridge deliberately carries the web-scrape cache alone. The path resolves from the **flipcommons** checkout, since that is where the runner `cd`s, and `ATTACH` takes a string literal so it cannot honour a `PINEXPLORE_DIR` override.
