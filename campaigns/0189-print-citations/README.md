# Print Citations

Attaching the **original print authority** to catalog facts that currently cite only IPDB.

> **This directory emits no patch `0189`.** The number is where this campaign started, not what it created. Its output is citations added to _prior_ patches.

## The problem

We've built a lot of data patches that use our DuckDB analytics foundation to mine the IPDB free text notes for information. In those patches we quote and cite IPDB, but often the IPDB note mentions that _THEIR_ original source of the information came from books like The Encyclopedia of Pinball and magazines like Billboard.

Some examples:

- /patches/0187-victory-games-kits.yaml cites IPDB, who themselves attribute all the information to particular volumes of Billboard, in a fairly regular textual formulation that would be amenable to extraction via parsing.
- /campaigns/0079-italian-makers/README.md has a corroborations.csv "ledger" of exactly these types of deferred cites.

Those print citation sources are the original source of the information. IPDB's free text is **secondary**, and it says so itself. Again and again a note records where _IPDB_ read a fact:

> 'Artists and Models' was a conversion for Chicago Coin's 1941 'Star Attraction'. [...] The earliest mention we have found for this conversion kit is in Victory Game's ad in Billboard 09/29/1945 p83.

The catalog cites IPDB. The **original authority is Billboard** — a specific issue, a specific page. [DataPatchAuthoring.md → Citing sources](../../../flipcommons/docs/DataPatchAuthoring.md) ranks a period magazine scan above any database that compiles facts from elsewhere, and tells you to follow a secondary source's own citations to the primary material. This campaign does that at corpus scale: mine the attributions out of IPDB's prose, and add the print cite alongside the IPDB one.

The same holds for books — the Encyclopedia of Pinball and the Pinball Compendium are quoted constantly in IPDB notes.

## We want to update the existing data patches

Flipcommons does not currently allow an actor to add after-the-fact citations to their previous claims. We _ARE_ working on that feature, but it will involve issuing a new ChangeSet that attaches the cites to prior claims, which makes the history messy and harder to reason about than if the citations had been added in the original ChangeSet.

So we'd rather update the existing data patches that are rewritable. The last data patch ingested on prod was `0038-model-game-formats`. We can rewrite any patch after that.

For testing this, blow the localhost dev db away, replace with `/Users/moses/dev/flipcommons/backend/db.pre-0039.sqlite3`, re-run migrations, and re-ingest data patches by using `--patches-dir` to point to this repo's patches directory. Don't save, snapshot or back up the current dev db.

## Why this is possible now

Recent enhancements make this possible now:

- **Multi-cite support**. One `cite:` can take a **list**, and every citation in it attaches to every claim the entry asserts.
- **Magazine roots are seeded**. `0041-citation-sources.yaml` declares every magazine root we think is in IPDB: Billboard, Cash Box etc, each with the `slug:` that the cite form addresses.
- **Book roots are seeded**. Every book that we think IPDB cites already has a root — Encyclopedia of Pinball Vol 1 & 2, the Compendium volumes, etc. Watch for the edition trap below.
- **Better analytics**. We have a DuckDB-based analytics layer now. See [analysis](#analysis) for the custom views already built to support this particular campaign.

If we find that we need to add new root citation sources, put them in `0041-citation-sources.yaml`. It's soon after 0038, making the citation sources available to the bulk of the mutable patches. There is already a [backlog of works needing one](#the-needs-root-backlog).

## How big is this actually? Read before scoping

**The campaign is a small fraction of the corpus, and conflating the two is the easiest way to mis-plan this work.** Three views answer three different questions, in descending size:

```bash
make analyze FILE=campaigns/0189-print-citations/citations.sql Q="FROM citation_rows;"        # every citable print reference
make analyze FILE=campaigns/0189-print-citations/citations.sql Q="FROM citation_candidates;"  # the worklist
```

| view                      | question                                                                            |
| ------------------------- | ----------------------------------------------------------------------------------- |
| `citation_rows`           | every citable print reference in `ipdb_notes`, whether or not anything can carry it |
| `citation_orphans`        | those no rewritable patch entry can carry — the [follow-up campaign](#follow-ups)   |
| **`citation_candidates`** | **the worklist**: patch entries whose own recorded quote contains the reference     |

`citation_candidates` is dramatically smaller than `citation_rows`, and that gap is the point. A citation attaches to every claim in its patch **entry**, and that entry's evidence is the quote it already recorded — so "this model is mentioned in a patch" is a much weaker predicate than "this entry's own evidence contains the print reference". `0179-gameplay-features-ipdb` is the cautionary case: it touches many of the same models, but its quotes are feature phrases while the Billboard reference sits three sentences away in the same note. Scoping by model would have targeted it; not one of its entries can carry a print cite.

`citation_candidates` also carries `patch_id`, so grouping it gives the per-patch worklist.

## What the print source actually supports

**A cite attaches to every claim its entry asserts, and the IPDB reference does not tell you which claim the print source backs.** IPDB frames these attributions several ways, and only some assert the fact:

- **`asserts`** — "Cash Box, page 85, states 'Made for the British Market'". The source asserts the proposition. Safe to attach to that claim.
- **`release` / `earliest`** — "…announced this game as a new release"; "The earliest mention we have found is in Victory Game's ad in Billboard 09/29/1945 p83". Both attest **existence by a date, and nothing more.**
- **`image`** — "…page 54, shows an NRA logo". Visual evidence; supports physical attributes.

The trap is concrete, and the conversion-kit patches are full of it — `0187-victory-games-kits` is nearly the whole candidate list. Take this note:

> 'Artists and Models' was a conversion for Chicago Coin's 1941 'Star Attraction'. [...] The earliest mention we have found for this conversion kit is in Victory Game's ad in Billboard 09/29/1945 p83.

Two sentences. The first asserts the relationship — that is IPDB's own research, unsourced. The second says only where the earliest **mention** appears. The entry asserts `model_relationship`, so attaching the Billboard cite there claims the 1945 ad identifies Star Attraction as the donor. It might; kit ads sometimes did. **You cannot tell from the IPDB text** — which is exactly the point. Note the patch's quote elides both sentences together with `[...]`, so the reference genuinely is in the entry's evidence; that is what makes it a candidate and what makes it dangerous.

So do not append the print cite to every entry by reflex. Some potential approaches:

- Attach only where the framing directly asserts the entry's claim (cheap and safe, but skips much of the conversion-kit population).
- Split with `changesets:` so the relationship keeps its IPDB-only cite while a separate changeset carries the datable fact with both cites.

`citation_framing` sizes each class and `citation_rows` carries a per-row `framing`. Treat it as a **routing hint, not a verdict** — it reads verbs in a window that crosses a sentence boundary 45% of the time, so a neighbouring sentence routinely decides the class. It is not what makes a citation safe to attach; matching the reference to the entry's own quote is.

## Analysis

Four SQL files. `citations.sql` is the entry point and the only one that `.read`s anything; each of the others answers a question the others do not and carries its own `*_checks`, so a session tuning one need not open the rest.

```bash
make analyze FILE=campaigns/0189-print-citations/citations.sql PREFIX=citation
```

Read any view with `Q=` (note the runner's `Q=` mis-parses quoted `IN (...)` lists — put a complex query in a scratch `.sql` that `.read`s this one):

```bash
make analyze FILE=campaigns/0189-print-citations/citations.sql Q="FROM citation_candidates;"
```

| file            | answers                                                                                               | self-test         |
| --------------- | ----------------------------------------------------------------------------------------------------- | ----------------- |
| `text.sql`      | where a term occurs, what sentence it sits in — vocabulary-agnostic mechanics, no notion of citations | `text_checks`     |
| `works.sql`     | which works IPDB names, whether our vocabulary is complete, what the catalog can address              | `works_checks`    |
| `locators.sql`  | what a date / page / volume looks like and how to decode one — a parser, never touches the corpus     | `locator_checks`  |
| `citations.sql` | the instances themselves, and which patch entry can carry them                                        | `citation_checks` |

### The views

| view                                 | what it answers                                                                                     |
| ------------------------------------ | --------------------------------------------------------------------------------------------------- |
| `citation_candidates`                | **the worklist** — patch entries whose own quote contains a print reference                         |
| `citation_orphans`                   | emittable citations no rewritable entry can carry ([follow-ups](#follow-ups))                       |
| `citation_rows`                      | every emittable citation in the corpus, one row per cite, with a verbatim quote                     |
| `citation_issues`                    | the distinct magazine issues to declare — **one row per `sources:` node**, slugged, named and dated |
| `citation_summary`                   | one row per work: is it seeded, root slug, ISBN, how many mentions are emittable                    |
| `citation_dropped`                   | the drop pile **with a reason** — read this before trusting the emittable count                     |
| `citation_vocab_gaps`                | citation-shaped phrases the vocabulary misses and nobody has ruled on                               |
| `citation_vocab_backlog`             | works we know we cannot cite yet, and what seeding each would unlock                                |
| `citation_shapes` / `citation_rules` | the formulations, and which patterns earn their place                                               |
| `citation_framing`                   | how emittable rows split by what the source attests — triage only                                   |

### How it's built

Declarative tables hold every pattern and every judgment: `pub_vocab` (which work an alias names), `shape_rules` (which locator part a regex matches), `book_editions` (which volume an ISBN belongs to), `vocab_review` (what we've decided about a phrase the vocabulary misses). A mention is decomposed along three **independent** axes — date, page, volume — so a formulation is a tuple of shape names rather than a bespoke regex. **Adding a phrasing is one row**, never an edit to an existing pattern.

Several tables are materialized rather than left as views (`pub_notes_src`, `pub_mentions`, `pub_mention_shapes`, `mention_resolved`, `pub_candidates`); a run costs tens of seconds because of it. That is deliberate — every answer reads the mention grain repeatedly, and as views each re-ran the whole corpus scan.

**Source text is canonicalized once**, in `pub_notes_src` via `text_norm`. Every whitespace run becomes a single character: a space, or a newline where the run contained a blank line. So `\n` means "paragraph break" and nothing else, and no run is ever longer than one character — which is what makes the sentence regexes single-character affairs instead of variable-length classes that can be consumed partially. The blank line is kept rather than flattened because it is the only thing bounding a colon-led list, which has no sentence punctuation at all. Quotes stay verifiable because `verify_quotes.normalize` collapses whitespace on both sides before comparing, and no emitted quote contains a newline.

**One drop ladder, in one place.** `mention_resolved.drop_reason` is the single emittability predicate; `NULL` means emittable. An earlier build repeated that predicate across four views and the gate, where they agreed by luck rather than construction.

### The gate, and what only it can catch

Every `*_checks` view is about **machinery health, not data opinions**: each fails when something has broken in a way that otherwise produces perfectly well-formed nonsense. The detector floors are the backstop — a silently-broken alias regex leaves every other view looking healthy, just smaller.

`works_vocab_gap_unreviewed` is the one that is different in kind. Everything else is measured _inside_ `pub_vocab`, so nothing else can tell "the corpus is this size" from "we are only looking at part of it". That check surveys citation-shaped text with no vocabulary at all and fails on anything unaccounted for. It exists because `Bingo Pinball Machines` was found by accident — it collided with an alias we already had — and that is not a search strategy.

### Fixtures are the regression suite

`locator_checks` and `text_checks` assert against **literals**, not the corpus, so they cannot be quieted by data changing underneath them. Every one records a bug this campaign actually shipped — a full month name degrading to a bare year, `pp 132, 161` truncating to `p. 132`, `Jun-39-1962` minting an issue that never existed, a quote running 917 characters through three paragraphs (a variable-length whitespace class being consumed partially — now unrepresentable rather than guarded against). If a fixture looks arbitrary, read the rule comment above it before deleting it.

**If you edit any of these files, read the comments at the site you are editing.** Nearly every regex has a silent-undermatch failure mode — a mis-grouped alias, a stem with a trailing `\b`, a month pattern that matches any capitalised word — and each produces plausible wrong output rather than an error.

## Traps

### In the source text

- **Abbreviated and full month names both appear.** IPDB writes `Aug-21-1954` and `June-17-1939`; a pattern demanding a dash after exactly three letters degrades the full form to a bare year and loses its month and day.
- **Page lists are not ranges.** `pages 78 and 83` is two pages; folding it to `78-83` claims the pages between them as evidence. There are comma forms too (`pages 1, 38, and 42`, `pp 132, 161`) that truncate to their first page unless every number is extracted.
- **The corpus contains impossible dates.** IPDB has at least one `Jun-39-1962`. Validity is treated as part of issue identity, so such a row yields no slug and lands in the drop pile — it must never mint a `sources:` node for an issue that never existed.
- **A bare year is not an issue.** Billboard was a weekly; `billboard:1940` addresses nothing a reader could check. Every such row turned out to be a parse failure with the real date sitting in the same sentence.
- **Two-digit years are deliberately unsupported.** IPDB does write `BB 4/17/43 pg 67`, but `mm/dd/yy` appears in 183 models and nearly all are manufacture dates in ordinary prose (`made on 02/20/50`). A rule would harvest those into citations and would have to invent a century to do it. That one row drops as `no parsable date` — the safe failure.
- **Datelines are too noisy to validate against — measured and rejected.** Billboard and Cash Box were Saturday-dated weeklies, but the corpus runs ~9% off-dateline, so a weekday rule would drop tens of probably-good rows to catch one known-bad one.
- **Print scans are not reachable programmatically.** worldradiohistory and ipdb.org both refuse automated fetches, and archive.org's Cash Box collection has no 1962 issues indexed — so resolving a citation against the page itself needs a human with archive access.

### Judgement calls left open

- **The ambiguity gate is conservative.** When a second publication is named inside the window _before_ the parsed locator ("Cash Box dated Feb-10-1962 page 54 and The Billboard dated Feb-17-1962 p…"), the date may belong to either, so the row is dropped. In many the first work's own date does immediately follow and the row is fine; **these are recoverable with a human read.** A work named _after_ the locator no longer condemns the row, since it cannot own a page that precedes it.
- **A book work with editions can't be cited by the work.** `isbn:` must name **one edition**, and ingest rejects an ISBN landing on a record with editions under it. `book_editions` in `works.sql` maps volume → ISBN where IPDB says which ("Vol 1", "1970-1981"); where it doesn't, the row drops rather than guessing a printing. Pinball Machines and The Complete Pinball Book have no citable edition seeded at all, which `citation_summary` shows as a NULL `root_isbn`.

### The drop pile

`citation_dropped` is one row per drop reason with a count and an example. Read it before trusting any emittable figure — the largest reasons by far are mentions with no locator at all, which is a property of IPDB's prose rather than of the detectors.

## Open decisions

### The `needs-root` backlog

`citation_vocab_backlog` lists works the corpus cites that the catalog cannot address. Each becomes citable the moment a root is declared in `0041-citation-sources.yaml`.

**Rank it by `citable`, not by `observed`.** A mention only earns a root if the surrounding text identifies an issue — for a magazine, a parsable date. Read the surrounding sentences before deciding: a phrase alone is not enough to tell a periodical from a book, or from a magazine the game was merely _named after_. Two entries were misread exactly that way before anyone looked at the sentences.

Several need domain judgment before seeding — a manufacturer house organ may or may not be a citable periodical — and two are newspapers, which would be the first newspaper roots. The European trade press is the biggest single seam, and the catalog is full of Italian and German makers whose dating evidence sits in their own trade papers, not Billboard.

Recording a verdict in `vocab_review` is how you quiet the gap check — never by narrowing a frame, which is how a coverage check stops covering.

### Rewriting safely

We are concerned we'll be touching a lot of data patches and could mess them up or drop parts of them.

We are wondering whether we might need script support for the writing. Like an update to PatchKit.

## Data patch syntax

Both magazines and books are fully documented:

- [DataPatches.md → Notes & citations](../../../flipcommons/docs/DataPatches.md) for the grammar.
- [DataPatchAuthoring.md → Magazine issues](../../../flipcommons/docs/DataPatchAuthoring.md) for the conventions.

The short version:

### A magazine issue

A magazine is the one **slug-addressed** type: no ISBN, no domain, no scheme key, so its nodes carry an authored `slug`. An issue is its own `sources:` node whose `parent:` names the magazine's slug. Declaring it is required — the cite form **never creates**, and an undeclared pair fails at dry-run.

```yaml
sources:
  - parent: billboard # the magazine root, already seeded in 0041
    slug: 1945-09-29
    name: September 29, 1945
    source_type: magazine
    year: 1945
    month: 9
    day: 29
    links: # optional; a scan benefits every later citer
      - { url: "https://books.google.com/books?id=…", link_type: archive }
```

Then cite it as `<root-slug>:<issue-slug>`, paired with the source that quoted it:

```yaml
cite:
  - ref: ipdb:3656 # the proximate source — carries the quote
    quote: "The earliest mention [...] is in Victory Game's ad in Billboard 09/29/1945 p83."
  - ref: billboard:1945-09-29 # the original authority — locator only
    locator: p. 83
```

`citation_issues` emits exactly this shape — `parent`, `slug`, `name`, `year`, `month`, `day` — one row per node, for every issue the emittable rows rest on.

### A book edition

Already seeded, so no `sources:` node — cite the ISBN directly. Same two-cite shape:

```yaml
cite:
  - ref: ipdb:3905
    quote:
      "According to the Encyclopedia of Pinball Vol 2 page 107, this game is a copy of Tura
      Automatenfabrik Gmbh's 1933 'Tura-Ball'."
  - ref: isbn:9781889933023 # the Encyclopedia volume itself
    locator: Vol. 2, p. 107
```

### Conventions that are easy to get wrong

- **A citation with no page is still a citation, and must still be emitted.** If the IPDB note names a magazine issue or a book without giving a page, add the cite with no `locator:` rather than dropping it — dropping it destroys information we have. A monthly house organ has no unit finer than its issue ("the January 1953 issue of Bally-Who, a monthly newsletter from Bally"), and a book cited by ISBN already names its volume. The catalog agrees: the overwhelming majority of its existing citation instances carry an empty locator. An earlier build required a page and silently discarded ~300 sound citations, most of them books; if you find yourself reintroducing that rule, this is why not.
- **The print cite carries no `quote:`.** We have not read Billboard 1945 — IPDB has. The honest claim is "IPDB says Billboard p83 says X", so the verbatim text stays on the IPDB cite and the print cite carries only a `locator:`. A quote here would be unverifiable by `make verify-quotes`, which has no resolver for print.
- **Locators dedup by exact text.** `p83` and `p. 83` mint two CitationInstances for one page. The convention is lowercase `p.`, a space, the number — `p. 83`, `pp. 83-84` for a range, `pp. 132, 161` for a list. The analysis normalizes to this.
- **The issue slug is an address, not data.** ISO date when dated (`1945-09-29`), year-month when the day is unknown (`1994-03`), `year-season` for a quarterly (`1986-fall`), slugified name otherwise. The `year`/`month`/`day` columns carry the date; nothing parses the slug back.
- **Archive links hang off the issue node**, not the cite. A cite's `archive:` key rides `http(s)://` refs only.

## Follow-ups

### Corroboration ledgers from earlier campaigns

`campaigns/0079-italian-makers/corroborations.csv` banks web-URL sources blocked by the same re-assertion rule. Same _shape_ of problem, different corpus and different fix — a `cite:` there is an `https:` ref resolving through `evidence.sql`, not a print locator. Deliberately out of scope here.

### Mining new claims from print-attributed prose

**`citation_orphans` — every citable print reference that no rewritable patch entry can carry.** IPDB notes holding a print-attributed fact that no patch has ever claimed. That is a different campaign from this one — this one adds evidence to claims we already made; that one would mine claims we never made — and it is more than an order of magnitude larger.

The analysis already supports it, deliberately. `citation_rows` is the whole corpus at one row per citation, each with a verbatim quote and a resolved `cite_ref`; `citation_orphans` is that minus anything this campaign will touch. Neither needs the patch layer. A follow-up should read those and **not re-derive the vocabulary, the locator grammar or the quote extraction** — that machinery is in `works.sql`, `locators.sql` and `text.sql`, and is vocabulary-agnostic where it can be.

Sizing it before starting: `citation_framing` splits by what the source actually attests. The `asserts` slice is the only one supporting a fact rather than a date, and it is a minority — so the honest scope is well below the raw orphan count.

### Promoting `text.sql`

`text.sql` is campaign-agnostic and self-tested but sits in this campaign on purpose: one consumer is not a pattern. If the orphan campaign — or any free-text campaign — copies it and its fixtures still pass against a different vocabulary, that is the evidence to move it to `scripts/analysis/` alongside `evidence.sql` The fixtures are what would justify promotion, not the genericness: writing them is what proved two of its functions wrong.

### Not covered by this analysis

`ipdb_notable_features` — a different column with its own idiom. Measured: only **16 models** mention a publication there, so the exclusion is cheap.
