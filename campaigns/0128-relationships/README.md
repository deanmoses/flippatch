# Bootleg / Licensed-Build / Conversion sweep

This doc coordinates a data-patch campaign to improve the lineage relationships between models.

The candidate models are derived live by [relationships.sql](relationships.sql), a reproducible DuckDB analysis over the current catalog — see [How the candidates are found](#how-the-candidates-are-found). It replaces the retired `Worklist.md`, a one-time regex mine frozen into a checklist (still in git history). Because the plan reads existing edges straight from the catalog, slugs are always current and "what's already done" is a column, not a snapshot to reconcile.

Read [DomainModel.md](../../../../flipcommons/docs/DomainModel.md) (Bootlegs / Licensed builds / Conversions) and [DataPatchAuthoring.md](../../../../flipcommons/docs/DataPatchAuthoring.md) before authoring. Treat every IPDB note in the worklist as a _recall aid to vet against the full page_, not as authority.

## What this campaign does

> **Model changed (ModelRelationships shipped).** Lineage now lives in the `catalog_modelrelationship` join table, not the retired `bootleg_of` / `licensed_build_of` / `converted_from` columns, and the `bootleg` / `licensed-build` / `conversion-kit` tags are gone. The Worklist's three buckets are historical labels for the same space: `licensed` ≈ copy+licensed, `bootleg` ≈ copy+unlicensed, `conversion` ≈ conversion / conversion_kit.

A lineage edge — a **`ModelRelationship`** — links a derivative machine to the design it reproduces. Read [DataPatches.md → Model relationships](../../../../flipcommons/docs/DataPatches.md) and [DomainModel.md](../../../../flipcommons/docs/DomainModel.md) before authoring. Each edge carries:

- a **`relationship_type`**: `copy` (reproduces another maker's design on newly built hardware), `conversion` (a complete machine built by reusing another machine's hardware with a new playfield/theme), or `conversion_kit` (a set of parts sold to convert a compatible donor — its target is often plural or unnamed, so a text label).
- a **`license_status`**: `licensed`, `unlicensed`, or `unknown`. "Bootleg" and "licensed build" are no longer fields or tags — they are `copy` + `unlicensed` / `copy` + `licensed`. Write `unknown` when the source establishes the copy/conversion but says nothing about authorization.
- a **target**: `target_machine` (a resolvable model slug) **XOR** `target_label` (plain text for a plural or unseeded target). A model may carry **several** machine-target edges and at most one label edge.

**The key structural fact that makes this cheap:** every foreign machine is _already seeded_ as its own model record (slug + corporate entity), and so is the US original it reproduces. Unlike the Italian sweep (which created models from tilt.it), this campaign mostly just **adds a `model_relationship` edge to an existing seeded model** and cites the source. No model creation, no title surgery in the common case.

## How the candidates are found

[relationships.sql](relationships.sql) is a analysis-local DuckDB analysis that reuses flipcommons' shared foundation (`scripts/analysis/catalog.sql`) **verbatim** via a `.read` — the same pattern as [0172-bingo-game-format](../0172-bingo-game-format/README.md). Run it through `make analyze`, which sets cwd to the flipcommons checkout, prints the `analysis_context` watermark + `relationships_summary`, and **gates on `relationships_checks`**:

```bash
F=campaigns/0128-relationships/relationships.sql
make analyze FILE=$F PREFIX=relationships                        # summary, gated on checks
make analyze FILE=$F CMD=describe ARGS=$F                        # the view reference
make analyze FILE=$F Q="FROM relationship_review LIMIT 40;"      # the actionable queue
make analyze FILE=$F Q="FROM relationship_open_questions;"       # recorded human judgement
make analyze FILE=$F Q="FROM relationship_edged_audit;"          # possible WRONG existing edges
make analyze FILE=$F Q="FROM relationship_uncited_edges;"        # existing edges with NO evidence
```

Membership is the union of two free-text detectors over `ipdb_notes` / `ipdb_notable_features` / `description`: **`by_copy`** (copy / clone / bootleg / "under licence" / licensed build / "identical to" / "same design as" / "same game as") and **`by_conv`** (conversion / conversion kit / converted game / repaint / re-theme). The type and license **split is not decided here** — that is the sweep's per-note judgement; detection only finds the model and surfaces the note.

Enrichment reads existing edges from the foundation's `model_relationships`, so `has_rel_edge` is the "already done" signal and `relationship_review` shows only what remains. That signal is deliberately **outbound only** — the campaign's job is to make a model state its own origin — but the inbound direction is read separately from `model_edges_bidir` and carried as `has_inbound_edge`, because a model that something else already points at is usually the original being described rather than a derivative to author. It feeds the `reverse-direction` disqualifier structurally, instead of relying on the note using the "also produced" formula. A quoted `'Game Name'` in the prose that resolves to a live model rides along as a best-effort **`target_guess`** — a hint the sweep audits, never authority. Caveats that still apply:

- `target_guess` is best-effort — a handful resolve to the wrong game when the note's first quoted title isn't the original (e.g. LAI `cosmic-princess`); always confirm the target before writing an edge.
- Both detectors over-count: a note that merely _mentions_ a conversion kit isn't a lineage claim (Big Chief's "Extra Ball Conversion Kit"). Every row wants source review before it becomes a claim.
- Re-read the full IPDB note (and prefer a web-cache source where one exists) for the verbatim `cite` quote.
- Some conversion candidates are the US originals themselves (`bally`, `williams`, `gottlieb`, `premier-technology`). These are in-house or same-lineage conversions, or reverse-direction note matches — vet each hard; some may not be conversion candidates at all.

**Known blind spot:** the detectors only see catalog free text, so edges authored from the pinexplore web cache or other off-catalog sources are not reproducible here. The `edged_models_missed` metric quantifies it (41 of 359 today) — it is a measured gap, not a silent one.

## The certain tier — author-ready rows with a first-cut quote

`relationship_green` is the high-confidence queue: not-edged rows with **exactly one** resolved target, no recorded open question, and a **verbatim quote extracted from the note itself** rather than hand-typed. `relationship_type` is read off the phrase; `license_status` defaults to `unknown` and claims `licensed`/`unlicensed` only when the quote itself carries the words — a bare "copy of" never becomes an authorization claim.

```bash
make analyze FILE=$F Q="FROM relationship_green;"            # author-ready, quote included
make analyze FILE=$F Q="FROM relationship_green_rejected;"   # disqualified, with reason
```

The extracted quote is a **proposal, not a verified quote** — `make verify-quotes` is the independent gate that proves each one verbatim against pinexplore's `ipdb_machines` corpus (the same IPDB pull the catalog's notes came from, so an exact substring of one is an exact substring of the other). Never ship an extracted quote that hasn't passed it.

Rows are disqualified into `relationship_green_rejected` with a `reject_reason`, each a false-positive class seen in the real output. They are **not a discard pile** — most are genuine relationships that just aren't the one a naive read would author:

| reason              | why it's held out                                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `same-maker-target` | a would-be **`copy`** whose target is the subject's **own maker's** game — a variant or reissue, never a copy (a copy reproduces _another_ maker's design). Type-specific, mirroring flipcommons' `RELATIONSHIP_TYPE_BEHAVIOR` and the sweep's `_OTHER_MAKER_TYPES`: an in-house `conversion` / `conversion_kit` / `retheme` is legitimate and is not tested. The SQL-tier counterpart of the sweep's `same-maker-target` disposition — TOOL-NOTES DEFECT 3 |
| `kit-or-conversion-unclear` | the note says "a conversion **for** X" — IPDB's 1940s phrasing for a **kit** — but doesn't settle it: either no kit language anywhere in the note, or the note describes the maker _performing_ the conversion and only later selling a kit (Glickman ×17). Where the note does corroborate, the row types `conversion_kit` and the cite carries the kit sentence as a second `[...]` span |
| `component-copy`    | the note says a **component** is a copy ("the backglass is a near copy of"), not the machine — TOOL-NOTES DEFECT 7 |
| `hedged`            | the note hedges ("a near copy of", "probably a copy of"); a hedged source can't support a flat assertion           |
| `reverse-direction` | the note is on the **original**, describing who copied _it_ — the edge belongs on the other model, pointing back   |
| `book-source`       | the note attributes to a book — see below                                                                          |
| `mojibake`          | the span carries a `?` replacement character; usually wants the `[...]` omission marker                            |

### Held out: notes that attribute to a book

Some notes cite a book as the original authority — "According to the Encyclopedia of Pinball Vol 2 page 107, this game is a copy of …". Such a claim wants **two** citations: the `ipdb:` cite carrying the quote (the proximate source) plus a quoteless cite to the book itself with a `locator` of "Vol. 2, p. 107".

The multi-cite part already works (`cite:` takes a list) and a quoteless cite already works (`quote` is optional), but **the book ref cannot be expressed**: `cite:`'s grammar is only `scheme:identifier` (no book scheme is registered) or an `http(s)` URL under a seeded _website_ root. The books _are_ seeded as CitationSources — only the ref form is missing. Until flipcommons closes that gap, `mentions_book_source` holds these rows out of the certain tier, rather than shipping a claim cited only to its proximate source. The detector is deliberately over-inclusive — a false positive costs one human read; a false negative ships an under-cited claim.

The blocker is now measured rather than described: `relationships_summary` reports `book_roots_seeded`, `book_roots_matchable` and `book_root_cited_claims` straight off `citation_roots`, so the day flipcommons registers a book ref form the last of those moves off zero without anyone remembering to re-check by hand. The matchable titles are **derived** from `citation_roots` too — the detector previously hardcoded four and silently missed the rest, so a note attributing to _Pinball Snapshots_ sailed into the certain tier under-cited. Titles too generic to hunt for as free text (_Pinball!_, _Pinball Machines_) are excepted on the record in `_rel_generic_book`, and `unmatched_book_title` fails if a newly seeded book is neither matchable nor excepted.

## Recorded human judgement

A query re-derives candidates but not a reviewer's verdict, so the campaign's open decisions are encoded as Reference lookups in the plan (`_rel_open_question`, `_rel_maker_question`) and **carried on the candidate row** as `open_question` / `maker_question` — they surface wherever the row is reviewed, and flagged rows sort to the top of `relationship_review`. `relationship_checks` catches an entry that has gone stale.

```bash
make analyze FILE=$F Q="FROM relationship_open_questions;"
```

This holds the three rows held back from 0127 (`cosmic-princess`, `high-ace-2`, `star-flite`) and the two maker-level licensed-vs-unlicensed questions (Petaco, Fipermatic), each shown against its **current** edge state. A held-back row that now carries an edge means the question was resolved _or_ authored past — verify which; don't assume.

## Decisions made

- **One patch per maker**, covering all its relationships — _except_ the clear-cut licensed builds (IPDB note literally says "under license"), which were pulled across makers into a single patch, [0127-licensed-builds.yaml](../../0127-licensed-builds.yaml). Segasa's and Alben's remaining _bootleg_ rows, and Taito do Brasil's _bootleg_ rows, still get their own per-maker patches later.
- **Excluded false positives** (not in the tables): Stern Electronics / Bally Midway / Genco _originals_ whose notes merely mention _their_ licensees; theme licenses that aren't builds of another machine (Spooky's Domino's Pizza); video recreations (Global VR UltraPin); and never-produced / prototype announcements (Dutch Pinball Bride 25th, The Pinball Factory Crocodile Hunter, Retro Pinball Bank-A-Ball).
- **Reverse-mine of US originals** ("also produced as …") was run per request: it surfaced 28 references, almost all player-count/technology _variants_ and same-maker _reissues_ (correctly not bootleg/licensed), plus a couple of Brazilian cross-maker items already caught by the forward pass. The forward self-description mine is authoritative; the reverse pass added nothing new in-scope.
- **Bally Wulff is done** (0124) and omitted here.

## Progress

- **[0127-licensed-builds.yaml](../../0127-licensed-builds.yaml) + [0128-licensed-build-title-removal.yaml](../../0128-licensed-build-title-removal.yaml) — done.** 27 licensed builds (IPDB note says "under license"): VIFICO ×13 (Gottlieb/Premier), LAI ×7 (Stern), Segasa ×4 (Williams), plus Taito do Brasil `meteor-2`, Automáticos MonteCarlo `lortium-2`, American Home Entertainment `the-getaway-high-speed-ii-2`. Same-name builds merged under the original's title (0127), emptied titles retired (0128); applied and verified 27/27 against a fresh db.pre-0039 snapshot. Three rows **held back** — now recorded in the plan and visible via `relationship_open_questions` (see [Recorded human judgement](#recorded-human-judgement)). (The 13 VIFICO builds were briefly name-suffixed `(VIFICO)` / `(Gottlieb)` under the since-retired naming convention; those names are bare again and no suffixing is owed to the other 0127 makers — see [Names](#names-leave-them-alone).)
- **[0140-maresa-bootlegs.yaml](../../0140-maresa-bootlegs.yaml) + [0141-maresa-bootleg-title-removal.yaml](../../0141-maresa-bootleg-title-removal.yaml) — applied.** (`ingest_runs` records both as `success`, 44 and 12 claims asserted, 0 rejected — check it there rather than trusting this line.) Maresa's 20 unlicensed Gottlieb copies. The 12 same-name builds got the full treatment (slug → `-maresa`, title merge, orphaned title deleted in 0141); the 8 renamed copies kept their own slug/title. (These also carried `(Maresa)` / `(Gottlieb)` names under the since-retired naming convention; those are bare again — see [Names](#names-leave-them-alone).) Structural + editorial lint + `make verify-quotes` pass. Big Brave (ipdb:4634) is the one judgment call — IPDB says "whether licensed or not is unknown"; tagged `bootleg` with a note.

- **[0159-fipermatic.yaml](../../0159-fipermatic.yaml) + [0160-europlay.yaml](../../0160-europlay.yaml) — authored, applied and verified against a fresh db.pre-0039 replay.** The first two makers driven through the post-redesign [corpus sweep](sweep/SESSION-BRIEF.md), one maker per run (6 rows each, sub-cent). Edges only — neither maker has a same-name build, so no slug/title/name work. Fipermatic ×6 copies of Gottlieb (and one of Bally's Xenon); Europlay ×4 copies + 2 conversions, one of them a **label**-target conversion (`jaws`, donor unnamed by the source). Three Europlay edge claims were rejected on review — see the run notes in [sweep/TOOL-NOTES.md](sweep/TOOL-NOTES.md), including DEFECT 7 (artwork reuse misjudged as a machine copy).

- **[0176-model-lineage.yaml](../../0176-model-lineage.yaml) + [0187-victory-games-kits.yaml](../../0187-victory-games-kits.yaml) — the certain-tier patches, generated from [relationships.sql](relationships.sql).** 0176 was the first tranche (36 rows). 0187 is the Victory Games rows gathered into one patch under the one-patch-per-maker convention — 23 edges, applied and verified (`ingest_runs`: success, 23 asserted, 0 rejected). Each row's type comes from its own IPDB note, which names the donor in one sentence and calls the thing a conversion kit in the next; the cite carries both sentences. Four of these models had been typed `conversion` in 0176 — those entries were removed from 0176 rather than contradicted by a later re-assert, so each model is asserted once, in one place. Two remain open: `play-ball-6` names two donors ("Gottlieb's 1940 'The Champ' and Gottlieb's 1941 'The New Champ'") and `sink-the-japs` is held as a reciprocal pair.

- **`0188-model-lineage-2.yaml` — the multi-maker tranche, generated but NOT YET AUTHORED.** [gen.py](gen.py) is wired to `relationship_green_other` and will emit it, but the certain tier grew 12 → 76 rows when the resolution defects below were fixed, and only the original 12 have been read. Ship it after a review pass, not before. `gen.py` excludes the makers authored as their own patch, so the two emitters cannot author the same model.

- **Detector fixes behind those patches** (each anchored in `relationships_checks`): the `same-maker-target` guard; the `same game as` phrase; possessive titles no longer truncating (`'Star's Phoenix'` → `Star`); conversion-vs-conversion-kit typed from the note's own kit sentence rather than the of/for preposition, with that sentence carried into the cite as a second `[...]` span; donor resolution restricted to the span after the lineage phrase, so a note quoting its own title first stops resolving to its namesakes; and the year IPDB writes before a title (`Gottlieb's 1940 'Gold Star'`) narrowing it to one of the catalog's seven Gold Stars.

## The dev DB

Verify every fact about the current catalog against the **Flipcommons localhost SQLite dev DB** (`../flipcommons/backend/db.sqlite3`) — a model's slug, its title, its Manufacturer, whether a maker's models are already tagged or duplicated. This doc goes stale; the dev DB is ground truth, and [relationships.sql](relationships.sql) reads it live.

Prod has ingested patches only through **`0038-model-game-formats`**, so **any patch numbered 0039 or higher can be rewritten in place** — that is why the VIFICO rows in 0127 could be edited after the fact.

Rebuild to preview your own uncommitted patches:

```bash
cd /Users/moses/dev/flipcommons/backend
cp /Users/moses/dev/flipcommons/backend/db.pre-0039.sqlite3 /Users/moses/dev/flipcommons/backend/db.sqlite3   # reset to the baseline
uv run python manage.py migrate
uv run python manage.py ingest_patches --patches-dir /Users/moses/dev/flippatch/patches/
# inspect, then re-run these lines to iterate
```

Then `make validate` in flippatch — the structural + editorial lint and `make verify-quotes` run independently of ingest, so they pass even when the ingest loop can't. Committing and `make push` are the user's call, never automatic.

## Status — what's done vs remaining

There is no status file to regenerate and nothing to reconcile: progress is a query. `relationships_summary` reports `edged` vs `not_edged` live, and `relationship_review` **is** the remaining work — a model drops out of it the moment its edge is applied.

```bash
make analyze FILE=$F PREFIX=relationships      # edged / not_edged / coverage, gated on checks
```

### Provenance of the edges already in the catalog

Progress is not the only thing a query answers. `relationship_edged_audit` — the "possible wrong existing edge" queue — now carries the **provenance** of each edge it flags: `edge_sources` / `edge_patches` name who asserted it and in which patch, `n_uncited` says whether anything backs it, `n_interactive` counts hand-edits made outside any patch, `license_disagreement` catches two eligible sources contradicting each other on authorization, and `n_tombstoned` / `n_ineligible` surface the two claim states the resolved catalog structurally cannot show. Judging a suspect edge without these means judging it blind: an edge authored in 0127 against a verbatim IPDB quote and a hand-edit with no evidence at all look identical once resolved.

`relationship_uncited_edges` is the queue that follows from it — live relationship edges carrying no external evidence at all. It is _uncited_, never _unsourced_: every row still has an ingest source, what it lacks is a citation. Authorization claims sort first, because a `licensed` / `unlicensed` edge asserts exactly the thing the campaign's standing discipline says a note cannot establish. Four such rows exist, all from `0124-bally-wulff-models` and all predating that rule; they are recorded in `_rel_uncited_licensed_known` so `uncited_licensed_edge` gates every **new** one without gating the run on the backlog, and `stale_uncited_licensed` fires when one is finally cited or removed.

(The analysis resolves the dev DB through flipcommons' foundation — no hard-coded path; override with `FLIPCOMMONS_DIR`.)

The campaign is wired onto the **AI corpus sweep** (`make sweep` — see [docs/corpus_sweep/CorpusSweepOperating.md](../../../docs/corpus_sweep/CorpusSweepOperating.md)), which does the per-note **judgement** the SQL deliberately doesn't. `uv run python3 emit_candidates.py` regenerates [sweep/candidates.jsonl](sweep/candidates.jsonl) from the plan's `relationship_sweep_candidates` view (target guesses ride along as audited-not-inherited `hint`s), then:

```bash
uv run python3 emit_candidates.py                                                                   # refresh the feed
make sweep ARGS="campaigns/0128-relationships/sweep/candidates.jsonl --no-ai"               # free reconcile
make sweep ARGS="campaigns/0128-relationships/sweep/candidates.jsonl --resume"              # trusted-tier judging
```

emitting `sweep/REVIEW.md` + `sweep/results.json`. Regenerate the feed after every dev-DB rebuild; `results.json` is keyed on `ipdb`, so regenerating never invalidates already-judged models. **A session picking up this campaign should start from [sweep/SESSION-BRIEF.md](sweep/SESSION-BRIEF.md)** — the orientation order, the run loop, and the tool-hardening duties live there.

The division of labour is the point: **the analysis discovers reproducibly, the sweep judges each note, you author.** Where they disagree — a `hint-mismatch`, or a row in `relationship_edged_audit` — adjudicate from the verbatim quote and the full note, not from either tool.

## Export-campaign overlap

Export editions are a **separate** relationship — the `MachineModel.export_edition_of` FK and the `ModelExportMarket` join table, not a `ModelRelationship` type — and they get their own campaign and their own analysis in [0177-exports](../0177-exports/README.md). A model can carry both: an export edition of another maker's game is often also a `copy`. The two are independent edges, so author each from its own evidence, but check a model against `export_candidate_lineage` there before writing a lineage edge here — 18 of its 221 candidates already carry one.

## Italian-sweep overlap — check these makers before authoring

Several Italian (and a few German) conversion/bootleg houses in the worklist were already touched by the Italian sweep (patches 0079–0116), which _created_ models from tilt.it data. The seeded IPDB records are usually _separate_ from the sweep's — but before authoring any maker below, rebuild the [dev DB](#the-dev-db) and check whether that maker's models are already tagged or duplicated. These may belong folded into the Italian series near 0109 rather than in a fresh patch:

`renato-montanari-giochi`, `skillgame-dba-renato-montanari-giochi`, `bell-games`, `nuova-bell-games`, `bell-coin-matics`, `l-v-mambelli`, `dama-srl`, `europlay`, `elettrocoin`, `idi`, `emmepi`, `ripepi`, `ditta-ripepi-spa`, `giuliano-lodola`, `nordamatic`, `pinball-shop`, `lori`.

## Authoring recipe

For each model, author a `model_relationship` under its changeset: a `cite` with `ref: ipdb:NNNN` (or a web-cache URL) and a **verbatim** quote establishing the relationship, then one or more list members, each with `relationship_type`, `license_status`, and exactly one of `target_machine: <slug>` / `target_label: <text>`:

```yaml
attribution: flipcommons-catalog
claims:
  - model.spin-out-maresa:
      cite:
        ref: ipdb:NNNN
        quote: "This is an unauthorized copy of Gottlieb's 1975 'Spin Out'."
      model_relationship:
        - target_machine: spin-out-gottlieb
          relationship_type: copy
          license_status: unlicensed
```

(A conversion kit fitting several donors uses `target_label:` instead — see [DataPatches.md](../../../../flipcommons/docs/DataPatches.md). Newer patches [0140-maresa.yaml](../../0140-maresa.yaml), [0142-geiger-conversions.yaml](../../0142-geiger-conversions.yaml) onward mirror this shape.)

A **same-name build** — a copy carrying the original's exact name — is merged under the original's **title** and gets its **slug** renamed ([Slug convention](#slug-convention-applies-to-licensed-bootleg-and-conversion-patches)); its `name` is left alone ([Names](#names-leave-them-alone)). Merge the title **only when it doesn't contradict how OPDB groups the two machines** — check their OPDB groups (`opdb_id` on each model, or their opdb.org pages). If OPDB already groups them together, or has no separate record of the copy, one Title is consistent; if OPDB keeps them in separate groups, that is a conflict: 🛑 **STOP and ask the user**, don't force the merge. A **renamed** copy (a different name) keeps its own title and slug — title placement is independent of the lineage link.

Validate against the [dev DB](#the-dev-db), then `make validate` here.

## Slug convention (applies to licensed, bootleg, and conversion patches)

When a derivative's slug ends in a disambiguation number (`spin-out-2`, `arena-4`), rename it to end in the maker instead (`spin-out-maresa`, `arena-vifico`) — **but only when the derivative carries the same name as the original it reproduces.** A same-named build (VIFICO's _Arena_ vs Premier's _Arena_; Maresa's _Spin Out_ vs Gottlieb's _Spin Out_) has a numeric suffix only to separate it from the identically-named original, and `-maker` says which one it is. When the names differ — Maresa's _Tahiti_ copies Gottlieb's _Tropic Isle_, its _King Ball_ copies _Rack-A-Ball_ — the number separates unrelated same-named games, not the original, so the maker clarifies nothing: **leave those slugs alone.** (Across the in-scope rows this splits almost exactly in half.) Compare names after normalizing away case and punctuation — `Chicago Cubs "Triple Play"` and `Chicago Cubs 'Triple Play'` are the same name.

The maker suffix is the model's **Manufacturer slug** — the brand as it appears on the cabinet. Manufacturer is its own first-class catalog record (one per brand, with a `slug`), reached from the model one hop past its corporate entity: `Model → corporate_entity → manufacturer`. Read it straight from the DB and use it verbatim — it already _is_ the short brand token:

```sql
SELECT mf.slug FROM catalog_machinemodel m
JOIN catalog_corporateentity ce ON m.corporate_entity_id = ce.id
JOIN catalog_manufacturer mf ON ce.manufacturer_id = mf.id
WHERE m.slug = '<model-slug>';
```

Every case the old trade-name/strip-the-legal-name heuristic fussed over is resolved by this lookup: `maquinas-recreativas-sociedad-anonima` → `maresa`, `vifico-sa` → `vifico`, `leisure-allied-industries` → `lai`, `fipermatic-…-ltda` → `fipermatic`, both R.M.G. corporate entities → `rmg`, `bally-manufacturing-corporation` → `bally`. **Do not** reconstruct the brand by trimming a corporate-entity slug (Premier Technology's brand is `gottlieb`, not `premier`) or from an IPDB `[Trade Name: …]` string — those only approximate a token the Manufacturer record stores exactly. One brand spans many corporate entities (Gottlieb ← both `d-gottlieb-company` and `premier-technology`), so two rows with different corporate entities can correctly share a suffix. If a model's Manufacturer is missing or its slug is genuinely unsuitable, that's a catalog gap to fix or flag — not a token to hand-derive. Check the result against existing slugs for collisions before writing.

## Names: leave them alone

A same-name copy and its original **keep their identical bare names** — _Spin Out_ and _Spin Out_. Do not suffix a model's `name` with its maker to tell the two apart. The UI shows the manufacturer everywhere a model appears, so the name never has to carry it, and the [slug](#slug-convention-applies-to-licensed-bootleg-and-conversion-patches) is what disambiguates the records.

(An earlier convention here did suffix both names — `<Name> (<Maker>)`, e.g. _Spin Out (Maresa)_ / _Spin Out (Gottlieb)_ — and a few patches applied it. It is **retired**: those names have been reverted in the catalog, and no new patch should reintroduce one. Parentheticals that are not maker suffixes — `Dragon (EM)`, `AC/DC (Pro)` — are a different thing entirely and stay.)
