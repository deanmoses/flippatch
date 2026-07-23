# 0177 — Export-market models

This directory coordinates a data-patch campaign to record which catalog models were **built for export to a foreign market**, and which model each is an export edition *of*.

It owns the analysis. The product model — the `MachineModel.export_edition_of` FK and the `ModelExportMarket` join table, and why they're shaped that way — is specified in flipcommons' [Exports.md](../../../../flipcommons/docs/plans/catalog_data_model/exports/Exports.md), which links back here for the data rather than carrying its own copy. Read it first: the two catalog structures are what the patches write, and it also records the retirement of the never-applied `export` tag.

## What the catalog carries today

Export status is recorded inconsistently — an `(Country)` suffix baked into the name, IPDB free-text prose in `extra_data` that the UI never shows, an `export` tag applied to zero of 6,913 models, and mostly nothing at all. This campaign converts that into the two structured forms.

## How the candidates are found: [exports.sql](exports.sql)

[exports.sql](exports.sql) is a analysis-local DuckDB analysis that reuses flipcommons' shared foundation (`scripts/analysis/catalog.sql`) **verbatim** via a `.read` — the same pattern as [0128-relationships](../0128-relationships/README.md) and [0172-bingo-game-format](../0172-bingo-game-format/README.md). Run it through `make analyze`, which sets cwd to the flipcommons checkout, prints the `analysis_context` watermark + `export_summary`, and **gates on `export_checks`**:

```bash
F=campaigns/0177-exports/exports.sql
make analyze FILE=$F PREFIX=export                       # summary, gated on checks
make analyze FILE=$F Q="FROM export_twin_pairs;"         # deterministic export_edition_of
make analyze FILE=$F Q="FROM export_titlemate_review;"   # likely target sits in the same Title
make analyze FILE=$F Q="FROM export_orphan_review;"      # candidates still needing a target
make analyze FILE=$F Q="FROM export_namesake_review;"    # same name, separate Title (edge + Title merge)
make analyze FILE=$F Q="FROM export_paired_brands;"      # two maker names, one operation — derived
make analyze FILE=$F Q="FROM export_name_cluster;"       # every same-name family + its state
make analyze FILE=$F Q="FROM export_cluster_pairs;"      # the pair grain — filter by lead
make analyze FILE=$F Q="FROM export_merge_backlog;"      # edge done, Title still split
make analyze FILE=$F Q="FROM export_duplicate_smell;"    # two records of one machine
make analyze FILE=$F Q="FROM export_slug_deficit;"       # bare -2 slugs + what they should say
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

**A slug handover is a second cross-patch boundary, distinct from the delete's.** Freeing a slug and claiming it cannot share a patch: 0183 tried to reslug `title.cavalier` → `cavalier-duplicate` and then `title.cavalier-2` → `cavalier` in file order, and the apply failed with `UNIQUE constraint failed: catalog_title.slug` — the engine does not write claims one entry at a time in a way that makes the freed slug visible to a later entry. (0137 avoided it without naming it, deferring the claim to a later patch.) So the shape is: **patch A** re-homes the movers and reslugs each doomed Title out of the way; **patch B** hands the freed slug to each survivor *and* retires the emptied Titles — the delete's referrer check is already satisfied by A, and the handover and the deletes touch different records, so both fit in one patch.

## Name clusters — the catalog-wide grain

Everything above is rooted in `export_candidates`: a model is visible only if a detector fired on its free text, its name suffix or an OPDB flag. That is the right root for authoring a claim and the wrong one for asking a question about the corpus, because a same-named pair where **neither** side has usable prose is structurally invisible — no detector, no candidate, no namesake row. *Cavalier* (Recel 1979) / *Cavalier* (Petaco 1979) only reached `export_namesake_review` because IPDB happened to write a twin sentence about it.

`export_name_cluster` and `export_cluster_pairs` drop that root and cluster the whole live catalog by `name_key`: **1,106 clusters over 3,087 models, 930 of them split across more than one Title**. Far too many to read, which is what `pair_state` and `lead` are for — the first retires what is finished, the second sorts the rest by what the pair is evidence *for*.

| view | grain | what it is |
| --- | --- | --- |
| `export_paired_brands` | maker pair | two maker names that are one operation, **derived** |
| `export_name_cluster` | name cluster | orientation — makers, era, `cluster_state` |
| `export_cluster_pairs` | model pair | the worklist; filter by `lead` |
| `export_merge_backlog` | model pair | edge already claimed, Title still split |
| `export_duplicate_smell` | model pair | two catalog records of one machine |
| `export_slug_deficit` | model | a bare `-2` slug, and what it should say instead |

### Paired brands, derived rather than declared

The Spanish makers ran paired brands, one domestic and one export: Recel/Petaco, Interflip/Recreativos Franco. This campaign found those only through IPDB's formulaic twin sentence, and every tier downstream then had to be told, one by one, that cross-maker does not mean `copy` here.

The catalog cannot answer it structurally, and `corporate_entity_slug` — the obvious place to look — is the wrong **level**, not merely unpopulated. DomainModel.md declares `Manufacturer ||--o{ CorporateEntity : incarnations`: a corporate entity is one legal incarnation *of* a maker, so it sits **below** the brand and partitions it across eras. Bally's models split into three (Bally Manufacturing 1932–82, Bally Midway 1983–88, Midway/WMS 1988–99); Gottlieb and Williams span four each.

So corporate entity divides one brand over time — it can never group two brands into one operation, and no level above Manufacturer exists to do so. That is why the paired-brand relationship has to be inferred from name-collision statistics rather than read off a foreign key.

What does separate a paired brand from two unrelated makers is the ratio of **contemporaneous** shared names to shared names. Bally and Gottlieb share 64 model names and exactly **one** within a year — generic nouns independently reused over four decades. Petaco and Recel share 30 and **22** are within a year, because they are the same games under two labels in the same season. The absolute count ranks Bally/Gottlieb first; the ratio inverts them. No maker name is hardcoded anywhere.

**`same_home` is not a verdict.** Recel/Petaco is one Spanish operation selling a domestic and an export label; Ace Novelty / Colonial Specialties (both USA, both 1932, five shared names) is a domestic rebadge with no export in it at all. So rather than guess, each cohort is calibrated on the edges a human has **already authored inside it** — `cohort_edge`. An unworked pair inherits the verdict its own cohort earned; a cohort nobody has judged inherits nothing and gets `'same-home partner, unjudged cohort'`, a review lead and explicitly not an export claim. A check fails the run if the export tier ever fires on an unjudged cohort.

What it finds, ranked by `n_unworked` (contemporaneous pairs carrying no edge):

| partner pair | kind | `cohort_edge` | close | unworked |
| --- | --- | --- | --- | --- |
| A. M. Amusement / Century Mfg | same-home | — | 8 | 8 |
| Mills Novelty / Shyvers | same-home | — | 6 | 6 |
| Ace Novelty / Colonial Specialties | same-home | — | 5 | 5 |
| Automatic Amusements / Bally | same-home | — | 5 | 5 |
| Bingo Novelty / Gottlieb | same-home | — | 5 | 5 |
| Europlay / Gottlieb | cross-border | — | 5 | 5 |
| Petaco / Recel | same-home | `export_edition_of` | 22 | 4 |
| Segasa / Williams | cross-border | `copy` | 9 | 4 |
| Bally / Bally Wulff | cross-border | `copy` | 10 | 1 |

The unjudged cohorts are the frontier: nine maker pairs nobody has opened, none of them reachable from any detector in this file.

### Two kinds of noise the clustering had to be taught

Both were found by reading the output, and both are measured rather than listed:

- **Placeholder names.** 37 live models are named `Unknown`, or `Unknown ("Three Bell")` where a cabinet marking is all anyone has. `name_key` strips the parenthetical and collapsed all 37 into one cluster spanning 12 makers and 1889–1984 — **579 pairs**, more noise than every real lead in the file combined. Two models being equally un-named is not a shared name; `_is_real_name` excludes them from all four grains.
- **Generic names.** *Baseball* is 19 models by 16 makers across 1931–1970; *Circus* is 16 by 12 across 1932–1980. A cluster with ≥6 makers spanning ≥20 years is a shared noun, and `'likely coincidence (generic name)'` demotes 749 pairs. The tier sits **below** every structural one — one operation, one maker, one border crossing — so it can never demote a partner pair: *Cavalier* is two makers in one year and is untouched by it.

### The merge backlog

`export_merge_backlog` promotes a number the README used to quote into a worklist: pairs already joined by an edge and still sitting in two Titles. Nothing here needs research — the edge is already the claim that the two are one game, so the Title split is a placement that claim decided. The work is the two-patch merge below.

The **singleton tranche is done**: [0183-export-title-merges.yaml](../../0183-export-title-merges.yaml) → [0184-export-title-merge-removals.yaml](../../0184-export-title-merge-removals.yaml) merged the 19 pairs carrying an `export_edition_of` edge where the doomed Title held only the mover, taking the backlog from 36 pairs to 17. What remains is the pairs whose doomed Title holds other models too — each of those members wants its own decision first — plus the `copy`/`conversion` rows, which are 0128 work.

**Which side moves is not readable off the slugs.** The `-2` placeholder sits on the *Petaco* record, but IPDB's twin sentence says *"Recel is the name used for export games"*, so the **Recel** model is the export edition and the **Petaco** original's Title survives. Every mover in the tranche was verified against its own `export_edition_of` edge rather than inferred from the pair's shape.

A consequence worth knowing: because the doomed Title carried the plain slug (`cavalier`) while the survivor carried the placeholder (`cavalier-2`), the merge also had to hand the slug over, or the canonical slug would have stayed parked on a soft-deleted Title forever.

### Duplicate records

`export_duplicate_smell` — same maker, same **exact** name, same year, same Title, no edge: 41 pairs, 5 of them touching an export candidate. Not an export finding, kept separate because it **blocks** export work when it lands on a target. *Kicker (Italy)* cites "Chicago Coin's 1966 'Kicker'" and abstains on its FK because the catalog holds two of those; Recel holds two 1975 *Criterium 75* records. Matching is `name_norm`, not `name_key` — here the parenthetical is the disambiguator, and stripping it would report A. M. Amusement's *Forward Pass (Junior)* and *(Marvel)*, two correctly distinct 1934 machines, as duplicates.

### Country resolution reads the catalog's aliases

`_country_lookup` unions three sources: the catalog's country **names**, the catalog's registered **aliases** (`country_aliases`), and this file's country **adjectives**. The split is the judgment/mechanic line the foundation's name macros are built on — an alternate name for a country belongs to the catalog, while "for the *German* market" is a parsing strategy that belongs here.

This file used to hand-copy the alternate names too, and knew 4 of the catalog's 11. A `country_lookup_ambiguous` check now fails the run if a token ever resolves two ways, since every consumer joins on `token` and a duplicate would multiply rows silently.

Worth recording honestly: **the swap changed no rows.** The seven aliases this file was missing (`England`, `Britain`, `West Germany`, `The Netherlands`, `U.K.`, `US`, `R.O.C.`) do not appear in the syntactic frames the market detectors require (`export to X`, `for the X market`, `X export`). The value is that the file is no longer a stale copy, not that it found anything today. `manufacturer_aliases` was tested the same way and likewise resolves nothing this campaign's maker-ref parse can't already reach.

### A gap the alias work surfaced: `exported to`

`_by_notes` matches `export to `, so the past-tense inflection misses entirely — 27 models say "exported to" and 23 are not candidates. Most are **reverse-direction** ("*Buccaneer*'s add-a-ball version is *Ship Ahoy* which was exported to Italy as *High Seas*"), and 8 of 9 spot-checked targets are already captured from the other end by `_reciprocal` — so widening the gate would mostly re-derive what the reciprocal parse already has.

The genuinely new self-claims are about six, and they are a different shape from the rest of the campaign: *"Games exported to the UK had three skill posts"*, *"the version exported to Germany has an additional EMC cage"*. Those are production variations shipped to a market, not separate export-edition models — a real `ModelExportMarket` fact, but a scope decision rather than an obvious inclusion. Left open deliberately; loosening `_by_notes` is exactly what the guard anchors exist to police.

### Bare numeric slugs — unfinished disambiguation

`alaska-2` says only "the second thing called Alaska". It is a placeholder minted at seed time because a name collided, and it survives long after the catalog learned *why* the two differ. Where the reason is known the slug should carry it, and the catalog already uses that convention — `hula-hula-italy`, `big-ben-segasa-italy`, `harley-davidson-bally`. A bare suffix is not cosmetic: it is disambiguation left unfinished, and this campaign is the work that supplies the missing fact.

So Alaska, Black Magic, Cherokee and Criterium 80 are **not** done just because their edges are. `export_slug_deficit` proposes what each slug should say:

| slug | name | proposed | basis |
| --- | --- | --- | --- |
| `alaska-2` | Alaska (Recreativos Franco) | `alaska-recreativos-franco` | maker |
| `alaska-3` | Alaska (EM) (Interflip) | — (`name_paren_raw` = `EM`) | *mint client-side* |
| `black-magic-2` | Black Magic (Petaco) | `black-magic-petaco` | maker |
| `cavalier-2` | Cavalier (Petaco) | `cavalier-petaco` | maker |
| `cherokee-2` | Cherokee (Recreativos Franco) | `cherokee-recreativos-franco` | maker |
| `criterium-80-2` | Criterium 80 (Petaco) | `criterium-80-petaco` | maker |
| `circus-10-2` | Circus 10 (SIRMO) | `circus-10-italy` | export destination |
| `criterium-75-2` | Criterium 75 (Recel) | — | *duplicate, merge instead* |

**1,485 live models carry a bare placeholder; 1,265 have an actionable proposal** (11 by export destination, 1,039 by maker, 215 by year). The destination comes from `model_export_markets` — what 0177 actually wrote into the catalog — not from this file's own parse, so a market corrected in review can't go on naming a slug from the parse that lost.

### The view composes slugs; it never mints them

Every proposal is an **existing** slug (`base_slug`, `manufacturer_slug`, a country slug) or an integer year, joined by a hyphen — slug-safe by construction and idempotent under the real slugifier. Turning free **text** into a slug is a different operation that does not belong in SQL: the catalog's slugs were minted client-side by standalone Python calling Django's `slugify`, whose `NFKD` + `ascii-ignore` pass is Unicode-table-driven and has no honest DuckDB equivalent.

That boundary was learned, not assumed. A `name parenthetical` basis lived here briefly, slugifying the trailing `(…)` with `name_norm` + `replace(' ','-')`, and produced `target-machine-type-ターケットマシン-タイフ１` — non-ASCII, **and** with the dakuten eaten by `strip_accents` (ゲ→ケ, プ→フ), the precise misuse `name_norm`'s own comment warns against. It also emitted `forward-pass-junior-junior`, the base slug already carrying the parenthetical. A `proposed_slug_not_slug_safe` check now guards the class.

The parenthetical survives **raw** as `name_paren_raw`, because it is a real distinguisher and often the best one — `alaska-3` is *Alaska (EM)*, and `alaska-em` is the right slug. The view surfaces the fact and leaves the minting to the authoring side, where Django's slugify is what every existing slug already went through.

Detection is structural rather than a re-implementation of Django's `slugify` (which differs on apostrophes and `&`, mis-sorting ~440 rows). A trailing number is a placeholder only when it is neither of the two things it might legitimately be:

- **the name itself** — `black-magic-4` is *Black Magic 4*, `criterium-2000` is *Criterium 2000*
- **a year already applied** — `big-ben-williams-1954` and `big-ben-williams-1975` are the exact shape this view wants the catalog to reach

Both were caught by checks after the first version reported them as deficits and proposed renaming them to the slugs they already held.

The four bases are tried in order and **fall through** when a preferred one is taken. Gottlieb's *Kicker* exports to Italy, but Chicago Coin's *Kicker (Italy)* already holds `kicker-italy`, so the destination basis yields and the maker basis supplies `kicker-gottlieb`. Dead-ending on the first choice lost 3 otherwise-actionable rows. `proposal_resolves` tests uniqueness on the distinguishing **fact**, not on the string — `alaska-3` cannot take `alaska-interflip` because `alaska` is Interflip too, which is why it falls to its own parenthetical.

**204 rows get no proposal, and that is the honest answer.** Two records with the same name, maker and year are not two machines needing better slugs — they are the `export_duplicate_smell` population, and the fix is a merge. *Criterium 75* (two Recel 1975 records) and *Kicker* (two Chicago Coin 1966 records) both land here; the latter is the same duplicate blocking `kicker-italy`'s FK.

One judgement call worth knowing: where a model has *both* a destination and a name parenthetical, destination wins. That affects exactly one row today — `beatniks-2` (*Beatniks (AAB)*, exported to Italy) proposes `beatniks-italy` where `beatniks-aab` is arguable.

## From candidates to claims: [gen.py](gen.py)

The buckets above are worklists for a **human**. The patch itself is generated from a much narrower gate, because `by_notes` membership is a keyword match and a keyword match is not a claim. [gen.py](gen.py) is a pure emitter over one view, `export_patch_rows`; all detection, gating and quote extraction live in [exports.sql](exports.sql). Regenerate with:

```bash
uv run python3 campaigns/0177-exports/gen.py
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

### Two hazards in the evidence itself

**A corroborating cite must identify the origin.** An entry-level `cite:` rides *every* claim the entry asserts (DataPatches.md), so a cite attached to an entry asserting both `export_edition_of` and `export_market` is claimed as evidence for both. A reciprocal cite therefore has to support the FK, not merely mention this model. Two shapes qualify — the cite's **ref is the origin's record** (the classic reciprocal, whose sentence subject is implicit and supplied by the record it sits on), or the **quote names the origin** (a third model's record describing the whole family: *"The Add-a-ball version of this game is … 'Ship Ahoy' which was exported to Italy as … 'High Seas'"*).

What that excludes is a cite whose subject is implicit *and* is someone else. *Ten-Up* was citing Pin-Up's note — *"The Add-a-ball version for export to Italy is Gottlieb's 1973 'Ten-Up'"* — whose implicit subject is **Pin-Up**, and which never names King Pin. Read alone it asserts a different original than the row claims (King Pin and Ten-Up are both 1973; Pin-Up is 1975 and cannot be the original). Corroboration from the wrong end is contradiction. `recip_cite_origin_unidentified` guards it.

**A title abbreviation severs a quote, and `verify-quotes` cannot see it.** Every sentence extractor here bounds a sentence with `[^.]*\.`, which breaks on the period inside `Mr.` or `Capt.`. It shipped *"…as Petaco's 'Mr."* — the game name cut mid-word, the opening quote never closed. A truncated span is **still a verbatim substring of the source**, so it verifies clean; only reading the quote reveals it. `_abbrev_guard` swaps the period for a sentinel before extraction and back after, so the emitted quote stays byte-identical, and `quote_truncated_at_abbreviation` fails the run if one reappears.

The guard recovered a claim, not just a quote. *Top Hand* had been abstaining with `- {}` because its own note — *"This is a version of Gottlieb's 1974 'Capt. Card' made for export to Italy"* — was being severed at `'Capt.`, so the export sentence never matched. With the full sentence it resolves `export_edition_of: capt-card` and an Italy market, corroborated by Capt. Card's own record. Guarded titles are `Mr Mrs Ms Dr St Capt Sgt` and only before a capitalized word; `Inc.`, `Co.`, `Ltd.`, `No.` and `Mfg.` are deliberately **not** guarded, since those genuinely do end sentences here and merging two would be its own defect.

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

- the **merge backlog**, singleton tranche done (36 pairs → 17) — what is left are pairs whose doomed Title holds other models, so each of those members needs its own decision first, plus `copy`/`conversion` rows belonging to 0128
- the **unjudged paired-brand cohorts** — nine maker pairs (A. M. Amusement/Century, Mills/Shyvers, Ace Novelty/Colonial, Automatic Amusements/Bally, Bingo Novelty/Gottlieb, Europlay/Gottlieb, PAMCO/Stoner, Giuliano Lodola/Gottlieb, Unidesa/Williams) that no detector in this file can reach; judging one pair in a cohort calibrates the rest
- the `export_cluster_pairs` rows at `lead = 'export edition (paired brand)'` and `pair_state = 'edge missing'` — co-titled Recel/Petaco pairs still carrying no edge (*Don Quijote*, *Torpedo*)
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
