# 2026 model enrichment

Patch `0215-frontier-2026.yaml` created names and themes some new-for-2026 models, but nothing else: no credits, gameplay features, production_status, game_format, cabinet, display, system etc.

We now want to fully flesh them out, as described in `/Users/moses/dev/flipcommons/docs/DataPatchAuthoring.md`#`Fill every field you can — grounded in DomainModel.md`.

## Model families

Each separate model family will be done by separate AI sessions in its own sub-campaign folder in campaigns/0215-frontier-2026/model-families. **Folder names carry no patch number** — a session claims the next free `patches/` number when its work starts and does not write it into the folder name. (The original reserved-number scheme died when 0218 went to the feature vocab and 0219 to Houdini's second patch.)

- [houdini](model-families/houdini) from American Pinball: 100th Anniversary **+ 2 older**: Master of Mystery, Master of Mystery (Deluxe) — **DONE** (0216 + 0219, snapshot-validated, unshipped). The worked example: its `Houdini.md` records the process, decisions and traps.
- [transformers](model-families/transformers) from Stern: MTMTE Pro / Premium / LE **+ 5 older**: Transformers Pro & LE (2011), Autobot Crimson LE, Decepticon Violet LE, The Pin (2012)
- [sonic-hedgehog](model-families/sonic-hedgehog) from Jersey Jack: Collector's / Special / Arcade Edition
- [galactic-tank-force](model-families/galactic-tank-force) from American Pinball: Victory Edition **+ 4 older** (2023): Classic, Deluxe, Limited Edition, Signature
- [cirqus-voltaire](model-families/cirqus-voltaire) from American Pinball: Remake **+ 1 older**: Cirqus Voltaire (Bally, 1997)
- [bon-jovi](model-families/bon-jovi) from Barrels of Fun: Bon Jovi
- [fish-tales](model-families/fish-tales) from Cardona: Ultimate Fishing Challenge (Kit) **+ 1 older**: Fish Tales (Williams, 1992)
- [arabian-nights](model-families/arabian-nights) from Pedretti: Tales of the Arabian Nights 30th Anniversary + Legacy Edition **+ 1 older**: TOTAN (Williams, 1996)
- [musketeers](model-families/musketeers) from HEXA: The 3 Musketeers base + Elegance Edition
- [p3-modules](model-families/p3-modules) from Multimorphic: Dungeon Crawler Carl, Ender's Game
- [yukon-yeti](model-families/yukon-yeti) from Turner: Yukon Yeti
- [ramps-pinball](model-families/ramps-pinball) from Ramp's: Monster League Hockey **+ 2 siblings**: Road Trip, Little Shop of Horrors
- [resident-evil](model-families/resident-evil) from World Pinball: Resident Evil — mostly **corporate-entity** work, see below
- [obsidian-high](model-families/obsidian-high) from UP Pinball: The Fiery End of Obsidian High
- [pokemon](model-families/pokemon) from Stern: Pokémon Pro / Premium / Limited Edition — **not created by 0215**; all three were already in the catalog, and are just as bare as the rest

The data patch is `patches/NNNN-<family-slug>.yaml` with NNNN the claimed number. The patch id is the filename stem — the YAML carries no id of its own — so renumbering is a rename the generator's `OUT` path must follow. A patch that attaches vocabulary from another patch must be numbered **after** it (patches apply in numeric-prefix order): that is why Houdini's feature patch is 0219, after the 0218 vocab.

Each model family campaign will be done by separate AI sessions; each one is indpendant work. Numbers already claimed: 0215 (models), 0216 (Houdini), 0217 (citation roots), 0218 (presentation-feature vocab), 0219 (Houdini features).

## Complete each model family's older siblings

Each per-family campaign fleshes out any missing data for **the whole family**, not just its 2026 member(s). This is because a family's primary documents mostly describe the _older_ machines -- for example, American Pinball's Houdini manual is 193 pages about the **2017** game; the GTF manual is the **2023** game; Cardona's kit documents install into Williams **1992** Fish Tales. An AI session holding those documents is already holding the evidence for the other models.

Don't overwrite data on existing models; only assert missing facts. If you think an existing fact is wrong you must get user approval to correct it.

## Research and fetch primary documents

This is new. We haven't done any patches like as follows before because we couldn't. We just revamped search, OCR and PDF handling in [Pinexplore's web cache](~/dev/pinexplore/docs/WebCache.md) and should now be able to source most facts from the manufacturer's own PDFs, at least for manufacturers that provide PDF flyers and manuals. This will be a bit of a test run of the new features in web cache, so LMK if there's any ways they could be improved.

Find as many primary documents for a model family as exist -- see `~/dev/flipcommons/docs/DataPatchAuthoring.md`#`Prefer primary sources`. Put them all in the [web cache](~/dev/pinexplore/docs/WebCache.md), even if you aren't sure they contain citable information. This makes the documents searchable and available to every later session; a document you looked at and did not fetch will probably be re-looked at by later sessions, so just get it.

`DataPatchAuthoring.md` is the authority on what a primary source is, but now that we're making a concerted effort to get more primary source, we are trying to get [crisper and more detailed as to what consitues a primary source](#primary-and-secondary-sources).

## PDF gotchas

- **PDFs over 100MB can't be `Read`** — Claude Code has a 100MB `Read` cap. Instead, extract the one sheet you need with `pypdf` to a scratch file first, then `Read` that. Or ask the user to get Pinexplore to provide a page extractor.
- **`outline` on a PDF is a flat page map.** It ignores the embedded bookmark tree. Most PDFs don't have one or they're useless garbage, but a few do. Read bookmarks with `pypdf` when you need a real table of contents.

## Process notes

**Houdini is the worked example** — the loop it proved (its `Houdini.md` is the full audit trail):

1. **Baseline survey — every field the patch might touch.** Table the catalog's current state per model (fields, credits, features, themes, lineage, `production_quantity`, `tag`, month). Houdini's first pass skipped `production_quantity`/`tag` and re-asserted what 0215 already set — the miss of the campaign so far. Only assert what's missing.
2. **Duplicate scan is against `model_claims` from other actors, not `patch_claims`.** The apply **silently swallows** an exact duplicate (same actor + claim key + value — no claim row, and its citation is dropped with it), so what your patch wrote is not what it asserted. (A flippatch AI session is reviewing whether that swallow should stay.)
3. **Evidence inventory into the family's own `<Family>.md`** — what's cached, what each document actually carries, traps — before extracting claims.
4. **Pre-verify every gated quote before generating**: drive `check_quote` via `_Sources` from `scripts/quote_verify` against the exact spans the generator will emit. Houdini shipped 41/41 on first `make verify-quotes` because every span was checked first.
5. **Facts inline in `gen.py`** (patchkit emitter) at family scale — a handful of models doesn't need the 0215 CSV architecture. Record user decisions in the family notes with dates.
6. **Snapshot loop freely** ([Rebuilding the database](#rebuilding-the-database)), verify resolution through `make analyze` (`patch_entry_cites` shows each claim with its quote and note).

**Check the feature vocabulary before creating terms** — 0218 (presentation features) and 0219 (Houdini's mechs/toys: subways, stages, trunks, marquees, balls, flipper-toppers, cabinet-armor, mylar…) added many nodes, and the seed has surprises (`ball-locks` already existed; Houdini's first apply failed on the duplicate create). Query `gameplay_feature_vocab` for your exact slugs — and don't `tail` the output.

**The variant rule (user decision, 2026-08-07):** a variant carries every credit of its base, and the shared design's hardware is a fact about every edition. Cite the base's evidence (e.g. the base IPDB row) with a `note:` saying why the value carries. **Feature wording (user decision, 2026-08-08):** represent ALL features in `gameplay_feature`, presentation or not (0218's charter); use the manufacturer's wording verbatim unless it's extremely clearly a synonym; when in doubt, create a child feature. Watch false synonyms — flipper toppers are not cabinet `toppers`.

We have an AI-based tool for extracting all the information from a model: [ModelPageExtractionAuthoring.md](../../docs/page_extractor/ModelPageExtractionAuthoring.md). It's never worked very well, and Houdini didn't need it (three models, hand-vetted). A bigger family (Transformers' ~55×3 matrix) might; investigate there.

Each family will probably have a `gen.py` to generate the patches. Use [DataPatchKit.md](../../../flipcommons/docs/DataPatchKit.md) for the emitter; never hand-roll YAML escaping.

Whatever shape a family picks, `cite_kind` has to be recorded rather than inferred later, because the emitter writes the two kinds differently: a `quote` cite carries a transcribed span, a `mark` cite carries a visual observation in a `note` with no `quote:`. Which one a row is depends on whether the evidence is text or a mark — see [Citing PDF evidence](#citing-pdf-evidence). Note this is a fact about the **evidence**, recorded in the generator's own input so the emitter can branch; it is never a claim in the patch about whether the quote is verifiable.

**`draft-evidence-aggregator.csv` is not a generator input.** It is a **superseded draft**: 166 of its 181 cites are Pinside, not a primary source, and we'd rather use primary sources. Use it as a **research checklist**, naming people and roles worth going to look for in primary documents, and corroborating info from other places.

## Citation roots

A URL cite fails the apply unless its host resolves to a seeded citation root. Maker subdomains resolve for free by longest-label-boundary suffix (`wp.sternpinball.com` → Stern, `marketing.jerseyjackpinball.com` → Jersey Jack), and a leading `www.` is normalized away, so a root registers bare and both forms resolve. CDN hosts do not resolve.

**The shared roots are already seeded — `patches/0217-enrichment-citation-roots.yaml` does it.** Do not re-declare them and do not invent roots of your own. It attaches American Pinball's two document hosts (`48804760.fs1.hubspotusercontent-na1.net`, `my.orbitgames.fun`) to the **existing** American Pinball root, and creates the **Planetary Pinball** root for the licensed Williams/Bally material the pre-2000 halves of several families rest on. It takes 0217 — originally Houdini's spare — because a roots patch has a hard ordering constraint that a family follow-up does not: patches apply in numeric-prefix order, so a root must be numbered below every patch that cites it, whereas a family's second patch only needs to follow its first and can take any later free number.

A root your family needs that 0217 does not cover is a **single-family** root, and it belongs in your own family patch — Cardona (`cardonapinball.com`) is the known case, and it rides in the fish-tales family's patch whenever that claims its number. The `sources:` block is **additive get-or-create**, matched by recognition host: a node matching an existing root has missing hosts backfilled and existing fields left alone, so a re-declaration is a harmless no-op. **Do not modify 0215 or 0217 and do not renumber.** The form:

```yaml
sources:
  - name: Cardona Pinball Designs
    source_type: web
    description: Manufacturer's own site. # only on a NEW root; a match ignores it
    links:
      - { url: "https://cardonapinball.com/", link_type: homepage }
```

**Attach a maker's document host to that maker's existing root, never to a new one.** Splitting AP's manuals off from AP's product pages would put one company's evidence under two sources, and nothing in the apply catches it — which is exactly why 0217 settles the shared hosts once instead of leaving them to whichever family session runs first.

Check what citation sources already resolve; most makers already do:

```sql
SELECT h.host, coalesce(cr.root_citation_source_name,'NO ROOT')
FROM (VALUES ('wp.sternpinball.com'), …) h(host)
LEFT JOIN citation_roots cr ON cr.root_citation_source_id = citation_root_for_host(h.host);
```

**Shared hosts must never be registered.** `cdn.shopify.com`, `img1.wsimg.com` and `storage.googleapis.com` carry many makers' files with the tenant id in the **path**, and recognition reads only the host — so registering any of them would resolve every unrelated URL on that CDN to one maker. There is no host string that means "this maker's corner of the CDN", which makes these unregisterable rather than merely unregistered. Prefer a maker-domain URL where one exists — the Sonic _manual_ is on `marketing.jerseyjackpinball.com`, and only the compare flyer is on Shopify — and otherwise treat the document as research-only: findable, not citable. Note the restraint is documentation, not enforcement: flipcommons hard-refuses "deliverer" hosts (Amazon, Netflix, Google Books) via `deliverers.py`, but no CDN is in that table.

**`web.archive.org` is deliberately rootless.** A cite carries an `archive:` key for exactly this: `ref` the original publisher URL, `archive:` the snapshot. Registering archive.org would make the archive the source rather than the publisher. This is the route for a maker document that has gone 404 — American Pinball's Houdini flyer is the worked case, dead on `american-pinball.com` but recoverable from Wayback, and citable because the original host resolves. Two traps: fetch the snapshot with Wayback's `id_` modifier (`/web/<timestamp>id_/<url>`) or you cache the HTML wrapper instead of the document — it reports a clean `200` either way — and the cache then holds the document under the _snapshot_ URL while the cite's `ref` is the original. `make verify-quotes` handles that second trap since 2026-08-08: when the `ref` isn't in the cache it resolves through the cite's `archive:` URL, so an archived document's quotes verify (or report `SKIP-PDF` for a PDF) instead of failing `NO-SOURCE`. Houdini's 0219 flyer cites are the worked example.

**`ipdb:` cites can now quote the structured row, credits included.** Since 2026-08-08 the quotable slice of an IPDB row (`ipdb_row_text` in `scripts/quote_verify/verify_quotes.py`) renders `Model Number:`, `MPU:` and the person-credit lines (`Design by:`, `Art by:`, `Dots/Animation by:`, `Mechanics by:`, `Music by:`, `Sound by:`, `Software by:`) exactly as the IPDB page shows them. This is how a variant's replicated credits get gated evidence — see the variant rule in [Process notes](#process-notes) — and it matters for every family with IPDB-rowed older siblings (Transformers 2011, Fish Tales, TOTAN).

## Citing PDF evidence

We haven't cited a lot of PDFs before because Pinexplore web cache didn't have the OCR and search to find the information. Now that we do, we need to establish some ground rules.

**PDFs often have TWO page numbers**: the printed one and the sheet index. Locators should name both: `printed page 7, PDF document page 22`. Get the printed folio by rendering the sheet unless it's super super clear from the text.

**Quote the words on the sheet — the text layer does not decide what's quotable.** Render the sheet, read the words, transcribe them into `quote:`. The Bon Jovi flyer's type is outlined so it has no text layer at all, and Stern's 2011 `Transformers-Manual.pdf` has none either (227K chars of OCR and nothing else) — the words are still words, and a transcription you made by looking is evidence. `make verify-quotes` **does not gate PDF quotes**; it reports them `SKIP-PDF`. That is deliberate: a correct span read off a sheet routinely isn't a substring of the reading-order extraction, and checking the OCR tier instead rejects ~25% of correct spans (measured on this corpus), so no threshold makes it honest. A PDF quote is your own check — transcribe it exactly as the next person rendering that sheet would read it. Nothing goes in the patch about which quotes are gated; the patch is the record.

**A mark is not text — that case is still quote-less.** A checkmark in a feature-matrix column, a diagram arrow, a filled cell: looking at it does not produce words to transcribe, so there is nothing to quote. The honest cite stays `ref` + `locator` naming the sheet + `note` recording what was seen, with no `quote:`. The line is whether the evidence **is** text, not whether extraction caught it.

**Do not quote the row label to establish a column.** `"Megatron Pinball Firing Fusion Cannon."` is verbatim, but it establishes the _row_, not the Premium/LE column. The AI linter's `RULE_QUOTE_SUPPORTS_CLAIM` will reject it. Being able to quote pixel text does not soften this — reading that label off the render splices exactly the same way.

## Primary and secondary sources

The authority on primary sources is `~/dev/flipcommons/docs/DataPatchAuthoring.md`#`Prefer primary sources`. Here we're noodling on a more detailed list, in rough order of what source is most authoritative:

### Best first party

- **The maker's own website**, and specifically its support, downloads, service and product pages — these are where flyers, feature matrices, manuals, quick-reference guides, service bulletins and release notes live.

### Other first party

- **The maker's YouTube channel**: the cache ingests transcripts, and reveal and gameplay videos are first-party.
- **Distributor and archive** copies where the maker's own copy is gone: archive.org, distributor sites, Planetary Pinball for Williams/Bally titles.
- For a **remake or a kit**, the _original_ machine's documents too — they are what the new one is derived from.
- For a **homebrew**, the builder's own build thread on a 3rd party site.
- **press releases**: the maker's own words reprinted verbatim by a publication, datelined and attributed

### Journalism

- **journalism**: a named outlet's own reporting — Pinball News, Arcade Heroes, Kineticist _news articles_.

Acceptable where nothing above states the fact; prefer multiple independent outlets.

### Crowdsourced

User-submitted database rows — Pinside game archive, Kineticist _game index_.

Do not use for any model that has a manufacturer PDF\*\*. Elsewhere, never the sole support for a claim.

Where a family's sources are thin, the reason differs per family and determines what to do — each is recorded in that family's own notes. Where nothing is available, the model gets **nothing beyond what 0215 already created**.

## Rebuilding the database

Standing recipe (user, 2026-08-08) — rebuild as often as you like:

```bash
cd ../flipcommons/backend
cp db.prod.patch-0214.2026-08-03.sqlite3 db.sqlite3
uv run python manage.py migrate
uv run python manage.py ingest_patches --patches-dir ../../flippatch/patches
```

If that snapshot file is gone or another campaign has moved the baseline, ask the user before picking a different one.
