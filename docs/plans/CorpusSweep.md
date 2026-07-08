# Design: the corpus-sweep pattern (sparse-field backfill)

**Status:** proposal / design. No code yet. Companion to [ExtractionTool.md](ExtractionTool.md) — the two are transposes of one toolkit (see [Relationship](#relationship-to-the-extraction-tool)). This captures the pattern so a localhost session (flipcommons + flippatch + pinexplore checked out with their live DBs) can build it.

## The problem

Many domain-model fields are **sparse** — set on few models, or on none, because they were never structured data in any prior system. Backfilling them means looking across the *whole* catalog, one field at a time:

- Is the model a **conversion kit**? If so, converted **from** which model?
- Is it a **bootleg**? If so, a bootleg **of** which model?
- Is it **not pinball** but one of the other ~6 game formats?
- Is it a **widebody**?
- Does it display via **Nixie tubes**?

The best source is IPDB's free-text notes, and all of IPDB is already in pinexplore's DuckDB analysis DB (the `ipdb_machines` table: `IpdbId, Title, Manufacturer, Type, Players, Theme, NotableFeatures, Notes`). A SQL/FTS prefilter over that free text — the reason the DuckDB exists — already narrows the catalog to the records that mention a field's vocabulary. **That prefilter is a solved, in-hand step; this design is about everything after it.**

## The real bottleneck: session accumulation, not model tier

The natural approach — have a high-powered model read every prefiltered hit inside one interactive session — hits a wall: it gets expensive and runs out of context fast. The instinct is to blame the model tier and reach for a cheaper model. That is the wrong diagnosis.

The cost and the context ceiling are artifacts of the **session shape**, not the model. Judging hit #300 inside one accumulating conversation means carrying hits #1–299 and all prior reasoning in the window — roughly O(N²) tokens across the sweep, against a hard context ceiling. The expense is the accumulation.

**The fix is to turn the judging step from one long session into N independent, stateless calls** — one note per call, fresh context each time. This keeps the trusted (expensive) model making every judgment while removing both the ceiling and the cost:

- Each call sees only `[field definition + hand-crafted guidance + the full note]`. The full note is the original context a judgment needs — nothing is judged from a bare snippet — and it always fits, because an IPDB note is a paragraph or two.
- Context never fills: N independent O(1) calls replace one O(N²) session.
- It is cheap **even at the trusted model's rates, because each call is tiny.** On the order of a few hundred hits × a few hundred tokens is well under a dollar per field; the [Batch API](#mechanics) halves that again.
- The model you trust makes every call. There is no cheap-model gate to distrust.

This is the crux of the whole pattern: **stateless fan-out of the trusted model.** Caching (nothing repeats across records) and a cheap-model gate (a judge you'd distrust and re-check anyway) were both solving problems this scenario doesn't have.

## Relationship to the extraction tool

This is the **transpose** of [ExtractionTool.md](ExtractionTool.md), and the two share machinery:

| | Extraction tool | Corpus sweep |
|---|---|---|
| Fans out over | many **questions**, one record | many **records**, one question (field) |
| Shared context | the page — so **cache** it | none — each record differs, so **batch** instead |
| Cheap vs expensive | cheap model fans out, master validates | **trusted** model judges every record |
| Verifier | `check_quote` | `check_quote` (same) |
| Source adapter | `_Sources` (web cache) | `_Sources` / `ipdb_row_text` (IPDB rows) |

Same primitives — `check_quote`, forced-schema output, candidate-not-fact, deterministic target-resolution — pointed at the other axis. Build them once.

**What forces the cheap-proposer split is the question count, not the document size.** Many distinct questions against one shared context is what creates satisficing — so the extraction tool fans out into narrow single-question calls, and because the *same* page is then read once per question, it offloads those repeated reads to a cheap proposer and has the arbiter read the page once to vet. A sweep has *one* question per record: no satisficing to decompose and no repeated read to offload, so the trusted model just reads each record once and answers — there is nothing for a cheap proposer to do. Document size only changes *how much* the offload-plus-cache saves (a big page read many times is a big saving; a small note, little) — it never creates or removes the need for a proposer. (If a sweep ever asked several sparse fields per record at once, it *would* satisfice and want the fan-out — which is why sweeps run one field at a time instead.)

## What already exists (reuse it)

- **IPDB note text** — `flippatch/scripts/quote_verify/verify_quotes.py`, `ipdb_row_text(...)` assembles the full quotable note for one IPDB id (title, structured fields, Notable Features, Notes) from the `ipdb_machines` DuckDB table; `_Sources._ipdb_text` reads the rows. This is the per-record payload for each fan-out call — no new extraction.
- **Deterministic quote verification** — `verify_quotes.check_quote(quote, source)` confirms the model's returned quote is verbatim in the note, with the sanctioned normalizations. Same definition of "verbatim" as the shipped-patch gate.
- **Claim emission** — `flippatch/patches/authoring/patchkit.py`, once a sweep's confirmed results become a patch.

## Mention ≠ membership: the trusted model reads every hit

There is no shortcut where a keyword hit or a verified quote settles the answer without a full read. The note text routinely inverts a naive match:

- *"Its companion model is a widebody"* — the machine in question is **not** a widebody.
- *"Unlike the bootlegs that followed, this was the licensed original"* — mentions "bootleg," is not one.
- *"Later converted **to** a two-player"* — a conversion, but the opposite direction from converted-**from**.

The keyword only got the record into the candidate set; whether the term actually applies to *this* machine — in the right polarity and direction — takes a full read of the note. That judgment is exactly what the high-powered model is for, and no field is so "lexically decisive" that it escapes it: "Nixie," "widebody," "conversion" all show up in negations, comparisons, and references to *other* machines. So the trusted model reads **every** prefiltered hit. `check_quote` guards against a fabricated quote; it does nothing about a real quote read the wrong way — that is the model's job, and the reviewer's.

This is not a problem to engineer around — it's the reason the [stateless fan-out](#the-real-bottleneck-session-accumulation-not-model-tier) matters. "Read every hit with the trusted model" is affordable and context-safe precisely because the reads are independent, so there is no need for a cheaper tier or a shortcut.

## The pipeline

For one field:

1. **SQL/FTS prefilter** over the IPDB notes in DuckDB → the candidate set (already in hand). Build the term list iteratively — seed obvious terms, sample hits, expand to the phrasings that actually appear. Paraphrases carrying no listed term are a known recall gap, closed only by widening the term list as misses surface.
2. **Stateless fan-out judging.** One independent request per candidate note to the trusted model, forced-schema output `{verdict: yes/no/uncertain, target_title (relational fields only), quote}`. Fresh context per call; the full note is the context, because [membership isn't decided by the keyword](#mention--membership-the-trusted-model-reads-every-hit).
3. **Deterministic post-steps** (no model):
   - `check_quote(quote, note)` — drop or flag any verdict whose quote isn't verbatim in the note.
   - `target_title → catalog ref` — resolve the named source/target model against the live catalog (slug / ipdb_id), the same cross-check the extraction tool uses for entity discovery. Ambiguous or unresolved targets escalate per-record.
4. **Human review of a compact results table** — `{ipdb_id, verdict, quote, note, resolution}`, quote-anchored, sortable by verdict/confidence. You skim a table, not a dying chat transcript. Confirmed rows become a `patchkit` patch (authored, `make validate`, then the usual hand-off — commit and push are the user's call).

### Mechanics

- **Batch API** is the right transport: N independent, non-latency-sensitive classification requests, 50% off, results keyed by a `custom_id` (the IPDB id). Forced-schema / strict tool output works in batch. Poll to completion, then collate. This is what makes "the trusted model over every hit" both cheap and context-safe.
- **Prompt layering** mirrors the extraction tool's [three layers](ExtractionTool.md#per-slice-prompt-three-layers): the field definition (derived from the DB / DomainModel.md), hand-crafted recognition guidance (synonyms, and explicit warnings about the polarity/direction traps above — companion-model references, negations, converted-to vs. -from), and any per-sweep caller context. There is no shared page to cache, so caching is irrelevant here; the small shared instruction prefix could be cached across a batch but it's a rounding error next to the batch discount.

## Output

A per-field results artifact (JSON or a table), each row `{ipdb_id, title, verdict, target_ref (relational), quote, quote_verified, note, resolution}`. Framed as **candidates with verbatim-checked evidence**, exactly as the extraction tool: `check_quote` proves the quote exists, not that it supports the verdict — the human (or a trusted-model pass) makes the final call. Carry the full note in the row so review needs no re-fetch.

## Build order — thinnest slice

1. Pick **one boolean field** (widebody) and **one relational field** (converted-from) — they exercise the two output shapes and the target-resolution step.
2. Run the existing SQL prefilter; feed each hit's `ipdb_row_text` through a stateless Batch fan-out to the trusted model with a forced schema; `check_quote` every result; for the relational field, resolve `target_title` against the catalog.
3. Compare the results table against a hand-labeled sample of the same hits — measure the trusted model's precision and recall specifically on the tricky cases (negations, companion-model references, wrong-direction conversions), and via a random sample of *non*-matched records, the SQL net's recall.
4. If the model handles the polarity/direction traps and the relational targets resolve cleanly, generalize to the rest of the sparse fields.

## Decisions still open

- **SQL net recall:** the term list bounds it. Decide per field how far to widen it (measured by a random-sample audit of non-matched records) versus accepting a known recall floor.
- **Where the field definitions live:** structured `help_text` vs. `DomainModel.md` prose — the same open question as the extraction tool; the hand-crafted guidance layer is the home for it either way.
