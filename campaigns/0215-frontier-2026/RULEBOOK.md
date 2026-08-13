# 2026 model enrichment — method

This is the rulebook for the campaign: what counts as a source, how evidence is cited, what may become vocabulary, how the gates behave. We are fleshing this out as we go through the campaigns, and once it's been hardened, much of it will eventually end up in Flipcommons docs like `DataPatchAuthoring.md`.

When you learn something durable, add it here. But don't put your run history here; that stays in the family's own `<Family>.md`.

## Surveying the catalog

**Enumerate a family by model slug, never `title_slug`.** Transformers The Pin has its own Title, so a title-keyed query silently misses it.

**Duplicate-scan against `model_claims` from other actors, not `patch_claims`.** The apply **silently swallows** an exact duplicate (same actor + claim key + value): no claim row, and its citation is dropped with it — so what your patch wrote is not what it asserted. (A flippatch session is reviewing whether that swallow should stay.)

## Primary and secondary sources

The authority on primary sources is `~/dev/flipcommons/docs/DataPatchAuthoring.md`#`Prefer primary sources`. Here we're noodling on a more detailed list, in rough order of what source is most authoritative:

### Best first party

- **A photo of the actual machine**, such as getting some of the people credits printed off the actual playfield.
- **The maker's own website**, and specifically its support, downloads, service and product pages — these are where flyers, feature matrices, manuals, quick-reference guides, service bulletins and release notes live.

### Other first party

- **The maker's YouTube channel**: the cache ingests transcripts, and reveal and gameplay videos are first-party.
- **Distributor and archive** copies where the maker's own copy is gone: archive.org, distributor sites, Planetary Pinball for Williams/Bally titles — IPDB's file trove last (user, 2026-08-12): still first-party evidence, cited to its publisher as a [document](#document-cites), but we over-rely on IPDB and its 403 makes acquisition a hand import.
- For a **remake or a kit**, the _original_ machine's documents too — they are what the new one is derived from.
- For a **homebrew**, the builder's own build thread on a 3rd party site.
- **The licensor's own store**, where the maker releases "in partnership with" one. PPS sells the TOTAN remake deposits itself, with per-edition bullet copy _cleaner_ than the maker's own pages and sometimes decisive wording: its "Infinite mirror side blades" identified as playfield blades what the maker ambiguously called "Side Rails", and "No second run planned." settled which edition count is a hard cap.
- **press releases**: the maker's own words reprinted verbatim by a publication, datelined and attributed. **A maker's own reveal post can be an abridged press release** — BoF's Bon Jovi post carries the credits and the limited-release paragraph but not the Game Attractions / Game Features spec blocks, which exist only in Pinball News's verbatim reprint (and on the flyer). Check the reprints before declaring a spec unsourced, and cite each fact to the document that actually carries it.

### Journalism

- **journalism**: a named outlet's own reporting — Pinball News, Arcade Heroes, Kineticist _news articles_.

Acceptable where nothing above states the fact; prefer multiple independent outlets.

### Distributor listings

For an **announced** machine whose maker has published nothing beyond a teaser, distributor pre-order listings can be the only public source of edition structure and specs (cirqus-voltaire: SD Amusements carried the Ringmaster Edition's unit count, art credit and feature list while AP's own site had one paragraph). Usable there with a single-family citation root, superseded the moment the maker publishes. **They are volatile — cache one the moment you see it**: of four distributor CV listings surfaced by search on 2026-08-10, three were already deleted (404 in a real browser, gone from the store's own search) and only the cached one remained citable.

### Crowdsourced

User-submitted database rows — Pinside game archive, Kineticist _game index_.

Do not use for any model that has a manufacturer PDF. Elsewhere, never the sole support for a claim.

Where a family's sources are thin, the reason differs per family and determines what to do — each is recorded in that family's own notes. Where nothing is available, the model gets **nothing beyond what 0215 already created**.

### Conflicts

**Conflicts between primary sources are a user decision.** Houdini's current site says 4 speakers where its flyer and IPDB say 6; JJP's site says 5,000+ callouts where the article it reprints says 6,000+. Surface the conflict and record the ruling in the family doc (Houdini's ruling: the maker's current site won). For a person-name spelling conflict, record the losing spelling as a `person_alias` so both forms resolve (GTF's ruling: Pollitt per AP's cast announcement, Politt aliased).

## Finding and fetching documents

Put every primary document you find in the [web cache](~/dev/pinexplore/docs/WebCache.md), even ones you aren't sure carry a citable fact — an unfetched document just gets re-hunted by the next session.

- **Search the document library before hunting the web.** `web_cache.py search` reads a metadata tier over documents not yet fetched — the classified IPDB trove plus hand registrations — so one search names a machine's manuals, schematics and flyers with the URL(s) to go get them. Write back: `web_fetch.py <url> --doc-class manual --subject-scope model --subject-pk N --subject-label "…"` annotates in the fetch; `web_docs.py hunt` records a dated "looked, not there" that later searches show.
- **`web_cache.py links <url> --ext pdf` is the discovery step on a cached maker page.** Across 60 cached maker pages it yielded 172 distinct PDF URLs, each with its anchor text — `Pokémon Pro Manual Download File` tells you what a document is without spending a fetch on it.

  ```bash
  uv run python scripts/web_scrape/web_cache.py links <maker-support-page> --ext pdf --limit 0 \
    | cut -f1 | uv run python scripts/web_scrape/web_cache.py have --from-file -
  ```

  **`--limit 0` matters when piping**: the default caps output at 100 rows. It warns on stderr, which a pipe still shows — but a redirect that swallows stderr loses the warning along with 32 of Stern's 132 manuals.

- **Anchor text is only as good as the source markup.** American Pinball's HubSpot-driven support pages return all 14 Houdini documents with **empty** anchors; there the filename is the only label.
- **Probe maker document hosts for open directory listings.** `marketing.jerseyjackpinball.com/distributors/Sonic/` indexed per-edition flyers, an all-models feature matrix, photography and the rules flowchart — none of it linked from any product page. `curl -s <dir>/` on a maker's file host costs nothing and can be the family's best find.
- **A maker's YouTube channel is a parallel document set**, ingested as transcripts. Cardona's release notes link six official videos — splash announcement, launch, gameplay UI, kit installation, two walkthroughs — for a model whose only other evidence is Pinside.
- **Maker software changelogs are evidence, and plain text caches.** JJP's `sonic_changelog.txt` dates every release build — corroborating launch timing and active support — and is fetchable, quotable and citable like any page.
- **A maker document that 404s is often recoverable from Wayback** — check the CDX index before declaring it lost. Fetching and citing (the `id_` trap included) is [Citation roots](#citation-roots) → archive.
- **A maker's news archive is a credits gold mine.** The GTF manual names nobody, but AP's old-domain news posts named the entire creative team in one sentence ("Slam Tilt Podcast interviews the Galactic Tank Force team") plus the display cast in another. When the manual and product pages are credit-silent, pull the Wayback CDX listing of `/news/` and fetch the team/interview/cast announcement posts — they are first-party.
- **A rebuilt maker site can silently merge editions.** AP's 2026 WordPress rebuild collapsed GTF's Limited and Signature editions into one "Limited" panel (its add-ons block is still headed "Signature Add Ons"). Per-edition facts for retired editions come from era-appropriate archived pages, not the live page's panels — the live page evidences only what it explicitly heads.
- **A maker's real domain may not carry its name.** Before declaring a maker web-less, follow the redirect from every domain variant its email and branding suggest — Pedretti publishes at `pinballremakes.com`, not at any `pedretti*` domain. Then read the site footer: street address, registry number (Italy: REA/P.IVA) and email domain are first-party identity and **location** evidence.
- **`web_fetch.py` rejects `image/webp`** ("skip (unsupported content-type)"), and modern outlets serve their images as webp. When a maker document survives only as a webp reproduction, look for a jpg copy on another outlet first (Pinball News's WordPress uploads are jpg — strip the `-NNNxNNN` thumbnail suffix for the original) before resorting to a hand download + `web_import.py`. Musketeers' flyer existed at 3509px webp on Kineticist and 1600px jpg on PN; only the PN copy could be cached.
- **A maker document that exists only as images inside an outlet's article is still that maker's document — and cites as one.** The worked example is 0229's HEXA spec sheet (two sheets, surviving only in Pinball News's reveal article). The moves: extract the image URLs from the article's raw HTML blob (`web_cache.py get` names it; Next.js sites bury them in escaped JSON, WordPress in `<img srcset>`), fetch the full-size images, transcribe each sheet and file it with `web_import.py --text-file`; then in the document library merge the per-URL auto-documents into one work (`web_docs.py merge`), set title/publisher and the `citation_ref`, and cite `<publisher>:<doc-slug>` with sheet-naming locators ("back sheet; in the PLAYFIELD FEATURES list"), declaring the document in the patch per [Document cites](#document-cites) with the outlet's image URLs as `catalog` links. The verbatim gate reads a multi-sheet document as every captured sheet's text joined in library order, so quotes gate on any sheet — a multi-span quote must still order its spans front-sheet-before-back.
- **A maker's site can drop a page from its nav while still serving it.** Turner's Ninja Eclipse product page and its ruleset PDF were live but linked from nothing — the CDX sweep surfaced the URLs, and a live probe (`curl -I`) found them still up. Probe the original URLs live before reaching for snapshots: a live maker URL cites clean, with no `archive:` needed.
- **A maker's manual lineup can promise more per-edition evidence than it holds.** Stern serves the 2011 Transformers manual under two filenames, byte-identical — `content_sha` is the tell, check it before treating two documents as two sources. Pokémon's `Pokemon_LE_Pre_web.pdf` is the other shape: one distinct manual explicitly covering two editions (LE **and** Premium). Either way, a per-edition filename is not per-edition evidence — verify what the document actually covers.

### Hunting machine photos

On-machine print — a credits panel, an apron card, a spec plate — is the most primary source there is (see [Primary and secondary sources](#primary-and-secondary-sources)), and photos of it are hunted by **document class first, recovery route second**:

1. **Maker PDF containing the photo.** Wins on every axis at once: stable URL on a rootable host; flyers and brochures are produced from print-resolution source assets rather than web-compressed derivatives, so small type survives zooming; and it is the cheapest to gate — a PDF quote is author-checked (`SKIP-PDF`), no transcription import needed. Sweep the maker's PDFs for playfield photography, not just spec text.
2. **Maker website images.** Rootable and first-party, but with two costs a PDF doesn't have: delivery images are usually downscaled — check pixel dimensions before spending effort, and hunt the original (strip WordPress's `-300x116` thumbnail suffix, ask Shopify for the master, prefer the `/img/` asset over the gallery preview — GTF's archived gallery previews were _smaller_ than the flyer embedding the same photo); and an image cite needs the `web_import.py --text-file` transcription before its quotes gate (see [Operating the quote gates](#operating-the-quote-gates)).
3. **Wayback is the transport fallback for either tier, not a tier of its own.** Same `id_` and `ref`+`archive:` mechanics as documents. A Wayback-recovered maker PDF outranks a live maker website image — the document class matters more than the liveness. You get only what was crawled at the resolution it was crawled, and it may be the last copy anywhere: GTF's GTK M13 flyer survives solely as one 585 KB JPG snapshot. Today's live maker image is tomorrow's single lossy snapshot — cache it now.

**Legibility is the binding constraint, not availability.** Before transcribing, check whether the print region is actually readable: crop and upscale to inspect, and when a name sits at the letterform-ambiguity floor (GTF's ~8 px cursive credits), cross-reference the reading against corroborating coverage before committing it, recording the aid in the note.

Discovery moves: probe maker file hosts for open directory listings (JJP's `marketing/` had a photography folder linked from nothing — see above), and **CDX-sweep the maker domain filtered to images** (`matchType=domain&filter=urlkey:.*<slug>.*`, read the mimetypes) — old sites' `/img/` and `/gallery/` trees surface there linked from nothing; that sweep is what found the GTK M13 flyer.

### What a manufacturer PDF carries

Three document classes, in descending density per page:

| class                                             | fills                                                                        | how you read it                                                       |
| ------------------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **feature matrix** (Stern)                        | gameplay features _per edition_, production count, system, display, designer | text layer readable; the grid itself needs a render                   |
| **flyer** (Barrels of Fun, JJP compare sheet)     | gameplay features with counts, display, art credit, dimensions, theme copy   | usually **vector outlines** — no text layer, so render and transcribe |
| **service manual** (Stern, JJP, American Pinball) | dimensions, weight, electrical, flipper/coil counts, playfield inventory     | text layer readable; tables need a render                             |

Manuals are the _weakest_ source for people credits: Stern's MTMTE manual names no person at all (`Eismin`, `Kyzivat`, `designer` → 0 matches across 66 pages). Credits live in the flyer and the matrix.

### The inventory floor (surveyed 2026-08-06)

**A floor, not a survey** — one afternoon across fifteen families, mostly spent testing tooling rather than hunting documents. Every **0** means _nobody has looked properly yet_, never _nothing exists_. One probe is not a search.

| maker                                               | first-party PDFs held                                                 | gap                                                                  |
| --------------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Stern                                               | 20 (incl. MTMTE feature matrix + Pro manual) + 2 Pokémon manuals      | Premium/LE manuals unpublished                                       |
| Jersey Jack                                         | 2 (Sonic manual, Sonic compare flyer)                                 | —                                                                    |
| Barrels of Fun                                      | 2 (BJ flyer 2026-07, Winchester flyer)                                | —                                                                    |
| American Pinball                                    | 8 (Houdini manual + QRG, GTF manual + QRG + release notes)            | no 100th Anniversary / GTF Victory / Cirqus Voltaire docs yet        |
| Cardona                                             | 2 (FT: Ultimate Fishing Challenge release notes, 2026-06 and 2026-07) | —                                                                    |
| HEXA                                                | 2 (0.911 notice FR/US)                                                | none found yet for The 3 Musketeers; HEXA does publish PDFs, so look |
| Multimorphic                                        | 0                                                                     | product pages only                                                   |
| Pedretti, Turner, World Pinball, UP Pinball, Ramp's | 0                                                                     | none found in one pass — unsearched, not absent                      |

Their web presence differs in ways that matter: World Pinball's real site is `worldpinball.ch` behind an HTTP 401, Ramp's site is live but silent on its 2026 machine.

### `draft-evidence-aggregator.csv` helps you know what to look for

[draft-evidence-aggregator.csv](draft-evidence-aggregator.csv) is a per-model list of credits already tracked down: person, slug, role, and the source from which it was taken. It helps you see what data we are missing so that you can search for it in primary documents. **Don't cite it**: most of its rows are an aggregator, Pinside. The p3-modules are an exception; they are **first-party rows**.

## Reading a PDF

- **`outline` is a flat page map.** It ignores the embedded bookmark tree. Most PDFs have none or have useless ones, but when you need a real table of contents, read the bookmarks with `pypdf`.
- **The text layer is a convenience, not the document.** Some PDFs have none at all — the Bon Jovi flyer's type is outlined, and Stern's 2011 `Transformers-Manual.pdf` carries 227K chars of OCR and nothing else. Render the sheet and read it.
- **Tables and grids need a render even when the text layer is readable.** Extraction flattens them: the Sonic manual's spec table comes out as unattached cells, and the Transformers matrix's column headers extract as a floating `PRO GAME FEATURES LE ONLY` and a trailing `PREM LE`, attached to nothing. Never reconstruct a row/column relationship from extracted text.

## Citing PDF evidence

- **A PDF often has two page numbers**: the index of the sheet (always) and the folio printed on it (sometimes). Name both in the locator: `printed page 7, PDF document page 22`. Get the printed folio by rendering the sheet unless the text makes it unmistakable.

**Quote the words on the sheet — the text layer does not decide what's quotable.** Render the sheet, read the words, transcribe them into `quote:`. A document with no text layer at all still has words on it, and a transcription you made by looking is evidence.

**An image quote stays gated — file a transcription first.** An image's OCR lands in `ocr_text`, findable but never citable; `NO-SOURCE` on an image cite means no transcription has been filed yet, not that images can't be cited. Read the words off the picture and file them through pinexplore's `web_import.py <blob> --url <cached-url> --text-file <transcription> --force` (recorded as `text_source = manual` — a person is answerable for the words; keep the document's line structure); the image's quotes then verify like any text. Worked example: the GTK M13 flyer's transcription (0222) unlocked the machine's printed CREDITS panel visible in its playfield photo — the family's only first-party source naming the code, animation, engineering and audio team. **Zoom before you give up on small print**: crop and upscale the credit lines, and cross-reference hard-to-read cursive names against corroborating coverage before transcribing them.

`make verify-quote-verbatim` **does not gate PDF quotes**; it reports them `SKIP-PDF`. That is deliberate: a correct span read off a sheet routinely isn't a substring of the reading-order extraction, and checking the OCR tier instead rejects ~25% of correct spans (measured on this corpus), so no threshold makes it honest. **A PDF quote is your own check** — transcribe it exactly as the next person rendering that sheet would read it. Nothing goes in the patch about which quotes are gated; the patch is the record.

**A mark is not text — that case stays quote-less.** A checkmark in a feature-matrix column, a diagram arrow, a filled cell: looking at it produces no words to transcribe, so there is nothing to quote. The honest cite is `ref` + `locator` naming the sheet + `note` recording what was seen, with no `quote:`. The line is whether the evidence **is** text, not whether extraction caught it.

**Do not quote a row label to establish a column.** `"Megatron Pinball Firing Fusion Cannon."` is verbatim, but it establishes the _row_, not the Premium/LE column, and the AI linter's `RULE_QUOTE_SUPPORTS_CLAIM` will reject it. Reading that label off a render rather than the text layer splices exactly the same way.

**Per-edition panels are positional.** A carousel or comparison layout repeating identical headings cannot be cited by position — only an explicitly-headed block ("Deluxe Features", "Autobot Crimson LIMITED EDITION Features:") establishes its own edition. Same splice rule as matrix columns.

**Worked example — the Transformers matrix**, the densest source in the campaign at ~55 feature rows × 3 edition columns. Its per-edition features are the one case here that genuinely cannot carry a quote, and the reason is the checkmark, not the text layer. Everything else on it is quotable: the design credit, the production count, the display spec, the `MAIN ATTRACTIONS` prose.

## Citation roots

A URL cite fails the apply unless its host resolves to a seeded citation root. Maker subdomains resolve for free by longest-label-boundary suffix (`wp.sternpinball.com` → Stern, `marketing.jerseyjackpinball.com` → Jersey Jack), and a leading `www.` is normalized away, so a root registers bare and both forms resolve. CDN hosts do not resolve.

**The shared roots are already seeded — `patches/0217-enrichment-citation-roots.yaml` does it.** Do not re-declare them and do not invent roots of your own. It attaches American Pinball's two document hosts (`48804760.fs1.hubspotusercontent-na1.net`, `my.orbitgames.fun`) to the **existing** American Pinball root, and creates the **Planetary Pinball** root for the licensed Williams/Bally material several families' pre-2000 halves rest on. It takes 0217 because a roots patch has a hard ordering constraint a family follow-up does not: patches apply in numeric-prefix order, so a root must be numbered below every patch citing it.

A root your family needs that 0217 does not cover is a **single-family** root and belongs in your own family patch — Cardona (`cardonapinball.com`) is the worked case, created by 0225. The `sources:` block is **additive get-or-create**, matched by recognition host: a node matching an existing root has missing hosts backfilled and existing fields left alone, so a re-declaration is a harmless no-op. **Do not modify 0215 or 0217 and do not renumber.**

```yaml
sources:
  - name: Cardona Pinball Designs
    source_type: web
    description: Manufacturer's own site. # only on a NEW root; a match ignores it
    links:
      - { url: "https://cardonapinball.com/", link_type: homepage }
    domains: # extra recognition hosts; a path scopes a shared CDN (below)
      - img1.wsimg.com/blobby/go/4bd466e8-edb0-49f6-afcc-31250ba5b0f3
```

**Attach a maker's document host to that maker's existing root, never to a new one.** Splitting AP's manuals off from AP's product pages would put one company's evidence under two sources, and nothing in the apply catches it.

Check what already resolves before generating — most makers do:

```sql
SELECT h.host, coalesce(cr.root_citation_source_name,'NO ROOT')
FROM (VALUES ('wp.sternpinball.com'), …) h(host)
LEFT JOIN citation_roots cr ON cr.root_citation_source_id = citation_root_for_host(h.host);
```

**Shared hosts must never be registered bare — register the maker's tenant path instead.** `cdn.shopify.com`, `img1.wsimg.com` and `storage.googleapis.com` carry many makers' files with the tenant id in the **path**; registering the bare host would resolve every unrelated URL on that CDN to one maker, and the apply rejects it. Since 2026-08-11 a `domains:` entry may carry a **path**, declaring exactly the maker's tenant slice of a declared shared host — see DataPatches.md → Citation sources and the allowlist in flipcommons `apps/citation/shared_hosts.py`; `patchkit.source_root(domains=[...])` emits it. The worked example is 0225's Cardona root: the maker's whole document set (release notes, instruction cards) lives only on GoDaddy's `img1.wsimg.com`, with no maker-domain mirror, and `img1.wsimg.com/blobby/go/<tenant-id>` resolves its files to the Cardona root while other tenants' stay unresolved. A shared host **not yet in the allowlist** is still unregisterable — extending the allowlist is a flipcommons change, not a patch.

**For a Shopify-backed maker store there is usually a maker-domain URL** — Shopify serves the same file under the store's own domain, so `cdn.shopify.com/s/files/<tenant>/files/X.pdf` is also at `<maker-domain>/cdn/shop/files/X.pdf`. The Sonic compare flyer resolved to the Jersey Jack root that way (0221's worked example). Fetch and cite the maker-domain URL. Where no such URL exists, the document is research-only: findable, not citable.

**`web.archive.org` is deliberately rootless.** A cite carries an `archive:` key for exactly this: `ref` the original publisher URL, `archive:` the snapshot. Registering archive.org would make the archive the source rather than the publisher. This is the route for a maker document gone 404 — American Pinball's Houdini flyer is the worked case, dead on `american-pinball.com` and recoverable from Wayback. Two traps:

1. Fetch the snapshot with Wayback's `id_` modifier (`/web/<timestamp>id_/<url>`) or you cache the HTML wrapper instead of the document — it reports a clean `200` either way.
2. The cache then holds the document under the _snapshot_ URL while the cite's `ref` is the original. Both quote checks handle this: when the `ref` isn't in the cache they resolve through the cite's `archive:` URL, so an archived document's quotes verify (or report `SKIP-PDF` for a PDF) instead of failing `NO-SOURCE`.
3. **Some captures are stored gzip-compressed at Wayback itself**, and `id_` returns the raw gzip bytes verbatim — a clean `200`, "(no title)", and a binary blob in the cache (4 of 10 Turner snapshots, 2026-08-13). Recover with `curl -sL <snapshot-url> | gunzip -c > page.html`, then `web_import.py page.html --url <snapshot-url> --force`; the extracted text then gates normally.

Houdini's 0219 flyer cites and Transformers' 0220 archived Stern game pages are the worked examples — 0220's Wayback recovery of Stern's dead 2011 `/Games/*.aspx` pages turned the family's worst-documented models into gated-HTML-cited ones. **Check the CDX index before declaring a maker's old documents lost.**

3. **Never fetch the dead original URL itself into the cache.** The quote gates fall back to the cite's `archive:` only when the `ref` is *absent* from the cache — a live fetch of the dead URL caches whatever the domain serves today (a rebuilt site's homepage, a redirect page) under the original URL, and the gate then resolves the ref to that junk and fails the quote instead of reaching the snapshot. If a probe already cached one, delete that cache row (0233's Knapp Arcade posts are the worked case: the relaunched site 200-redirects every dead post to its homepage).

**`ipdb:` cites can quote the structured row, credits and Toys included.** The quotable slice (`ipdb_row_text` in `scripts/quotes/sources.py`) renders every quotable page field — `Model Number:`, `MPU:`, the person-credit lines (`Design by:`, `Art by:`, `Dots/Animation by:`, `Mechanics by:`, `Music by:`, `Sound by:`, `Software by:`), `Toys:` and the other labeled fields — exactly as the IPDB page shows them. The analytics foundation carries toys and marketing features as plain columns too, and `make analyze CMD=describe` searches, so don't truncate its output. This is how a variant's replicated credits get gated evidence, and it matters for every family with IPDB-rowed older siblings (Transformers 2011, Fish Tales, TOTAN).

## Document cites

A discrete published document — manual, schematic, flyer, service bulletin, patent — cites as `<publisher>:<doc-slug>` (`williams:tales-of-the-arabian-nights-operations-manual-1996`, `uspto:us4373731`): the `document` source type, added 2026-08-12. The publisher is who **issued** it, never the host holding a copy — a Williams manual on ipdb.org cites as Williams, the IPDB URL riding along as a `catalog` link. (`ipdb:<id>` still cites the structured IPDB row itself.) Grammar: DataPatches.md → Citation sources; design: flipcommons `docs/plans/citations/DocumentCitations.md`. The indexed trove is classic-heavy (Williams 1,077 documents, Bally 991), so pre-2000 family halves gain the most — several done families' notes record Williams-era documents skipped when they were uncitable.

- **Publisher roots are seeded — `patches/0227-document-publisher-roots.yaml`** (53 manufacturers + USPTO; slugs are the catalog manufacturer slugs). Same standing as 0217: never re-declare, and a patch citing them numbers above 0227. A publisher 0227 lacks is one `source_root(slug=…, source_type="document")` node in your own patch — no links; a publisher root is an abstract container.
- **The document is declared by the first patch citing it**: a `sources:` node with `parent:` the publisher slug and its own authored `slug` — full model slug + class + year, no abbreviations (`tales-of-the-arabian-nights-operations-manual-1996`); subject-neutral when it covers more than one model (`wpc-95-schematic-manual`); versions and languages are sibling documents. Name: model first, class, date parenthesized — "Tales of the Arabian Nights Operations Manual (May 1996)". Slugs freeze at creation; fix a misread date in the fields, never by renaming.
- **Attach every copy you hold as typed links**: `reference` the publisher's own URL, `catalog` IPDB, `archive` a snapshot. Never mistype a link to steer the reader.
- **Acquire the copy the fetcher can reach** — maker site, Planetary Pinball, archive.org. ipdb.org 403s the fetcher, but an IPDB-only copy is still acquirable: with the user's go-ahead the session drives the Claude Code in-app browser itself — the full recipe is WebCache.md → "An AI session can be the person with the browser". archive.org `/download/` URLs redirect to rotating datanode hosts — the cache stores the capture under the datanode URL with the stable address as its alias, so declare and cite the stable URL and let the library join resolve it.
- **Wire the library as you acquire — it's what makes the gates work.** Attach the fetched copy to the seeded document (`web_docs.py register <url> --role archive`, then `merge` into the seeded id), set `--citation-ref` to the exact ref your patch will cite, and fold per-side image scans into the one work they capture. The quote gates resolve a document ref through `citation_ref` (0228's worked example): SKIP-PDF on a scan, fully gated on text, NO-SOURCE only when no copy is cached.
- **Emit with `patchkit.source_child(...)`** — parent + slug + dates + typed links, same escaping safety as `source_root`. Declare only documents the patch actually cites; an identified-but-uncited document stays in the library (pre-seeding the trove is deliberately deferred).

## Asserting claims

**One assertion per changeset (user, 2026-08-13).** Facts that assert different things get their own changesets even when one source line supports them all — a Creative Director credit and a Rules credit, `system` and `technology_generation`, `cabinet` and `display_type`. A later correction then touches exactly one assertion (say a new role is created just for rulesets) instead of unpicking a bundle. Split the quote along with the changeset when the source's spans separate — each fact carries only the span that supports it.

**Delete every `note:` the citation already carries (user, 2026-08-13).** The golden rule is DataPatchAuthoring.md → `note:`: if you can delete the note and the cite still carries the change, delete it. Mapping a maker's "Cabinet Artist" to the art role, or "Creative Director" to design, needs no note — it is obvious from the quote and the value. The 0220-era generators (and 0231's first emit) over-noted heavily; don't copy that habit from the templates.

**`cabinet: floor` is asserted on standard machines too (user decision, 2026-08-12).** The field is not reserved for the novelty formats (cocktail/countertop/tabletop): classify from documented full-size dimensions — a spec line or manual dimensions table — with a note saying the classification is from the dimensions, since no source names a cabinet type for a standard machine. 0228's TOTAN 1996 is the worked example.

**`production_status` has no `retired` value.** The vocabulary is announced / produced / unreleased / one-off / aftermarket, so a maker's RETIRED badge answers no catalog field — a retired machine stays `produced`.

**A model's `month` (like `year`) is the manufacture date — an announcement date is not evidence for it (user, 2026-08-13).** DataPatchAuthoring.md states this outright, and two families still got it wrong before the ruling: 0229 and 0231's first draft both asserted the reveal month on `announced` machines and were corrected by hand. An announced machine gets **no month** until a source dates manufacture; keep the reveal date in a `note:` if it earns its place. A *document source node's* `year`/`month` is different — it dates the document itself and is correct to set.

**The remake credit rule (user decision, 2026-08-10).** All creative credits — design, art, animation, music, sound — carry from an original to its remake, cited to the original's evidence with a note; mechanics and software do not (a remake is re-engineered). Matches the seed's Medieval Madness Remake rows. When the remake replaces a creative element (cirqus-voltaire's Ringmaster Edition has a new Brian Allen art package), that slot's original credit does not carry to the model that replaced it. Remake editions are named the seed's way: "Medieval Madness (Remake Limited Edition)", and carry `remake_of` to the original plus `variant_of` to their base remake model.

**A two-peer-edition remake family has a base: the cheaper, less-limited edition (user decision, 2026-08-11).** When a remake launches as two editions with no plain "Remake" base model (TOTAN: Legacy + 30th Anniversary), the cheaper/standard edition is the base and the pricier strictly-limited one is `variant_of` it — the shape the seed already gives Pedretti's own Funhouse remakes (Limited `variant_of` Collector's). Both still carry `remake_of` the original. (Medieval Madness Remake's flat all-`remake_of` shape predates this ruling.)

**The variant rule (user decision, 2026-08-07).** A variant carries every credit of its base, and the shared design's hardware is a fact about every edition. Cite the base's evidence (e.g. the base IPDB row) with a `note:` saying why the value carries. Convention survey so far: every modern Stern LE is `variant_of` its Premium (40+ catalog precedents; 0220), and JJP's multi-edition families point at the mid-tier base — the Harry Potter shape; 0221's CE and AE → Special Edition, user-approved 2026-08-10.

**The conversion-kit rule (fish-tales, 2026-08-11).** A licensed 2.0 kit is neither a variant nor a remake: no credits carry from the donor machine, and the donor's hardware facts (flippers, ramps, player count) stay off the kit model — the donor supplies them, the kit doesn't include them. The kit-to-donor link is a `model_relationship` edge, `relationship_type: conversion_kit` + `license_status`, targeting the donor. Kit-specific facts (its displays, its system, its new modes' features) assert normally. `production_status` follows the DomainModel definitions, not the word "kit": an officially licensed, commercially sold kit is `produced` (`aftermarket` means _not_ an official commercial release).

**Locate the city for every corporate entity.** City, not state. A **state business registry is first-rate evidence**, and when a stable republisher (City-Data.com) is its only citable carrier, root and cite the republisher with the underlying registry named in the note — 0225's Cardona → Pennsville NJ.

**A `credit:` needs its person to exist** — the apply fails with `relationship 'credit' member '<slug>' does not resolve to a Person`, and the structural gates don't catch it. People new to the catalog are created in the same patch (`person.<slug>`, `create: true`, name only). Same trap collides the other way when two in-flight patches create the same person: the second apply fails on the duplicate create (0233 hit this after 0234 validated first).

**A System create requires a `manufacturer:` FK** — `catalog_system.manufacturer_id` is NOT NULL, and the structural gates don't catch its absence; the apply fails. A platform maker that builds no machines of its own (FAST Pinball) is still created as a manufacturer to hold its system.

**A wrong value held by several sources needs one retract per holding source.** `retract:` drops only the claim held by the patch's own `attribution:` source, and claim resolution is priority-ranked — retracting just the flipcommons-catalog copy lets a lower-priority source's copy (OPDB, IPDB) resurface as the resolved value. Query `model_claims` for every actor holding the field, then emit a companion patch per foreign source, attributed to that source (the DataPatches.md retract example's own pattern). 0233 + 0235's Road Trip month fix is the worked case. Numbers are claimed by file presence, so a session emitting a multi-patch family must create all its files at claim time — 0233's companion lost its first number to a concurrent session.

**`cite_kind` is recorded, never inferred later.** The emitter writes the two kinds differently: a `quote` cite carries a transcribed span, a `mark` cite carries a visual observation in a `note` with no `quote:`. Which one a row is depends on whether the evidence is text or a mark (see [Citing PDF evidence](#citing-pdf-evidence)). This is a fact about the **evidence**, recorded in the generator's own input so the emitter can branch — never a claim in the patch about whether a quote is verifiable.

## Feature vocabulary

**Generic only (user decision, 2026-08-10 — supersedes the 2026-08-08 wording rule).** The authority is flipcommons `docs/plans/catalog_data_model/unique_features/UniqueFeatures.md`; the working rules are in [campaigns/features-corpus/CHARTER.md](../features-corpus/CHARTER.md) → Toys.

- **A new vocab node must be generic** — an unrelated title from another manufacturer could plausibly attach it. Presentation features included (0218's charter stands). Manufacturer wording verbatim unless extremely clearly a synonym; branded names for generic features are children of the generic (the InvisiGlass pattern), created only by the family patch that attaches them.
- **Unique features (one-off toys, bespoke mechs, model-specific decorations) are NOT vocabulary.** Classify them into the generic taxonomy — the toys tree (0219) and any applicable mechanisms — and record the identity in the family doc's **future unique features** list for the coming UniqueFeature entity. The verbatim wording is already preserved in the cite `quote:`.
- **Never attach a grouping node** (`toys`, `interactive-toys`, `interactive-lighting`, `expression-lighting-system`) to a model — attach leaves. The editorial lint's `feature-grouping-node` rule enforces this; new grouping nodes join its list in `lint_patches.py`.
- The interactive-lighting DAG (0220) is the pattern for maker-branded systems: a location axis crossed with the maker's brand family, product leaves carrying both parents.

**Check the vocabulary before creating terms.** 0218 (presentation features), 0219 (Houdini's generic mechs plus the toy classification tree), 0220 (optical spinners, LE staples, the interactive-lighting DAG) and 0221 (generic equipment) added many nodes, and the seed has surprises — `ball-locks` already existed, and Houdini's first apply failed on the duplicate create. Query `gameplay_feature_vocab` for your exact slugs, and don't `tail` the output.

Watch false synonyms — flipper toppers are not cabinet `toppers`.

## Patch generator

Each family gets a `gen.py` emitting via patchkit ([DataPatchKit.md](../../../flipcommons/docs/DataPatchKit.md)); never hand-roll YAML escaping. The best template so far is [transformers/gen.py](model-families/transformers/gen.py) — start by copying it.

**Keep the facts inline in `gen.py`** at family scale; a handful of models doesn't need 0215's CSV architecture. Record user decisions in the family notes.

The AI page extractor ([ModelPageExtractionAuthoring.md](../../docs/page_extractor/ModelPageExtractionAuthoring.md)) has never worked very well. Houdini didn't need it (three models, hand-vetted). A bigger family might; investigate there rather than assuming.

## Operating the quote gates

An uncommitted patch is cheap to regenerate, so iterate freely: emit → `make verify-quote-verbatim` → fix spans → re-emit. Transformers shipped 93/0 that way.

Then run the AI support check scoped to your patch — `make verify-quote-support ARGS="<NNNN>"` — and triage. It reads the changeset `note:` alongside the cite, so **state the reasoning for a carried or classified value in the note**; 0221's variant-rule ladder passed on exactly that.

**A note is not a pass guarantee, and a clean pass is not the goal.** Taxonomy-level disagreements warn with or without a note and vary run to run — 0221's `cabinet-armor` "cosmetic, not gameplay" (presentation features are vocabulary by charter) and an occasional "the note is the author's inference" on classification-by-absence like static toys. Triage those against the charter and keep your call. **Do not re-run chasing a clean pass**: each scoped run costs ~300k tokens and samples differently. Genuine catches remain worth folding in — 0221's `production_status: produced` justly warned until the cite said the maker ships from stock rather than merely "available for purchase".

If the patch changed after a snapshot apply, restore and replay before re-verifying — the ledger fingerprints content.

**A locator says where the words sit, not how good they are.** When a reprinted press release and the outlet's own reporting share one document and read alike, quote the release text rather than the reporter's paragraphs around it, and let the locator draw the line: `in the manufacturer's press release reprinted verbatim in the article`.

**Lift spans from `web_cache.py quote` output verbatim — don't "fix" the source's own text.** Page text sometimes genuinely contains joined words ("Cabinet Armor &Matching Speaker Panel" in PN's Bon Jovi reprint is the HTML's own text, not a scrape artifact); a span lifted as `quote()` returns it matches both the stored text and the page, artifact-looking or not, while a hand-corrected spacing never will. And a multi-span `[...]` quote must list its spans in source order; the gate fails an out-of-order chain even when every span verifies individually.

**A page's meta description is quotable.** The cache's extracted text includes the meta block, so a `<meta name="description">` sentence gates like body text, with a locator naming the meta description (0223 quotes AP's "American Pinball is remaking Cirqus Voltaire…" from one; GTF's `game_format` rests on the only sentence where the maker states it). Useful when the page body is thinner than its own summary.

## Rebuilding the database

Standing recipe (user, 2026-08-08) — rebuild as often as you like:

```bash
cd ../flipcommons/backend
cp db.prod.patch-0214.2026-08-03.sqlite3 db.sqlite3
uv run python manage.py migrate
uv run python manage.py ingest_patches --patches-dir ../../flippatch/patches
```

If that snapshot file is gone or another campaign has moved the baseline, ask the user before picking a different one.
