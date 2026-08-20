# 0277 — IPDB January months

Fills `production_month` for **217 models the catalog dates only to a year**, where IPDB names the month and our baseline could not read it. Every one of them is January, and that is the whole story.

- `january_months.sql` — the analysis: the classification, the gate, the anchors.
- `gen.py` — the emitter, one entry per `jm_patch_rows` row.
- `patches/0277-ipdb-january-months.yaml` — 217 entries, attribution `flipcommons-catalog`.

## The signal

`DateOfManufacture` in the IPDB dump is a full timestamp, so a listing IPDB dates only to a year arrives padded to the first of January — `1938-01-01`. In that field, the padding is indistinguishable from a machine genuinely dated January 1938. Our baseline read `-01-01` as year-only precision, which is the only safe call for a field that cannot tell the two apart, and every genuine January without a day lost its month.

The header line has no such ambiguity, because IPDB renders the two cases differently:

```text
IPD No. 12   / January, 1938 / 1 Player     <- month precision
IPD No. 6592 / 1990                         <- year precision
```

The shortfall is visible in a single table. Across every model whose IPDB listing holds a manufacture date naming a month, the catalog carries that month on 100% of every month — except January:

| month | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| IPDB names it | **374** | 481 | 314 | 341 | 379 | 392 | 294 | 328 | 282 | 338 | 331 | 306 |
| catalog holds it | **156** | 481 | 314 | 341 | 379 | 392 | 294 | 328 | 282 | 338 | 331 | 306 |
| shortfall | **218** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

`jm_month_shortfall` recomputes it live. Eleven months at zero is what makes this a mechanism rather than a coincidence: nothing about January is special to pinball, only to a timestamp with a padding rule.

The claim record confirms it from the other side. Of the January listings, `ipdb` asserted a `production_month` only where the date also names a **day** — `1936-01-15`, which is not `-01-01` and so survived the padding rule. Not one January month ever came from a `-01-01` date. Correspondingly, **none** of the 217 rows here quotes a day-precision date, and none of the 218 candidates carries a `production_month` claim from any source.

## Totals

From `jm_summary`, against the dev DB at `0276-big-lebowski-first-model-date` (6,942 live models):

| metric | value |
| --- | ---: |
| models_with_ipdb_id | 6664 |
| ipdb_manufacture_dates_naming_a_month | 4167 |
| january_shortfall | 218 |
| candidates | 218 |
| **patch_rows** | **217** |
| patch_rows_january | 217 |
| patch_rows_makers | 83 |
| rejected | 1 |

Not an early-era artifact, though it leans that way: **173 pre-1950, 29 from 1950–1979, 15 from 1980 on**, spanning Caille-Schiemer's *Log Cabin* in 1901 to Jersey Jack's *Guns N' Roses (Not In This Lifetime) Team Edition* in 2021. 83 makers, led by Genco 13, PAMCO 11, Gottlieb 10, Williams 10, Bally 9 — the long tail of the pre-war trade, not one maker's record-keeping quirk. One row has no manufacturer at all (`pittsburgh-penguins`).

## The one rejection

`asteroid-killer` (Universal, IPDB 3810). The catalog says 1979; the listing says `January, 1980`.

A year disagreement is not a month gap. Emitting the month here would attach IPDB's January to our 1979 and produce a date neither source states. It belongs in a year review, and `jm_checks` asserts no emitted row can carry a year the cited listing contradicts.

## Judgment calls

**No `production_year` is emitted, only the month.** Every target already carries one, asserted by `ipdb` from this same listing — the baseline read the year out of the structured field and lost only the month. Re-asserting the year would put a second claim next to one that already says the same thing, for no gain.

**The quote is the whole header line.** IPDB's rendering difference — `January, 1938` versus a bare `1938` — *is* the evidence, so the line has to be quoted whole for a reader to see it. It is also what keeps the quote verbatim by construction: the `ipdb:` resolver reproduces `AdditionalDetails` unlabelled in the document `make verify-quote-verbatim` matches against, so the quote is cut from the source text rather than reassembled from a parse.

**Every entry carries the same note, and it earns its place.** The usual rule is that a cite with a quote needs no note. Here the quote proves a *date* but cannot say which *kind* of date, because IPDB never labels the header line — so the note states the premise that puts the month in `production_month`:

> IPDB has a date of manufacture for this model, which means the quoted header date here is a production date.

That is 0268's note inverted, and for the same reason.

**Attribution is `flipcommons-catalog`, not `ipdb`.** IPDB supplies the month, and it is cited and quoted as such. But the claim being asserted is not "January" — it is "January is the month of **manufacture**", read out of an unlabelled string plus the presence of a second field, under a rule about IPDB's page behaviour that we apply on IPDB's behalf. The reasoning is ours, so the attribution is ours. This is 0268's argument unchanged; the two campaigns sit on opposite sides of the same classifier and must be attributed the same way.

## The load-bearing check

`header_month_disagrees_with_structured_field` is the one this campaign would die without. It asserts, over the **whole corpus** rather than the emitted set, that the header line and `DateOfManufacture` never name different months. They are two renderings of one date, and this campaign trusts the header over the field on precision alone — which is only safe while they agree on the month itself. Today: **4,167 records name a month in both, and 4,167 agree.** Zero disagreements. That is what makes the padding story a reading of the data rather than a guess about it.

## Anchors, and why they don't point at the patch

The emitted set drains to zero the moment this patch applies — every model it targeted now has a month and drops out of scope — so anchoring the checks on `jm_patch_rows` could not tell "the campaign finished" from "the grammar rotted". The anchors probe the parse and the join instead:

- **`anchor_january_padding`** — IPDB 12 must still parse `January, 1938` onto `across-the-board` with a structured field reading `1938-01-01`. This is the shape the campaign exists for.
- **`anchor_january_day_precision_out_of_scope`** — a day-precision January is *not* padding, its month is already in the catalog, and it must stay out of the candidates. The contrast case that keeps the scope honest.

Verified after apply: `jm_summary` gives `patch_rows: 0` and `january_shortfall: 1` (the held-back `asteroid-killer`), with `jm_checks` still clean — the parse and the join anchors hold on a drained set.

## Reaching the parse

`january_months.sql` opens with `ATTACH '../pinexplore/explore.duckdb'`, as 0268 does and for the same reason: `AdditionalDetails` never became catalog data, so it is absent from `models.extra_data` and every foundation column, and flippatch's `scripts/analysis/evidence.sql` bridge deliberately carries the web-scrape cache alone. The path resolves from the **flipcommons** checkout, since that is where the runner `cd`s, and `ATTACH` takes a string literal so it cannot honour a `PINEXPLORE_DIR` override.
