# 0299–0301 — IPDB relationship specialties, worked into lineage edges

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

## The sweep run and its two patches

The 119-model feed (no `hint`s — 0128's target guesses live only in its regenerable candidate file, so there was nothing standing to audit against) judged clean: 119/119 models, 180 edge rows, at a cost of one tooling fix (the judge's output cap rose 1024 → 4096 after `opportunity`'s ten-donor note truncated a structured answer).

**Patch 0300** (`0300-conversion-lineage-sweep.yaml`, applied) — the vetted green tier: 73 edges over 51 models. The vet corrections live beside `_lineage_fill_edges` in `lineage.sql`; the load-bearing one is structural — **an edge's identity is its machine target** (the apply engine rejects a second member to the same target, whatever the type), so the Glickman converted-game-then-kit cohort carries one `conversion` edge per donor, not two.

**Patch 0301** (`0301-conversion-lineage-escalations.yaml`, applied) — the adjudicated review tier: 114 edges over 58 models, from the 98 escalated rows. The rules, argued in full at `_lineage_escalation_edges`: and-lists become machine edges; or-lists become one label (the coal-town rule); Exhibit/esco maker-token gate artifacts are authored on their correct resolutions; catalog twins and unseeded donors take labels; IPDB's reasoned "likely X" identifications are authored with the hedge riding in the quote; mixed lists use machine edges plus the one label slot for the remainder (`flat-top`, `laura`, `soft-ball-queens`). Six dismissals are recorded with reasons in `_lineage_escalation_dismissals`.

Every quote in all three patches was `--check`-verified before being recorded, and every routing is asserted by `lineage_checks` ledgers that hold on both sides of each apply.

## End state

Scope went **139 models → 11**: the two no-prose census assertions (`cadillac-2`, `sky-chief-2`) and nine `no-claim` models whose notes carry no lineage claim to quote. All eleven stay as expected worklist rows — research exhausted for now is not adjudication.

Still deferred, for their own pass:

- `other_type_edge` — **36** after the applies (the census asserts both `Converted Game` and `Conversion Kit` on many of these machines; one type is now carried and the other lands here, joining the original mistyped-or-second-edge questions).
- `edge_points_inward` — 3: same question from the far end.
