# Corpus-wide feature enrichment — charter

Decisions governing the campaign to sweep **all existing models** for missing `gameplay_feature` assignments and missing feature vocabulary. Settled with the user 2026-08-08. Later sessions follow this document; a change to it is a user decision, dated here.

The folder carries no patch number — a session claims the next free `patches/` number when it generates (same convention as `0215-frontier-2026/model-families/`).

## Scope

- **All features, not just gameplay-affecting ones** (0218's charter): presentation, trim, lighting, sound, cabinet equipment — toppers, art blades, shaker motors, powder-coated trim.
- **Out of scope**: rules and specs — play-rules ("5-ball play", "cooperative play modes"), scoring ("match feature"), rewards, dimensions, and stat-tail text (score maxima, replay wheels). The 0178 audit's `negation` guard stands: an absence statement ("no slingshots", 113 models) must never become an assignment.
- **Basic components of every machine are never features**: translite, shooter rod, lockdown bar, legs. Standing exclusion list, grown during review.
- The **affects-gameplay axis** (a `kind`/flag on vocab nodes) is deliberately deferred: the vocab stays small (hundreds of nodes), so retrofitting is a one-pass tagging job over nodes, never over models. Do not block acquisition on it.

## Vocabulary rules

- **[0218](../../patches/0218-presentation-feature-vocab.yaml) is the style exemplar** — generic terms, rich alias lists, DAG parents (the blades family). [0219](../../patches/0219-houdini-features.yaml) as first written is the counter-example: too granular, model-specific (see Toys below).
- **Manufacturer wording verbatim** unless it is extremely clearly a synonym; **when in doubt, create a child feature** (InvisiGlass is-a Anti-Reflection Playfield Glass). Judgment calls go on the batch's close-calls list for user review.
- **Parent = is-a, only.** A child *is a kind of* its parent. Composition is not parentage: a stage curtain is not a kind of stage (0219's `stage-curtains` ← `stages` is the recorded error).
- **Prefer detail over conflation** (0178's principle): positional/qualified variants are children, not aliases; only phrasings carrying no distinguishing fact become aliases. Exact-segment matching means "mirrored art blades" can never be assigned as bare `art-blades`.
- **Nameable-across-titles test**: a new *non-toy* vocab node must be generically nameable across titles (subways, magnets — even if only one title asserts it so far). Single-model phrasings enter as aliases of existing features, or as manufacturer-branded children (the InvisiGlass pattern), never as new top-level vocab.

## Toys (user decision, 2026-08-10 — SUPERSEDES the 2026-08-08 ruling)

Bespoke toys are **NOT vocab nodes**. The authority is flipcommons `docs/plans/catalog_data_model/unique_features/UniqueFeatures.md`: bespoke identities (Rudy, the Ringmaster, the GoT dragons) will become **UniqueFeature** records — a future entity, not yet built. Until it exists, a model asserts only the generic **toy classification tree** (built by 0219):

- `toys` — *grouping node, never attached to a model* (the editorial lint's `feature-grouping-node` rule enforces this)
  - `static-toys` — decorative; never moves, ball never touches it
  - `interactive-toys` — *grouping node, never attached*
    - `bash-toys` — the ball strikes it
    - `animatronic-toys`
    - `pop-up-toys` — rises from or drops below the playfield
    - `ball-holding-toys` — locks, holds or delivers balls

Consequences for this campaign:

- **Classify, don't name.** A toy's evidence supports leaf classifications plus its generic mechanisms (Houdini's trunk ⇒ `ball-holding-toys` + `ball-locks`); the identity and its prose wait for UniqueFeature. A toy whose evidence states no behaviour classifies as `static-toys` only when the source itself reads as decorative; otherwise it classifies nothing.
- **Keep the worklist.** Each family doc records its future unique features (name + best source) so the UniqueFeature backfill campaign has its inputs.
- **The 2026-08-08 family-scoped collision gate is dissolved** — with no bespoke nodes there is nothing for it to gate.
- **Branded names for generic features stay vocabulary** (UniqueFeatures.md → Branded names): InvisiGlass, Magic Glass, Expression Lighting System — brand as child of the generic, dedup gate intact. A maker's brand node is created by the family patch that attaches it, from that maker's own documents, never speculatively.
- **Evidence**: IPDB's toys field — now a foundation column and quotable via `ipdb:` cites — plus manufacturer pages. Mined per-family/batch, not in bulk.

## Evidence sources, in order

1. **IPDB Notable Features** (5,213 models) via the [0178 audit machinery](../0178-gameplay-features/README.md) — re-runnable live, completeness-gated, verbatim `ipdb:` quotes. **Known rework needed**: the audit truncates each blob at its first blank line to drop the stats tail, but modern entries (e.g. TMNT Premium's "Powder-coated…" trim) carry in-scope presentation text *after* that blank line. Fix the cleaning before batch 1.
2. **IPDB toys prose** (294 models, above).
3. **OPDB features** (`opdb_features` varchar[], 751 models).
4. Manufacturer wording for modern games — the per-family campaigns' job (`0215-frontier-2026`); the corpus loop does not duplicate it.

Not used: `make sweep` (relationship archetype only today; the deterministic path is cheaper and stronger for this data) and the AI page extractor.

## Review process (user decision, 2026-08-08)

**Model-centric batches, not vocab-term lists** — the user reviews a handful of models at a time, never thousands of terms.

1. **Batch = ~8 models**, chosen for vocab diversity early (modern Stern + EM-era + solid-state). The review doc shows, per model, **every segment** of its source text with a **±20-char snippet** and a disposition: already-assigned / new assignment to existing vocab / new vocab proposed / not-a-feature (prose, stat, negation, component). Snippets are for review only, never cited.
2. Each **new vocab term** additionally shows corpus-wide reach and 2–3 snippets **from other models** — a term is not judged from one occurrence.
3. Every batch carries a **close-calls section**: the synonym-vs-child and wording judgment calls, surfaced explicitly.
4. User corrections become **standing rules** (exclusion lists, aliases, category calls) enforced by checks thereafter.
5. **Calibration → scale**: early batches generate patches covering only the reviewed models. After a few near-zero-correction batches, approved vocab is assigned **corpus-wide** by the deterministic exact-match machinery (0178 shipped 1,812 assignments this way, zero quote failures), and review narrows to close-calls and samples.

Patches per batch: vocab creates and assignments can share one file (creates topologically above references) or split into a pair; vocab must precede any later patch that references it (numeric-prefix apply order).

## Prerequisite: rationalize 0219 — DONE 2026-08-10

0219 was rewritten under the superseding Toys ruling above (snapshot-restore-replay; unshipped throughout): the bespoke nodes (`stages`, `stage-curtains`, `trunks`, `marquees`, `spirit-planchettes`, `milk-cans`, `steampunk-flippers`) are gone, the toy classification tree is created there, and the Houdini attaches classify into it. The generic mechs (`subways`, `multiball` counts, `rgb-playfield-inserts`, `mirrored-art-blades`, …) stand. 0220 (Transformers) was reworked the same day: leaf toy classifications only, plus the interactive-lighting DAG (location axis × brand family; Stern's Expression Lighting leaves carry both parents). Houdini.md and Transformers.md carry the future-unique-features worklists.

The fix belongs to the Houdini family campaign (`0215-frontier-2026/model-families/houdini/` — regenerate via its `gen.py`, record decisions in its notes), but this charter's rules govern it.
