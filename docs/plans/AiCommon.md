# Common AI Layer

This doc is the plan for the shared foundation that AI-driven tools sit on. The code now lives under `scripts/common/`: `scripts/common/ai/` (`common.ai`) for model-call and candidate primitives, `scripts/common/catalog/` (`common.catalog`) for deterministic catalog lookup, and `scripts/common/related_projects.py` for sibling checkout paths.

## The problem

We are planning to build multiple tools that use AI models to do their work:

- [AiLint.md](AiLint.md)
- [AiPageDataExtractor.md](AiPageDataExtractor.md)
- [AiCorpusSweep.md](AiCorpusSweep.md)

Three tools were planned independently by sessions unaware of each other. All three quietly describe the **same substrate**: a forced-schema Anthropic call, deterministic verbatim quote verification, name→live-catalog resolution, and a "candidates, not facts" output discipline. The current branch has now lifted that substrate into `scripts/common/` and pointed AiLint and the page extractor at it; the sweep still only has the plan.

Left unreconciled, that would have yielded two Anthropic wrappers, two catalog indexes, three re-arguments of which model tier to trust, and three copies of the "how do we introduce an API key + spend + network without breaking the offline test gate" question. This branch introduces the repo's first LLM dependency and policy once, in `common.ai.client`, with one cost/mock/key policy — and every tool imports it rather than reinventing it.

## What it is

`common` is a **library, not a tool** — nothing here is run directly by a developer or the Makefile. It holds the primitives the AI tools build on, so `ai_lint`, `ai_page_extract`, and the future sweep are each thin: their own domain logic (rules / slices / field pipelines) plus imports from `common.ai`, `common.catalog`, and the existing `quote_verify`.

It lives under `scripts/` like every other Python group in the repo (`quote_verify`, `patch_validation`, `cloud_store`, …), made importable by the existing `pythonpath = ["scripts", ...]` in `pyproject.toml`. There is no `lib/` or `src/` convention to slot into, and introducing one would fork the layout for no benefit.

## What's in it

### 1. Anthropic client — the one model-call primitive

A structured-output call: the model is forced to call a `report` tool whose `input_schema` is the caller's JSON schema. Forcing the tool guides the model, but the returned `tool_use.input` is still **validated locally** against that schema — via the repo's existing `jsonschema` `Draft7Validator` (already used by the patch gate) — before it's handed back, so a drifted or malformed result fails cleanly and testably instead of surfacing as a downstream `KeyError`; call sites keep their defensive readers (`parsing.as_bool` / `as_str`) on top. This now lives in `scripts/common/ai/client/`, imported as `common.ai.client`.

- **Sync single call** — AiLint's per-sentence/per-pair rules.
- **Prompt-caching over a fan-out** — the extraction tool caches a per-record prefix (page + record context) and reuses it across many slices; the client exposes the `cache_control` breakpoint placement and reports per-call `usage`. It does **not** own the sequencing: which slice primes the cache and when the rest fan out concurrently is orchestration that stays in the extraction tool, which the client serves with cached structured calls and (optionally) a concurrency helper. The load-bearing constraint — a cache entry is only readable once the priming request has responded, so prime one call and await it before fanning out, or every slice pays full price. With the non-streaming client that means awaiting the priming call's **full response** (simplest, fine for v1); a streaming cached call would let the fan-out start at first token, but that's a later optimization, not a v1 need. Either way it's caller orchestration, not client-enforced logic.
- **Batch submission** — the corpus sweep wants the Batch API (N independent classification requests, results keyed by `custom_id`, 50% off).

Cross-cutting, and **absent from AiLint's current version** — these are shared policy, not per-tool:

- **A per-run request-count cap.** The only thing worth guarding against is a bug firing unbounded calls before you notice — a fan-out loop with a bad exit, a retry storm. A hard cap on requests per run (a counter, a max, abort when exceeded) covers that and doubles as a sanity assertion, since every run's call count is knowable up front (roughly slices × ensemble for extraction; the prefilter's row count for the sweep). No dollar cap, no price table, no pre-dispatch estimation — this is a manually-run localhost tool with tiny per-call payloads, not a service. The client also sums each response's `usage` and **prints the token total at the end of a run** — visibility, not enforcement. (A hard dollar budget would need a model-price table; add it only if that need ever appears.)
- **Retry / timeout** on transient API failures.
- **An offline, sibling-free test seam.** Unit tests, pre-commit, and `make test` must **never** hit the network, spend money, or depend on a sibling checkout. The client sits behind a `Protocol` (AiLint already does this) so tests inject a fake; the entity index is tested against a tiny temporary SQLite fixture (as AiLint's tests already do), and the source/corpus wrappers against fakes. Real `../flipcommons` / `../pinexplore` access is for integration and manual runs only; the real client is constructed only at the CLI entry points.
- **Key handling and explicit model per call.** `ANTHROPIC_API_KEY` is the master switch — a missing key is a fatal startup error, not a degrade-to-static path (AiLint's `require_ai_client` is the pattern). The client has **no default model**: every call site names one, so the tiering principle (§5) is forced into the open at each call and nothing can silently inherit the cheap tier. Two module constants — `CHEAP_MODEL` (Haiku 4.5) and `TRUSTED_MODEL` — give the tiers a single home so raw model ids don't scatter across call sites; `quote-supports-claim` passes `TRUSTED_MODEL`, AiLint's other rules pass `CHEAP_MODEL`.

### 2. Catalog entity index — name→live-catalog resolution

Read directly from flipcommons' dev SQLite (`backend/db.sqlite3`): the resolved slug/name per catalog row plus the per-type alias tables, folded to a dash/space/punctuation/case-insensitive key. This is AiLint's old `entity_index.py`, **lifted and generalized** into `scripts/common/catalog/entity_index.py`, imported as `common.catalog.entity_index`. It exposes two entry points and lets each caller pick its own type profile, because the three tools enter it from opposite ends:

- **`find_mentions(text)`** — n-gram scan of prose for unlinked catalog surface forms. AiLint's `missing-wikilink` / `unknown-model` rules. This exists today.
- **`resolve(name)`** — single-name lookup. The extraction tool's entity-discovery cross-check (`existing:<ref>` vs. `possible-gap`) and the sweep's `target_title → catalog ref` step both use this same `by_norm` index. Each supplies its own type profile — the sweep resolves model↔model relations (`model` + `title` + aliases), extraction resolves models/manufacturers/people — because the wikilink-tuned `DEFAULT_TYPES` is wrong for target resolution.

The entity-type→table map is a generated mirror of flipcommons' registry (regenerated when flipcommons adds an entity type — see the module docstring). Note this primitive is **not itself "AI"** — it's pure SQLite + string matching — so it lives in `common.catalog`, not `common.ai`.

### 3. Candidate shape + the "candidates, not facts" discipline

Two things are shared; a third is deliberately not. **Shared as a discipline:** everything a cheap call emits is a **candidate with checked evidence, never a verified fact**. `check_quote` proves a quote _exists verbatim_; it never proves the quote _supports_ the claim, and that gap is closed downstream (the master session's full-page vet in extraction; the human table skim in the sweep; the developer reacting to a warning in the lint) — never inside a cheap call.

**Shared as data — kept narrow:** `EvidenceQuote` and `Candidate` live in `common.ai.candidates`; `Usage` lives in `common.ai.client`; `EntityRef` lives in `common.catalog.entity_index`. These are what extraction and the sweep both emit or consume.

**Not shared:** AiLint's `Finding` is a _diagnostic_ (rule, severity, message, reason) and often carries no value, quote, or `quote_verified` at all — a `missing-wikilink` finding has no quote. It stays lint-specific in `ai_lint.report`. Don't fold candidates and findings into one shape; unify only if real duplication actually appears.

### 4. Prompt-assembly discipline

A shared discipline for building a prompt from distinct, separately-sourced layers — **not** a fixed schema every prompt must fit. Three roles recur: **grounding context** (the authoritative data the call reasons over), **hand-crafted recognition guidance** (synonyms, disambiguation cues, tricky phrasings, false positives the data doesn't hold), and **caller-supplied situational context** (per-run notes). What fills the grounding role is tool-specific: for extraction and the sweep it's the DB-introspected field, its legal enum, and canonical vocab descriptions (never hardcoded); for lint it's whatever the rule reasons over — cited source text, overlap-prefilter output, entity-index candidates, a segmented sentence. So the _discipline_ (keep the layers distinct; source the grounding layer authoritatively rather than hardcoding it) is shared; the extraction-style "DB field + enum" is one instance of the grounding role, not a universal, mandatory layer 1. Where caching applies, the convention also fixes cache-breakpoint placement: stable grounding + global-caller context before the breakpoint, slice-specific layers after.

### 5. The model-tiering principle

Written down once, so every future slice and rule inherits it instead of re-arguing it: **use the cheap tier only where something trusted disposes downstream.**

- The extraction tool's cheap fan-out is licensed because the master (expensive) session re-reads the whole page and vets every candidate — precision is deferred, so the cheap model only needs recall.
- The corpus sweep has no downstream trusted disposer (just a human skimming a table), so it must judge with the **trusted** model on every record — this is why it explicitly refuses cheap models on the polarity traps (_"the other model is a widebody"_).
- The lint's semantic-entailment judgment (`quote-supports-claim`) is the same polarity-sensitive call the sweep distrusts cheap models for; its "disposer" is only a developer reacting to a warning, so it should run on the **trusted** tier, not Haiku. Tier is therefore configurable per rule/slice, defaulting by this principle rather than by cost alone.

## What stays out

- **`check_quote` / `_Sources` / `ipdb_row_text`** stay in `scripts/quote_verify/verify_quotes.py` — already correctly placed and reused by `make verify-quotes`. The tools import them directly; they do not move. This keeps one definition of "verbatim" across extraction, sweep, lint, and the shipped-patch gate.
- **`patchkit`** stays at `patches/authoring/patchkit.py` — claim emission, imported when a tool's confirmed results become a patch.
- **Tool-specific logic** stays in each tool's own package: AiLint's rules (`overlap.py`, `description_check/`, `citation_verify/`), the extraction tool's slice definitions and per-record cache assembly, the sweep's SQL prefilter and field pipeline.

## What each tool imports

|                    | Anthropic client       | entity index    | shared data shapes                    | prompt discipline | `check_quote`/`_Sources` |
| ------------------ | ---------------------- | --------------- | ------------------------------------- | ----------------- | ------------------------ |
| AiLint             | sync                   | `find_mentions` | `Usage`, `EntityRef` (own `Finding`)  | rules-as-prompts  | yes                      |
| PageExtractionTool | caching (owns fan-out) | `resolve`       | `Candidate`, `EvidenceQuote`, `Usage` | slices            | yes                      |
| CorpusSweep        | Batch                  | `resolve`       | `Candidate`, `EvidenceQuote`, `Usage` | field guidance    | yes                      |

## Provenance — this is extracted, not greenfield

AiLint's session got ahead of the review and wrote a working first draft (`scripts/ai_lint/`, uncommitted). That code is the **quarry**, not a deliverable to finish in place:

- `ai_client.py`, `config.py` (key/model/sibling-path handling), and `entity_index.py` were the seeds of primitives 1–2 and have been split into `common.ai.client`, `common.related_projects`, and `common.catalog.entity_index`.
- The lint rules, CLIs, and report shapes stay in `ai_lint` and import from those shared packages.
- The client grows the caching, batch, request-cap, and retry/timeout surface the lint didn't need but the other two tools do.

`ai_lint` being written first is an accident of sequencing; it must not dictate the package boundary. The extraction tool is the stated priority, so `common.ai` is built as its foundation, and `ai_lint` is retrofitted onto the shared package afterward.

## Dependency footprint — a deliberate, one-time expansion

This adds the repo's first `anthropic` SDK dependency, an `ANTHROPIC_API_KEY` in `.env`, and per-run network + cost. The consequences, honored once here rather than three times:

- Self-contained under `scripts/common/`.
- Unit tests **mock the client** — the `Protocol` seam guarantees pre-commit and `make test` never touch the network or spend.
- A hard per-run request-count cap, enforced by the client, and an end-of-run token total printed for visibility.
- Localhost-only reach **at runtime**: the flipcommons dev DB and pinexplore web cache are gitignored / R2-backed, so the tools themselves run only where the sibling checkouts exist. The unit tests do not — they use fixtures and fakes (above), so `make test` and pre-commit pass in any checkout.

## Decisions still open

- **Field-level semantics: DB `help_text` or `DomainModel.md` prose?** Both the extraction tool and the sweep need the meaning of a field (what distinguishes tech generation from subgeneration, what a reward type means). If it lives only as doc prose, the grounding role for those tools should point at a doc-reading step rather than paraphrasing the doc into code. Audit on localhost. (Shared open question, so it lands here.)
- **How much of the client's transport surface to build up front.** The sync path is needed for AiLint and the extraction prototype; caching is needed for the real extraction tool; batch only for the sweep. Build sync + caching first (what the priority tool needs), add batch when the sweep is built — but design the client interface so batch is an added submission mode, not a fork.

## Build order

1. **Done.** Lift `ai_client.py` + `config.py` + `entity_index.py` out of `ai_lint` into `common.ai.client`, `common.related_projects`, and `common.catalog.entity_index`, behind the existing `Protocol`; add `resolve(name)` and caller-supplied type profiles to the index; keep AiLint green by importing from the new home. Client refactored to explicit-model-per-call (no default; `CHEAP_MODEL` / `TRUSTED_MODEL` constants), per-run request-count cap, end-of-run token total, and local `jsonschema` validation of the tool output. `quote-supports-claim` now binds `TRUSTED_MODEL`.
2. **Partly done.** Shipped: the request-count cap, token total, `Usage`, `EvidenceQuote`, and `Candidate`. **Deferred to their first consumer** (build-ahead-of-need discipline): retry/timeout and any shared prompt-assembly helper beyond the discipline already embodied in `ai_page_extract.framework` / `ai_page_extract.fields`.
3. Add the prompt-caching surface to the client — `cache_control` placement + `usage` reporting — for the page extractor's cost-effective fan-out. The extraction tool owns the prime-then-fan-out orchestration on top.
4. Add Batch submission when [AiCorpusSweep.md](AiCorpusSweep.md) is built.
