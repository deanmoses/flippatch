# 0178 — Gameplay features

Extends the gameplay-feature vocabulary with the features IPDB names but our catalog never modelled, and assigns them to models. This directory is the audit trail: how the gap was found, quantified, and vetted.

## Why there is a gap at all

Our then-177-feature vocabulary was harvested out of IPDB's `Notable Features` free text. That blob opens with a comma-separated feature list — `Trap holes (25), Rollover buttons (2), Magic Squares, Bally Hole` — and the harvest parsed it with a **count filter**: it kept only segments carrying a parenthesized `(N)` (pinexplore `sql/04_staging.sql`, `WHERE regexp_matches(segment, '\(\d+\)')`). Every **countless** feature name was silently dropped.

That is a systematic hole, not a scatter of misses. A feature IPDB never counts could not enter the vocabulary by that path **at all** — which is why the entire bingo feature family (Magic Squares, Magic Screen, Magic Lines, Mystic Lines, Bally Hole) is absent, along with detour gates, lockdown-bar buttons, crossover return lanes and mini-playfields.

## The audit: [features.sql](features.sql)

A read-only DuckDB analysis over the live flipcommons catalog. It reuses flipcommons' shared DuckDB layer **verbatim**: the decode foundation (`scripts/analysis/catalog.sql`, pulled in by a `.read`) and its runner (`scripts/analysis/analysis`) — we keep no copy of either. `make analyze` sets cwd to the flipcommons checkout (so the `.read` and the foundation's `ATTACH backend/db.sqlite3` resolve) and delegates to that runner, which prints the `analysis_context` watermark + `gpf_summary` and **gates on `gpf_checks`** (nonzero exit on any row):

```bash
F=campaigns/0178-gameplay-features/features.sql
make analyze FILE=$F PREFIX=gpf                        # watermark + summary, gated on checks
make analyze FILE=$F Q="FROM gpf_new_features;"        # the campaign candidates
make analyze FILE=$F Q="FROM gpf_review LIMIT 100;"    # the gap with the human call attached
make analyze FILE=$F Q="FROM gpf_assignments;"         # the generator feed
```

Requirements: the `duckdb` CLI on `PATH` and the flipcommons dev DB (`../flipcommons/backend/db.sqlite3`, overridable with `FLIPCOMMONS_DIR`). Nothing is written or persisted; every count is a live snapshot — the SQL is the source of truth, re-derived on each run rather than frozen into an exported file.

It re-parses the same blob the harvest did, **without** the count filter, and asks of each distinct segment: does it already resolve to a catalog gameplay feature? The residue — uncounted **and** unmatched — is the gap.

Two cleaning steps keep the residue readable. IPDB's blob is two parts, a feature list and then, after a blank line, a fixed stats tail (`Maximum displayed point score is …`, `Replay wheel maximum: 37`, `Sound: 3 chimes, knocker.`); `_gpf_cleaned` **truncates at the first blank line**, and `is_stat` catches the minority of entries whose tail hangs off a single newline instead. Without that, machine specs and sound hardware dominate the gap by sheer repetition — `knocker` alone reaches 281 models.

## The principle: position is a distinguishing fact

The campaign's rule is **prefer detail over conflation**. A Left Kickback Lane is not an alias of Kickback Lanes — it is a *child* of it; an Upper Right Kickback Lane is a child of Right Kickback Lane, not the same thing; and only phrasings carrying no distinguishing fact of their own (`Autoplunger` → `auto-launch`, `Left-Side Kickback Lane` → `left-kickback-lanes`) become aliases. The catalog already worked this way before the campaign — `right-side-ball-return-gates` and `mid-field-ball-return-gates` are both children of `ball-return-gates` — so this extends an existing pattern rather than inventing one.

Six features are **taxonomy nodes**: created because a child needs a parent, though no IPDB text names them (`right-kickback-lanes`, `right-kicker-lanes`, `stationary-posts`, `drop-lanes`, `free-ball-gates`, `right-ball-return-rollunders`). They carry zero assignments by design, and `gpf_checks` knows to expect that — while any *assignable* feature that finds zero models fails the run as a broken matcher.

## One source, two patches

`_gpf_new` in [features.sql](features.sql) is the single source for both patches: slug, name, parents, aliases, and how the feature is matched. With 62 features across a parent/child tree, a hand-written YAML copy would drift from the analysis that justifies it, and the assignment view would silently reference features the vocab patch never created. `gen.py` emits both files from it; `gpf_checks` gates the pairing from the other side.

Normalization is the foundation's `name_norm` macro on **both sides** — the parsed IPDB segment and the catalog vocabulary — so the two agree by construction. It replaced a hand-rolled normalizer that only lowercased and collapsed whitespace; `name_norm` also folds diacritics and collapses every run of non-alphanumerics to one space, which is why `Open-elbow inlanes` and `open elbow inlanes` now key alike and `Trocadéro` no longer depends on its accent. The hardcoded terms in `_gpf_new` were re-normalized *through the macro itself* rather than by re-implementing it here.

Two matchers, because the tree needs both:

- **`pattern`** (15 features, 356 assignments) — a regex, for families whose phrasing is too varied to enumerate. **Magic Lines is why this exists**: as exact terms it scores **zero** models (`magic lines` 2, `magic line e` 2, `three magic lines` 1, `5 magic lines` 1 — every phrasing under the classification threshold); as a pattern it finds **9**. Loose on purpose, paid for by `_gpf_family_excluded`, a vetted false-positive list keyed by model + feature.
- **`terms`** (41 features, 1,359 assignments) — exact normalised terms, for the positional variants. Here exactness *is* the point: `left kickback lane` and `upper left kickback lane` are different features, and a regex loose enough to catch one would swallow the other. A term may feed two features — `left and right dual inlanes` (49 models) asserts both the left and the right child rather than naming a third thing.

## The classification

Every gap term at 4+ models must be **accounted for**: it becomes a feature, it becomes an alias on an existing feature, or it carries a call in `_gpf_class`. `gpf_checks` fails the run on any term above the threshold that is none of those, and on any term double-booked across two of them.

What remains once the vocabulary has taken its share:

| category | terms | what it means |
| --- | --- | --- |
| `negation` | 9 | an **absence** statement |
| `descriptive` | 6 | an existing feature, but the phrase describes an *instance* rather than naming it |
| `fence` | 5 | still genuinely ambiguous even under the prefer-detail rule |
| everything else | 172 | belongs to another dimension (cabinet, display, sound, lighting, art, scoring, reward, play-rule, dimension, tech, layout, construction, toy) or is a split fragment |

- **`negation` is the most dangerous class in this data.** `no slingshots` reaches **113 models**, `no pop bumpers` 37, `no outlanes` 25, `no flippers` 14. A naive "assign every feature name you find" pass would assert exactly the feature the source denies. Two of the vetted family false positives are the same trap in longer form — A-B-C and Bingo-Cards both say the playfield "resembles a roulette wheel **but does not spin**". A `negation_became_feature` check stands guard.
- **`fence` is now only five terms**: unqualified `upper gate` / `lower gate` that may just be ball-return gates, a conjunction the splitter left glued together (`ball guides and playfield inserts`), a behaviour rather than a mechanism (`both slingshots operate simultaneously`), and a one-off novelty phrasing. Everything else that was fenced under the original err-on-caution rule was **promoted** when the rule changed — `shaker-motors` (55), `free-ball-return-lanes` (30), `time-clocks` (30), the animation family, the bingo card counts, the centre posts, `outholes`, `lane-change`, `video-modes`.
- **Counts, where the count is the fact.** `bingo-cards` is asserted with a membership count parsed from the term (`six cards` → ×6), the one place a number carries meaning. Everything else is bare even where IPDB supplies one.

## Does this add any bingos?

**No** — checked before authoring, because it was the first thing the gap suggested. Of the 39 models whose notable features name Magic Squares / Magic Screen / Magic Lines / Mystic Lines, **38 already carry `game_format = bingo-pinball`** from [0172](../0172-bingo-game-format/README.md). The one exception is a true negative and is the family's single vetted false positive: **Gulfstream** (Williams 1972) is a flipper game whose centre playfield lights form a bingo-*inspired* "Magic Square" — same name, different mechanism.

0172's recall stands because its `by_struct` detector already regexes `(magic|mystic) (squares|screen|lines?|card|numbers?)` out of the same prose. The signal was consumed for format detection; it was just never promoted to a structured feature. That is what this campaign fixes.

## Limitations

- **Coverage is partial, and the summary says so.** The audit accounts for terms at 4+ models: 446 accounted terms reaching 2,545 models, against a gap of 7,570. The long tail below the threshold is unaudited. Lower `_gpf_threshold` to go deeper; `gpf_checks` will then demand a call for everything newly above it.
- **There is no upper length bound any more, and that mattered.** An earlier cut capped gap terms at 40 characters to keep the residue readable. It also hid every feature IPDB describes in a full clause — `Open-elbow inlanes allow ball to pass from inlane to outlane and vice-versa` is 74 characters and reaches 31 models. The trap was that completeness only fires on terms that *reach* `gpf_gap`, so the hidden band could never be reported as unaudited: **the audit read clean precisely because it was not looking.** Lifting the ceiling exposed 60 unjudged terms, of which 7 were real features and the rest filed elsewhere. Any filter upstream of a completeness check is a blind spot that reports itself as healthy.
- **The splitter does not break on `;`.** A handful of entries list features semicolon-separated (WIMI's *Miss Bonus*: `Advancing odds/scores; Ballyhole; Colored lines; …`), so those arrive as one long segment. The family patterns still match inside it, but the quoted `segment` is the whole blob.
- **Every candidate still wants source review before it becomes a claim.** These are detector outputs, not vetted claims.

## The patches

Two files, both generated, both **regenerated whole** on every run.

Production has ingested only through `0038-model-game-formats`, so every patch above that is still rewritable. When the audit widens — a lifted filter, a new foundation macro — the right move is to re-emit these two and replay the dev DB from `db.pre-0039.sqlite3`, not to bolt a second pair on beside them. An earlier pass did split the campaign across `0178/0179` + `0182/0183` under the mistaken belief the first pair was frozen; it has been collapsed back. Although prod has only ingested through `0038-model-game-formats` — so `0039+` are technically rewritable — nothing here needed a rewrite: `create:` adds features, and `gameplay_feature_alias` members are independent claims, so a later patch can hang aliases on a feature [0072](../../0072-gameplay-feature-vocab.yaml) created just as effectively as editing 0072 would. Rewriting would have bought tidiness at the cost of putting applied, working content back in play. **0072 and 0073 are untouched.**

- **[`0178-gameplay-feature-vocab.yaml`](../../0178-gameplay-feature-vocab.yaml)** — 69 `create:` blocks with parents and aliases, plus 4 pre-existing features gaining aliases. Emitted in **topological order**: a patch may reference an entity it creates earlier in the same file, but only *above* the reference, so the tree is sorted parents-first rather than alphabetically.
- **[`0179-gameplay-features-ipdb.yaml`](../../0179-gameplay-features-ipdb.yaml)** — 1,336 entries, 1,812 assignments across 63 features. Each entry is a `cite: ipdb:<id>` carrying the verbatim phrase, attributed `ipdb` since the claim is IPDB's.

  **No `note:`.** A note could only say what the feature IS — which belongs in the feature's own description, written once for its detail page, not copied across 1,336 model claims — or that IPDB lists it, which the cite already says. The cite carries the whole claim.

```bash
uv run python3 campaigns/0178-gameplay-features/gen.py
make validate          # structural + editorial lint
make verify-quotes     # every cite quote verbatim vs the IPDB corpus
```

### What the gates caught

Every one of these was a real defect found by a check rather than by reading:

- **Span order.** `verify-quotes` requires the `[...]`-joined spans of a multi-feature cite to appear **in source order**; the generator first sorted them by feature name. `gpf_assignments` now exposes `quote_pos`.
- **Duplicate spans.** `left and right dual inlanes` assigns two features from *one* phrase, so both rows carried the same span and the second copy read as out of order. The generator dedupes spans.
- **Mojibake in a quote.** patchkit strips U+FFFD from a quote (it is encoding damage, not source text), so a span running through one was emitted differently from the source. The span now stops at it.
- **Emission order.** `center-stationary-posts` was emitted before the `stationary-posts` it parents, and the ingest refused it. Hence the topological sort.
- **A broken node test.** `assignable_feature_dark` fired for six features because the `kind` expression misdetected taxonomy nodes.
- **Terms claimed but not adopted.** After an earlier landing, `alias_not_resolving` flagged terms classified `alias` that the patch never actually aliased — they became the `descriptive` category.
- **Normalized needle, raw haystack.** Adopting `name_norm` silently broke every quote: the term is matched in normalized space but the `cite:` must be verbatim from the source, so a term reading `open elbow inlanes` could no longer find `Open-elbow inlanes`. `assignment_without_quote` caught all 69 at once. Each space in a term or pattern now becomes "any run of non-alphanumerics" before it meets raw text — zero-or-more, not one-or-more, because `name_norm` folds `Ballyhole` to a single word and `bally ?hole` must keep matching both it and `Bally Hole`.
- **`regexp_escape` breaking the thing it was meant to protect.** It renders a space as backslash-space, whose trailing backslash then escapes the `[` of the character class built next to it. Dropped entirely: `name_norm` guarantees a term holds only letters, digits and single spaces, so there is no metacharacter to escape.

## Verification

- **`make check` green** (493 tests) and **`make verify-quotes`: 2871 verified, 0 failed.**
- **Differential check.** `gpf_vocab` and `gpf_memberships` were frozen with `CMD=snapshot` before ingest and diffed after: **nothing removed** from either, both reverse `EXCEPT`s empty. No collateral damage.
- **`gpf_checks` clean post-landing**, verifying the patches did what the analysis said: every declared feature exists, every alias resolves, every assignment is a live membership, every counted feature got its count and no uncounted one did, no negation became a feature, and the Magic Squares anchor now resolves to `magic-squares` rather than appearing in the gap.
- **The gap shrank**: `vocab_features` 177 → **246**, `terms_resolved` 283 → **348**.

### Foundation macros adopted

`name_norm` / `name_key` landed in the foundation while this campaign was in flight, and replaced the analysis's own normalizer outright — the case the macro block argues for, that "every plan that does it was writing its own. Two copies drift." The plan also now reads `gameplay_feature_vocab` and `gameplay_feature_aliases` instead of `fc.catalog_gameplayfeature*`; those two views were added *because* of this campaign, and `gameplay_feature_vocab.children` is what makes the `node_parents_nothing` check expressible.

### A patchkit gap this exposed

`gameplay_feature` is the one namespace whose members carry a count, and `patchkit.entry()` could not express the `{public_id: count}` form at all — its relationship emitter ran every member through `_scalar`. Added, test-first per the repo's TDD rule, with validation that the count is a positive integer (the backend enforces `>= 1`).

## Status

- **Applied and verified** on the dev DB, replayed clean from the pre-0039 baseline (140 patches). **69 features created, 1,812 assignments**, vocabulary 177 → 246.
- **Descriptions still owed — 69 of them.** The pre-existing 177 features each carry a description; none of 0178's creates do. Same split [0072](../../0072-gameplay-feature-vocab.yaml) took, with [0074](../../0074-gameplay-feature-descriptions.yaml) supplying the prose afterwards — a follow-up patch should do the same, writing one encyclopedia-quality description per feature for its detail page. The six taxonomy nodes need them most: they have no assignments to explain themselves by.
- **Hand off** — commit and `make push` are the user's call.
