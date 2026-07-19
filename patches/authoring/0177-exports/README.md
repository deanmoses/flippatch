# 0177 — Export-market models

This directory coordinates a data-patch campaign to record which catalog models were **built for export to a foreign market**, and which model each is an export edition *of*.

It owns the analysis. The product model — the `MachineModel.export_edition_of` FK and the `ModelExportMarket` join table, and why they're shaped that way — is specified in flipcommons' [Exports.md](../../../../flipcommons/docs/plans/catalog_data_model/exports/Exports.md), which links back here for the data rather than carrying its own copy. Read it first: the two catalog structures are what the patches write, and it also records the retirement of the never-applied `export` tag.

## What the catalog carries today

Export status is recorded inconsistently — an `(Country)` suffix baked into the name, IPDB free-text prose in `extra_data` that the UI never shows, an `export` tag applied to zero of 6,913 models, and mostly nothing at all. This campaign converts that into the two structured forms.

## How the candidates are found: [exports.sql](exports.sql)

[exports.sql](exports.sql) is a plan-local DuckDB analysis that reuses flipcommons' shared foundation (`scripts/analysis/catalog.sql`) **verbatim** via a `.read` — the same pattern as [0128-relationships](../0128-relationships/README.md) and [0172-bingo-game-format](../0172-bingo-game-format/README.md). Run it through `make analyze`, which sets cwd to the flipcommons checkout, prints the `analysis_context` watermark + `export_summary`, and **gates on `export_checks`**:

```bash
P=patches/authoring/0177-exports/exports.sql
make analyze PLAN=$P PREFIX=export                       # summary, gated on checks
make analyze PLAN=$P Q="FROM export_twin_pairs;"         # deterministic export_edition_of
make analyze PLAN=$P Q="FROM export_titlemate_review;"   # likely target sits in the same Title
make analyze PLAN=$P Q="FROM export_orphan_review;"      # candidates still needing a target
make analyze PLAN=$P Q="FROM export_market_review;"      # the ModelExportMarket shape per candidate
make analyze PLAN=$P CMD=ui                              # live GUI at localhost:4213
```

Nothing is persisted and no count is frozen into this doc: progress is a query, re-derived on each run against the live catalog. Requirements are the `duckdb` CLI on `PATH` and the flipcommons dev DB (`../flipcommons/backend/db.sqlite3`, overridable with `FLIPCOMMONS_DIR`).

Membership is the union of **four detectors**, minus one positive exclusion:

- **`by_notes`** — the IPDB notes carry export-edition phrasing ("for export", "export to X", "export edition/version/model"). The "quantity produced for export: N" production statistic is blanked before matching so a sales figure can't create a candidate. The `"for the <X> market"` phrasing was **removed** from membership as mostly noise; the rows it uniquely supplied are parked in `export_market_phrase_review` for a separate careful pass rather than deleted.
- **`by_suffix`** — a trailing `(Country)` in the model name.
- **`by_opdb`** — an OPDB feature flag containing "export".
- **`by_twin`** — the formulaic IPDB twin sentence. Spanish-market makers ran paired brands, one domestic and one export (Petaco/Recel, Recreativos Franco/Interflip), and IPDB writes **both** sides, each stating its own role and naming its counterpart. This is the highest-quality signal in the file — and it works in both directions, so it also **positively excludes** the domestic half of every pair, which the freetext detectors otherwise flag (a Petaco note says "export" only because it is naming its Recel twin).

Destination markets are parsed separately from membership: a candidate with no parseable market simply has empty `markets`, which is the common case, not an error.

**Export is maker-relative.** A model built for the same country its maker is based in is domestic, not export. `market_is_maker_home` flags those for review — a review signal, not a check.

All four are heuristics that over- and under-count; every row wants source review before it becomes a claim. `export_checks` includes **anchor checks** (the region detector, the `(Country)` suffix detector) that fail the run if a detector goes dark — e.g. from a renamed foundation column.

## The review buckets — each a first-cut worklist

`export_edition_of`:

| view | what it is |
| --- | --- |
| `export_twin_pairs` | the deterministic tier — a parsed, not guessed, `export_edition_of` target. `domestic_model_id IS NULL` means the note names a counterpart that isn't in the catalog yet: create it, or reconcile the name. The twin is **not** always in the same Title (Interflip's *Dragon* pairs with Recreativos Franco's *Dragoon*). |
| `export_titlemate_review` | the likely target sits in the candidate's own Title. One row per (candidate, title-mate) pair, with `reward_differs` and `same_maker` to judge which shape the link takes. |
| `export_orphan_review` | no edge and alone in its Title. `origin_lead` says how far the free text gets: an origin named and in the catalog, named but unseeded, prose that names none, or no prose at all. |
| `export_name_family` | regroup leads for the orphans — a same-maker sibling in a separate singleton Title whose significant name tokens nest (*Palm Beach Club* ← *Palm Beach*). Narrows the field; judge from the note. |

`ModelExportMarket`:

| view | what it is |
| --- | --- |
| `export_market_review` | which shape each candidate's market row takes. `market_kind` is the headline: `country` → `target_market_location`, `region` → `target_market_label`, `unknown` → a row with neither, or no row at all. `unknown` means no detector *resolved* a market, **not** that the prose names none — so the `notes` column rides along for a reviewer to fill or correct one. |
| `export_market_phrase_review` | the parked `"for the <X> market"` hits, deliberately not candidates, with a `lead` triaging the few worth rescuing. |

## Status

**Blocked on flipcommons.** `MachineModel.export_edition_of` and `ModelExportMarket` are being implemented now, and the patch keys that write them are not settled yet. Do not invent a YAML shape — take it from [DataPatches.md](../../../../flipcommons/docs/DataPatches.md) once the work lands, then author against a snapshot as usual.

The analysis itself is complete and runs clean; the buckets above are ready to work the moment the write path exists.

## Overlap with the lineage campaign

A model can be **both** an export edition and a copy or conversion — the two are independent edges and the [0128-relationships](../0128-relationships/README.md) campaign authors the latter. `export_candidate_lineage` reads existing edges from the foundation's `model_edges`, so `has_edge` / `rel_types` show what a candidate already carries; 18 of the 221 candidates carry one today. Check a candidate against that campaign's `relationship_review` before authoring, so the two campaigns don't write contradictory claims about the same pair.

## The dev DB

Verify every fact about the current catalog against the **Flipcommons localhost SQLite dev DB** (`../flipcommons/backend/db.sqlite3`) — this doc goes stale; the dev DB is ground truth, and [exports.sql](exports.sql) reads it live. Ask the user which snapshot to reset from; never pick one yourself. The rebuild loop and the snapshot-validate discipline are in [0128-relationships/README.md → The dev DB](../0128-relationships/README.md#the-dev-db) and flipcommons' DataPatchAuthoring.md.

Then `make validate` here. Committing and `make push` are the user's call, never automatic.
