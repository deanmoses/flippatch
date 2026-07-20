# 0177 — Export-market models

This directory coordinates a data-patch campaign to record which catalog models were **built for export to a foreign market**, and which model each is an export edition *of*.

It owns the analysis. The product model — the `MachineModel.export_edition_of` FK and the `ModelExportMarket` join table, and why they're shaped that way — is specified in flipcommons' [Exports.md](../../../../flipcommons/docs/plans/catalog_data_model/exports/Exports.md), which links back here for the data rather than carrying its own copy. Read it first: the two catalog structures are what the patches write, and it also records the retirement of the never-applied `export` tag.

## What the catalog carries today

Export status is recorded inconsistently — an `(Country)` suffix baked into the name, IPDB free-text prose in `extra_data` that the UI never shows, an `export` tag applied to zero of 6,913 models, and mostly nothing at all. This campaign converts that into the two structured forms.

## How the candidates are found: [exports.sql](exports.sql)

[exports.sql](exports.sql) is a analysis-local DuckDB analysis that reuses flipcommons' shared foundation (`scripts/analysis/catalog.sql`) **verbatim** via a `.read` — the same pattern as [0128-relationships](../0128-relationships/README.md) and [0172-bingo-game-format](../0172-bingo-game-format/README.md). Run it through `make analyze`, which sets cwd to the flipcommons checkout, prints the `analysis_context` watermark + `export_summary`, and **gates on `export_checks`**:

```bash
F=patches/authoring/0177-exports/exports.sql
make analyze FILE=$F PREFIX=export                       # summary, gated on checks
make analyze FILE=$F Q="FROM export_twin_pairs;"         # deterministic export_edition_of
make analyze FILE=$F Q="FROM export_titlemate_review;"   # likely target sits in the same Title
make analyze FILE=$F Q="FROM export_orphan_review;"      # candidates still needing a target
make analyze FILE=$F Q="FROM export_namesake_review;"    # same name, separate Title (edge + Title merge)
make analyze FILE=$F Q="FROM export_market_review;"      # the ModelExportMarket shape per candidate
make analyze FILE=$F Q="FROM export_patch_rows;"         # what gen.py emits
make analyze FILE=$F Q="FROM export_patch_rejected;"     # what the notes gate held back, and why
make analyze FILE=$F Q="FROM export_opdb_review;"        # the OPDB-flagged models, held out
make analyze FILE=$F Q="FROM _reciprocal;"               # the edge as stated by the original's record
make analyze FILE=$F CMD=ui                              # live GUI at localhost:4213
```

Nothing is persisted and no count is frozen into this doc: progress is a query, re-derived on each run against the live catalog. Requirements are the `duckdb` CLI on `PATH` and the flipcommons dev DB (`../flipcommons/backend/db.sqlite3`, overridable with `FLIPCOMMONS_DIR`).

Membership is the union of **four detectors**, minus one positive exclusion:

- **`by_notes`** — the IPDB notes carry export-edition phrasing ("for export", "export to X", "export edition/version/model"). The "quantity produced for export: N" production statistic is blanked before matching so a sales figure can't create a candidate. The `"for the <X> market"` phrasing was **removed** from membership as mostly noise; the rows it uniquely supplied are parked in `export_market_phrase_review` for a separate careful pass rather than deleted.
- **`by_suffix`** — a trailing `(Country)` in the model name.
- **`by_opdb`** — an OPDB feature flag containing "export".
- **`by_twin`** — the formulaic IPDB twin sentence. Spanish-market makers ran paired brands, one domestic and one export (Petaco/Recel, Recreativos Franco/Interflip), and IPDB writes **both** sides, each stating its own role and naming its counterpart. This is the highest-quality signal in the file — and it works in both directions, so it also **positively excludes** the domestic half of every pair, which the freetext detectors otherwise flag (a Petaco note says "export" only because it is naming its Recel twin).

Destination markets are parsed separately from membership: a candidate with no parseable market simply has empty `markets`, which is the common case, not an error.

**Export is maker-relative.** A model built for the same country its maker is based in is domestic, not export. `market_is_maker_home` flags those for review — a review signal, not a check.

All four are heuristics that over- and under-count; every row wants source review before it becomes a claim. `export_checks` includes **anchor checks** (the region detector, the `(Country)` suffix detector) that fail the run if a detector goes dark — e.g. from a renamed foundation column.

## The review buckets — each a first-cut worklist

`export_edition_of`:

| view | what it is |
| --- | --- |
| `export_twin_pairs` | the deterministic tier — a parsed, not guessed, `export_edition_of` target. `domestic_model_id IS NULL` means the note names a counterpart that isn't in the catalog yet: create it, or reconcile the name. The twin is **not** always in the same Title (Interflip's *Dragon* pairs with Recreativos Franco's *Dragoon*). |
| `export_titlemate_review` | the likely target sits in the candidate's own Title. One row per (candidate, title-mate) pair, with `reward_differs` and `same_maker` to judge which shape the link takes. |
| `export_orphan_review` | no edge and alone in its Title. `origin_lead` says how far the free text gets: an origin named and in the catalog, named but unseeded, prose that names none, or no prose at all. |
| `export_name_family` | regroup leads for the orphans — a same-maker sibling in a separate singleton Title whose significant name tokens nest (*Palm Beach Club* ← *Palm Beach*). Narrows the field; judge from the note. |
| `export_namesake_review` | the **same game name in a separate Title**, across makers — the other half of `export_name_family` (exact name rather than token nesting, cross-maker rather than same-maker). `lead` tiers the pair; `title_merge_lead` is a separate, independent signal. See below. |

`ModelExportMarket`:

| view | what it is |
| --- | --- |
| `export_market_review` | which shape each candidate's market row takes. `market_kind` is the headline: `country` → `target_market_location`, `region` → `target_market_label`, `unknown` → a row with neither, or no row at all. `unknown` means no detector *resolved* a market, **not** that the prose names none — so the `notes` column rides along for a reviewer to fill or correct one. |
| `export_market_phrase_review` | the parked `"for the <X> market"` hits, deliberately not candidates, with a `lead` triaging the few worth rescuing. |

### Namesakes across Titles — one row, two independent decisions

`export_namesake_review` matches a candidate's name against every model in a **different** Title. It is the bucket the *Acapulco* case lives in: Splin S.A.'s Belgian bingo *Acapulco* ("This game was made for export to France") sits alone in `acapulco-2` while Bally's *Acapulco* sits alone in `acapulco`, with no edge and no shared Title. `export_titlemate_review` can't see it — that view only looks *inside* a Title — and `export_name_family` can't either, being same-maker and token-nesting.

Each row carries two decisions that must not be conflated:

- **the edge.** Same maker → `export_edition_of`. A **different** maker's build of the same game is a `copy` — the [0128](../0128-relationships/README.md) campaign's edge, never an export edition. That is the same rule `patch_fk_cross_maker` enforces on the emit layer, and it is why this view is a review worklist and not a tier: most of its rows want a `copy`.
- **the Title.** DomainModel.md: "The edge records what was copied; the copy's Title placement is a separate editorial decision." `title_merge_lead` flags it independently — both models alone in their Titles, same game format, years not far apart.

`lead` tiers the pair, calibrated on the actual pair distribution. The two axes that separate signal from coincidence are **year gap** and **game format**: *Bazaar* (Bally 1966) and *Bazaar* (ESCO 1937) are unrelated games sharing a generic noun, and 117 of the 242 pairs are of that kind.

An undated model does **not** default to a small gap. Where a model has no year of its own the tier falls back to its **maker's era** — the span its maker's dated models occupy, requiring at least 3 of them so one stray date cannot define an era — and `gap_basis` records which measurement was used, since a model's own year is evidence while its maker's era is an inference from siblings.

That fallback is what finally resolved the case this view was built for. [0181-bingo-years](../0181-bingo-years/README.md) dated 109 bingos, but bingo.cdyn.com lists no Splin *Acapulco*, so that model stayed year-less and the pair stayed mis-tiered as a `foreign build (copy)`. What 0181 *did* establish is Splin's era — six models dated 1999–2003 — which puts the maker **38 years** after Bally's 1961 *Acapulco*. The pair now falls out as `likely coincidence (years apart)` with `gap_basis = 'maker era'`, derived rather than special-cased.

| `lead` | what it means |
| --- | --- |
| `export edition` | same maker, same format, ≤2 years apart — the `export_edition_of` shape outright (*On Beam (Italy)* / *On Beam*, both Bally 1969) |
| `foreign build (copy)` | cross-maker, same format, maker homes differ — the *Volcano*/Fipermatic shape; a `copy` for 0128 |
| `cross-maker, contemporaneous` | same format, ≤5 years, same maker home — needs a source read |
| `already related` | the pair already carries an edge; only the Title question may be left |
| `likely coincidence (…)` | ≥16 years apart, or the game formats differ — a shared noun and nothing more |

Name matching strips **one** trailing parenthetical, which is what lets the campaign's own `(Country)` models find their original (*On Beam (Italy)* → *On Beam*) — but it also collapses *KISS (Limited Edition)* onto *KISS*, so `name_match` records whether the match was exact or needed the strip. When both models are candidates the pair appears from both ends (*Kicker* / *Kicker (Italy)*); that mirroring is deliberate, and the duplicate it exposes — two Chicago Coin 1966 *Kicker* records — is the same one blocking that row's FK above.

`namesake_merge_backlog` is the number worth watching: pairs this campaign has **already joined with an edge** but left sitting in two singleton Titles.

#### Merging two Titles

A merge is two patches, never one — `delete:`'s referrer check reads live DB state, so a model reassigned earlier in the *same* patch isn't yet visible (DataPatches.md). The precedent is [0148-rmg.yaml](../../0148-rmg.yaml) → [0149-rmg-title-removal.yaml](../../0149-rmg-title-removal.yaml): the first re-homes the model (`title:` onto the survivor, a disambiguating `slug:` if the names collide, and the `model_relationship` edge with its cite), the second retires the emptied Title with `delete: true` and a `note:` naming the model that left. The Title is **soft-deleted**, not retracted — `status` is not directly assertable. Reslugging the doomed Title first ([0137](../../0137-nugent-consolidation.yaml) used `-duplicate`) is needed only when the survivor has to claim its slug.

## From candidates to claims: [gen.py](gen.py)

The buckets above are worklists for a **human**. The patch itself is generated from a much narrower gate, because `by_notes` membership is a keyword match and a keyword match is not a claim. [gen.py](gen.py) is a pure emitter over one view, `export_patch_rows`; all detection, gating and quote extraction live in [exports.sql](exports.sql). Regenerate with:

```bash
uv run python3 patches/authoring/0177-exports/gen.py
make validate && make verify-quotes
```

It writes [patches/0177-exports.yaml](../../0177-exports.yaml) in four tiers, differing mainly in what they cite:

| tier | evidence | `export_edition_of` |
| --- | --- | --- |
| `twin` | `cite: ipdb:<id>` — two spans joined by a marked `[...]`: "<Brand> is the name used for export games" and the sentence naming the counterpart | **yes** — parsed |
| `notes` | `cite: ipdb:<id>` — the verbatim export sentence | **when the sentence names an original that resolves** |
| `suffix` | no cite of its own; the evidence is the model's `(Country)` name, so the reasoning goes in a `note:` | only from a reciprocal note |
| `reciprocal` | `cite: ipdb:<id>` of the **original's** record, which names this model as its export | **usually** |

### Reciprocal notes — the edge stated from the other end

IPDB often records an export on the **original's** record rather than the export's: *Paul Bunyan*'s note says "The Italian version is Gottlieb's 1968 'Big Jack'." `_reciprocal` mines those, and they do three jobs:

- **corroborate** an edge already claimed — a second, independent source on 24 rows;
- **fill an origin** the model's own note couldn't support — *Jackpot* → *Gold Rush* comes back this way, after `same game as` was excluded;
- **discover** models with no usable note at all — *Western*'s own note only hedges ("would make 'Western' the last 2-player game made for export"), while *Lariat*'s states it flat.

Corroborating cites ride the **same entry** as extra `cite:` list members, never a second entry. That isn't a style choice: a cite list attaches every citation to every claim the entry asserts, and DataPatches.md requires entries targeting one record to assert **disjoint claim keys** — so a second entry re-asserting `export_edition_of` would be a hard error.

The parse binds the model reference **directly** to an export-designating predicate, which is what keeps it honest:

> "The replay version of this game is Gottlieb's 1973 'High Hand' **and the Italian version is** Gottlieb's 1973 'Top Hand'."

Both halves have the same shape; only the second is an export. A sentence-level keyword match would bind *High Hand*.

Three further gates, each earned by a false positive found in the data:

- **Export is maker-relative.** "A single-player **Spanish** version is **Maresa**'s 1972 'Dakota'" is a Spanish maker's home-market build — domestic, however export-shaped the sentence reads. Dakota is now a guard anchor.
- **An export edition shares its original's maker.** A different maker's build is a `copy`, not an export, so a cross-maker note can evidence the export *fact* but never the *origin* — this is what stops Gottlieb's *Texas Ranger* being recorded as an export edition of Maresa's *Dakota*. The `twin` tier is the deliberate and only exception: its sentence says "the **same company** made…", one company running two brands (Recel/Petaco, Interflip/Recreativos Franco).
- **A relative clause re-anchors the subject.** "…is Gottlieb's 1977 'Team One' **which was** exported to Italy as Gottlieb's 1977 'Kicker'" — Kicker's original is Team One, not the model whose note this is. Those rows keep the export fact and drop the origin.
- **Two sources naming different origins abstain** — *Kicker (Italy)* is claimed by both Chicago Coin *Kicker* records, *Top Hand* by both *Capt. Card* and *High Hand*.

### A regex hazard worth knowing

A blanket `(?i)` also makes `[A-Z]` match lowercase, silently voiding every capitalization requirement in the pattern. It made a maker capture read `player Williams` out of "a 4-player Williams' 1971 'Jackpot'". Capitalization is load-bearing here — it marks a proper name and a country — so case-insensitivity is **scoped** with `(?i:…)` and `[A-Z]` stays case-sensitive. (Relatedly: IPDB drops the possessive *s* on makers whose name ends in one — `Gottlieb's` but `Williams'` — hence `'s?`.)

### Where `export_edition_of` comes from

A target is only ever **parsed out of the sentence the claim cites** — never inferred. Two forms qualify, both in `_origin_ref`:

- the twin tier's formulaic paired-brand sentence;
- a `version of` / `conversion of` reference in the notes tier: "A version of Gottlieb's 1969 **'Mini Pool'** made for export to Italy".

This is not the inference DataPatchAuthoring.md warns off. That rule is about a shared **Title** being a lead rather than evidence; here the source names the original outright, inside the quote that ships with the claim. The title-mate and orphan buckets remain human worklists.

Three gates keep a wrong FK — worse than a missing one — out:

- **`same game as` is excluded**, because it marks a *sibling*, not an original. Troubadour's note says "Same game as Gottlieb's 1967 'Harmony'", but Harmony's own note shows both are versions of *Melody*; reading that as an origin would invert a peer relation.
- **"version of *this* … game" is excluded** — a self-reference naming no other model (Bronco).
- **the reference must resolve to exactly one live model**, never itself. Name + maker + year is what separates same-named games — Chicago Coin's 1968 *Gun Smoke* (Replay) really is the original of the candidate *Gun Smoke* (Add-a-Ball). Where even that is ambiguous the row abstains: *Kicker (Italy)* cites "Chicago Coin's 1966 'Kicker'" and the catalog holds **two** of those, so it emits its market row with no FK.

`patch_fk_reciprocal_confirmed` reports how many targets name the candidate **back** in their own note — an independent statement of the same edge from the other end, and the main reason to trust the parse. It is reported, not enforced: a one-sided note is normal. Where such a note exists it is also *cited*, on the same entry (below).

### Why the notes gate is an opener whitelist

In this corpus "… made for export to Italy" is a **floating participle**: it attaches to whichever noun the sentence is about, and the tail alone is ambiguous. Compare

- "**This is** the add-a-ball version of Segasa's 1975 'Big Ben' made for export to Italy." — an export
- "**The playfield layout was used again on** Gottlieb's 1972 'Space Orbit' made for export to Italy." — *Space Orbit* is the export; this model is not

Identical tails, opposite meanings. So green requires the sentence to **open with a self-referential subject**, rather than merely lacking a disqualifier. Everything else is routed to `export_patch_rejected` with a reason (`not a self-claim`, `reverse-direction`, `export attaches elsewhere`, `hedged`, `truncated sentence`, `component subject`, `mojibake`, `market names an unseeded country`) — a real review queue, since a reverse-direction row usually *names* the model that is the export.

`export_checks` carries a **guard anchor** listing every row observed emitting a wrong claim while the gate was built (Eclipse, Mini Cycle, Polo, Royal Cards, Sky Devil's, The Card, M-79 Ambush, Dimension, Wall Street, Extra Inning, Hyde Park, Gold Rush). If a loosened regex re-admits one, the run fails — and a companion check fails if any guard slug stops resolving, so a reslug can't quietly turn the guards into no-ops.

### Why `by_opdb` is not a tier

All 34 OPDB "Export edition" models are Brazilian, Spanish, Italian or Japanese makers' **local builds** (Taito do Brasil, Electromatic, LTD, Rowamet, Maresa), and 7 already carry a `copy` edge. OPDB writes that flag from the **original design's** point of view — a foreign-market build of a US game — which is the inverse of the maker-relative definition used here: Taito do Brasil building *Sultan* in Brazil for Brazil is domestic. Emitting `- {}` for those would assert "built for export" of models that were not. They sit in `export_opdb_review`, and for most of them the honest edge is a `copy` from the [0128](../0128-relationships/README.md) campaign.

## Status

**The write path has landed and the first patch is authored.** [patches/0177-exports.yaml](../../0177-exports.yaml) validates, every quote passes `make verify-quotes`, and it applies clean to a rebuilt dev DB.

The generator is expected to keep evolving — the numbers below are a query (`make analyze FILE=$F PREFIX=export`), not a frozen count, and re-running `gen.py` rewrites the patch in place. The patch is **not** shipped; committing and `make push` are the user's call.

Still open, in rough order of value:

- the **title-mate** bucket (95 candidates) — the largest source of further `export_edition_of` targets, needing a per-row source read
- the **namesake** bucket — `lead = 'export edition'` first (a parsed-quality `export_edition_of` the notes never stated), then the `foreign build (copy)` rows as 0128 work, then the `title_merge_lead` merges, including the `namesake_merge_backlog` pairs already joined by an edge
- the reciprocal rows that abstained on an origin because two sources disagreed (*Kicker (Italy)*, *Top Hand*)
- the notes rows whose sentence names an original that **doesn't resolve uniquely** (e.g. *Kicker (Italy)*, blocked by two same-named Chicago Coin 1966 models); these want a human to pick the right one, and the duplicate itself may be worth a look
- the `export_patch_rejected` queue, especially `reverse-direction` rows, which name a real export on the *other* model
- `export_opdb_review` — mostly `copy` edges for the 0128 campaign
- `export_market_phrase_review` — the ~5 genuine exports parked out of the "for the <X> market" noise
- countries the catalog doesn't carry yet (Israel, Indonesia); those rows re-green automatically once seeded

## Overlap with the lineage campaign

### Connectedness is bidirectional

`has_edge` — "does this candidate already carry a relationship?" — reads the foundation's `model_edges_bidir`, not `model_edges`. The distinction is not cosmetic. `model_edges` is outbound-only by design (the direction *is* the fact: a variant points at its base, and the base is not a variant of the variant), so a connectedness test written against it returns a confident **false** for any model whose relationship is stated from the other end — 416 live models are in that position catalog-wide.

While `has_edge` read the outbound view, **30 of the 221 candidates were called edge-less despite carrying an inbound edge**, and 24 of them sat in `export_titlemate_review` asking a reviewer to find a relationship the catalog had already recorded. Fixing it moved `no_edge` from 150 to 120 and cut the title-mate queue from 67 to 43. `has_inbound_only` keeps those rows visible — a model whose only edge points *at* it is often the **original** of an export, which is exactly the reciprocal case this campaign mines.

`has_variant_of` and `rel_types` still read the directional `model_edges`, because those ask what the model itself *states*.

A model can be **both** an export edition and a copy or conversion — the two are independent edges and the [0128-relationships](../0128-relationships/README.md) campaign authors the latter. `export_candidate_lineage` reads existing edges from the foundation's `model_edges`, so `has_edge` / `rel_types` show what a candidate already carries; 18 of the 221 candidates carry one today. Check a candidate against that campaign's `relationship_review` before authoring, so the two campaigns don't write contradictory claims about the same pair.

## The dev DB

Verify every fact about the current catalog against the **Flipcommons localhost SQLite dev DB** (`../flipcommons/backend/db.sqlite3`) — this doc goes stale; the dev DB is ground truth, and [exports.sql](exports.sql) reads it live. Ask the user which snapshot to reset from; never pick one yourself. The rebuild loop and the snapshot-validate discipline are in [0128-relationships/README.md → The dev DB](../0128-relationships/README.md#the-dev-db) and flipcommons' DataPatchAuthoring.md.

Then `make validate` here. Committing and `make push` are the user's call, never automatic.
