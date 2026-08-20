# 0269 — IPDB `Never Produced`

Sets `production_status: unreleased` on **36 models the catalog filed as unknown** and IPDB's own machine page records as never produced.

- `never_produced.sql` — the analysis: the classification, the dump-wins safety gate, the anchors.
- `gen.py` — the emitter, one entry per `np_patch_rows` row.
- `patches/0269-ipdb-never-produced.yaml` — 36 entries, attribution `flipcommons-catalog`.

## The signal

IPDB prints one `Production:` row per machine, and it is not a number field. A machine that shipped gets a quantity — `1,750 units (confirmed)` — and a machine that did not gets the words `Never Produced`.

Our IPDB baseline, `ipdb_xantari.json`, types that row as an integer. The quantity survives; the words do not:

| carrier | holds |
| --- | --- |
| dump `ProductionNumber` (INTEGER) | the quantity, on the machines that shipped |
| dump, anywhere | `Never Produced` — **zero** times in 6,664 records |
| the machine page's `Production:` row | both, verbatim |

So a cancelled project reached us as a null indistinguishable from "IPDB does not say", and the catalog files both as unknown. The status is recoverable only from the page. Pinexplore's web cache now holds archive.org captures of IPDB machine pages, and `extract_ipdb_to_jsonl.py` renders each through the machine-page parser into `ingest_sources/ipdb_archive/models.jsonl`, where `production.status` is the row's words when they are not a quantity.

**83 of the 300 cached pages say `Never Produced`.** 47 of those models the catalog already had right; 36 are this patch.

## Why a stale page is allowed to speak here

The captures are mostly 2018 and the dump is February 2025. **The dump is the newer and more correct source and nothing here may overwrite it** — that rule is the reason this campaign is narrow.

IPDB has visibly moved on since those captures. It has relabelled header dates between `Date Of Manufacture` and `Project Date`, and it has added dates to listings that had none in 2018. A page's **date** fields are therefore actively untrustworthy, and this analysis never reads one.

Production status is the opposite case, for one structural reason: **the dump has no column for it**, so there is no newer value to lose. Either the dump holds a quantity, in which case the dump wins and the row is rejected, or the dump is silent and the page is the only carrier.

That the two never actually disagree is asserted, not assumed. Across all 292 corpus rows the dump also carries:

| assertion | result |
| --- | ---: |
| pages stating a status for a machine the dump gives a quantity | **0** |
| pages and dump both stating a number, disagreeing | **0** |
| emitted rows whose dump record states a quantity | **0** |

The first two are `np_checks` running over the whole corpus, not just the emitted set — if the "no newer value to lose" argument ever stops being true, the check says so rather than the rejection branch quietly papering over a conflict.

The same rule is enforced a second time downstream, by the tooling rather than by this campaign. flippatch's `ipdb:` resolver was extended for this patch (`scripts/quotes/sources.py`) to top a dump row up from the cached page for the few labels the dump has no column for — `Production`, `Specialty`, `Concept by`, `Easter Eggs` — and **only where the dump rendered no line under that label**. Dates are deliberately not on that list. A quote of `Production: Never Produced` therefore cannot verify against a machine the dump credits with a production run, whatever this analysis might have emitted.

## Totals

From `np_summary`, against the dev DB at `0268-ipdb-project-dates` (6,941 live models), immediately before this patch applied:

| metric | value |
| --- | ---: |
| models_live | 6941 |
| models_with_production_status | 253 |
| models_unreleased | 112 |
| pages_cached | 300 |
| pages_never_produced | 83 |
| pages_with_a_quantity | 28 |
| candidates | 83 |
| **patch_rows** | **36** |
| patch_rows_with_project_year | 35 |
| rejected | 47 |
| rejected_already_unreleased | 47 |

Applying it takes `models_unreleased` from **112 to 148** and writes nothing to `production_year` or `production_quantity`.

The population is the big three and a short tail: **Williams 21, Bally 9, Gottlieb 3**, then Alvin G., Data East, and one model with no manufacturer recorded — spanning 1933 to 1993. Across all 83 never-produced pages the split is Gottlieb 28, Williams 28, Bally 10: Gottlieb's cancelled designs were largely known to the catalog already, and Williams' were not. The same three makers dominate [0268](../0268-ipdb-project-dates/README.md)'s project dates, for the same reason — they are the ones whose internal design records IPDB holds.

## The corroboration this patch inherits

**47 of the 83 were already marked `unreleased`** — by hand, years ago, read out of IPDB's free-text prose by somebody who never saw a `Production:` row. **Not one was marked anything else**: no `produced`, no `one-off`, no `announced`.

That is the mapping confirming itself. Two independent readings of IPDB — one from prose, one from the structured row — agree on all 47 overlapping machines and contradict each other nowhere. It is also why those 47 are rejected rather than emitted: re-asserting a value a record already holds changes nothing, and the apply engine rejects a provenance-carrying unit that changes nothing.

## Judgment calls

**`unreleased`, not `one-off`.** [DomainModel.md](../../../flipcommons/docs/DomainModel.md) separates `unreleased` ("a project intended for commercial production, but cancelled — it may have resulted in prototypes or sample runs") from `one-off` ("built by a manufacturer but never intended for commercial production — gifts, movie props, test pieces"). Every machine here carries a manufacturer's own model listing, and 35 of the 36 carry a project date out of that manufacturer's design records: a catalogued commercial design that was cancelled. IPDB does not use our vocabulary, so the mapping is ours.

**No entry carries a note.** The quote is the whole justification: IPDB recorded no production for this machine. The `unreleased`-not-`one-off` decision above is made once for the population, not per record — repeating a boilerplate sentence on 36 records would tell a reader nothing the citation did not already carry, and the vocabulary reasoning belongs here where it can be argued with.

**Attribution is `flipcommons-catalog`.** IPDB supplies the fact and is cited and quoted for it, but `unreleased` is our word, chosen against our own vocabulary. Attributing it to IPDB would rank our reading against genuinely IPDB-asserted claims as though IPDB had made it.

**Never-produced is not the same as never-built, and the patch says nothing about quantities.** IPDB itself pairs `Never Produced` with nothing, but pairs a project date with a real run often enough that the two are independent: `beauty-contest` has a project date and 1,750 confirmed units. Sample runs and prototypes are inside the definition of `unreleased`; this patch leaves `production_quantity` alone on every model it touches.

## Anchors, and why they don't point at the patch

The emitted set **legitimately drains to zero the moment this patch applies** — every model it targeted now carries a status and moves to the `catalog_already_unreleased` rejection. Verified: re-running `np_summary` after apply gives `patch_rows: 0`, `rejected: 83`, with `np_checks` still clean.

So anchoring the checks on `np_patch_rows` could not tell "the campaign finished" from "the extract rotted". The anchors probe the **extract and the join** instead:

| anchor | shape |
| --- | --- |
| `ipdb 3711` → `Never Produced` on `ice-castle`, dump silent | the positive case |
| `ipdb 2049` (San Francisco) → 2,000 units, not never-produced | the negative case |
| every page's `source_url` restates its own `ipdb_id` | the mis-keyed-extract tripwire |
| the cached corpus has not collapsed below 250 pages | drift |

The second is the one that matters most. Without it the parse could go one-sided — every page reading as never produced — and every row-level invariant above it would still pass.

## Dead ends, from the wider investigation

- **The dump's prose is not a substitute.** `Notes ILIKE '%never produced%'` matches 31 of 6,664 dump rows against a population of at least 83, and only 9 of them overlap the pages that state the status outright. Of the other 22, four have a production quantity in the catalog — the phrase in those notes is about a donor game, an artwork reuse or a different model entirely. It is a per-row reading exercise, not a signal.
- **`Never Produced` never appears in `AdditionalDetails`.** Zero of 6,664. The header line carries the date and the player count and nothing about production, so the field that rescued [0268](../0268-ipdb-project-dates/README.md) has nothing to offer here.
- **`ipdb.org` returns HTTP 403** to the fetcher. There is no live re-scrape path; archive.org is the only route to a machine page, and it is why the captures are as old as they are.

## Out of scope

- **The 10 models with a project date and no cached page** (`aces`, `lost`, `wwe-raw-vs-smackdown`, `lolly-dolly`, …). All are IPDB ids above 6588 — listings added after archive.org stopped capturing the site. IPDB may well record them as never produced; there is no way to read it.
- **The 22 dump rows whose prose says "never produced" but that have no cached page.** Only four of them have an unknown production status, and each needs its own note read. A hand-authored patch, not a generated one.
- **`Specialty` and `Concept by`.** The same cached pages carry `Specialty` on 18 of these 83 machines (7 Widebody, 2 Add-A-Ball, 2 Flipperless, 2 Bingo Machine, and one each of Bat Game, Cocktail Table, Table Top/Counter Game, Not A Pinball, Non-Commercial Machine) and `Concept by` on five (Pat Lawlor, Joe Kaminkow twice, Matt Walsh, Marc Rosenberg with Roger Shiffman). Both are now quotable through the `ipdb:` resolver. `Specialty` maps onto several different catalog concepts — game formats, tags, and in one case the home-use tag — so it needs its own decisions and its own patch.
- **`Easter Eggs`.** One page in the whole corpus carries the label, and it is a pointer at somebody else's list rather than a fact about the machine.
