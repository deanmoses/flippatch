# Bootleg / Licensed-Build / Conversion sweep

This doc coordinates a data-patch campaign to improve the lineage relationships between models.

The candidate models live in [Worklist.md](Worklist.md), a checklist originally machine-mined from pinexplore's DuckDB snapshot of IPDB's free text; maker-specific doubts and held-back rows are flagged inline there as ⚠ callouts. Its slug columns are a frozen pre-re-slugging snapshot, so re-resolve every slug against the live [dev DB](#the-dev-db) before authoring.

Read [DomainModel.md](../../../../flipcommons/docs/DomainModel.md) (Bootlegs / Licensed builds / Conversions) and [DataPatchAuthoring.md](../../../../flipcommons/docs/DataPatchAuthoring.md) before authoring. Treat every IPDB note in the worklist as a _recall aid to vet against the full page_, not as authority.

## What this campaign does

> **Model changed (ModelRelationships shipped).** Lineage now lives in the `catalog_modelrelationship` join table, not the retired `bootleg_of` / `licensed_build_of` / `converted_from` columns, and the `bootleg` / `licensed-build` / `conversion-kit` tags are gone. The Worklist's three buckets are historical labels for the same space: `licensed` ≈ copy+licensed, `bootleg` ≈ copy+unlicensed, `conversion` ≈ conversion / conversion_kit.

A lineage edge — a **`ModelRelationship`** — links a derivative machine to the design it reproduces. Read [DataPatches.md → Model relationships](../../../../flipcommons/docs/DataPatches.md) and [DomainModel.md](../../../../flipcommons/docs/DomainModel.md) before authoring. Each edge carries:

- a **`relationship_type`**: `copy` (reproduces another maker's design on newly built hardware), `conversion` (a complete machine built by reusing another machine's hardware with a new playfield/theme), or `conversion_kit` (a set of parts sold to convert a compatible donor — its target is often plural or unnamed, so a text label).
- a **`license_status`**: `licensed`, `unlicensed`, or `unknown`. "Bootleg" and "licensed build" are no longer fields or tags — they are `copy` + `unlicensed` / `copy` + `licensed`. Write `unknown` when the source establishes the copy/conversion but says nothing about authorization.
- a **target**: `target_machine` (a resolvable model slug) **XOR** `target_label` (plain text for a plural or unseeded target). A model may carry **several** machine-target edges and at most one label edge.

**The key structural fact that makes this cheap:** every foreign machine is _already seeded_ as its own model record (slug + corporate entity), and so is the US original it reproduces. Unlike the Italian sweep (which created models from tilt.it), this campaign mostly just **adds a `model_relationship` edge to an existing seeded model** and cites the source. No model creation, no title surgery in the common case.

## How the candidates were found

A one-time mine (since-removed script, in git history) built the Worklist from `pinexplore/explore.duckdb`: `ipdb_machines.Notes` joined to seeded `models` on `ipdb_id`, self-description regexes classifying each note — license language (`under licen…`) → licensed, copy language (`(this is) a copy of…`) → bootleg, conversion language (`conversion kit for…`) → conversion — and the note's `Maker's YEAR 'Name'` reference parsed back to a seeded slug for the target. The classification is fallible, hence these caveats:

- `→ target slug` is best-effort — most are right, but a handful resolve to the wrong game when the note's first quoted title isn't the original (e.g. LAI `cosmic-princess`); always confirm the target before writing `*_of:`.
- Rows marked **TODO** in the target column need manual resolution.
- Re-read the full IPDB note (and prefer a web-cache source where one exists) for the verbatim `cite` quote.
- In the conversion section, a few "makers" are the US originals themselves (`bally-manufacturing-corporation`, `williams-electronics-incorporated`, `d-gottlieb-company`, `premier-technology`). These are in-house or same-lineage conversions, or reverse-direction note matches — vet each one hard; some may not be conversion candidates at all.

## Decisions made

- **One patch per maker**, covering all its relationships — _except_ the clear-cut licensed builds (IPDB note literally says "under license"), which were pulled across makers into a single patch, [0127-licensed-builds.yaml](../../0127-licensed-builds.yaml). Segasa's and Alben's remaining _bootleg_ rows, and Taito do Brasil's _bootleg_ rows, still get their own per-maker patches later.
- **Excluded false positives** (not in the tables): Stern Electronics / Bally Midway / Genco _originals_ whose notes merely mention _their_ licensees; theme licenses that aren't builds of another machine (Spooky's Domino's Pizza); video recreations (Global VR UltraPin); and never-produced / prototype announcements (Dutch Pinball Bride 25th, The Pinball Factory Crocodile Hunter, Retro Pinball Bank-A-Ball).
- **Reverse-mine of US originals** ("also produced as …") was run per request: it surfaced 28 references, almost all player-count/technology _variants_ and same-maker _reissues_ (correctly not bootleg/licensed), plus a couple of Brazilian cross-maker items already caught by the forward pass. The forward self-description mine is authoritative; the reverse pass added nothing new in-scope.
- **Bally Wulff is done** (0124) and omitted here.

## Progress

- **[0127-licensed-builds.yaml](../../0127-licensed-builds.yaml) + [0128-licensed-build-title-removal.yaml](../../0128-licensed-build-title-removal.yaml) — done.** 27 licensed builds (IPDB note says "under license"): VIFICO ×13 (Gottlieb/Premier), LAI ×7 (Stern), Segasa ×4 (Williams), plus Taito do Brasil `meteor-2`, Automáticos MonteCarlo `lortium-2`, American Home Entertainment `the-getaway-high-speed-ii-2`. Same-name builds merged under the original's title (0127), emptied titles retired (0128); applied and verified 27/27 against a fresh db.pre-0039 snapshot. Three rows **held back** — flagged as ⚠ callouts in [Worklist.md](Worklist.md). (The 13 VIFICO builds were briefly name-suffixed `(VIFICO)` / `(Gottlieb)` under the since-retired naming convention; those names are bare again and no suffixing is owed to the other 0127 makers — see [Names](#names-leave-them-alone).)
- **[0140-maresa-bootlegs.yaml](../../0140-maresa-bootlegs.yaml) + [0141-maresa-bootleg-title-removal.yaml](../../0141-maresa-bootleg-title-removal.yaml) — authored, snapshot apply-verify still to run.** Maresa's 20 unlicensed Gottlieb copies. The 12 same-name builds got the full treatment (slug → `-maresa`, title merge, orphaned title deleted in 0141); the 8 renamed copies kept their own slug/title. (These also carried `(Maresa)` / `(Gottlieb)` names under the since-retired naming convention; those are bare again — see [Names](#names-leave-them-alone).) Structural + editorial lint + `make verify-quotes` pass. Big Brave (ipdb:4634) is the one judgment call — IPDB says "whether licensed or not is unknown"; tagged `bootleg` with a note.

- **[0159-fipermatic.yaml](../../0159-fipermatic.yaml) + [0160-europlay.yaml](../../0160-europlay.yaml) — authored, applied and verified against a fresh db.pre-0039 replay.** The first two makers driven through the post-redesign [corpus sweep](sweep/SESSION-BRIEF.md), one maker per run (6 rows each, sub-cent). Edges only — neither maker has a same-name build, so no slug/title/name work. Fipermatic ×6 copies of Gottlieb (and one of Bally's Xenon); Europlay ×4 copies + 2 conversions, one of them a **label**-target conversion (`jaws`, donor unnamed by the source). Three Europlay edge claims were rejected on review — see the run notes in [sweep/TOOL-NOTES.md](sweep/TOOL-NOTES.md), including DEFECT 7 (artwork reuse misjudged as a machine copy).

## The dev DB

Verify every fact about the current catalog against the **Flipcommons localhost SQLite dev DB** (`../flipcommons/backend/db.sqlite3`) — a model's slug, its title, its Manufacturer, whether a maker's models are already tagged or duplicated. This doc and the Worklist go stale; the dev DB is ground truth.

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

## Status tooling — what's done vs remaining

Two read-only scripts (in this dir) reconcile the Worklist against the freshly-rebuilt [dev DB](#the-dev-db), keyed on the stable `ipdb` number rather than the Worklist's frozen slugs. **Run both after every rebuild** (the dev DB is ground truth; both this file and the Worklist go stale):

```bash
uv run python3 check_status.py --write        # (re)generate STATUS.md: per-bucket/per-maker done vs remaining, + target-guess discrepancies to vet
uv run python3 reconcile_worklist.py          # stamp ✅ onto Worklist rows already applied in the DB, so nobody re-authors them (idempotent)
```

(Both resolve the dev DB via `scripts/common/related_projects.py` — no hard-coded path; override with `FLIPCOMMONS_DIR`. Run under `uv` so that resolver's deps are present.)

- **[STATUS.md](STATUS.md)** is the generated source of truth for progress — read it, don't hand-maintain it.

The campaign is also wired onto the **AI corpus sweep** (`make sweep` — see [docs/corpus_sweep/CorpusSweepOperating.md](../../../docs/corpus_sweep/CorpusSweepOperating.md)): `uv run python3 emit_candidates.py` regenerates [sweep/candidates.jsonl](sweep/candidates.jsonl) from the Worklist (the Worklist's target guesses ride along as audited-not-inherited `hint`s), then `make sweep ARGS="patches/authoring/0128-relationships/sweep/candidates.jsonl --no-ai"` reconciles for free and the same command without `--no-ai` judges every note on the trusted tier, emitting `sweep/REVIEW.md` + `sweep/results.json`. Note the sweep's exact target compare flags re-slugging-era discrepancies `check_status.py`'s loose compare tolerates — adjudicate those from the note, not from either script. **A session picking up this campaign should start from [sweep/SESSION-BRIEF.md](sweep/SESSION-BRIEF.md)** — the orientation order, the run loop, and the tool-hardening duties live there.
- A row in the discrepancy table means the DB's relationship target ≠ the Worklist's guess; open the IPDB note (pinexplore DuckDB `ipdb_machines.Notes`) and decide which is right before trusting either.
- After stamping, re-align the Worklist tables with `npx prettier@3.8.1 --write Worklist.md` (this dir is excluded from the commit-time markdown hooks, so it won't auto-format).

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
