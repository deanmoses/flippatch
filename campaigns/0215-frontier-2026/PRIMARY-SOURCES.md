# 0215 enrichment — the primary-source PDF inventory

Surveyed 2026-08-06, as the first customer of pinexplore's rebuilt PDF support ([WebCache.md](../../../pinexplore/docs/WebCache.md)).

**This is a floor, not a survey.** One afternoon across fifteen families, mostly spent testing tooling rather than hunting documents. Every "0" below means _nobody has looked properly yet_, never _nothing exists_. Finding and fetching more is each session's job — see ENRICHMENT-PLAN.md.

The superseded draft (`draft-evidence-aggregator.csv`) sources **166 of its 181 credit rows from Pinside** — 92%, with the other 15 from Multimorphic. The premise behind that is wrong: the manufacturer publishes this material, in flyers, feature matrices and manuals, and the cache already holds enough of it to move most of 0215 onto first-party evidence.

## What a manufacturer PDF actually carries

Three document classes, in descending order of density per page:

| class                                             | fills                                                                        | how you read it                                                      |
| ------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **feature matrix** (Stern)                        | gameplay features _per edition_, production count, system, display, designer | text layer readable; the grid itself needs a render                  |
| **flyer** (Barrels of Fun, JJP compare sheet)     | gameplay features with counts, display, art credit, dimensions, theme copy   | usually **vector outlines** — no text layer, so render and transcribe |
| **service manual** (Stern, JJP, American Pinball) | dimensions, weight, electrical, flipper/coil counts, playfield inventory     | text layer readable; tables need a render                            |

**All three are quotable.** Whether a document has a text layer decides how you _read_ it, never whether you may quote it: render the sheet, read the words, transcribe them. Only a **mark** — a checkmark in a column, a diagram arrow — has nothing to transcribe and stays a quote-less cite. `make verify-quotes` skips PDF quotes entirely (`SKIP-PDF`), so they are the author's own check; see ENRICHMENT-PLAN.md → Citing PDF evidence.

Manuals are the _weakest_ source for the field that draft most wants: Stern's MTMTE manual names no person at all (`Eismin`, `Kyzivat`, `designer` → 0 matches across 66 pages). People credits live in the flyer and the matrix, not the manual.

## Verified first-party claims — machine-confirmed from the text layer

These happen to sit in the text layer, so `web_cache.py quote` confirmed them mechanically. That makes them convenient, not privileged: a span transcribed off a rendered sheet is equally citable, and `verify-quotes` checks neither, since it skips PDFs. All three verbatim from Stern's own `Transformers-More-Than-Meets-the-Eye-Feature-Matrix.pdf`:

- `"Individually Autographed by Game Designer Elliot Eismin."` → **design credit**, replacing the draft's Pinside cite
- `"Production limited to 750 machines."` → **production count**, LE only — a field 0215 does not currently carry at all
- `"Custom animations on larger, 18.5” full HD display."` → **display type/size**

From JJP's Sonic manual, PDF sheet 5 (printed folio `V`):

- `"Hall of Fame game designer Steve Ritchie is known for his fast-flowing games. He and his design team have created Sonic pinball."` → **design credit**, first-party, replacing Pinside

Sonic manual sheet 7 (printed folio `VII`) is a specification table — 325 lbs with topper, 87 × 29 × 57 in., 120/230 VAC. The text layer flattens the table into unattached cells, so read it by rendering the sheet — and then those figures are quotable off the render like any other words.

## The per-edition problem, and the honest cite

The Transformers matrix is the single densest source in the campaign: ~55 feature rows × 3 edition columns. Per-edition features are the one case here that genuinely **cannot** carry a quote, and the reason is not the text layer — it is that **a checkmark is a mark, not text.** Rendering the sheet shows you which column is ticked; it does not hand you words to transcribe, because there are none.

So per-edition features stay quote-less: `ref` the matrix URL, `locator` naming the sheet and the row, `note` recording what was seen in which column. Quoting the row label to establish a column is the column-splice forgery the rule exists to stop, and reading that label off the render rather than the text layer changes nothing about it.

Everything else on the matrix is quotable — the three claims above, the `MAIN ATTRACTIONS` prose behind theme and description work, and any wording you render and read. The grid's own column headers are a fair warning about the text tier, though: they extract as a floating `PRO GAME FEATURES LE ONLY` and a trailing `PREM LE`, attached to nothing, so do not reconstruct a column relationship from extracted text — that is what the render is for.

## Inventory, by maker

| maker                                               | first-party PDFs held                                                 | gap                                                                  |
| --------------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Stern                                               | 20 (incl. MTMTE feature matrix + Pro manual, both 2026)               | Premium/LE manuals unpublished                                       |
| Jersey Jack                                         | 2 (Sonic manual, Sonic compare flyer)                                 | —                                                                    |
| Barrels of Fun                                      | 2 (BJ flyer 2026-07, Winchester flyer)                                | —                                                                    |
| American Pinball                                    | 8 (Houdini manual + QRG, GTF manual + QRG + release notes)            | no 100th Anniversary / GTF Victory / Cirqus Voltaire docs yet        |
| Cardona                                             | 2 (FT: Ultimate Fishing Challenge release notes, 2026-06 and 2026-07) | fetched this session                                                 |
| Stern (Pokémon)                                     | 2 (Pro + LE manuals, 2026-04)                                         | fetched this session; already-catalogued 2026 models                 |
| HEXA                                                | 2 (0.911 notice FR/US)                                                | none found yet for The 3 Musketeers; HEXA does publish PDFs, so look |
| Multimorphic                                        | 0                                                                     | product pages only; the draft's 15 first-party rows come from those  |
| Pedretti, Turner, World Pinball, UP Pinball, Ramp's | 0                                                                     | none found in one pass — unsearched, not absent                      |

No PDF turned up for those five in one pass, and their web presence differs in ways that matter — Pedretti's own domain did not resolve yet its full press release is public, World Pinball's real site is `worldpinball.ch` behind an HTTP 401, Ramp's site is live but silent on its 2026 machine. Each was probed once. ENRICHMENT-PLAN.md has the leads; **do not read "0 PDFs" as "no evidence"**, and do not read one probe as a search.

## Also surfaced

Manufacturer **YouTube** is a parallel first-party channel the cache already ingests as transcripts: the Cardona release notes link six official videos (splash announcement, launch, gameplay UI, kit installation, two gameplay walkthroughs) for a model whose only other evidence is Pinside.

Stern publishes **Pokémon Pro and LE manuals dated 2026/04**. Pokémon is absent from `candidates.csv` but _is_ in the catalog — `pokemon-pro`, `pokemon-premium`, `pokemon-limited-edition`, all 2026, three of the six 2026 models the sweep found already present. No gap; the manuals are now cached and are enrichment material like any other.

## Blocker: five PDF hosts have no citation root

A URL cite needs its host to resolve to a seeded website root (Citations.md). The match is a longest-label-boundary suffix, so maker subdomains resolve for free — `wp.sternpinball.com` → Stern Pinball, `marketing.jerseyjackpinball.com` → Jersey Jack. **CDN hosts do not**, and that is where much of the best evidence lives:

| host                                      | serves                                | verdict                                                                                                                                |
| ----------------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `48804760.fs1.hubspotusercontent-na1.net` | every current AP Houdini + GTF manual | **safe to register** — `48804760` is American Pinball's own portal id, so the host is account-specific                                 |
| `my.orbitgames.fun`                       | AP release notes                      | **safe to register** — AP's own domain                                                                                                 |
| `cardonapinball.com`                      | Cardona product pages                 | **needs a new root** — new manufacturer, like the entities 0215 created                                                                |
| `cdn.shopify.com`                         | JJP Sonic compare flyer               | **do not register** — shared host; the account id is not in the host, so registering it would resolve every Shopify URL to Jersey Jack |
| `img1.wsimg.com`                          | Cardona release notes                 | **do not register** — same shape; the account id sits in the _path_                                                                    |

`0216` was unaffected because it cites `americanpinball.com/...` pages, which resolve. Anything citing the manuals will fail the apply until the first three are seeded. For the last two, prefer a maker-domain URL where one exists (the Sonic _manual_ is on `marketing.jerseyjackpinball.com` and resolves; only the compare flyer is on Shopify) and otherwise treat the document as research-only — findable, not citable.

Re-run the check before generating:

```sql
SELECT h.host, coalesce(cr.root_citation_source_name,'NO ROOT')
FROM (VALUES ('wp.sternpinball.com'), …) h(host)
LEFT JOIN citation_roots cr ON cr.root_citation_source_id = citation_root_for_host(h.host);
```

## Finding the documents

`web_cache.py links <url> --ext pdf` is the discovery step. Run across the 60 cached maker pages it yields **172 distinct PDF URLs**, each with its anchor text — `Pokémon Pro Manual Download File` tells you what a document is without spending a fetch on it. 25 were already held; the 0215-relevant remainder was fetched this session.

```bash
uv run python scripts/web_scrape/web_cache.py links <maker-support-page> --ext pdf --limit 0 \
  | cut -f1 | uv run python scripts/web_scrape/web_cache.py have --from-file -
```

`--limit 0` matters when piping: the default caps output at 100 rows. It says so on stderr, which a pipe still shows — but a redirect that swallows stderr will lose the warning along with 32 of Stern's 132 manuals.

Anchor text is only as good as the source markup: American Pinball's HubSpot-driven support pages return all 14 Houdini documents with **empty** anchors, so there the filename is the only label.
