# Missing years

We have a lot of models that are missing years. This is a very basic and important piece of identifying a model, to have its year.

Weirdly, IPDB's website shows years for many machines for which we do NOT have years. An example: we have no year for models/ice-castle but IPDB does. This means that our baseline information from IPDB is incomplete. We got all our IPDB info from a JSON dump, ~/dev/pinexplore/ingest_sources/ipdb_xantari.json , loaded into the pinexplore DuckDB. The year was a structured field in there but I don't know how that JSON was built... but apparently whoever created that JSON missed the year for some models.

Anyway, for plenty of our missing-year models, plenty of OTHER catalog sites have years. We need not and should not rely solely on IPDB.

We need years for as many machines as possible and I'm okay mining catalog sites.

Let's think through how to build a sweep for this.

## Option 1: Table

My first thought is to build a CSV or SQLite DB or DuckDB with data from multiple sites. Maybe a table with columns something like

model_id ⬅️ Flipcommons ID
model_slug ⬅️ Flipcommons model slug

pinside month
pinside year
pinside ID ⬅️ ID or slug or path, but definitely NOT full URL

arcade-museum.com month
arcade-museum.com year
arcade-museum.com ID ⬅️ ID or slug or path, but definitely NOT full URL

kineticist month
kineticist year
kineticist ID ⬅️ ID or slug or path, but definitely NOT full URL

I forget if there's other catalog sites we should be looking at.

I would actually like to get the IDs/slugs for these catalog sites into our system along with IPDB and OPDB IDs. Not only would this help us with data gathering, we could link to those site from the appropriate model pages.

---

## Findings (2026-08-18 analysis)

### The population

|                                      | count       |
| ------------------------------------ | ----------- |
| live models                          | 6,941       |
| **missing year**                     | **1,161**   |
| missing month                        | 2,451       |
| yearless **with** an `ipdb_id`       | 1,131 (97%) |
| yearless with no external id at all  | 30          |
| yearless with no manufacturer either | 300         |

Concentration: 300 have no manufacturer, then Bally 125, Maresa 38, Williams 37, Gottlieb 36, SIRMO 30, Automaticos 19, Splin 17 — i.e. a US-major tail plus the Spanish/Belgian/Brazilian/Italian obscurities. Bingo is over-represented: 115 of 311 bingo models are yearless vs. a ~17% base rate.

### Why IPDB's site shows years we don't have

Answered, and it is not an IPDB gap — it's an ingest gap. `ipdb_xantari.json` has **two** date carriers:

- `DateOfManufacture` — the structured field, present on 5,265 of 6,664 records. **This is the only one our ingest read.**
- `AdditionalDetails` — present on **all 6,664**, and it is verbatim the header line IPDB renders on the machine page: `IPD No. 3711 / May, 1989 / 4 Players`.

The user's example proves it exactly. `ice-castle` = IPDB 3711, `DateOfManufacture` **null**, `AdditionalDetails` = `IPD No. 3711 / May, 1989 / 4 Players`. IPDB's site shows May 1989 because IPDB's site shows _that line_.

`AdditionalDetails` parses cleanly into four buckets across the whole dump:

| bucket                           | n     | meaning                    |
| -------------------------------- | ----- | -------------------------- |
| `ymd` — `March 21, 1961`         | 842   | day-precision date         |
| `ym` — `May, 1989`               | 3,566 | month + year               |
| `y` — `1961`                     | 1,162 | **year only, explicitly**  |
| none — `IPD No. 5864 / 1 Player` | 1,094 | IPDB genuinely has no date |

Two facts that make this trustworthy: **zero** records contain a year the parser fails to extract (no unparsed remainder), and where both fields exist the parse **agrees with `DateOfManufacture` 5,265 / 5,265 — no disagreements**. The regex is not guessing; it is reading a fixed-format field.

### Tier 0 — deterministic, offline, no new evidence needed

Just re-reading the dump we already have:

|                                                               | yield                               |
| ------------------------------------------------------------- | ----------------------------------- |
| **years recovered** for currently-yearless models             | **187** (90 `ymd`, 45 `ym`, 52 `y`) |
| **months recovered** for models that have a year but no month | **307**                             |
| month present but _disagrees_ with our year                   | 7 (audit these by hand)             |

And it **finishes the January problem** that campaign 0055 left open. 0055 retracted OPDB's fake-January but noted ~403 models stayed January because IPDB's dump has the same `YYYY-01-01` year-only default underneath. `AdditionalDetails` disambiguates them, because a year-only record _says_ `1961` where a real January says `January, 1961`. Of the 475 models currently sitting at month = January:

- **350 — IPDB's own text is year-only. The January is an artifact and should be retracted** (attributed to `ipdb`, same shape as 0055).
- **125 — IPDB confirms a real January.** No patch needed; these are now positively known rather than ambiguous.

Citations cost nothing extra: `ipdb:` refs already resolve to reconstructed text that **contains the `AdditionalDetails` line verbatim**, confirmed against `make show-source` and `--check`. So `cite: {ref: ipdb:3711, quote: "IPD No. 3711 / May, 1989 / 4 Players"}` passes `verify-quote-verbatim` today.

Caveats: `ymd` day-precision truncates to month (the catalog has no day field) — 842 records' worth of precision is discarded, worth noting in the ChangeSet. The dump also carries mojibake (`Barrel O� Fun �61`); quotes must be lifted from the resolver's text, not the raw JSON.

**Do this first regardless of what else we do.** It is one generator script, no network, no AI, no judgment calls, and it shrinks every downstream tier's target set.

### Tier 1 — AI sweep over IPDB free text

After Tier 0, **944 yearless models remain that have an `ipdb_id` but no date anywhere in `AdditionalDetails`**. Of those, **708 mention at least one 4-digit year somewhere in `Notes`/`NotableFeatures`/`Source`**; 387 mention exactly one distinct year.

But raw regex on `Notes` is a trap — the years are usually about a _different_ game:

- `bamboo` → "This is a conversion of Bally's **1967** 'Orient'" (about Orient)
- `bingo-vacation` → "Keaon Corporation was founded in **2001**" (about the company)
- `berlin-or-bust` → "The slogan appeared earlier on a WWI recruiting poster from **1917**"

Tighter patterns don't rescue it: `circa` hits 80 but a third are decade-level (`Circa 1940's`, `Circa 1950's` — unusable), and "made/produced in YYYY" hits 10 and still half are about a comparand. Union of all high-precision patterns: **90 models**, and they still need reading.

So this is precisely the **AI corpus sweep** (`make sweep`, per `docs/corpus_sweep/CorpusSweepOperating.md`) — one JSONL row per model, the full IPDB `Notes` as the source note, and the deterministic gate (verbatim quote + unique target + catalog diff) doing the work regex can't. Feed the manufacturer span and lineage neighbours (below) as never-shown `hint`s. Start `--no-ai --limit 10`. Guess: 150–250 real years, with a meaningful "circa/decade only" bucket that we should be willing to leave unasserted.

### Tier 2 — the multi-site table (the doc's Option 1)

This is the right shape for the residual (~700 after Tiers 0–1), which is overwhelmingly the obscure non-US makers where IPDB is thin and Pinside/arcade-museum/tilt.it are not. Two adjustments:

1. **Sequence it third, not first.** Tier 0 costs an afternoon and removes ~190 rows plus 300 month rows from scope; more importantly it gives a **calibration set** — models where we now know IPDB's answer — to score each candidate site's accuracy against before we trust it at scale.
2. **Storing the site IDs in the catalog is right, and there's already a slot.** `models` carries `ipdb_id`, `opdb_id`, and — already — **`pinside_id`, which is 100% null across all 6,941 models**. So the column exists and has never been populated. Filling it is independently valuable (model-page outbound links) and is the join key the table needs. arcade-museum / kineticist / tilt.it would need new fields; that's a flipcommons schema question to raise before authoring.

Web-cache reality check on the candidate sites — current holdings are small, so this is real scraping work, not mining what we have: pinside 68 pages, kineticist 59, tilt.it 55, arcade-museum 28.

**One hard constraint: IPDB blocks the fetcher.** `web_fetch.py https://www.ipdb.org/machine.cgi?id=5864` → **HTTP 403**. There is no live-rescrape path to IPDB; the Feb-2025 dump _is_ our IPDB access. That makes Tier 0's completeness more important, not less.

The hardest part of Tier 2 is **matching**, not scraping — these are exactly the models with ambiguous names, no external ids, and (300 of them) no manufacturer to disambiguate on. Budget for match precision; a wrong match silently writes a wrong year into a field whose whole point is identity.

### Tier 3 — bounding, not dating

Two cheap signals that should **not** be asserted as years:

- **Manufacturer span.** Several makers have a span tight enough to pin near-exactly: FAER 1966–1966 (6 yearless), Joseph Schneider 1935–1935 (6), J. Esteban 1978–1978 (5), TSCC 1991–1991 (6), Lindstrom 1932–1934 (13), Automaticos 1966–1970 (19), Splin 1999–2003 (17), LTD do Brasil 1977–1982 (13).
- **Lineage neighbours.** 146 yearless models have at least one dated neighbour via `model_edges_bidir`; 36 share a Title with a dated sibling; only 1 has a dated `variant_of` parent.

A single-year manufacturer span is _strong_ evidence but it is our own inference over our own data, not a source — asserting it would be circular and uncitable. **Use these as sweep `hint`s and as a post-hoc QA filter** ("Tier 1/2 proposed 1954 for a maker that only operated 1966–1970 → reject"). That check is free and will catch real errors.

### Recommended order

1. **Tier 0 now** — one generator, ~190 years + ~307 months + 350 January retractions + 125 January confirmations, fully cited off `ipdb:` refs, zero network. Split into two patches (dates asserted; Januarys retracted) since they're different operations with different ChangeSet notes.
2. **Audit the 7 disagreements** by hand while Tier 0 is in flight.
3. **Tier 1 sweep** over the 944, hinted by Tier 3 bounds.
4. **Then** decide on Tier 2 with a real calibration set and a real residual count — and settle the `pinside_id`/site-id schema question with flipcommons before scraping.

### Open questions for the user

- The **300 yearless models with no manufacturer** are a distinct problem — the year is probably not findable until the maker is. Split them out of this campaign?
- **Bingo** is disproportionately yearless (115/311). `bingo.cdyn.com` is the single largest thing in the web cache at 228 pages. Worth a dedicated bingo-year pass ahead of the general Tier 2?
- Do we want to assert **decade-only / "circa"** values at all, or leave them null? The catalog has no precision field, so `1945` and `circa 1940s` would land identically.

---

## Revision: the "Never Produced" question (same session)

Two hypotheses raised: (1) that missing years are IPDB's _production_ years, absent because the game was never produced; (2) that we missed a "not produced" field in the dump. Tested both. **(1) is wrong on the main population but has a real kernel. (2) is right, and the hole is bigger than one field.**

### IPDB has _two_ labels for the same date row

The live page for Ice Castle reads `Project Date: May, 1989` / `Production: Never Produced`. Pulling archived captures for three machines gives the pattern:

| IPDB | machine      | date row                                                                              | Production row            |
| ---- | ------------ | ------------------------------------------------------------------------------------- | ------------------------- |
| 3711 | Ice Castle   | `Date Of Manufacture: May, 1989` _(2018 capture; live page now says `Project Date:`)_ | `Never Produced`          |
| 3    | Acapulco     | `Project Date: March 21, 1961`                                                        | _(no Production row)_     |
| 125  | Baby Pac-Man | `Project Date: October 11, 1982`                                                      | `7,000 units (confirmed)` |

**Baby Pac-Man settles it: `Project Date` is not a never-produced marker.** 7,000 units, confirmed, and still labelled Project Date. IPDB uses that label when its date comes from the manufacturer's internal project/design log rather than a shipping record — which is exactly why the 305 "header date but no `DateOfManufacture`" records are **210 Bally, 34 Williams, 31 Gottlieb**: the big three are the makers whose factory project logs IPDB holds.

**So the real mechanism is one level upstream of where I put it.** The dump builder mapped only rows labelled `Date Of Manufacture:` into the `DateOfManufacture` field and dropped `Project Date:` rows to null — while the page header line (`AdditionalDetails`) carries the date under either label. That's the whole story of the 305, and Tier 0 recovers them correctly.

**Hypothesis 1, verdict:** not the explanation. IPDB publishes May 1989 for Ice Castle _despite_ Never Produced. And the ~1,094 records with no date anywhere carry never-produced prose at **2.8%** — _below_ the 4.0% base rate. Those are obscure makers IPDB simply can't date, not suppressed production years.

**The kernel that is real:** among the 305 `Project Date` records, never-produced/prototype prose runs **26.2%** vs. a 4.0% base rate — 6.5×. Not because the label means never-produced, but because a never-produced game can _only_ ever have a project date. Which raises a genuine editorial question for Tier 0: for a game that was never produced, is `Project Date` a `year`? It is a design/intent date, not a manufacture date. **We can now decide this per record, because the archived page carries the label.**

### Hypothesis 2, verdict: correct, and it's a whole missing field

Not a miss on our side — **the dump has no production-status field at all.**

- The string `Never Produced` appears **0 times** in the entire 6,664-record dump.
- `ProductionNumber` is **100% numeric** (1,451 populated). It is the quantity parsed out of `Production: 7,000 units (confirmed)`. When the row reads `Never Produced`, the builder wrote **null** — indistinguishable from "quantity unknown."
- `explore.duckdb`'s `compare_models_ipdb.ipdb_production` is just `ProductionNumber` re-exposed. Red herring; it's a count, not a status.

So **every never-produced game IPDB knows about is invisible to us.** Our catalog carries only 112 `unreleased` (72 of them yearless) out of 6,941, with 6,688 at `production_status` NULL — and NULL currently means "never asked," not "produced."

And it isn't only Production. Acapulco's page carries a **`Specialty:`** row (IPDB's Add-A-Ball / woodrail / etc. classifier) that has no field in the dump either. The dump is a lossy projection of the page, and we've now caught it dropping at least three things: `Project Date`-labelled dates, `Production` status, and `Specialty`.

### The recovery path: archive.org serves what ipdb.org refuses

`ipdb.org` returns **HTTP 403** to our fetcher. **web.archive.org returns 200** — I fetched three machine pages successfully, and they render the full row table including the date label, `Production:`, and `Specialty:`.

Wayback CDX coverage for `ipdb.org/machine.cgi*`:

|                                      | count                    |
| ------------------------------------ | ------------------------ |
| distinct IPDB ids with a 200 capture | 6,297                    |
| ∩ our models carrying an `ipdb_id`   | **6,277 of 6,664 (94%)** |
| ∩ our **yearless** models            | **968 of 1,131 (86%)**   |
| yearless with no archived capture    | 163                      |

That reframes the whole plan. A one-time archive.org harvest of ~6,300 pages (batchable via `web_fetch.py --from-file`, and it lands in the web cache as durable citable evidence) recovers, in one pass:

- the **date row and its label** — settling every Tier 0 record's `Project Date` vs `Date Of Manufacture` question
- **`Production:`** — the never-produced status for the whole corpus, a field we have essentially none of
- **`Specialty:`** and anything else the dump projected away
- and a **citable `https:` web-cache page per model**, stronger than the reconstructed `ipdb:` ref

Caveats: captures are undated snapshots of varying vintage (Ice Castle's was 2018 and shows the older label), so the harvest records the capture timestamp and we treat it as evidence-as-of-then; and the 163 yearless models with no capture still need Tier 2.

### Revised order

1. **Harvest archived IPDB pages first** (~6,300, one batch, no AI). It is the cheapest single action available and it subsumes most of Tier 0's open questions rather than deferring them.
2. **Tier 0 off the harvest, not the dump** — same ~187 years and ~307 months, but now each one carries its IPDB label, a real `https:` cite, and a production status alongside.
3. **A production-status patch** — genuinely new catalog data, arguably worth more than the years. Needs a decision on what `production_status` NULL should mean once we can distinguish "never produced" from "unknown."
4. Then Tier 1 sweep → Tier 2 site table, as before.

### Added open questions

- For a **never-produced** game, do we want IPDB's `Project Date` in `year` at all? Or `year` + `production_status: unreleased` together, letting the status qualify the date?
- IPDB's **`Specialty`** row does not fold into one concept — see the sample below; it spans game_format, tags, and gameplay_features at once. Which of the three should absorb which values?
- `production_status` NULL currently spans "never asked" and "produced, unremarkable." Post-harvest we could assert `produced` positively for the ~1,451 with a confirmed unit count. Worth it, or noise?

### What `Specialty` actually is (13-page archive sample)

`Specialty:` is a row on the IPDB machine page holding one or more glossary terms, each linking to IPDB's own definition (`Bingo Machine [?]`). The vocabulary is `ipdb_glossary` in `explore.duckdb` — already loaded, 339 terms — but the per-machine _assignments_ are not: the glossary's `games` column is populated for exactly one term (`woodrail`), so the assignments only exist on the pages.

A 13-page archive sample, showing `Specialty` fill at roughly **6/13**:

| IPDB | our slug           | Specialty                    | Production              | date row                                 |
| ---- | ------------------ | ---------------------------- | ----------------------- | ---------------------------------------- |
| 3    | acapulco           | Bingo Machine                | —                       | Project Date = March 21, 1961            |
| 250  | big-guns           | Mechanical Backbox Animation | 5,250 units (confirmed) | Date Of Manufacture = September 28, 1987 |
| 1286 | james-bond-007     | **Widebody**                 | 3,625 units (confirmed) | Date Of Manufacture = October, 1980      |
| 3169 | hyperball          | Not A Pinball, Flipperless   | 5,000 units (confirmed) | Date Of Manufacture = December 30, 1981  |
| 3585 | zodiac-2           | Bingo Machine                | —                       | Project Date = October 12, 1966          |
| 3711 | ice-castle         | —                            | **Never Produced**      | Date Of Manufacture = May, 1989          |
| 4935 | gold-mine-3        | Not A Pinball                | —                       | Date Of Manufacture = 1988               |
| 5402 | showdown-2         | —                            | **Never Produced**      | —                                        |
| 6206 | deadville-one-ball | Bingo Machine                | —                       | —                                        |

Three things fall out:

1. **It is multi-valued and cross-cutting.** `Bingo Machine` / `Not A Pinball` / `Flipperless` are game_format questions; `Mechanical Backbox Animation` is a gameplay_feature; **`Widebody` is a tag** — and `CorpusSweepOperating.md` names widebody explicitly as a planned sweep target. IPDB has been carrying it structurally the whole time.
2. **Where we already have a `game_format`, IPDB agrees** — acapulco / zodiac-2 / deadville-one-ball are all `bingo-pinball` here and `Bingo Machine` there. That is a clean validation of campaigns 0010/0011/0172/0173/0175, and it means the harvest can extend that hand-built work rather than contradict it. We currently have a `game_format` on only **737 of 6,941** models.
3. **`showdown-2` is the shape of the whole problem in one row** — Never Produced, no date row at all, and yearless in our catalog. For that model the year may simply not exist to be found.

Sample caveat: 13 pages, hand-picked to span formats, so the ~46% fill rate is indicative only.

---

## The harvest plan

**This section supersedes the tier sequencing above.** The earlier tiers were written before we knew archive.org served IPDB; the free dump-mining work (Tier 0) still stands exactly as described, but everything downstream of it reorganizes around the harvest.

### Shape: one long table, not a wide one

The doc's Option 1 sketched a wide table (`pinside_year`, `pinside_month`, `pinside_id`, `arcade_museum_year`, …). Go **long** instead — one row per observation:

```text
model_id · model_slug · site · site_ref · label · value · capture_ts · source_url
```

Three reasons, all learned the hard way in this session:

1. **The label set is open and we keep finding more.** A 13-page sample found `Specialty`; widening to 22 turned up `Concept by` and `Easter Eggs`, each appearing exactly _once_. There is certainly a tail below that floor. A long table absorbs a new label as rows; a wide table needs a migration per discovery.
2. **`Date Of Manufacture` and `Project Date` are one slot with two labels, not two fields.** Across 22 pages: 16 carry one, 3 carry the other, **0 carry both**, 3 carry neither. Storing the label as data keeps the distinction — which is exactly the distinction that explains the whole missing-year bug — instead of forcing a column name that discards it.
3. **Each observation needs its own capture timestamp.** Wayback captures range from 2018 to 2025 in the sample, and IPDB relabels rows over time (Ice Castle's 2018 capture says `Date Of Manufacture`; the live page says `Project Date`). An observation is a claim-as-of-a-date, and the table should say so.

Pivot to wide for eyeballing and for the three-way cross-reference against the xantari dump and the flipcommons analytics foundation.

### IPDB field inventory

Confirmed present on the page and **absent from the xantari dump**:

| field                    | seen in 22-page sample | note                                                                                       |
| ------------------------ | ---------------------- | ------------------------------------------------------------------------------------------ |
| `specialty`              | 12                     | multi-valued; cuts across game_format / tag / gameplay_feature                             |
| `production`             | 11                     | `Never Produced` or `N units (confirmed)` — the status half is 100% absent from the dump   |
| `project_date`           | 3                      | the missing-year root cause                                                                |
| `owners_list_url`        | 6                      | not in the user's list; cheap to carry                                                     |
| `concept_by`             | 1                      | **an 8th credit role** — the dump carries only 7, so some credits are missing catalog-wide |
| `easter_eggs`            | 1                      | external link                                                                              |
| `serial_number_database` | 20                     | boilerplate IPSND link; probably derivable, low value                                      |

In the dump but **never ingested** (no scraping needed — these are a re-read of a file on disk):

| field                | dump fill    |                                                      |
| -------------------- | ------------ | ---------------------------------------------------- |
| `additional_details` | 6664 (100%)  | the only 100%-fill field that went nowhere           |
| `photos_in`          | 3104 (46.6%) | print citations                                      |
| `source`             | 2541 (38.1%) | IPDB's own provenance tag (sample value: `pictures`) |
| `average_fun_rating` | 899 (13.5%)  | not in the user's list; plausibly a deliberate skip  |

**On "year / month announced": there is no such field.** Every row label matching `date|announc|release|ship|introduc` across the 22-page sample resolves to exactly two — `Date Of Manufacture` (16) and `Project Date` (3). The string "announce" does not appear anywhere on any sampled page, including in Notes prose. The long-table shape means that if the harvest turns one up in the tail, it costs nothing to absorb — so carry the expectation, but don't design a column for it.

### The other catalog sites

All three are in the Wayback Machine with real depth:

| site          | 200 captures | distinct machine entities | key shape                                           |
| ------------- | ------------ | ------------------------- | --------------------------------------------------- |
| arcade-museum | 35,939       | **20,695** `game_id`s     | numeric `game_detail.php?game_id=N`                 |
| kineticist    | 33,485       | 2,702 slugs               | `/pinball-machines/<slug>`, `/games/pinball/<slug>` |
| pinside       | 16,369       | 3,184 slugs               | `/pinball/machine/<slug>`                           |

But coverage of the _target_ population is far thinner than headline coverage — these sites index what collectors care about, and yearless obscurities are what they don't:

| population                         | pinside | kineticist |
| ---------------------------------- | ------- | ---------- |
| all models (6,941)                 | 43%     | 20%        |
| yearless (1,161)                   | 25%     | 9%         |
| yearless with a manufacturer (861) | **30%** | **10%**    |

(Naive slug match — a rough floor, with some false positives.) **Verdict: pinside is worth harvesting; kineticist at 10% is not, on its own.** arcade-museum is unmeasured because it is keyed by opaque numeric id — establishing name→`game_id` needs an index crawl first, and on a video-arcade-first site with 20,695 entities that is its own sub-project. Do it after pinside proves the pipeline, not before.

We already hold a small amount of all of these in the web cache (pinside 68 pages, kineticist 59, tilt.it 55, arcade-museum 28) — enough to sanity-check extraction, nowhere near enough to mine.

### Batching

Filter: **yearless AND has a manufacturer** = 861 models. Budget:

|                                                   | n       |
| ------------------------------------------------- | ------- |
| solved free from the dump, no scraping            | **182** |
| need scraping, IPDB capture exists                | **560** |
| need scraping, no IPDB capture (other sites only) | 99      |
| no `ipdb_id` at all (other sites only)            | 20      |

**Do not order batches by manufacturer model count.** That was the working assumption and it is actively counterproductive: it puts Bally, Gottlieb and Williams first, and those are precisely the `Project Date` makers whose yearless models are _already free from the dump_.

| manufacturer | models | yearless | free from dump | needs scraping |
| ------------ | ------ | -------- | -------------- | -------------- |
| Bally        | 762    | 125      | **98**         | 25             |
| Gottlieb     | 702    | 36       | **31**         | 5              |
| Williams     | 522    | 37       | **32**         | 5              |

The three largest manufacturers in the catalog yield **15 models** of scraping value between them.

**Order by models-needing-a-scrape, and read the density column:**

| manufacturer               | models | yearless | % yearless | needs scrape |
| -------------------------- | ------ | -------- | ---------- | ------------ |
| Maresa                     | 56     | 38       | 68%        | 38           |
| SIRMO Games S.A.           | 63     | 30       | 48%        | 30           |
| Bally                      | 762    | 125      | 16%        | 25           |
| Splin S.A.                 | 23     | 17       | **74%**    | 17           |
| Automaticos                | 29     | 19       | 66%        | 14           |
| LTD do Brasil              | 20     | 13       | 65%        | 12           |
| Petaco                     | 51     | 12       | 24%        | 11           |
| J. Martina                 | 19     | 11       | 58%        | 11           |
| Lindstrom Tool and Toy Co. | 27     | 13       | 48%        | 10           |
| R.M.G.                     | 21     | 11       | 52%        | 8            |
| Fipermatic                 | 11     | 11       | **100%**   | 8            |
| Playmatic                  | 74     | 8        | 11%        | 8            |
| Keeney                     | 126    | 11       | 9%         | 8            |
| Irmacor                    | 8      | 8        | **100%**   | 7            |
| T.H. Bergmann              | 18     | 7        | 39%        | 7            |

Density beats raw count as a signal. Fipermatic and Irmacor are _entirely_ undated; Splin is 74%, Maresa 68%. Those are coherent research targets where one good Spanish / Brazilian / Belgian source plausibly fixes a whole manufacturer at once — which is how the Italian tilt.it campaign (0079–0110) already worked.

**Proposed first batch: Maresa + SIRMO + Splin = 85 models.** Big enough to prove the harvest → extract → cross-reference → patch pipeline end to end, small enough to throw away if the shape is wrong.

### Cross-referencing

Three-way, per the user's framing:

1. **vs. the xantari dump** — the calibration set. For the ~5,265 models where the dump has a `DateOfManufacture`, the harvest should reproduce it. Any disagreement is either a bad extraction or a real IPDB revision since Feb 2025; both are worth seeing, and the rate is the trust metric for everything else the harvest asserts.
2. **vs. the flipcommons analytics foundation** — what the catalog already believes, so the patch emits only genuine diffs.
3. **vs. pinside / arcade-museum** — independent corroboration for the residual, where IPDB is silent.

The Tier 3 bounds (manufacturer operating span, lineage neighbours) stay what they were: a free QA filter, not an assertion source. A harvested year outside its maker's known span is a rejection signal.

### Still open

- The 300 yearless models **with no manufacturer** are excluded by this filter and remain the single largest bucket. Their year is probably not findable until the maker is; they likely need their own campaign.
- `production` status is arguably worth more than the years and falls out of the same harvest for free — but it needs a decision on what `production_status` NULL should mean once "never produced" is distinguishable from "never asked."
- `concept_by` implies the credits ingest is short a role catalog-wide. Independent of this campaign, worth its own check.
- Getting harvested fields into `model.extra_data.ipdb.*` is **parked** — patches can technically park EXTRA claims, but the design intent is a separate ingest, and that is not where the value is right now. Live fields first.

---

## Batch 1 result: Maresa + SIRMO + Splin (85 models) — the harvest does not work for this population

Harvested 84 of 85 (one fetch failed despite having a capture; retryable). **Decisive negative result.**

### Zero years

|                                |             |
| ------------------------------ | ----------- |
| models cross-referenced        | 84          |
| **years recovered**            | **0**       |
| conflicts with catalog         | 0           |
| pages with any date row at all | **0 of 85** |
| Production status recovered    | **0**       |

This is not an extraction failure — it was checked against raw page text, not the parser: **the strings `Date Of Manufacture` and `Project Date` appear zero times across all 85 cached pages.** IPDB simply has no date for any of these machines, and the xantari dump was _faithful about that absence_. The archived page adds nothing a re-read of the dump wouldn't.

That kills the premise for this population. The harvest recovers dates only where the dump's `DateOfManufacture` was null but IPDB _did_ publish one under the `Project Date` label — and that population is Bally / Williams / Gottlieb, whose yearless models are **already free from the dump** via `AdditionalDetails`. For the obscure European and Brazilian makers the two sources agree: nobody knows.

**Practical consequence: do not harvest archive.org for years.** The remaining ~560 "needs scraping" models were scoped on the assumption IPDB might know. On this evidence it does not. Years for that population have to come from national/specialist sources (the tilt.it model from campaigns 0079–0110) or from inference, not from IPDB in any form.

### What the harvest _did_ deliver

| label                                                        | fill (of 84) |
| ------------------------------------------------------------ | ------------ |
| Manufacturer, Serial Number Database, Average Fun Rating     | 100%         |
| Type                                                         | 99%          |
| Notable Features                                             | 90%          |
| Notes                                                        | 88%          |
| Source                                                       | 86%          |
| **Specialty**                                                | **62%**      |
| Theme                                                        | 50%          |
| Photos in / Marketing Slogans / Model Number / Documentation | 1% each      |

`Specialty` against our existing `game_format`:

|                                               | n     |
| --------------------------------------------- | ----- |
| agrees with our `game_format`                 | 46    |
| **new — Specialty present, no `game_format`** | **6** |
| we have a format, page has no Specialty       | 1     |
| neither                                       | 32    |

46 clean agreements is a good validation signal for the hand-built bingo work. The 6 new ones are `Mechanical Backbox Animation` (×5) and `Zipper Flippers` (×1) — note these are **gameplay_feature / tag** territory, not `game_format`, which confirms `Specialty` cannot be mapped to a single catalog concept.

### The real dating signal for this population is in the Notes, and it is a bound not a date

34 of 74 Notes mention a year, and almost all take one shape:

- `dakota-ii` — "Backglass is identical to Maresa's **1972** 'Dakota' except…"
- `big-brave-maresa` — "This game is a copy of Gottlieb's **1974** 'Big Brave'…"
- `centigrade-37-2` — "Replica of Gottlieb's **1977** 'Centigrade 37'…"
- `royal-flush-4` / `flush` — "Both are copies of Gottlieb's **1976** 'Royal Flush'…"

Every one of those years belongs to a _different machine_. What they give is a **lower bound** — a Maresa clone of a 1974 Gottlieb cannot predate 1974, and in practice Spanish clones followed within a few years. That is real, citable evidence, but it is an inference, not a date, and a regex would read it as a date. This is squarely AI corpus sweep territory (`make sweep`), with the relationship as the unit of judgment rather than the year.

One Note is worth quoting for what it says about the ceiling here — `surfer-maresa`: "The owner of the game pictured here did not find a copyright date anywhere on/in the game." IPDB has looked and does not know.

### Pipeline lessons (both real bugs, both now fixed in the harness)

1. **A title can be a four-digit number.** Maresa's game is literally named **2002**; the page header reads `2002 / IPD No. 4632 / 1 Player`, and the first header parser read the title as a year — the batch's single "recovered year" was this false positive. Header parsing must only consider segments _after_ the `IPD No. N` marker.
2. **`Specialty` terms are space-separated, not delimited.** The raw value `Bingo Machine One Ball Game Payout Machine` is three glossary terms run together. It cannot be split on a delimiter; it has to be matched against the `ipdb_glossary` vocabulary (already in `explore.duckdb`, 339 terms), longest-first.
3. **`web_fetch.py` exits 0 on failure.** A first pass reported 85/85 fetched while actually landing 10 pages — archive.org had rate-limited us with `Connection refused`. Success has to be detected by parsing output for `fetched [200]`, and the harvest needs pacing (~3s) plus backoff retries.
4. Fetching the **exact CDX capture timestamp** rather than `/web/2024/` avoids a redirect round-trip and is materially more reliable.

### Revised verdict

- **Tier 0 (dump `AdditionalDetails`) is still the whole cheap win: ~187 years, ~307 months, 350 January retractions.** Nothing in this batch changes it, and it needs no network.
- **The archive.org harvest is decoupled from the year problem.** Its value is `Specialty` / `Production` / `Concept by` enrichment across the _popular_ corpus — worth doing on its own merits, not as a year strategy.
- **Years for the obscure ~560 need national sources or inference.** Before scoping that, measure pinside/arcade-museum coverage of a _specific_ maker (Maresa, 20 of 38 pinside-matched) rather than the population average.

---

## Update: the parse now lives upstream

`ipdb_machine_additional_details` (pinexplore, `04_staging.sql`) parses the header date out of `AdditionalDetails`, and `ipdb_machines_staged` carries the result. **Tier 0 should read that view, not re-parse the dump.**

It reproduces every Tier 0 figure independently, off a differently-written parser:

|                                     | ad-hoc parse (this doc, above) | `ipdb_machine_additional_details` |
| ----------------------------------- | ------------------------------ | --------------------------------- |
| dump rows with a parsed year        | 5,570                          | **5,570**                         |
| …with a month                       | 4,408                          | **4,408**                         |
| …with day precision                 | 842                            | **842**                           |
| years recoverable (yearless models) | 187                            | **187**                           |
| months recoverable                  | 307                            | **307**                           |
| bogus Januarys                      | 350                            | **350**                           |
| real Januarys                       | 125                            | **125**                           |

New detail the view surfaces: of the 187 recoverable years, **135 carry a month** and **90 are day-precision**. Our schema has no day field, so those 90 truncate to month on the way into a patch — the ChangeSet note should say so.

Three reasons it is the better base:

- **Full-string anchored** (`^IPD No\. (\d+)…$`) rather than segment-scanning. Note the batch-1 title-as-year bug came from the _page header_ (`2002 / IPD No. 4632 / 1 Player`), which carries the title; the dump's `AdditionalDetails` does not, so the view was never exposed to it. Keep that in mind if the view is ever pointed at harvested page headers.
- **Day precision kept in its own column**, so the truncation is a deliberate choice at patch time rather than a loss at parse time.
- **A redundancy tripwire** — `additional_details_ipd_no` and `additional_details_players` are carried precisely because they duplicate `IpdbId`/`Players`, so a capture-group slip makes them disagree (asserted in `05`). That is the guard against a silent regex regression writing wrong years into the catalog, which is the worst failure mode this campaign has.

Tier 0 is now a generator over a typed view rather than a parsing exercise.

---

## Resolution: the recovered dates are Project Dates, and they get their own field

### Confirmed, from IPDB's own explanation

IPDB's Jay posted the rule directly ([Pinside topic 215548](https://pinside.com/pinball/forum/topic/display-of-ipdb-project-dates-and-manufacture-dates)), and it settles the question this campaign kept circling:

> Project Dates (aka Design Dates)

The display rules, as stated there:

1. Listing has **only a Project Date** → shown in the header, and in the body labelled `Project Date`.
2. Listing has **only a Manufacture Date** → shown in the header, and in the body labelled `Date Of Manufacture`.
3. Listing has **both** → both in the body; the **header always shows the Manufacture Date**. (Before ~2018 the header always showed the _Project_ Date — which is why pre-2020 Wayback captures disagree with the Feb-2025 dump.)

Jay's three worked examples, checked against the dump, match exactly:

| IPDB           | per the post            | dump `DateOfManufacture` | dump `AdditionalDetails`   |
| -------------- | ----------------------- | ------------------------ | -------------------------- |
| 1930 Red Arrow | only a Project Date     | **None**                 | `… / October 02, 1934 / …` |
| 17 Action (Jr) | only a Manufacture Date | `1934-12-01`             | `… / December, 1934 / …`   |
| 987 Gator      | both                    | `1969-06-01`             | `… / June, 1969 / …`       |

Independently, across 152 cached IPDB pages: pages labelled `Project Date` have a dump date **0 / 41** times, and pages labelled `Date Of Manufacture` on a capture contemporaneous with the dump (2020+) have one **10 / 10** times. A 45-model sample drawn from the 187 themselves reads **84% `Project Date`**, with every exception a pre-2018-change capture.

**The rule: the dump's `DateOfManufacture` is populated if and only if IPDB holds a Manufacture Date.** A Project-Date-only listing arrives with a null date and the date surviving only in the header line — which is `AdditionalDetails`, which we never ingested.

So the 187 need no page harvesting to classify. `DateOfManufacture IS NULL AND additional_details_date_year IS NOT NULL` **is** the definition of "IPDB has only a Project Date."

### Why this matters: the gap is years, not rounding

From the post: _"a Bally game manufactured in 1978 but with a Project Date of 1976 would appear with games manufactured in 1976."_ A project date can precede manufacture by ~2 years. Writing these into a production-date field would have been a real error, not a technicality.

### Where they go

Flipcommons is building exactly the right home for them (`docs/plans/catalog_data_model/ModelProjectDate.md`): new claim-controlled `project_year` / `project_month`; existing `year`/`month` renamed to `production_year` / `production_month`; and a derived, read-only, non-claim-controlled `year`/`month` that falls back to the project date when there is no production date.

That resolves the campaign's original goal without semantic corruption: the 187 get `project_year`, production stays null, and the derived `year` falls back — so they read as dated models on the site while the catalog still records what the date actually is.

|                                                              | n       |
| ------------------------------------------------------------ | ------- |
| `project_year` assertable                                    | **187** |
| …also carrying a month → `project_month`                     | **135** |
| …where IPDB has day precision (discarded; year+month schema) | 90      |

Per the user's instruction, the day precision is preserved as **evidence rather than prose**: each claim cites `ipdb:<id>` quoting the full `AdditionalDetails` line verbatim (e.g. `IPD No. 3 / March 21, 1961 / 1 Player`), which carries the day even though the field cannot. Confirmed quotable — `make show-source ARGS="ipdb:3711 --check '…'"` passes.

**One validation of the flipcommons migration assumption.** That plan states "all the existing dates in the database are production dates." For IPDB-sourced years that is verifiably true, by the same rule above: no project date has ever reached the existing `year` column via IPDB, because the dump never carried one. The rename is safe on that axis.

### Status: unblocked

The flipcommons rename is done on branch `feat/model-project-date` (uncommitted at time of writing). Flippatch itself needs no change to proceed — `schema/patch.schema.json` leaves `additionalProperties` unset on the claim blocks, so `project_year` / `project_month` validate today.

One small gap worth closing while the work is fresh: `year` and `month` are declared there against `yearValue` (integer, 1800–2100) and `monthValue` (integer, 1–12), and that typing is load-bearing — the schema's own note explains that a string-typed year never equals the integer the same year carries elsewhere, so duplicate detection misses it and cross-source comparison silently finds no match. `project_year` / `project_month` currently get no such check. Adding them to the typed properties (and renaming `year`/`month` → `production_year`/`production_month`) restores it.

### What is NOT in scope

Deliberately dropped, and not to be revived without a separate decision:

- Changing years on models that already have one — including the IPDB-over-OPDB question (111 candidates) and the 6 conflicts carrying patch-set years.
- The January retractions. The evidence for them stands on its own (IPDB renders a year-only date as `1975` and a real January as `January, 1961`; 125 confirmed real), but the attribution was never verified and it is a separate campaign.
- The archive.org harvest, which [batch 1 showed](#batch-1-result-maresa--sirmo--splin-85-models--the-harvest-does-not-work-for-this-population) recovers no years for the obscure-maker population.

### Next step

Author one patch asserting `project_year` (187) and `project_month` (135) from `ipdb_machine_additional_details`, attributed to `ipdb`, each claim citing `ipdb:<id>` with the full `AdditionalDetails` line as the verbatim quote. Generated with `patchkit`, never hand-rolled YAML. Nothing built yet.
