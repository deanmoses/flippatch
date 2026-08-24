# Field merge views for the external data sources layer

Status: built — `scripts/analysis/external_data_sources/fields.sql`. Written 2026-08-24, measurements against the 2026-04-11 Xantari snapshot and the current OPDB export.

## Why

The comparison layer was architected per source — each file interrogates one witness against the catalog — without accounting for a basic fact: sources disagree with each other. By contrast, Flipcommons itself is claims-based _because_ sources disagree. For scalar fields this produced seesaw worklists: 88 of IPDB's 106 production-year disagreements have OPDB agreeing with the catalog, so "fixing" toward IPDB would recreate every row in the OPDB bucket. A per-witness disagreement where another witness backs us is a standoff already adjudicated, not a defect.

The fix is to compare the catalog against the testimony _pool_: merge views over all sources, per (model, field).

## The two buckets

**Worklist** — at least one external source has a value for the field, and NO source has the same value as Flipcommons (including Flipcommons having no value). Shows the Flipcommons value plus every source's value. These are findings: our value has zero external support while testimony exists, or we have no value at all.

**Disagree list** — MULTIPLE sources have a value, at least one disagrees with the other(s), and at least one agrees with the (non-null) Flipcommons value. NOT a worklist — a standoff where we sided with a witness — but browsable, with the same columns. No findings; summary-counted so the detector is visibly alive.

Sub-shapes inside the worklist, distinguishable from the row itself: _backfill_ (Flipcommons null), _outvoted_ (sources agree with each other against us — the strongest signal, and fixing it satisfies every witness at once), _lone witness_ (one source speaks, disagrees), _scatter_ (sources disagree with each other and none matches us).

## Measured sizes

One row per (model, field), sources: IPDB (header-parsed dates, kind-routed), OPDB.

| field                              | backfill | lone witness | outvoted | scatter | → worklist | disagree list |
| ---------------------------------- | -------- | ------------ | -------- | ------- | ---------- | ------------- |
| production_year                    | 13       | 5            | 17       | 0       | 35         | 90            |
| production_month                   | 13       | 2            | 1        | 0       | 16         | 377           |
| project_year / project_month       | 5 / 2    | 0            | 0        | 0       | 7          | 0             |
| player_count                       | 2        | 0            | 0        | 0       | 2          | 19            |
| technology_generation              | 2        | 0            | 0        | 0       | 2          | 16            |
| display_type                       | 0        | 1            | 0        | 0       | 1          | 0             |
| production_quantity / model_number | 2 / 1    | 0            | 0        | 0       | 3          | 0             |
| **total**                          |          |              |          |         | **66**     | **502**       |

The per-source design this replaces would have emitted ~430 findings, mostly standoffs. Note player*count and technology_generation are \_entirely* disagree-list: every IPDB dissent has OPDB backing the catalog.

## Field roster and routing

- `production_year` / `production_month` — catalog `production_*`; IPDB `additional_details_date_*` where `date_kind = 'manufacture'`; OPDB `production_*`.
- `project_year` / `project_month` — catalog `project_*`; IPDB where `date_kind IN ('project', 'project_inferred')` (carry the kind: `_inferred` is parse inference); OPDB has no project concept.
- `player_count`, `technology_generation` — both sources.
- `display_type` — OPDB only. `production_quantity`, `model_number` — IPDB only.

Never the catalog's bare `year`/`month` (coalesced display columns — see bridge.sql's kind-qualification rule). IPDB dates come only from the header parse, never `date_of_manufacture` (padding trap, campaigns 0277/0268).

## Architecture

- A cross-source internals file, `scripts/analysis/external_data_sources/fields.sql`, read by the entry file **after** the per-source files — the one place every source is guaranteed attached. Per-source files keep what is genuinely per-source: id linkage and stale ids (ids are source-namespaced), credits (IPDB-only), vocabulary carriage (additive assertions, not conflicting scalars), maker comparisons (different grains per source).
- Shape: wide — one row per (model, field) with the catalog value and one value column per source. A new source is one column plus its term in the classification booleans.
- One private base view; two public views (worklist, disagree list); findings from the worklist only, one warning rule per bucket-shape or one rule with the sub-shape in the message (decide at build). Finding `source` is the literal `'cross'`, blessed by a line in bridge.sql — a merge finding has no single witness.
- Retirement: `opdb_model_fields_disagreeing`, its `opdb-field-disagrees` rule, its `field_unknown` check and summary rows all fold into this. The IPDB fields view is never built in per-source form.
- The header of `fields.sql` carries this document's Why in brief, so per-source field comparison does not get re-proposed by the next reviewer.

## Open questions

- Lone-witness rows are worklist by the rule and measured tiny (8). Confirmed acceptable, revisit if a new source inflates it.
- Whether the worklist emits one finding rule or one per sub-shape (affects dismissal granularity; sizes suggest one rule is fine).
