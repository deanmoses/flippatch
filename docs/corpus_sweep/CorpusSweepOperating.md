# Operating the AI corpus sweep

How to run `make sweep` — the tool that judges **corpus-vs-catalog deltas** for a model's copy / conversion / conversion-kit relationships, per [docs/plans/AiCorpusSweep.md](../plans/AiCorpusSweep.md). You bring a candidate set (the deterministic SQL/FTS mining is a separate, human/AI-designed step); the sweep does the rest: reconciles every model against the live dev DB, judges its full source note in an independent trusted-tier call, gates the verdicts deterministically, and hands you a short review queue instead of a babysat transcript.

Since ModelRelationships shipped, lineage is one join table — `catalog_modelrelationship`, carrying `relationship_type` × `license_status` × a `target_machine` XOR `target_label` — not the retired `bootleg_of` / `licensed_build_of` / `converted_from` columns. So the sweep judges a single field, **`model_relationship`**: the model reports **every** relationship its note supports, each becomes its own gated row, and every catalog edge the note leaves unsupported surfaces too. ("Bootleg" and "licensed build" are just `copy` + `unlicensed` / `copy` + `licensed`.)

## The trust model (read this first)

The sweep exists because two AI sessions can disagree and a human can't cheaply tell who's right. Its answer is that **no model's opinion is ever trusted directly** — every green row is green because pure code checked three things:

1. **The quote is verbatim** in the source note (`check_quote`, the same gate shipped patches pass).
2. **The stated target resolves to exactly one catalog model** (`EntityIndex.resolve`, narrowed only by facts the note itself stated — year, maker — never by model preference). A plural/unseeded target rides a `target_label` instead and is never resolved to a slug.
3. **The claim agrees with, fills, or conflicts with the catalog edge set** — a matching edge greens, a missing one fills, an edge with a different target/type/license conflicts, and a catalog edge no claim accounts for escalates as set-but-unsupported.

Prior guesses (a Worklist column, an earlier session's answer) ride along as `hint` and are **never shown to the model**; they are diffed afterward. When the sweep and a hint disagree on a fill, the row escalates as `hint-mismatch` with the verbatim quote attached — you adjudicate from evidence, not from which AI you like better.

## Inputs

A **candidates JSONL** file — one `{ipdb_id, hint?, evidence?}` object per **model**:

```jsonl
{"ipdb_id": 4101, "hint": ["rock", "rock-encore"]}
{"ipdb_id": 6015, "evidence": ["ipdb:6015", "https://www.tilt.it/pag/..."]}
```

- `ipdb_id` — the stable join key to both the corpus and the catalog; the sweep judges a model's whole relationship set in one call, so it is also the dedupe and `--resume` key.
- `field` — optional. Only `model_relationship` exists today (the relationship archetype); the key is kept in the contract so a future archetype — a boolean/tag field like widebody or nixie — can slot in.
- `hint` — optional prior guess(es) at a target slug, a string or a list. Audited, never inherited: never shown to the model, only diffed against the sweep's own resolution.
- `evidence` — optional source refs (defaults to the model's own `ipdb:` note). Any scheme `quote_verify`'s `free_text_for` resolves works, so tilt.it / flippers.be web-cache pages plug in per model.

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

- **`results.json`** — every row, machine-readable, full note text included. The durable audit artifact; `--resume` keys off it by `ipdb_id` (a model is judged once, yielding several edge rows), and it survives session handoffs.
- **`REVIEW.md`** — what you actually read. Review rows first, each with the full note inline (no re-fetching); then pre-greened fills ready to author; then collapsed auto-audited tallies.
- **`RECONCILE.md`** (`--no-ai` only) — the free Layer-1 preview: set/empty/no-model buckets plus catalog-vs-hint mismatches.

## Dispositions

| green (auto-audited)                                                                                                                                                                                                           | needs review                                                                                                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `agrees` — note independently confirms an existing edge, same target + type + license (incl. an ambiguous resolution that _contains_ it)                                                                                       | `conflict` — the catalog's edge disagrees with the note on `relationship_type`, `license_status`, or (for a text edge) the `target_label` wording; the reason names the axis |
| `fill` — no matching catalog edge; verbatim quote; a unique resolution (machine target) or a text label; quote **supports** the claim (ai_lint's quote-supports-claim rule, the same standard `make verify-citations` applies) | `set-but-unsupported` — a catalog edge no judged claim accounts for (its target/type/license the note doesn't support — the wrong-seeded case)                               |
|                                                                                                                                                                                                                                | `quote-unsupported` — the fill's verbatim quote fails to establish the claim in context                                                                                      |
|                                                                                                                                                                                                                                | `multi-target-quote` — the fill's quote names a second candidate target (an and-joined donors note)                                                                          |
| `no-claim` — keyword-net false positive (note and catalog both empty of relationships)                                                                                                                                         | `facts-mismatch` — the sole resolution contradicts the note's stated maker/year                                                                                              |
|                                                                                                                                                                                                                                | `same-maker-target` — a **copy** target by the subject's own maker (a chain link, not the original)                                                                          |
|                                                                                                                                                                                                                                | `hint-mismatch` — this sweep and a prior guess disagree on a fill                                                                                                            |
|                                                                                                                                                                                                                                | `ambiguous-target` / `unresolved-target` — resolution not unique/found                                                                                                       |
|                                                                                                                                                                                                                                | `uncertain` / `quote-unverified` / `no-model` / `no-evidence` / `ai-error`                                                                                                   |

A fill's quote-supports-claim check asserts the **license too** when it isn't `unknown`: an edge records authorization as its own fact, so a `licensed` / `unlicensed` fill must be established by the quote on both axes (`unknown` asserts nothing to check — it means the source is silent).

**Label fills face that same check**, with the label rendered into the claim. It matters most there: a machine target earns its green through deterministic unique resolution, but a text target is unresolvable by design, so quote-supports-claim is the only gate standing between model-written `target_label` prose and a patch.

A text edge's **wording is compared too**, not just its type and license — a label is payload a patch rewords in place, so "unknown Williams donor" must not confirm a stored "several Gottlieb EM models". The compare normalizes case, punctuation and whitespace away, so only a real word-level difference escalates. (If that proves noisy in practice, `--regate` re-buckets every stored answer for free.)

Resolution reaches `(Maker)`-suffixed catalog names from bare note titles (and vice versa), narrows by the note's stated maker first and year second (exact year preferred, ±1 tolerated, unknown years never excluded), and a unique survivor that _contradicts_ the stated facts escalates as `facts-mismatch` instead of greening — these rules came out of the 0128 hardening run's TOOL-NOTES defects.

`fill` rows are _auto-eligible_, not auto-applied: they still pass through you, then patch authoring (`patchkit` or hand YAML), the snapshot apply-verify loop, and `make validate`. Committing and `make push` remain your call, always.

## Reviewing escalations

Work `conflict` and `set-but-unsupported` first — they are the wrong-existing-value bucket the whole design exists for. Each detail block carries the quote, the resolution trail (e.g. `2 catalog match(es); year 1978 → 1`), the candidates considered, and the full note. Cross-model evidence (the note that proves a fact about _another_ machine) and web-cache corroboration are your job here, exactly as before — the sweep shrinks the queue, it doesn't replace judgment.

## Tuning or extending the field

The one field today, `model_relationship`, is defined by `SPEC` in `scripts/ai_corpus_sweep/fields.py`: the question plus the hand-crafted recognition guidance covering the polarity / direction / type / license traps (written from real notes, not from imagination — sample the corpus first). Tune that guidance and trial with `--limit` before a full run. A genuinely different archetype — a boolean/tag field like widebody — is more than a new spec: it needs its own judge schema and gate (the current judge emits a list of relationship claims), so add it as a sibling archetype, not a `FieldSpec` variant.
