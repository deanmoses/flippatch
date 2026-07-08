# Design: the page-extraction tool

**Status:** proposal / design. No code yet. This captures the design so a localhost session (where flipcommons, flippatch and pinexplore are all checked out with their live DBs) can build it. Companion: [CorpusSweep.md](CorpusSweep.md) — the transpose of this tool (many records, one field), for sparse-field backfill.

## The problem

Across many patch-authoring sessions, the catalog claims we extract from a source page are **incomplete**. The page routinely contains a year, themes, a display type, a conversion-kit tag, a credited person — and the session sets three of them and moves on. The source has more than we harvest.

This is a **recall** problem, not a precision problem. Sessions don't assert wrong years; they *forget* years. Every design decision below follows from that one fact: bias the machinery toward surfacing everything plausibly present, then let cheap deterministic checks and the expensive master session prune. A false positive is cheap to kill; a forgotten theme is the failure we are trying to end.

## What the tool is

A **developer inner-loop tool**, run in a localhost AI session that is authoring data patches. It reads a cached source page (or PDF text, or video transcript) plus the live catalog vocabulary, fans the page out across many cheap-model requests — each asked about one narrow slice of the possible facts — collates the answers, deterministically verifies every supporting quote is verbatim in the source, and hands back a JSON **packet of candidate claims with checked evidence**. The master (expensive) session that called it is the **arbiter**: it vets every collated assertion against the *entire* page before authoring anything — full context, never the quote alone.

It is emphatically **not** a patch generator and **not** an authority. It raises recall for the master session; it does not decide what is true. The packet is *candidates*, never *facts*.

### Why the master-session-in-the-loop split is the whole point

A cheap model run over a narrow slice has good recall and mediocre judgment. The master session has excellent judgment and (as observed) poor recall when facing the whole checklist at once. The tool converts the cheap models' recall into a checklist the master session can *validate* rather than *originate* — which is exactly the direction each model is good at.

This is the **propose/dispose split**: the cheap model may *propose* candidates but never *dispose* of them. The expensive arbiter disposes — by re-reading the **whole page** and vetting every collated assertion against it (mandatory, non-negotiable; no digest, no quote-only shortcut). That full-page vet is precisely what **licenses** an untrusted cheap model at the fan-out: every precision or judgment error it can make — a mistagged widebody, a wrong inference off a real quote — is caught downstream against full context, so the fan-out only has to be good at *recall*, which is the cheap thing to be good at. The tool removes the master's obligation to *remember to look* for each field; it never removes its obligation to confirm each claim against the source.

## What already exists (build on it, don't rebuild)

Almost all the plumbing is already written and read for this design:

- **Input / source text** — `pinexplore/scripts/web_scrape/web_cache.py`: `get(url)["text"]` returns the extracted readable text of a page. HTML, PDF and YouTube transcripts are all normalized to that one `text` field upstream, so the tool is content-type-agnostic. The row also carries `title`, `last_updated` (a real date the page states, or null), `content_type`, and a `rendered` flag.
- **Ref → source resolution** — `flippatch/scripts/quote_verify/verify_quotes.py`, class `_Sources`: already resolves an `http(s)` URL, `opdb:<id>`, `youtube:<id>` or `ipdb:<id>` ref to its source text, out of pinexplore's `cache.sqlite` and `explore.duckdb`. This is the tool's input adapter — reuse it verbatim.
- **Deterministic quote verification** — `verify_quotes.check_quote(quote, source)`: the exact verbatim-substring-in-source-order check, with the sanctioned normalizations (smart quotes straightened, whitespace collapsed, `[...]` omission spans). Every quote the cheap models return runs through this. Reusing it guarantees one definition of "verbatim" across extraction and the shipped-patch gate.
- **Claim emission (later, if the packet ever drafts YAML)** — `flippatch/patches/authoring/patchkit.py`.
- **DB access pattern** — `flippatch/patches/authoring/0010-game-formats/gen.py`: run from `flipcommons/backend` with `django.setup()`, then read live vocab/refs via the Django ORM. This is the template for the introspection layer below.

The tool's core is therefore small: `text → fan-out to a cheap model → collate → check_quote → packet`.

## Grounding: where the checklist and legal values come from

The single most important anti-duplication rule: **the tool must not hardcode the field list or the vocabularies.** It introspects them from the live flipcommons DB, so when the domain model grows a `display_subtype` term or a new field, the tool covers it for free.

- The **field list** (game format, production status, year, reward types, tech generation/subgeneration, themes, display type/subtype, cabinet style, description, credits/roles, relationships, gameplay features, system, franchise, tags) maps to Django model fields plus FK/M2M vocab tables. Introspect the model; don't type the list.
- The **legal values and their descriptions** for each controlled vocab are vocab entities in the DB, and they almost certainly carry descriptions — patches *create* vocab with `description:` folded blocks (that is what `patchkit.entry(description=...)` exists for). So a themes slice can be handed the real theme terms and their real descriptions.
- The **current value on the target model** should be fetched too, so each slice asks "is there evidence to add/change this?" rather than "what does the page say?" — and so the packet can flag *disagreements* with what the catalog already holds, which is high-signal.

**What the anti-duplication rule does and doesn't govern.** It governs the *data* — fields, legal values, their canonical descriptions — which stays DB-derived. It does **not** forbid hand-crafting the *recognition guidance* for each topic (synonyms, disambiguation cues, tricky phrasings), because that guidance isn't in the DB and never was: the term's definition is data, "here's how it shows up in prose" is craft. Nor does it forbid the caller injecting per-run context. Each slice's prompt is built from three layers — derived, hand-crafted, caller-supplied — detailed in [Per-slice prompt: three layers](#per-slice-prompt-three-layers).

### Open question to settle on localhost (day one)

Vocab-term descriptions almost certainly exist. **Field-level semantics** — what distinguishes tech generation from subgeneration, what the reward types mean — may live only as prose in `flipcommons/docs/DomainModel.md`, not as structured `help_text`. Audit this first. If it is doc-only, the anti-duplication answer is to have the tool *read DomainModel.md* as the single source, not paraphrase it into the tool.

(Note: flipcommons is under the `The-Flip` org; a `deanmoses`-scoped web session cannot add it. This audit and everything DB-touching happen on localhost, where all three repos and the dev DB are present.)

## Chunking

Slices come in **four axes**, distinguished by *what part of the system each feeds*:

- **Field-extraction slices** → structured fields, of the current record *or of a directly-related entity* (e.g. the corporate entity's location). "What does the page say about attribute X of the model, or of its maker?" (year, themes, display type, maker location, …)
- **Entity-discovery slices** → the catalog's completeness. "What models / manufacturers / people does this page mention at all?" A page about one game routinely names its conversion kits, its manufacturer's other titles, and a cast of designers/artists — each a candidate record or credit the catalog may not yet hold.
- **Description-enrichment slices** → the free-text `description` of a model or manufacturer. "What on this page would make a richer description of the model or its maker?" This axis exists because descriptions are the field most often left thin, and the material for them (an anecdote, a bit of era context) is exactly what a field-oriented pass skips.
- **Source-discovery slices** → the evidence corpus. "What other sources of information does this page point to?" Outbound links, cited articles, "see also" / bibliography entries, "as first reported by…". These feed the *research* loop rather than the catalog: a surfaced URL can be fetched into pinexplore's web cache with `web_fetch.py` and later become a `cite:` (once its website root is seeded). This is how the tool answers a standing question of the overall session — *where do we look next?*

**Principle (field-extraction slices): one question per call by default.** Satisficing is per-call: a call carrying two *independent* jobs can satisfy one and under-serve the other, so each independent field gets its own slice. Cheap cache reads make the extra calls affordable (~0.1× the prefix each), so cost is not the binding constraint — *coherence* is. **Combine two fields into one slice only when they are a dependent parent/child pair** — the child is a *refinement* the model must resolve the parent to answer at all (tech generation → subgeneration; display type → subtype). That isn't two jobs, it's one reasoning act; splitting it yields an *under-specified* question ("what's the subgeneration?" with no generation established), which lowers recall rather than raising it. **Combine for dependency, never for topical adjacency** — the latter is the trap that lumps themes with franchise (two independent fields that merely share a subject). A corrected partition — one slice each, except the two dependency pairs:

- production status
- year
- reward type(s)
- tech generation + subgeneration — dependency pair
- display type + subtype — dependency pair
- themes
- franchise
- cabinet style
- game format
- gameplay features
- tags
- system
- **credits / roles** — its own slice; a different *task* (person recognition + role mapping), not a field lookup
- **relationships** — bootleg_of / variant_of / remake_of / converted_from…
- **corporate-entity location** — a field slice that targets a *related* entity rather than the model: the structured `location` field on the model's corporate entity (its maker / parent company). It surfaces geographic places (city, region, country) plausibly tied to the corporate entity as a **candidate value for that structured field** — not description prose. Told to over-include: "plausibly" is a recall setting, so any place that *might* be the maker's location is surfaced, and the deterministic step + master session prune (a place with no real tie is cheap to drop; a missed headquarters city is the gap). Its output is tagged with the corporate-entity ref, since the candidate belongs to that entity, not the model.
- one **open-ended catch-all slice**: "anything catalog-relevant on this page that none of the other slices asked about" — the safety net for facts that fall between the named axes

**Entity-discovery slices** (each returns a list of mentions, each with a verbatim quote and the *reason* it's mentioned):

- **models mentioned** — every pinball machine / game named on the page (conversion kits, the manufacturer's other titles, predecessors, remakes), so the master session can check each against the catalog and spot missing records.
- **manufacturers mentioned** — every maker / operator / distributor named.
- **people mentioned + why** — every person named *and the reason* (designer, artist, programmer, music, mechanics, a quoted collector, the page author). The reason is what lets a credit be mapped to a role; a bare name is nearly useless.

The cheap slice only *lists mentions with quotes* — it does not resolve them against the catalog (it can't reliably). Resolution is a **deterministic post-step**: cross-check each mentioned name against the live catalog (same DB access as the field slices) and label it *resolves to existing X* vs. *not found — possible gap*. That cross-check is as mechanical as `check_quote`, and it turns a raw mention list into a ranked "the catalog may be missing these" list for the master session.

**Description-enrichment slices** (each returns findings tagged with the entity they enrich — this model, its manufacturer, or a related entity — plus a verbatim quote):

- **anecdotes / interesting facts** — amusing or notable material that would give a model's or manufacturer's description color (a naming origin, a production quirk, a record set, a quoted reaction).
- **historical context** — grounding that situates the model or maker in its era, industry, or lineage (what came before, what it competed with, why it mattered).

The discipline specific to this axis: **the slice harvests raw material; it does not write the description.** The catalog's `description` must pass the editorial lint, and composing lint-clean prose is the master session's job — the slice's output is quotable source snippets tagged by target entity, never a finished paragraph. As everywhere, over-include and let the master session prune: enrichment findings are candidates, and the master session decides what actually lands in a description.

**Source-discovery slice** (returns candidate leads, each with what it points to and why it looks useful):

- outbound links, cited/referenced articles, "see also" and bibliography entries, and prose references to other sources ("as first reported in *Pinball News*, 1998", "per the manufacturer's flyer") — tagged with what they inform (this model / the manufacturer / general) and whether they are a live URL or a bare reference to run down.

Two things specific to this axis:

- **A deterministic post-step ranks the leads**, like the entity cross-check: for each URL, is it *already in pinexplore's web cache* (`web_cache.get`), and is its *website root already seeded* as a citation source in flippatch's patches? That splits leads into "already have it," "new — fetch it," and "new domain — needs a source root seeded before it can be cited." The master session (or a follow-up `web_fetch.py` run) acts on the "new" ones.
- **Link targets may not survive text extraction — a real wrinkle for this slice.** The cache's `text` field is trafilatura's *readable-text* extraction; a bare URL written in prose survives, but an `<a href>` whose anchor text differs from its target loses the target. So a slice fed only the extracted `text` will miss navigational links. Two honest options: (a) restrict this slice to references *visible in the extracted text* (fully quote-verifiable via `check_quote`, but misses hidden hrefs), or (b) additionally scan the **raw HTML blob** (`raw/<sha>.html`, on disk, content-addressed) for hrefs — richer, but those hrefs aren't quote-verifiable the same way, so treat them as *leads*, not quoted claims. Recommend starting with (a) and adding (b) only if link recall proves inadequate.

**Why narrow slices at all:** satisficing. Ask one model for all ~15 categories and it returns four and feels finished. A slice that asks *only* about themes cannot feel finished until it has looked for themes. That is the core mechanism.

**Two kinds of satisficing, two levers.** One-question-per-call fixes *cross-field* satisficing (list 4 of 15 categories, stop). It does nothing for *within-field* satisficing — a themes-only call that names 2 of 5 themes and feels done. That second mode is what the ensemble/multi-sample union and an explicit "list every one, don't stop at the obvious" instruction are for, and they apply to every slice no matter how atomic. Atomizing is necessary but not sufficient. Where a pairing is genuinely marginal, don't settle it by theory: the proving slice measures recall, so A/B the lumped vs. split versions on real pages and let the numbers decide.

**Vocab-payload bound:** a slice whose controlled vocab is huge (themes, tags can be hundreds of terms) cannot fit every description in the prompt. Either give that slice its own call with a trimmed/retrieved vocab, or do a two-step (free extraction, then map to legal terms). This is a per-vocab decision, driven by size.

## What goes in the cached prefix

The cached prefix is **per-record**, not global — it's rebuilt once per (page, record) pair and reused across every slice for that pair (see the caching mechanics below). Put in it, in stable order, everything the slices share:

1. **The page text** — the dominant payload, identical across slices.
2. **The catalog's existing record** — what flipcommons already holds for this model (its current field values, existing credits, existing relationships). This lets a field slice frame its question as "is there evidence to *add or change* this?" and flag disagreements with the catalog, and lets the discovery slices avoid re-reporting entities already on the record.
3. **Known related entities** — the manufacturer, the family/franchise, sibling models, already-credited people. Context that helps the model resolve ambiguous mentions ("Steve" → which credited Steve) and recognize when a mentioned entity is already known vs. genuinely new.
4. **Global caller context** — any per-run situational notes the master session supplies that apply to *every* slice ("Manufacturer A was renamed to B — treat mentions of either as the same maker"). Stable across the run's slices, so it caches; see the three-layer section.
5. **Fixed framing/instructions** — the standing "you are extracting candidate claims, quote verbatim, say nothing if absent" preamble.

Everything *slice-specific* varies and goes *after* the cache breakpoint: the question, that field's derived enum/vocab, its hand-crafted recognition guidance, and any caller note *targeted* at that one slice. Because the block above is stable for the whole fan-out over one record, it's cached once and read by every slice — the caching section explains why that ordering is load-bearing.

### Prompt caching: mechanics that bound the design

The page (plus the record context above) dominates token cost, and naively it is re-sent on every slice — N slices ≈ N × the prefix. Prompt caching removes that, but only if used correctly:

- **It's a prefix match.** The API caches the prompt from the start up to a `cache_control` marker; a later call reuses it only if those leading bytes are *byte-for-byte identical*. Render order is tools → system → messages. So: stable content (page + record context + framing) first, with the marker at its end; the volatile per-slice question after it. Assemble the prefix deterministically — a stray timestamp, reordered field, or unsorted JSON silently breaks the match.
- **Economics (Haiku, $1/1M input):** a cache **write** costs ~1.25× normal input (5-min TTL); a cache **read** costs ~0.1×. For a ~4,000-token page across 8 slices: no cache ≈ 32,000 token-equivalents; cached ≈ 5,000 (write) + 7 × 400 (reads) ≈ 7,800 — about 4× cheaper, and ~7× with 3× ensemble sampling. This is what *inverts* the chunking tradeoff: each extra slice or repeat pass costs ~0.1×, so fine slicing and ensembles become affordable rather than prohibitive.
- **Prime, then fan out — do NOT fire all slices at once.** A cache entry is only readable *after the request that wrote it starts responding.* Fire all slices in parallel and none can read a cache the others are still writing — every slice pays full price and caching buys nothing. Correct sequence: send one slice first, await its first token (the prefix is now cached), *then* fan out the rest concurrently.
- **Minimum cacheable prefix on Haiku 4.5 is 4,096 tokens.** A shorter prefix silently doesn't cache (no error — the write count just comes back zero). Most source pages clear it; short pages won't, and they're cheap anyway. If the page is thin, adding the record context to the prefix may itself push it over the floor.
- **Verify it's working:** each response reports `cache_read_input_tokens`. If it's zero across slices, something in the prefix is varying that shouldn't be — diff the assembled prefix bytes between two slices to find it.

### What caching does and doesn't do, and where each model's cost lands

Two clarifications keep expectations honest, then the actual accounting:

- **The master session cannot share the tool's cache.** Caches are keyed by model (within your org) plus exact prefix bytes. The fan-out runs on Haiku; the master runs on Opus — a model change invalidates the whole cache, so a Haiku-written entry is invisible to an Opus request. Even same-model, the master's prefix (its own Claude Code system prompt + tools + conversation) is nothing like the tool's minimal `[page + record context]` prefix, so the bytes never match. The master's mandatory full-page read is its own cost; the tool's cache doesn't defray it.
- **Caching is cost + latency only — it does *not* free context window.** A cached token is billed ~10× cheaper and skips recomputation, but it still occupies the window exactly as if uncached. Caching never shrinks the window.

So where do the costs land? The **cheap fan-out** reads the page N times (once per slice, ensemble-multiplied), and caching is exactly what makes those N reads cheap — each extra one is ~0.1× the prefix. The **expensive arbiter** reads the full page **once**, with the collated checklist in hand, to vet every assertion. That single full-page pass is the price of the mandatory vet, and it's context-safe: it's *one* page, not the many-records accumulation that blows a window in the [corpus sweep](CorpusSweep.md).

The fan-out's payoff is therefore **not** keeping the page out of the master's window — the arbiter reads it in full, by design and by mandate. It's that the arbiter reads the page **once, to vet a ready-made per-field checklist**, instead of reading it many times to extract each field itself (the context blowup) or once while free-forming what to look for (satisficing — the recall failure this whole tool exists to end). The cheap model builds the checklist; the expensive model, reading the whole page, disposes.

## Per-slice prompt: three layers

A slice's prompt is not derived wholesale from the DB. It composes three sources, and keeping them distinct is what lets DB-single-sourcing and hand-crafted extraction expertise coexist:

1. **Derived (from the DB) — the data.** The field, its legal enum values, and their canonical descriptions, introspected live from flipcommons. Stays DB-sourced: authoritative there, and it drifts, so hardcoding it re-introduces the duplication the Grounding section warns against. **Automatic and mandatory for every field** — a field with no other layer still gets this.
2. **Hand-crafted (in the tool) — the recognition guidance.** How to *spot* a value in messy prose: synonyms and alternate spellings ("translite" ≈ "backglass"), disambiguation cues ("mentions of a CPU or circuit chips *suggest* solid-state, not EM"), examples of tricky phrasings, and common false positives to avoid. This is extraction expertise the DB doesn't hold — the term's definition is data; how it surfaces in a forum post is craft. Authored per topic, versioned in the tool, keyed by field. It's also the home for field-level semantics if the day-one audit finds they live only in `DomainModel.md` rather than structured `help_text` — encode them here rather than duplicating the doc.
3. **Caller-supplied (per run) — the situational context.** Ad-hoc facts the master session injects for this page/record: "Manufacturer A was renamed to B in 1998 — treat mentions of either as the same maker," "ignore the sidebar's related-games list," "this page conflates two same-named models." A note can be *global* (every slice) or *targeted* at one slice.

Two disciplines keep this from backsliding into hardcoded data or brittle rules:

- **Layers are additive and degrade gracefully.** The derived layer covers every field automatically; the hand-crafted layer is optional *lift*. Add a new display subtype to the DB and the derived layer picks it up immediately, while the hand-crafted synonyms won't mention it until someone updates them — recall on the new term just falls back to what the model already knows, rather than the field going uncovered. Every field has layer 1; layers 2 and 3 are additive, and their absence is not a gap.
- **Hints raise recall; they don't assert truth.** A hand-crafted rule is a *cue*, phrased as one ("chips *suggest* solid-state"), never a hard mapping — a cheap model applies a hard rule literally and misfires on edge cases (early solid-state, hybrid EM). Whatever a heuristic surfaces is still a candidate with a verbatim quote, gated by `check_quote` and the master session. A wrong heuristic costs a prunable false positive, never a silent bad fact.

**Placement vs. the cache breakpoint** (see [What goes in the cached prefix](#what-goes-in-the-cached-prefix)): the derived record context and any *global* caller note are identical across a run's slices, so they sit in the cached prefix; the question, that field's derived enum/vocab, its hand-crafted guidance, and any *targeted* caller note vary per slice and go after the breakpoint. And a trust note — the page is the one untrusted input (arbitrary web text); the derived data, hand-crafted guidance, and caller notes are trusted framing, so delimit the page clearly enough that its text can't pose as an instruction.

## Output format

- **Per slice: a forced tool call with a JSON schema**, not "please return JSON." Constrain controlled fields to **enums built from the live vocab**, so the cheap model must pick a legal term (or say absent) rather than invent "widebody-ish." Require a verbatim `quote` for every asserted value.
- **The packet back to the master session** is JSON, framed as **candidate claims with verbatim-checked evidence — not facts.** Per field category, one of three states:
  - `candidates`: `[{value, quote, source_ref, quote_verified: bool}, …]`
  - `checked-absent`: a slice looked and found nothing
  - `not-checked`: no slice covered it (e.g. it errored)
- Making "we looked, the page has no year" explicit is itself a deliverable: it lets the master session distinguish *page lacks a year* from *nobody checked* — precisely the forgot-the-year failure.
- **Entity-discovery slices have a different output shape** from field slices: not a three-state field map but a list of mentions, each `{name, kind (model/manufacturer/person), reason, quote, resolution}` where `resolution` is the deterministic cross-check result (`existing:<ref>` / `possible-gap` / `ambiguous`). The master session reads this as "records/credits the catalog may be missing," ranked by the `possible-gap` label.
- **Field slices that target a related entity** (the corporate-entity location) carry a `target` ref alongside the usual `{value, quote, source_ref, quote_verified}`, so the master session knows the candidate belongs to the corporate entity, not the model.
- **Description-enrichment slices** output a list of `{kind (anecdote/historical-context), target (this-model / manufacturer / related-entity ref), quote, snippet}` — quotable raw material, never finished prose. The master session composes any actual description (and runs it past the editorial lint) from these snippets.
- **Source-discovery slice** outputs a list of `{lead (url or reference string), form (url/reference), informs (this-model / manufacturer / general), why, quote, status}` where `status` is the deterministic result (`in-cache` / `new-url` / `new-domain-needs-root`). The master session (or a follow-up `web_fetch.py`) acts on the `new-*` leads.
- Include page metadata in the packet: `last_updated`, `content_type`, `rendered`. A thin JS-rendered page has lower-quality text; the master session should see that quality signal. `last_updated` is useful context for the year slice — but it is the page's date, not the game's, so it is a hint, never a candidate.

### The gap the verifier cannot close

`check_quote` proves a quote *exists verbatim*. It cannot prove the quote *supports* the claimed value (a real quote, a wrong inference). The arbiter closes that gap by re-reading the **full page**, never the quote alone — because a verbatim quote can be inverted by its surroundings: *"its companion model is a widebody"* is a real quote that does **not** make *this* machine a widebody, and only the full context reveals it. Partial context destroys semantic meaning, so the vet is against the whole page, always. The packet pairs each claimed value with its quote and never presents a verified quote as a verified fact. An unverifiable quote (source missing from the cache, or non-verbatim) is dropped or flagged, never silently kept.

## Patterns that buy recall (the real wins)

Standard robust-extraction shape — **schema-constrained structured output → citation-required grounding → deterministic verification → strong-model-in-the-loop** — plus, on top, for recall:

- **Ensemble / multi-sample — but match the aggregation to the slice type.** Cheap models miss stochastically, so re-running a slice and combining catches misses. *Union* (any sample's hit counts) on **enumerative** slices — list all themes / people / tags — where the failure mode is a miss and union catches it; a **single read** on **boolean/judgment** slices — is it a widebody? — where union would only amplify false positives and precision is the arbiter's job anyway. With the page cached the extra enumerative samples are nearly free, and this is the biggest recall lever after slicing. Precision is protected downstream, so union freely on the enumerative slices.
- **Completeness critic.** One final cheap pass gets the page + the flattened list of everything found and asks "what catalog-relevant fact on this page was *not* captured?" This catches things that fall between slice boundaries — otherwise a failure mode that slicing *reintroduces*.
- **Coverage report.** The three-state map above is the anti-satisficing receipt.
- **No silent caps.** If the tool trims a vocab, samples, or drops an unverifiable quote, the packet says so. A silent drop reads as "covered everything" when it wasn't.

## Architecture

Build it as a **plain Python script that calls the Anthropic Messages API directly with a cheap model (Haiku 4.5)** — not via the Claude Code subagent mechanism. It is deterministic, unit-testable like the rest of flippatch's tooling, cost-controllable, and independent of whatever harness the session runs in. The master session just runs the script and reads the JSON packet.

### Dependency footprint — a deliberate expansion

flippatch's tooling is 100% offline/stdlib today; there is no `anthropic` dependency anywhere. This tool would be the repo's **first LLM call**: a new SDK dependency, an API key in `.env`, per-run network + cost. Consequences to honor:

- Keep it self-contained (under `scripts/`, or beside `patchkit.py`).
- Unit tests must **mock the API** — pre-commit and `make test` must never hit the network or spend money.
- Give it a hard cost ceiling per run.

### Where it runs

Localhost only. The web-scrape cache (`cache.sqlite`) and the flipcommons dev DB (`db.sqlite3`) are both gitignored / R2-backed, so they exist on a developer's machine, not in any web session. This tool cannot be run or demoed from a web session; it can only be authored there.

## Build order — prove it with the thinnest slice

Do not build the DB-introspection layer first. Build one vertical, measure, then generalize.

1. Pick **one model** with a rich source page already in the web cache, and **two slices** — themes and credits. They are the highest-value misses and the two hardest tests: controlled-vocab matching vs. open-ended person/role recognition.
2. Hardcode those two slices' vocab for now (skip introspection). Pull page text via `_Sources`, fire the Haiku calls with a forced schema, run every returned quote through `check_quote`, print the JSON packet.
3. **Measure recall against ground truth** — what a careful human (or the expensive session) finds on that page vs. what the tool surfaced. If a 2-slice toy already surfaces themes/credits that shipped patches missed, the idea is proven.
4. Then generalize: DB-driven field slices + enums (including the corporate-entity location slice), the three-layer prompt (derived data + hand-crafted per-topic guidance + caller-context injection), the entity-discovery slices (models / manufacturers / people-with-reason) plus their deterministic catalog cross-check, the description-enrichment slices (anecdotes / historical context), the source-discovery slice plus its cache/citation-root cross-check, the per-record cached prefix (page + existing record + related entities + global caller context), the prime-then-fan-out sequence, the ensemble pass, the completeness critic, and the coverage report.

(The two-slice proving cut naturally exercises layers 1–2 already — its hardcoded themes/credits vocab *is* the derived layer stubbed, and any synonym hints you add to make it work *are* the hand-crafted layer. Caller-context injection is the one piece to add when generalizing.)

A go/no-go in a day, on real cached data, reusing code that already exists — before committing to the introspection layer.

## Decisions still open

- **DB access:** recommended — follow `gen.py` (run from `flipcommons/backend`, Django ORM) for drift-safe vocab with real descriptions. Alternative: raw SQL against `db.sqlite3` to skip the Django boot, at the cost of losing that.
- **Field-level descriptions:** structured (`help_text`) or doc-only (`DomainModel.md`)? Audit on localhost; it decides whether the tool needs a doc-reading step.
- **Prototype fields:** themes + credits recommended.
