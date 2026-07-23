# relationships.sql — performance brief

Handoff for a session doing **only** this. Goal: make the analysis fast, and see whether a small, generally useful relationship explorer can be teased out for other campaigns to reuse.

## Where the time actually goes (measured, dev DB, 2026-07-21)

| step | wall |
| ---- | ---- |
| load the file (8 materialized tables + ~20 views) | 3s |
| `SELECT count(*)` from any one public view | +0s |
| `relationships_checks` | +3s |
| `relationships_summary` | **+15s** |
| full `make analyze PREFIX=relationships` | ~34s |

It was **16+ minutes** before the private `_`-prefixed helpers became `CREATE OR REPLACE TABLE` (the pattern `0177-exports` uses). That change is already in.

**No single query is slow.** Every individual view answers in well under a second on top of the 3s load. The summary is slow purely by accumulation: ~45 `UNION ALL` branches, most of them scanning `relationship_candidates`.

## The one thing to fix first

`relationship_candidates` is still a **view**, and it carries roughly six correlated subqueries per row (existing edge types, edge targets, lineage kinds, inbound-edge existence, resolved target guesses) over ~870 rows. Every summary branch that touches it re-runs all of that. Roughly a dozen do.

Fix: compute it once into a private `_rel_candidates` table and leave `relationship_candidates` as a thin `SELECT * FROM _rel_candidates`. Public objects should stay views — the runner's `describe` enumerates views, and each public view carries a `COMMENT ON VIEW` contract — so the shape to reach for throughout is **thin public view over materialized private table**.

Second, smaller: the summary's reject-reason branches are ~10 separate `count(*) FILTER (...) FROM relationship_green_rejected` scans that could be one grouped scan.

Third: `_title_key(name)` appears in join conditions (`ON _title_key(a.name) = _title_key(b.name)`), so every join recomputes it per row and nothing can be pre-hashed. A single `_model_key(id, key, year, maker_slug)` table joined by equality would help the namesake self-joins most.

## What might not be earning its keep

Ask this per view before optimizing it — deleting beats tuning. Rough guide to what is load-bearing:

- **Daily drivers, keep:** `relationship_green`, `relationship_green_rejected`, `relationship_review`, `relationships_summary`, `relationships_checks`.
- **Used occasionally:** `relationship_edged_audit`, `relationship_uncited_edges`, `relationship_open_questions`, `relationship_sweep_candidates` (feeds `emit_candidates.py` — check that's still live before touching).
- **One-time research, already did its job:** `relationship_namesake_review`. It exists to find phrasebook gaps and it found them; its `namesake_window_drifted` check does a full models-on-models self-join *again* to re-derive the year window. Strong deletion candidate — it is 3s of the 6s checks pass, and the window it validates is now stable.
- **Narrow, cheap, but a lot of surface:** the derived book-title machinery (`_rel_book_phrase`, `_rel_generic_book`, `unmatched_book_title`, `unlisted_generic_book`, three `book_root_*` metrics). It exists only because `cite:` cannot express a book reference upstream. Worth keeping while that is true, but it is four objects and two checks for one blocked case.

## The reusable nugget

Most of this file is campaign bookkeeping — recorded human judgement, the book-cite blocker, the sweep feed, provenance audits. The part that is **generally** useful to any campaign asking "what does the catalog say about model-to-model lineage" is small and sits at the front:

1. `_rel_signal` — per-model prose (`ipdb_notes` + `ipdb_notable_features` + `description`) with the detector phrasebook applied.
2. `_rel_quote` — the lineage sentence, normalized exactly as `verify_quotes.py` normalizes the source side, so an extracted span is quotable.
3. `_rel_donor_span` / `_rel_year_qualified` / `_quoted_resolved` — resolve the donor a note names: titles quoted **after** the lineage phrase, narrowed by the year IPDB writes before the title. Both narrow and never eliminate.
4. Edge enrichment from `model_relationships` / `model_edges_bidir` — what the catalog already claims.

That is the explorer. Everything after it is this campaign's opinion. If it moves, the two candidate homes are flipcommons' `scripts/analysis/` foundation (if other campaigns want it) or a shared file under `campaigns/`. Two things must travel with it or it silently rots: the phrasebook macros are shared by both the membership detectors **and** the quote extractor (`phrase_not_extractable` checks that), and every phrase has an anchor in `relationships_checks` pinned to a real specimen.

## Rules for this work

- `relationships_checks` must stay clean, and the row counts in `relationships_summary` must not move. This is a refactor: if `green` changes, something broke.
- Nothing here writes to the catalog. The SQLite attach is read-only; the materialized tables live in DuckDB's own in-memory catalog.
- Bug fixes need a failing check first (this repo's TDD rule); for SQL that means an anchor that fails before the change and passes after.
- Do not run `gen.py` or `gen_victory_games.py` — their patches are applied. Regenerating is only safe after rebuilding the dev DB without them.
