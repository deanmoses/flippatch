# 0299 — IPDB relationship specialties, worked into lineage edges

Works the external data source layer's `ipdb_model_relationships_missing` worklist — the models IPDB marks `Converted Game` / `Conversion Kit` / `Re-themed Game` that carry no such edge, the research campaign the [0297 census](../0297-ipdb-specialties-census/README.md) deferred on shape ("a relationship edge needs a target and a `license_status`, and IPDB's one word supplies neither").

- `lineage.sql` — the analysis: the scope cut, the two routes, the hand-pass adjudication table, the checks. The worklist itself is the layer's live view; this file only routes it.
- `emit_candidates.py` — the sweep feed, one `{ipdb_id}` per un-judged model, regenerated from the analysis on each run.
- `gen.py` — emits `patches/0299-conversion-lineage.yaml` from `lineage_patch_rows`.

## The scope cut

Scope is the worklist's `no_edge` class only (151 rows, 139 models at the start). `other_type_edge` (14) and `edge_points_inward` (3) are **deferred**: whether an existing edge of another type is the same relationship mistyped or a second relationship is an adjudication question, not a research gap, and wants its own pass.

Within scope, two routes that partition it exactly (checked, both directions, on both sides of the apply):

| route | models | what happens |
| --- | ---: | --- |
| `lineage_parked_0128` | 20 | hand pass over campaign 0128's standing sweep verdicts — **no AI re-judging** |
| `lineage_sweep_candidates` | 119 | fresh `make sweep` run |

The 20 were judged by 0128's sweep, parked in doubt buckets (`uncertain`, `ambiguous-target`, `quote-unverified`, …), and never worked — the AI half was done, the human half outstanding. Being on 0128's *candidate* list without a result row is not adjudication (that file is regenerated live), so such models stay in the sweep feed.

## The hand pass (patch 0299, applied)

`_lineage_adjudications` in `lineage.sql` records the 21 edges over 20 models, each vetted against the full note (`make show-source`), each quote `--check`-verified before being recorded, each with its rationale in the `why` column. The recurring calls, argued in full in the table's header comment:

- **Type follows the note's prose** where it diverges from the census heading (four Italian machines whose notes say "conversion of" under a `Conversion Kit` specialty). Those four (`western-2`, `summer-time-4`, `top-hand-4`, `kiss-2`) deliberately migrate to the deferred `other_type_edge` class post-apply, where the mistyped-or-second-edge question belongs.
- **License is `unknown` on every row** — an IPDB note establishes the conversion, never the authorization (0128's standing rule).
- **Homonym donors resolve by feasibility** (a 1970 Dama EM kit cannot target a 1937 flipperless `Bazaar` or a 1976 `Rancho`) and by IPDB's bare-name convention (bare "Ice Show" means the non-`(Italy)` listing — the Western note demonstrates the convention by spelling out "or perhaps also … 'Subway (Italy)'" when it means both; that hedged second donor stays unauthored).
- **Either/or and unidentified donors become `target_label`** in the note's own words (the `coal-town` disjunction, six unknowns), never a guessed machine.

Status: `make validate` clean, all 20 quotes verbatim-verified, applied to the dev DB (reset from `db.prod.patch-0298.2026-08-31`), `make validate-in-db` clean — 0 errors, 0 warnings.

## The sweep (patch pending)

The 119-model feed is emitted and reconciles clean (`--no-ai`: all 119 `empty`, as a `no_edge` scope must). The judge run is **blocked on API credit** — the trial (`--limit 10`) hit the Anthropic billing wall. Once topped up:

```bash
make sweep ARGS="campaigns/0299-ipdb-relationship-lineage/sweep/candidates.jsonl --limit 10"
make sweep ARGS="campaigns/0299-ipdb-relationship-lineage/sweep/candidates.jsonl --resume --max-requests 119"
```

The feed carries no `hint`s: 0128's target guesses live only in its regenerable candidate file, not in any adjudicated record, so there is nothing standing to audit against. Two feed models (`cadillac-2` ipdb:4795, `sky-chief-2` ipdb:3256) have no IPDB note at all and will land in review rather than green.

## What stays deferred, and where it now stands

- `other_type_edge` — **18** after the apply (14 original + the 4 type divergences above): the type-adjudication pass.
- `edge_points_inward` — 3: same question from the far end.
- The one `retheme` row (`retro-spa`, ipdb:7037) is in the sweep feed; note a retheme patch requires `target_machine` — no label allowed.
