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

## Toys (user decision, 2026-08-08)

Bespoke toys **are vocab nodes**, all children of a `toys` interior node. Chosen over a `model.toys` text field for: encyclopedia entries on iconic toys (Rudy, the Ringmaster), and comparing toy loadouts between editions within a title. No flipcommons schema change needed.

- **Dual representation**: a toy that does something also asserts its generic mechanism features (Houdini's trunk ⇒ `ball-locks` + `magnets`). Faceting rides the mechanism; identity rides the toy node.
- **Naming**: prefer the toy's proper/community name ("Rudy", "Iron Throne"); otherwise a short noun phrase, title-prefixed only when slugs would collide across titles. The rich description ("motorized animated interactive dragon") goes in the node's **description** (0074-style descriptions patch), which is where the encyclopedia entry lives.
- **Gating**: children-of-`toys` are **excluded** from the global resolve-or-collide duplicate gate (a bespoke toy legitimately resolves to nothing). In its place, a **family-scoped collision check**: a new toys-child assigned to a model is compared against toys-children already on that model and its lineage-connected family; overlapping normalized names/aliases flag for review. Sound because toy duplication is family-local by nature; a toy genuinely recurring across unrelated families is *recurring* and belongs in the real vocab under the normal gate.
- **Evidence**: IPDB's toys field — descriptive prose on 294 models, in `extra_data` at `$.ipdb.toys`, not yet a foundation column — plus manufacturer pages. Mined per-family/batch, not in bulk.

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

## Prerequisite: rationalize 0219

0219 is applied on dev but unshipped, therefore rewritable via snapshot-restore-replay (recipe in [ENRICHMENT-PLAN.md](../0215-frontier-2026/ENRICHMENT-PLAN.md) → Rebuilding the database). Changes owed:

- Create the `toys` parent node; re-parent the bespoke toys under it: `trunks`, `milk-cans`, `spirit-planchettes`, `marquees`, and likely `stages` (Houdini's stage is a toy; judgment call at fix time).
- Fix the is-a violation: `stage-curtains` is not a kind of `stages` — fold into the stage toy's description or make it parentless under `toys`; judgment call at fix time.
- Keep the generic mechs as-is: `subways`, `multiball` counts, `rgb-playfield-inserts`, `mirrored-art-blades`, etc.
- Re-check every remaining 0219 node against the nameable-across-titles test and 0218 style.

The fix belongs to the Houdini family campaign (`0215-frontier-2026/model-families/houdini/` — regenerate via its `gen.py`, record decisions in its notes), but this charter's rules govern it.
