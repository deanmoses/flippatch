# AI Corpus Sweep Tool

We have sparse structured fields that matter to catalog quality, and the best available evidence is trapped in unstructured corpus notes. We need a repeatable way to discover, verify, review, and patch evidence-backed candidate claims with known precision/recall.

## The problem

Many fields in the Flipcommons catalog domain model are **sparse**; not many models populate the field. Things like:

- Is the model a **conversion kit**? If so, what other model is it converting from?
- Is the model a **bootleg**? If so, what other model is it a bootleg of?
- Is the model **not a pinball**, but one of the other ~6 game formats?
- Is the model a **widebody**?
- Does the model display via **Nixie tubes**?

These fields were not represented as structured data in any previous system -- not IPDB, not OPDB -- so they weren't set in Flipcommons baseline seed data. Now we're trying to populate those fields.

The best source of this data is IPDB’s free text notes about each model. We have all of IPDB in a raw JSON dump in pinexplore‘s DuckDB db (the `ipdb_machines` table: `IpdbId, Title, Manufacturer, Type, Players, Theme, NotableFeatures, Notes`).

What we've been doing, and continue to think is the right approach, is to work on one field at a time across all models -- like tagging all the widebody models with the `widebody` tag. It's simple enough to find candidates in DuckDB via a SQL/FTS prefilter over that free text, that looks for words related to the field.

The issue is how to further refine and filter those results. We've only tried one approach so far: ask an interactive AI session with a high-powered AI model to ideate on the keywords, run the queries and then do the triage -- all inside of one interactive session. We've been frustrated with this approach: it's not a repeatable process, it's tedious for the developer to babysit and verify, the session runs out of context pretty quickly, it's pretty slow and pretty expensive. And after it's done I still wonder whether it omitted any positives or include false positives. Later on I wonder how well the session did its work, or maybe pass on unfinished work to a new session, but there's nothing to go back to and inspect.

## What's NOT the solution

You might think that we could use cheaper models to decide on most of the obvious ones. Spawn a session for each candidate and use a cheaper model to answer. If the answer is a confident yes or no, accept it and don't bring in the more expensive model.

I'm not willing to try that for two reasons:

1. I don't trust the judgement of the cheaper models to know what's obvious. A real world example from IDPB is this: _"The other model is a widebody"_, which is saying that the machine in question is **not** a widebody. I'm fairly sure the cheaper models would get that wrong.
2. The "other" model the example above does NOT itself mention it's a widebody: a note in another model is the ONLY evidence that it's a widebody. So to resolve a field on a model you sometimes need the IPDB notes from **MULTIPLE** models.

## The solution

TODO: the solution needs to account for coverage, accuracy, reviewer throughput, and auditability. The solution below was written with a cost framing, which _is_ a consideration, but it's not the main one.

### Cost

The cost and the context ceiling are artifacts of the **session shape**. Judging the 300th candidate inside one accumulating conversation means carrying candidates #1–299 and all prior reasoning in the window — roughly O(N²) tokens across the sweep, against a hard context ceiling. The expense is the accumulation. The fix is to turn the judging step from one long interactive session into N independent, stateless calls. One IPDB note per call, fresh context each time. This removes both the ceiling and the cost:

- Each call sees only `[field definition + hand-crafted guidance + the full note]`. The full note is the original context a judgment needs — nothing is judged from a bare snippet — and it always fits, because an IPDB note is a paragraph or two.
- Context never fills: N independent O(1) calls replace one O(N²) session.
- It is cheap **even at the trusted model's rates, because each call is tiny.** On the order of a few hundred hits × a few hundred tokens is well under a dollar per field; the [Batch API](#mechanics) halves that again.

For cases that are still uncertain or where information in the note of one model suggests that the field might be set on another model, the stateless call surfaces that, for judging by the coordinating session.

## Relationship to the extraction tool

This is the **transpose** of [the page data extractor](AiPageDataExtractor.md), and the two share machinery:

|                    | Extraction tool                        | Corpus sweep                                     |
| ------------------ | -------------------------------------- | ------------------------------------------------ |
| Fans out over      | many **questions**, one record         | many **records**, one question (field)           |
| Shared context     | the page — so **cache** it             | none — each record differs, so **batch** instead |
| Cheap vs expensive | cheap model fans out, master validates | **trusted** model judges every record            |
| Verifier           | `check_quote`                          | `check_quote` (same)                             |
| Source adapter     | `_Sources.free_text_for` (web cache)   | `_Sources.free_text_for` (IPDB free-text notes)  |

It uses the same primitives — `check_quote`, forced-schema output (via `common.ai.client`), candidate-not-fact framing (`common.ai.candidates`), deterministic target-resolution (`common.catalog.entity_index.EntityIndex.resolve`) — pointed at the other axis. Those primitives are now built once, under `scripts/common/`; this tool adds only the Batch submission mode (see below).

## What already exists (reuse it)

- **The shared foundation** — `flippatch/scripts/common/` (see [AiCommon.md](AiCommon.md)). This tool is a _consumer_ of it: `common.ai.client` provides the forced-schema structured call with the per-run request-count cap, token accounting, local `jsonschema` validation, and the offline mock seam already built in; `common.catalog.entity_index.EntityIndex.resolve(name)` is the deterministic name→catalog cross-check the `target_title` step needs; `Usage` lives in `common.ai.client`; `Candidate` / `EvidenceQuote` live in `common.ai.candidates`. The one piece it does _not_ yet provide is **Batch submission** — that's AiCommon build-order **step 4**, and adding it is this tool's first task (see [Batch API](#batch-api)).
- **IPDB note text** — `flippatch/scripts/quote_verify/verify_quotes.py`, `ipdb_notes_text(...)` (via `_Sources.free_text_for`) assembles the free-text Notable Features + Notes prose for one IPDB id from the `ipdb_machines` DuckDB table. That prose is the per-record payload the model judges; the structured columns (Manufacturer, Type, Players, Theme, year) are deterministic data, joined or filtered directly in SQL rather than read by the model.
- **Deterministic quote verification** — `verify_quotes.check_quote(quote, source)` confirms the model's returned quote is verbatim in the note, with the sanctioned normalizations. Same definition of "verbatim" as the shipped-patch gate.
- **Claim emission** — `flippatch/patches/authoring/patchkit.py`, once a sweep's confirmed results become a patch.

## Mechanics

### Batch API

**Prerequisite — not built yet.** Batch submission on `common.ai.client` is AiCommon build-order **step 4**, currently unbuilt. Adding it — as a submission mode on the existing client, not a fork (see [AiCommon.md](AiCommon.md)) — is this tool's first implementation task, not an existing capability.

The Batch API is the right transport: N independent, non-latency-sensitive classification requests, 50% off, results keyed by a `custom_id` (the IPDB id). Forced-schema / strict tool output works in batch. Poll to completion, then collate. This is what makes "the trusted model over every hit" both cheap and context-safe.

### Prompt layering

Prompt layering follows `common.ai`'s prompt-assembly discipline (AiCommon §4) — the same three roles the [page extractor](AiPageDataExtractor.md#per-slice-prompt-three-layers) uses: the field definition as the grounding layer (derived from the DB / DomainModel.md), hand-crafted recognition guidance (synonyms, and explicit warnings about the polarity/direction traps above — companion-model references, negations, converted-to vs. -from), and any per-sweep caller context. There is no shared page to cache, so caching is irrelevant here; the small shared instruction prefix could be cached across a batch but it's a rounding error next to the batch discount.

## The pipeline

For one field:

### SQL/FTS prefilter

Do a SQL/FTS over the IPDB notes in DuckDB → the candidate set (already in hand). Build the term list iteratively — seed obvious terms, sample hits, expand to the phrasings that actually appear. Paraphrases carrying no listed term are a known recall gap, closed only by widening the term list as misses surface.

### Stateless fan-out judging

One independent request per candidate note through `common.ai.client` on the trusted tier (`TRUSTED_MODEL`), forced-schema output `{verdict: yes/no/uncertain, target_title (relational fields only), quote}`. The trusted tier is mandatory here, not the cheap one: the sweep has no downstream disposer — a human skims the results table, but nothing re-reads each note — so precision is the model's job at judge time (AiCommon §5, and [What's NOT the solution](#whats-not-the-solution) above). Fresh context per call; the full note is the context, because membership isn't decided by the keyword — the model reads every hit in full.

### Deterministic post-steps

- `check_quote(quote, note)` — drop or flag any verdict whose quote isn't verbatim in the note.
- `target_title → catalog ref` — resolve the named source/target model against the live catalog with `common.catalog.entity_index.EntityIndex.resolve(name)` built with `types=("model", "title")`, the same cross-check the extraction tool uses for entity discovery. An ambiguous (multiple refs) or unresolved (empty) target escalates per-record.

### Human review of a compact results table

`{ipdb_id, verdict, quote, note, resolution}`, quote-anchored, sortable by verdict/confidence. You skim a table, not a dying chat transcript. Confirmed rows become a `patchkit` patch (authored, `make validate`, then the usual hand-off — commit and push are the user's call).

## Output

A per-field results artifact (JSON or a table), each row `{ipdb_id, title, verdict, target_ref (relational), quote, quote_verified, note, resolution}` — its `quote` + `quote_verified` pair is `common.ai.candidates.EvidenceQuote`. Framed as **candidates with verbatim-checked evidence**, exactly as the extraction tool: `check_quote` proves the quote exists, not that it supports the verdict — the human (or a trusted-model pass) makes the final call. Carry the full note in the row so review needs no re-fetch.

## Build order — thinnest slice

1. Pick **one boolean field** (widebody) and **one relational field** (converted-from) — they exercise the two output shapes and the target-resolution step.
2. Add Batch submission to `common.ai.client` (the step-4 prerequisite), then run the existing SQL prefilter; feed each hit's `ipdb_notes_text` (the free-text Notes / Notable-Features only, via `_Sources.free_text_for` — never the structured columns) through a stateless Batch fan-out on the trusted tier (`TRUSTED_MODEL`) with a forced schema; `check_quote` every result; for the relational field, resolve `target_title` with `common.catalog.entity_index.EntityIndex.resolve`.
3. Compare the results table against a hand-labeled sample of the same hits — measure the trusted model's precision and recall specifically on the tricky cases (negations, companion-model references, wrong-direction conversions), and via a random sample of _non_-matched records, the SQL net's recall.
4. If the model handles the polarity/direction traps and the relational targets resolve cleanly, generalize to the rest of the sparse fields.

## Decisions still open

- **SQL net recall:** the term list bounds it. Decide per field how far to widen it (measured by a random-sample audit of non-matched records) versus accepting a known recall floor.
- **Where the field definitions live:** structured `help_text` vs. `DomainModel.md` prose — the same open question as the extraction tool; the hand-crafted guidance layer is the home for it either way.
