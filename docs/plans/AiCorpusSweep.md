# AI Corpus Sweep Tool

> **Status: v1 built** — `scripts/ai_corpus_sweep/`, run via `make sweep`; operator guide at [docs/corpus_sweep/CorpusSweepOperating.md](../corpus_sweep/CorpusSweepOperating.md). It ships the relational archetype — one `model_relationship` field judged against the `catalog_modelrelationship` join table (`relationship_type` × `license_status` × a `target_machine` XOR `target_label`), after ModelRelationships retired the `bootleg_of` / `licensed_build_of` / `converted_from` columns — with the JSONL candidate contract, the reconciler, the trusted-tier fan-out, the deterministic gates (verbatim quote, unique resolution with year/maker narrowing, catalog edge-set + hint diff), resumable `results.json`, and `REVIEW.md`. A model reports every relationship its note supports; each becomes its own gated row and unsupported catalog edges surface too. Not yet built: the boolean/tag archetype, model-assisted disambiguation of still-ambiguous targets (v1 escalates them with the candidate facts listed), and Batch submission. First consumer: the 0128-relationships campaign (`emit_candidates.py` there adapts its discovery plan, `relationships.sql`).

We have sparse structured fields that matter to catalog quality, the best available evidence is trapped in unstructured corpus notes, and some of the values that _are_ set were imported wrong. We need a repeatable way to discover, verify, review, and patch evidence-backed candidate claims — measured against the catalog's current state — with known precision/recall and an audit trail.

## The problem

Many fields in the Flipcommons catalog domain model are **sparse**; not many models populate the field. Things like:

- Is the model a **conversion kit**? If so, what other model is it converting from?
- Is the model a **bootleg**? If so, what other model is it a bootleg of?
- Is the model **not a pinball**, but one of the other ~6 game formats?
- Is the model a **widebody**?
- Does the model display via **Nixie tubes**?

These fields were not represented as structured data in any previous system -- not IPDB, not OPDB -- so they weren't set in Flipcommons baseline seed data. Now we're trying to populate those fields.

But "sparse" isn't the whole story. Some of these fields _were_ populated in the seed or by an earlier import from a weaker source, and a fraction of those values are **wrong**. The relationships campaign (`campaigns/0128-relationships/`) found six seeded conversion links pointing at the wrong donor game — e.g. Dama's _Spider_ linked to _Central Park_ when its IPDB note plainly says "Conversion kit for Gottlieb's 1966 'Hurdy Gurdy (Italy)'." A sweep framed only as _empty → filled_ sails right past every one of those. So the target isn't just the empty cells; it's every cell where the corpus disagrees with the catalog.

The best source of this data is IPDB’s free text notes about each model. We have all of IPDB in a raw JSON dump in pinexplore‘s DuckDB db (the `ipdb_machines` table: `IpdbId, Title, Manufacturer, Type, Players, Theme, NotableFeatures, Notes`). It is not the _only_ source — for foreign conversion/bootleg makers the pinexplore web scrape cache (tilt.it, flippers.be) is often better — see [multi-source evidence](#evidence-is-not-ipdb-only) below.

What we've been doing, and continue to think is the right approach, is to work on one field at a time across all models -- like tagging all the widebody models with the `widebody` tag. It's simple enough to find candidates in DuckDB via a SQL/FTS prefilter over that free text, that looks for words related to the field.

The issue is how to further refine and filter those results. We've only tried one approach so far: ask an interactive AI session with a high-powered AI model to ideate on the keywords, run the queries and then do the triage -- all inside of one interactive session. We've been frustrated with this approach: it's not a repeatable process, it's tedious for the developer to babysit and verify, the session runs out of context pretty quickly, it's pretty slow and pretty expensive. And after it's done I still wonder whether it omitted any positives or include false positives. Later on I wonder how well the session did its work, or maybe pass on unfinished work to a new session, but there's nothing to go back to and inspect.

## What's NOT the solution

You might think that we could use cheaper models to decide on most of the obvious ones. Spawn a session for each candidate and use a cheaper model to answer. If the answer is a confident yes or no, accept it and don't bring in the more expensive model.

I'm not willing to try that for two reasons:

1. I don't trust the judgement of the cheaper models to know what's obvious. A real world example from IDPB is this: _"The other model is a widebody"_, which is saying that the machine in question is **not** a widebody. I'm fairly sure the cheaper models would get that wrong. (A lived example from the relationships campaign: a note reading "a conversion kit for Bally's 1978 'Mata Hari'" — the catalog holds _two_ Mata Haris, the 1977 EM and the 1978 solid-state; only the trusted tier reliably knows "1978" selects the SS one.)
2. The "other" model the example above does NOT itself mention it's a widebody: a note in another model is the ONLY evidence that it's a widebody. So to resolve a field on a model you sometimes need the IPDB notes from **MULTIPLE** models.

## The solution

The solution has to account for coverage, accuracy, reviewer throughput, and auditability. The core insight is a reframing of the _unit of work_, and then a layered pipeline built on it.

### Judge the delta, not the corpus

The naive framing makes the candidate the unit of work: classify each hit, populate empty fields. The better framing makes **the delta between what the notes say and what the catalog already holds** the unit of work. That one change reorganizes everything:

- It catches **wrong existing values**, not just missing ones — the six mis-seeded conversion links above are invisible to an empty-cells sweep but fall straight out of a corpus-vs-DB diff.
- It makes a **deterministic reconciler the spine of the tool**, not a prefilter. The reconciler joins the candidate set to the live catalog on the stable `ipdb_id` and buckets every row: **agrees** (catalog already holds the value the note supports — silent green), **empty** (fill it), **conflict** (catalog holds a value the note contradicts — the high-value bucket). This is deterministic and free; you never pay a model to re-derive what the catalog already knows.
- It produces the **audit artifact** the interactive approach never had. The reconciler's output is a durable, regenerable status file — coverage at a glance, resumable across sessions, inspectable after the fact. (The relationships campaign's `check_status.py` → `STATUS.md`, keyed on `ipdb_id` — since retired in favour of that campaign's `relationships.sql`, which derives status as a query; in git history — was the worked precedent: one read-only script that says what's done, what remains, and where the catalog and the notes disagree.)
- It **collapses reviewer load**. A human — or the coordinating session — should only ever see rows where the model and the catalog _disagree_, or where the model is _unsure_. Every row where the model confirms the catalog's existing value is auto-audited green and never surfaces. That directly answers the babysitting/throughput/"dying transcript" complaints: the coordinating session inherits a short, well-scoped queue, not a 300-row triage.

### Why the fan-out is stateless (the cost/context sub-point)

The context ceiling and cost of the old approach are artifacts of the **session shape**. Judging the 300th candidate inside one accumulating conversation carries candidates #1–299 and all prior reasoning in the window — roughly O(N²) tokens against a hard context ceiling. The fix is to turn judging into N independent, stateless calls: one note per call, fresh context each time.

- Each call sees only `[field definition + hand-crafted guidance + the full note(s)]`. The full note is the original context a judgment needs — nothing is judged from a bare snippet — and it always fits, because an IPDB note is a paragraph or two.
- Context never fills: N independent O(1) calls replace one O(N²) session.
- It is cheap **even at the trusted model's rates, because each call is tiny** — a few hundred hits × a few hundred tokens is well under a dollar per field. Cost is real but it is _not_ the main driver, and it should not drive the design (see [Batch is not the first task](#batch-is-not-the-first-task)).

## Architecture — three layers

For one field:

### Layer 1 — deterministic reconciler (the spine)

SQL/FTS prefilter over the DuckDB notes → the candidate set. Join it to the live catalog on `ipdb_id`. This layer is pure code: it defines the work-list, diffs against current state, and emits the status artifact. It does **not** decide membership — that is the model's job in Layer 2 — it decides only what is _already settled_ and what needs judging, and it is where the audit trail lives.

Build the term list iteratively — seed obvious terms, sample hits, expand to the phrasings that actually appear. Paraphrases carrying no listed term are a known recall gap, closed only by widening the term list as misses surface.

### Layer 2 — stateless fan-out judging

One independent request per candidate through `common.ai.client` on the trusted tier (`TRUSTED_MODEL`), forced-schema output `{verdict: yes/no/uncertain, target_title (relational fields only), quote}`. Run it over **every** candidate the net catches, regardless of the catalog's current value — that is what lets Layer 3 catch conflicts. The trusted tier is mandatory (AiCommon §5, and [What's NOT the solution](#whats-not-the-solution)); the full note is the context, because membership isn't decided by the keyword — the model reads every hit in full. Where the note implies the field belongs on a _different_ model, the call surfaces that for the coordinating session.

For relational fields, hand the model what it needs to disambiguate the target — see [target disambiguation](#target-disambiguation-needs-the-candidate-facts).

### Layer 3 — deterministic gates, diff, and disposition

The model returns a verdict; **the script decides trust**, not the model's self-report. Compose a deterministic "confident" gate:

- `check_quote(quote, note)` — the quote is verbatim in the source (drop/flag otherwise).
- `target_title → catalog ref` via `common.catalog.entity_index.EntityIndex.resolve(name)` (built with `types=("model", "title")`) — resolves to **exactly one** ref.
- no conflict — the resolved value equals, or fills, the catalog's current value.

A row that clears all three is **auto-eligible** (still lands in the review table, but pre-greened). Anything else routes to the coordinating session: `verdict: uncertain`, an ambiguous or empty resolution, or a resolved value that **conflicts** with what the catalog holds. "100% sure" is not a number the model reports — it is a unique resolution plus a verbatim quote plus catalog agreement. The interactive session investigates the escalations (cross-model notes, the web cache) and makes the call.

### Human review of a compact results table

`{ipdb_id, title, verdict, quote, note, resolution, catalog_now}`, quote-anchored, sortable by verdict/confidence, **filtered to disagreements + uncertain by default**. You skim a short table, not a dying chat transcript. Confirmed rows become a `patchkit` patch (authored, `make validate`, then the usual hand-off — commit and push are the user's call). For a field with existing bad values, the fix supersedes the seed in a rewritable post-0038 patch where one already touches the model, exactly as the relationships campaign corrected the six conversion links in `0109`/`0142`.

## Refinements the relationships campaign surfaced

### Target disambiguation needs the candidate facts

AiCorpusSweep's rule "keep the structured columns away from the model" is right **for the field being judged** — Manufacturer/Type/Players/year are deterministic and filtered in SQL, not read by the model. But for a **relational** field the verdict is usually trivial (the note says "conversion kit for X" outright); the hard part is picking the right X. Resolution against the catalog frequently returns _more than one_ candidate — "Mata Hari" → EM vs SS, "Big Ben" → three of them — and the model can only choose correctly if the call includes those candidate refs **with their structured facts** (year, technology, manufacturer). So the relational path is: resolve the note's named title → N candidate refs → if N > 1, give the model those N and let it select. That is a narrower, more reliable task than open classification, and it is where seed errors actually hide.

### Evidence is not IPDB-only

`_Sources.free_text_for` already abstracts the source, but the sweep should treat that as first-class, not IPDB-with-a-footnote. Every one of the six conversion fixes was corroborated by tilt.it in the web scrape cache, whose parentheticals name the donor directly (`Sisters (Royal Pair)`); the Petaco licensed-vs-bootleg question the IPDB notes _couldn't_ settle was resolved on flippers.be. For foreign conversion/bootleg makers specifically, the web cache is frequently the better source. Let a field's sweep draw the per-record free text from IPDB notes, the web cache, or both.

### Batch is not the first task

The Batch API is the right eventual transport — N independent, non-latency-sensitive classification requests, 50% off, results keyed by `custom_id` (the `ipdb_id`), forced-schema output supported. But at a few hundred hits per field the whole run is sub-dollar un-batched, and building Batch submission on `common.ai.client` (AiCommon build-order **step 4**) should **not** gate the first slice. Start with a plain parallel fan-out over the residual; add Batch when a field's candidate set runs to the thousands. Do not gold-plate the transport before the pipeline exists.

## Relationship to the extraction tool

This is the **transpose** of [the page data extractor](AiPageDataExtractor.md), and the two share machinery:

|                    | Extraction tool                        | Corpus sweep                                      |
| ------------------ | -------------------------------------- | ------------------------------------------------- |
| Fans out over      | many **questions**, one record         | many **records**, one question (field)            |
| Shared context     | the page — so **cache** it             | none — each record differs, so **batch** instead  |
| Cheap vs expensive | cheap model fans out, master validates | **trusted** model judges every record             |
| Verifier           | `check_quote`                          | `check_quote` (same)                              |
| Source adapter     | `_Sources.free_text_for` (web cache)   | `_Sources.free_text_for` (IPDB notes + web cache) |

It uses the same primitives — `check_quote`, forced-schema output (via `common.ai.client`), candidate-not-fact framing (`common.ai.candidates`), deterministic target-resolution (`common.catalog.entity_index.EntityIndex.resolve`) — pointed at the other axis. Those primitives are now built once, under `scripts/common/`; this tool adds the reconciler/diff spine and (later) the Batch submission mode.

## What already exists (reuse it)

- **The shared foundation** — `flippatch/scripts/common/` (see [AiCommon.md](AiCommon.md)). This tool is a _consumer_ of it: `common.ai.client` provides the forced-schema structured call with the per-run request-count cap, token accounting, local `jsonschema` validation, and the offline mock seam already built in; `common.catalog.entity_index.EntityIndex.resolve(name)` is the deterministic name→catalog cross-check both the resolution step _and_ the relational [candidate disambiguation](#target-disambiguation-needs-the-candidate-facts) need; `Usage` lives in `common.ai.client`; `Candidate` / `EvidenceQuote` live in `common.ai.candidates`. The one piece it does _not_ yet provide is **Batch submission** — AiCommon step 4, and explicitly _not_ the first task here (see above).
- **IPDB note text** — `flippatch/scripts/quote_verify/verify_quotes.py`, `ipdb_notes_text(...)` (via `_Sources.free_text_for`) assembles the free-text Notable Features + Notes prose for one IPDB id from the `ipdb_machines` DuckDB table. That prose is the per-record payload the model judges; the structured columns (Manufacturer, Type, Players, Theme, year) are deterministic data, joined or filtered directly in SQL rather than read by the model — _except_ the candidate targets' columns fed in for relational disambiguation.
- **Deterministic quote verification** — `verify_quotes.check_quote(quote, source)` confirms the model's returned quote is verbatim in the note, with the sanctioned normalizations. Same definition of "verbatim" as the shipped-patch gate.
- **The reconciler pattern** — `campaigns/0128-relationships/check_status.py` (candidate/worklist vs live DB, keyed on `ipdb_id`, emits a status artifact) and `reconcile_worklist.py` were a hand-built, field-specific instance of Layer 1 (both since retired, in git history; that campaign now derives status from `relationships.sql`). Generalizing that pattern — arbitrary field, arbitrary candidate set — is this tool's spine.
- **Claim emission** — `flippatch/campaigns/patchkit.py`, once a sweep's confirmed results become a patch.

## Prompt layering

Prompt layering follows `common.ai`'s prompt-assembly discipline (AiCommon §4) — the same three roles the [page extractor](AiPageDataExtractor.md#per-slice-prompt-three-layers) uses: the field definition as the grounding layer (derived from the DB / DomainModel.md), hand-crafted recognition guidance (synonyms, and explicit warnings about the polarity/direction traps — companion-model references, negations, converted-to vs. -from), and any per-sweep caller context. For relational fields the guidance layer also frames the candidate-target choice. There is no shared page to cache; the small shared instruction prefix could be cached across a batch but it's a rounding error next to the batch discount.

## Build order — thinnest slice

1. **Generalize the reconciler (Layer 1).** Lift `check_status.py`'s pattern (since retired; in git history) into `scripts/common/`-adjacent code that takes a field + a candidate set (SQL/FTS result) and diffs it against the live catalog on `ipdb_id`, emitting the done/empty/conflict buckets and a status artifact. This is the spine and it's pure code — build and trust it first.
2. Pick **one boolean field** (widebody) and **one relational field** (converted-from) — they exercise the two output shapes and the target-resolution + candidate-disambiguation steps.
3. **Fan out (Layer 2), plain parallel — not Batch.** Feed each hit's `ipdb_notes_text` (free-text Notes / Notable-Features only, via `_Sources.free_text_for`; for the relational field also the resolved candidate targets' structured facts) through a stateless trusted-tier call with a forced schema.
4. **Gate and diff (Layer 3).** `check_quote` every result; resolve `target_title` with `EntityIndex.resolve`; diff verdict-vs-catalog; route conflicts + uncertain + ambiguous-resolution to the review table, auto-green the rest.
5. Compare the results table against a hand-labeled sample of the same hits — measure the trusted model's precision and recall on the tricky cases (negations, companion-model references, wrong-direction conversions), and via a random sample of _non_-matched records, the SQL net's recall.
6. If the model handles the polarity/direction traps and the relational targets resolve cleanly, generalize to the rest of the sparse fields, and add Batch submission only when a field's candidate set warrants it.

## Output

A per-field results artifact (JSON or a table), each row `{ipdb_id, title, verdict, target_ref (relational), quote, quote_verified, note, resolution, catalog_now}` — its `quote` + `quote_verified` pair is `common.ai.candidates.EvidenceQuote`, and `catalog_now` is what makes the diff (and the conflict bucket) visible. Framed as **candidates with verbatim-checked evidence**, exactly as the extraction tool: `check_quote` proves the quote exists, not that it supports the verdict — the human (or a trusted-model pass) makes the final call. Carry the full note in the row so review needs no re-fetch.

## Decisions still open

- **SQL net recall:** the term list bounds it. Decide per field how far to widen it (measured by a random-sample audit of non-matched records) versus accepting a known recall floor.
- **Where the field definitions live:** structured `help_text` vs. `DomainModel.md` prose — the same open question as the extraction tool; the hand-crafted guidance layer is the home for it either way.
- **How aggressively to re-judge already-set values:** judging every candidate regardless of catalog state is what catches wrong seed values, but for a field with many correct existing values it re-pays (cheaply) to confirm them. Decide whether to always re-judge, or only re-judge existing values whose provenance is a weak import.
