# 0290 — IPDB `Specialty`

Lands IPDB's `Specialty:` row on the catalog's own classification vocabulary: **75 assertions over 66 models**, plus the two vocabulary entries they need.

- `specialties.sql` — the analysis: the specialty mapping, the single-valued safety gate, the anchors.
- `gen.py` — the emitter, one entry per `spec_patch_rows` row.
- `patches/0290-ipdb-specialties.yaml` — 77 entries, attribution `flipcommons-catalog`.
- `patches/0291-flipperless-tag-description.yaml` — the new tag's prose, which needs the `flipcommons-ai-desc-tag` attribution and so cannot ride the same file.

## The signal

IPDB prints one `Specialty:` row per machine naming what KIND of machine the listing is — `Bingo Machine`, `Widebody`, `Add-A-Ball`, `Flipperless`. It is the source of basic classification we have otherwise had to synthesize by reading free-text notes.

Our IPDB baseline has no column for it:

| carrier | holds |
| --- | --- |
| dump, anywhere | `Specialty` — **zero** times in 6,671 records |
| the machine page's `Specialty:` row | the headings, verbatim |

So the whole field arrives only from the page. Pinexplore's web cache holds archive.org captures of IPDB machine pages and publishes the parsed rows as `px.ipdb.model_specialties`.

## Why a stale page is allowed to speak here

The captures run 2018 to 2026 and the dump is April 2026, so **the dump is the newer source in the general case and nothing here may overwrite it**. IPDB has visibly moved on since the older captures — it has relabelled header dates and added dates to listings that had none — so a page's *date* fields are actively untrustworthy and this analysis never reads one.

Specialty is the same case 0269 made for production status: **the dump has no column for it**, so there is no newer value to lose. The page is the only carrier there has ever been. The rule is enforced a second time downstream by flippatch's `ipdb:` resolver, which renders a page-only label only where the dump rendered no line under it — `Specialty` sits on that short list beside `Production`.

## The single-valued trap

`game_format` and `cabinet` hold one value; `tag`, `reward_type` and `gameplay_feature` hold many. That decides what "the model does not carry this" means, and it is the reason this campaign rejects rows a naive replay would have written.

For a multi-valued field, not-carried is a gap and asserting fills it. For a single-valued field it can instead mean **the slot is taken**, and asserting would overwrite. IPDB routinely prints two specialties competing for that one slot:

| listing | IPDB's `Specialty:` row | catalog holds |
| --- | --- | --- |
| `one-ball-circus` and 7 more | `Bingo Machine One Ball Game` | `bingo-pinball` |
| `sunshine-park` | `Horserace Game One Ball Game` | `one-ball` |

These are not catalog defects. In **every** such row the value we hold is one IPDB also asserts on the same page — the disagreement is between two of IPDB's own headings, not between IPDB and us, and choosing between them needs the machine read. `conflict_value_unsupported_by_page` asserts that property rather than assuming it, so the day a row is a real disagreement with the source it stops the run.

## The one inference

A machine IPDB calls a widebody has a wider-than-standard **pinball** cabinet and playfield, so `game_format: pinball` follows from the designation and rides the same changeset as the tag. It is withheld wherever the format slot is otherwise spoken for — by the catalog, or by another specialty on the same page.

`big-inning-2` is the case that rule was written for and the case `anchor_big_inning_called_a_pinball` pins: a 1947 Bally automatic-pitch baseball game whose page reads `Specialty: Bat Game Widebody`. It takes the widebody tag and `pitch-and-bat`, and must never be called a pinball.

## The vocabulary

Two of the fourteen mapped headings needed something before they could land:

- **`Flipperless`** is a new tag. Nothing in the catalog expressed it, and none of the 23 models carries a contradicting `flippers` feature.
- **`Mechanical Backbox Animation`** needed no new term at all. `mechanical-backbox-animations` has been here all along under 102 models; only IPDB's singular spelling of it was missing, so this is an alias. Five of the twelve models turned out to carry the feature already.

## What is deferred, and why

Four headings map to nothing and emit nothing (26 rows). They share a shape: IPDB's heading **crosses our axes** rather than filling a gap in them, so no new term resolves it and the models have to be read one at a time.

| heading | rows | the problem |
| --- | ---: | --- |
| `Payout Machine` | 11 | spans `cash-payout`, `merchant-paid` and `ticket-payout` |
| `Not A Pinball` | 9 | says what a machine is not; what it *is* has to come from elsewhere |
| `Horserace Game` | 5 | may be a kind of `one-ball` rather than a peer of it — IPDB asserts both on four of the five |
| `Table Top/Counter Game` | 1 | spans the `tabletop` and `countertop` cabinets |

A deferral is a decision to emit nothing, not an oversight. `unmapped_specialty` fires the day IPDB prints a heading the reference table has never seen, so the corpus cannot grow a new classification silently.

## Coverage

**Partial, and not randomly so.** 151 of IPDB's 6,671 listings have a cached page to read a Specialty off, and those pages were fetched for the 0268 project-date work — a cohort skewed toward dateless, never-produced, bingo and EM machines. A model with no row here **has not been cleared, it has not been looked at**: `Widebody` returning 8 hits in a cohort selected against modern solid-state machines is the tell. A later fetch campaign widens this without changing anything in the analysis.

## Totals

From `spec_summary`, against the dev DB at `0289-gtf-victory-edition-variant-base` (6,944 live models), immediately before this patch applied:

| metric | value |
| --- | ---: |
| listings_with_a_specialty | 151 |
| candidates | 188 |
| candidate_models | 150 |
| **patch_rows** | **75** |
| patch_models | 66 |
| patch_rows_implying_pinball | 7 |
| rejected | 113 |
| rejected_already_carried | 79 |
| rejected_conflicting | 8 |
| rejected_deferred | 26 |

The 79 already-carried rows are the corroboration set: classifications somebody had already made by hand, years ago, from IPDB's prose, with nobody having read a `Specialty:` row.
