# Operating the AI corpus sweep

How to run `make sweep` — the tool that judges **corpus-vs-catalog deltas** for one sparse field at a time, per [docs/plans/AiCorpusSweep.md](../plans/AiCorpusSweep.md). You bring a candidate set (the deterministic SQL/FTS mining is a separate, human/AI-designed step); the sweep does the rest: reconciles every candidate against the live dev DB, judges each one's full source note in an independent trusted-tier call, gates the verdicts deterministically, and hands you a short review queue instead of a babysat transcript.

## The trust model (read this first)

The sweep exists because two AI sessions can disagree and a human can't cheaply tell who's right. Its answer is that **no model's opinion is ever trusted directly** — every green row is green because pure code checked three things:

1. **The quote is verbatim** in the source note (`check_quote`, the same gate shipped patches pass).
2. **The stated target resolves to exactly one catalog model** (`EntityIndex.resolve`, narrowed only by facts the note itself stated — year, maker — never by model preference).
3. **The result agrees with, or fills, the catalog** — any contradiction escalates.

Prior guesses (a Worklist column, an earlier session's answer) ride along as `hint` and are **never shown to the model**; they are diffed afterward. When the sweep and a hint disagree on a fill, the row escalates as `hint-mismatch` with the verbatim quote attached — you adjudicate from evidence, not from which AI you like better.

## Inputs

A **candidates JSONL** file — one `{ipdb_id, field, hint?, evidence?}` object per line:

```jsonl
{"ipdb_id": 5441, "field": "converted_from", "hint": "amazon-hunt"}
{"ipdb_id": 6015, "field": "bootleg_of", "evidence": ["ipdb:6015", "https://www.tilt.it/pag/..."]}
```

- `field` — a `scripts/ai_corpus_sweep/fields.py` registry key. v1: `converted_from`, `bootleg_of`, `licensed_build_of` (the relational archetype; boolean/tag fields are the next increment).
- `hint` — optional prior guess at the target slug. Audited, never inherited.
- `evidence` — optional source refs (defaults to the row's own `ipdb:` note). Any scheme `quote_verify`'s `free_text_for` resolves works, so tilt.it / flippers.be web-cache pages plug in per row.

Requirements: the flipcommons dev DB (rebuild it first — it is ground truth), pinexplore's web cache + `explore.duckdb`, and `ANTHROPIC_API_KEY` in `.env` (not needed for `--no-ai`).

## The loop

```bash
# 0. (campaign-specific) emit candidates, e.g. for 0128:
uv run python3 patches/authoring/0128-relationships/emit_candidates.py

# 1. free wiring + coverage check — no AI, no spend
make sweep ARGS="path/to/candidates.jsonl --no-ai"

# 2. cheap trial — judge 10, skim the review, tune field guidance if needed
make sweep ARGS="path/to/candidates.jsonl --limit 10"

# 3. the full run (size --max-requests to the pending count, deliberately)
make sweep ARGS="path/to/candidates.jsonl --resume --max-requests 320"

# 4. interrupted or budget-stopped? results.json is written after every row:
make sweep ARGS="path/to/candidates.jsonl --resume --max-requests 320"

# anytime, from any terminal or session, free — read progress off the artifact:
make sweep ARGS="path/to/candidates.jsonl --status"

# after a gate fix or a dev-DB rebuild — re-bucket the stored answers, no AI spend:
make sweep ARGS="path/to/candidates.jsonl --regate"

# retrofit the fill cite-quote check onto a run judged before it existed (1 call per fill):
make sweep ARGS="path/to/candidates.jsonl --verify-fills"
```

**The safety contract:** `results.json` _and_ `REVIEW.md` are rewritten after **every** judged row (atomic replace). Ctrl-C at any moment loses at most the single row in flight (~2 seconds of spend); `--resume` continues from where it stopped. The run prints this contract as its first line, and `--status` proves it — the artifact on disk is the status, readable while the run is going.

**If you drive the full run from an AI session:** run it in the background and poll `--status` / read `REVIEW.md` between other work — a foreground tool call swallows the per-row narration for 10–20 minutes and shows the human nothing.

**Re-gating is free.** The model's answers (verdict, quote, the target as the note stated it) are persisted per row; resolution and disposition are pure code. So a fixed gate, a widened resolver, or a rebuilt dev DB re-buckets the entire run in seconds via `--regate` — never re-judge with AI what is already judged.

Every candidate is judged **regardless of the catalog's current value** — that is what catches wrong seeded links, not just empty cells. A few hundred rows cost well under a dollar and run in minutes, unattended; progress narrates one line per row.

## Outputs (written to the candidates file's directory, or `--out`)

- **`results.json`** — every row, machine-readable, full note text included. The durable audit artifact; `--resume` keys off it (by `ipdb_id` + `field`), and it survives session handoffs.
- **`REVIEW.md`** — what you actually read. Review rows first, each with the full note inline (no re-fetching); then pre-greened fills ready to author; then collapsed auto-audited tallies.
- **`RECONCILE.md`** (`--no-ai` only) — the free Layer-1 preview: set/empty/no-model buckets plus catalog-vs-hint mismatches.

## Dispositions

| green (auto-audited)                                                                                                                                                                                | needs review                                                                                                  |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `agrees` — note independently confirms the existing value (incl. an ambiguous resolution that _contains_ it)                                                                                        | `conflict` — catalog holds a **different** value than the note supports                                       |
| `fill` — catalog empty; verbatim quote; unique resolution; quote **supports** the claim (ai_lint's quote-supports-claim rule, the same standard `make verify-citations` applies to shipped patches) | `set-but-unsupported` — catalog set, but the note supports no claim                                           |
|                                                                                                                                                                                                     | `quote-unsupported` — the fill's verbatim quote fails to establish the claim in context                       |
|                                                                                                                                                                                                     | `multi-target-quote` — the fill's quote names a second candidate target (an and-joined donors note)           |
| `no-claim` — keyword-net false positive                                                                                                                                                             | `facts-mismatch` — the sole resolution contradicts the note's stated maker/year                               |
|                                                                                                                                                                                                     | `same-maker-target` — a licensed/bootleg "target" by the subject's own maker (a chain link, not the original) |
|                                                                                                                                                                                                     | `hint-mismatch` — this sweep and a prior guess disagree on a fill                                             |
|                                                                                                                                                                                                     | `ambiguous-target` / `unresolved-target` — resolution not unique/found                                        |
|                                                                                                                                                                                                     | `uncertain` / `quote-unverified` / `no-model` / `no-evidence` / `ai-error`                                    |

Resolution reaches `(Maker)`-suffixed catalog names from bare note titles (and vice versa), narrows by the note's stated maker first and year second (exact year preferred, ±1 tolerated, unknown years never excluded), and a unique survivor that _contradicts_ the stated facts escalates as `facts-mismatch` instead of greening — these rules came out of the 0128 hardening run's TOOL-NOTES defects.

`fill` rows are _auto-eligible_, not auto-applied: they still pass through you, then patch authoring (`patchkit` or hand YAML), the snapshot apply-verify loop, and `make validate`. Committing and `make push` remain your call, always.

## Reviewing escalations

Work `conflict` and `set-but-unsupported` first — they are the wrong-existing-value bucket the whole design exists for. Each detail block carries the quote, the resolution trail (e.g. `2 catalog match(es); year 1978 → 1`), the candidates considered, and the full note. Cross-model evidence (the note that proves a fact about _another_ machine) and web-cache corroboration are your job here, exactly as before — the sweep shrinks the queue, it doesn't replace judgment.

## Adding a field

Add a `FieldSpec` in `scripts/ai_corpus_sweep/fields.py`: the DB column, the question, and guidance covering that field's polarity traps (write them from real notes, not from imagination — sample the corpus first). Trial with `--limit` before a full run.
