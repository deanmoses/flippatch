# Model Page Extraction — Authoring Loop

This is the how-to for a **master (authoring) session** using the AI page extractor to pull a pinball model's data out of an unstructured source page. It is the operator's guide — distinct from [ModelPageExtractionChecklist.md](ModelPageExtractionChecklist.md) (the field-by-field _vetting_ reference) and [the plan](../plans/AiPageDataExtractor.md) (the architecture). Read this to drive the loop; read the checklist to vet a field.

The one thing to internalize first: **the extractor raises recall; it does not decide what is true.** It hands back _candidate_ claims with verbatim-checked quotes. **You are the arbiter** — you dispose of every candidate against the full page before anything reaches a patch. The packet is candidates, never facts.

## Before you start

- **Localhost only.** It needs the pinexplore web cache, the flipcommons dev DB (`../flipcommons/backend/db.sqlite3`), and `ANTHROPIC_API_KEY`. It cannot run from a web session.
- **The page must already be in the pinexplore web cache.** The extractor _reads_ the cache; it does not fetch. Pull the page first with `web_fetch.py <url>` in pinexplore (see `../pinexplore/docs/WebCache.md`).
- **Unstructured sources only.** This tool is for free text (reviews, maker pages, blogs, IPDB free-text Notes). Structured IPDB/OPDB columns (Manufacturer, Type, Players, Theme, date) are deterministic data — resolve them directly, never through the AI. An `ipdb:` ref deliberately yields only its free-text Notes / Notable-Features, never the structured columns.

## 1. Run it — one packet per page

```sh
make extract-page ARGS="<source-ref> --target '<model name>' --maker '<maker>'"
```

- **`source-ref`** — an `http(s)` URL, or an `opdb:<id>` / `youtube:<id>` / `ipdb:<id>` scheme ref.
- **`--target` / `--maker`** — the model this run is about and its manufacturer. **Always pass these, and treat them as mandatory on maker-index / whole-lineup pages.** Framing _reduces_ cross-machine leakage but does **not** prevent it — a sibling's fact can still come back attributed to your target with `quote_verified: true`, so the disposal step (§3) has to catch it. (`--maker` sharpens disambiguation; `--note "<instruction>"` injects a per-run hint like `ignore the sidebar's related-games list`.)
- **One packet per page.** A model with several source pages is run **once per page**; you union the packets yourself. Never combine pages into a single call — they would share a satisficing budget and recall drops.
- **Sampled slices vary run to run.** Themes, gameplay features, and credits sample and union, but `lineage`, `year`, `franchise`, and the catch-all (`other`) are single-read — a candidate can appear in one run and not the next (the catch-all is the most volatile). For thorough authoring, run the page **twice and union the packets**.
- **Heed the ref/target banner (stderr, before the packet).** For an `ipdb:` / `opdb:` ref with `--target`, the tool resolves the ref by its external id and diffs it against the target name, printing a warning or note if they diverge — because IPDB splits EM/SS (and other variants) into separate records, so a ref can name a _different_ machine than the name you passed. A `note:` that your target is ambiguous and the ref pins one record tells you **which** record the candidates describe; a `warning:` that the ref and name disagree (or that the ref id isn't in the catalog) means stop and confirm which model you are authoring — the candidates may otherwise land on the wrong record, or flag a model the catalog is missing.

The packet prints to stdout as a **compact view** by default: the `candidates`-state fields in full, the empty states collapsed to a coverage tail. Pass `--verbose` (`-v`) for the full JSON — you rarely need it, since the compact view keeps every candidate and its evidence and only drops the scaffolding around empty fields.

## 2. Read the packet

Top level: `source_ref`, `page_metadata`, and `fields`. `page_metadata` (`last_updated`, `content_type`, `rendered`, `title`) is a **text-quality signal** — a thin, JS-rendered page yields lower-quality text; weight its candidates accordingly. `last_updated` is the _page's_ date, not the game's — a hint for the year, never a candidate.

Every field is in one of three states:

| State            | Meaning                                                                | What you do                                                             |
| ---------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `candidates`     | a slice found one or more values                                       | vet each against the full page (step 3)                                 |
| `checked-absent` | a slice looked and the page says nothing                               | the page likely lacks this; do **not** backfill a catalog default       |
| `not-checked`    | no slice covered the field (a deferred field, or every sample errored) | not the same as absent — nobody looked; check it yourself if it matters |

Each candidate carries `value`, `quote`, `source_ref`, `quote_verified`, plus slice-specific keys flattened alongside them — `related` (lineage), `role` (credit), `count` (gameplay feature), `month` (year), or `quote_unverified_reason`. **`quote_verified: false`** means the quote did not check out verbatim in the source — treat it as a weak lead, never author on it.

The compact view puts the `candidates`-state fields first (each candidate printed in full as a one-line JSON object), then the coverage tail: a `checked-absent` line, a `not-checked` line, and — when a slice errored or a sampled slice lost some samples — a **`gaps`** section listing those fields with `⚠` and the reason. The gaps section is the one part of the tail to read closely: an errored or partially-failed slice is a coverage hole (nobody, or not everybody, looked), not a real absence, so re-run the page if a field you care about lands there. `--verbose` restores the full per-field JSON if you need the sample tallies or slice labels on the empty fields.

## 3. Dispose — the non-negotiable rule

**Vet every candidate against the _whole page_, never the quote alone.** A verbatim quote can be inverted by its surroundings — _"its companion model is a widebody"_ is a real quote that does not make _this_ machine a widebody. Partial context destroys meaning, so the vet is always against full context.

Three things `quote_verified` does **not** tell you — check each yourself as you dispose:

- **Whose fact is it?** `quote_verified: true` proves the quote is on the page, **not that it is about your target.** On a maker-index or whole-lineup page a sibling's fact leaks in with a verified quote — e.g. a `home-use` tag whose quote is really about the machine one row down. For every candidate on such a page, read the quote's own line/row and confirm it names the **target**, not a sibling; drop it if it doesn't.
- **Is the evidence just the name?** A candidate whose only quote is the model's own name is **nominal evidence**, not a stated fact — `theme: Jungle` evidenced solely by the title _"Jungle Life"_ is a guess from the name, however plausible. Confirm it against the page's prose and decide knowingly (deriving a theme from the name is sometimes fine, but it is not the same as the page stating it).
- **Did a qualifier get dropped?** The year slice returns a bare number, so an adjacent hedge — `(?)`, `circa`, `ca.`, `~`, `[presumed]` — is lost unless you catch it. If the source hedges the date, carry the hedge into the patch `note:`; don't launder it into a clean year.

## 4. Prune the known over-fires

The fan-out over-includes **by design** — a false include is cheap to drop, a miss is the failure the tool exists to end. So over-inclusion is correct behavior, not a bug. But a handful of over-fires recur predictably; scan for them and prune rather than treating them as findings:

- **lineage** — `conversion` co-firing with `variant`: an art-only re-skin (same playfield, new artwork) is a **variant**, not a conversion; and a look-alike _comparison_ (_"nearly identical playfield"_, _"echoes"_) is **not a derivation** at all unless the page says this machine was derived from the other.
- **tag** — `manufacturer-retheme` fired across _different_ makers (only a maker re-theming _its own_ earlier design qualifies); `export` fired on a US-made game that was merely imported, sold, or renamed abroad (export is about where the _maker built it for_); `export` fired for a **non-US maker** at all — the tag is US-outward (_"built for a market outside the US"_), so it is vacuous or inverted for a non-US maker (e.g. an Italian maker whose US-censored backglass means the game was exported _to_ the US, the opposite of what the tag models).
- **gameplay** — one feature fragmented into **locational sub-counts** (_"flippers on the main playfield"_, _"on the upper playfield"_, _"in the outlanes"_ surfaced as three flipper entries) — collapse to the single feature. But keep the location when it names a **structure**: an _"upper / second / lower playfield"_ is a **multi-level playfield** feature in its own right, easy to lose while pruning the split.
- **credits** — people named only as researchers, collectors, photographers, the page's author, historians, or company representatives. Those are _not_ creators; they belong to entity discovery, not `credits`.
- **themes** — subjects lifted from company history or a designer's biography (e.g. "children" from a founder describing his audience) rather than the machine's own subject.

## 5. The catalog diff — do this every time

Before authoring, **resolve the target and read its current values from the flipcommons DB**, then:

- author only the **deltas** — new field values, new credits, new relationships. A patch is a correction or addition, not a restatement of what the catalog already holds, so drop any candidate that merely re-asserts a current value.
- surface any **page-vs-catalog disagreement** (page says 1969, catalog holds 1970) as a candidate _correction_ — this is the highest-signal output of the whole loop.

## 6. Out of scope — handled elsewhere

- **Does the quote _support_ the claim?** The extractor proves a quote is _verbatim_, not that it _establishes_ the value. That judgment is `ai_lint`'s `quote-supports-claim` rule — run `make verify-citations` on the authored patch.
- **Siblings, other makers, other people the page names** (entity discovery); **description-enrichment** material (anecdotes, era context); and **outbound source leads** — these axes are **not built yet**. Today's packet is model-info fields only. Note such material for later; don't expect the tool to surface it.

## 7. Then — vet field-by-field with the checklist

With the packet disposed and the catalog diffed, work [ModelPageExtractionChecklist.md](ModelPageExtractionChecklist.md) field by field to author the patch. The checklist is the field spec (legal values, the tells, the lineage and open-collection rules); this doc is only the loop around it.

As always in flippatch: **committing and `make push` stay the user's call** — never something the loop does on its own.
