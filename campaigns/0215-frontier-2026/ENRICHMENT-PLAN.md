# 2026 model enrichment

Patch `0215-frontier-2026.yaml` created names and themes some new-for-2026 models, but nothing else: no credits, gameplay features, production_status, game_format, cabinet, display, system etc.

We now want to fully flesh them out, as described in `/Users/moses/dev/flipcommons/docs/DataPatchAuthoring.md`#`Fill every field you can — grounded in DomainModel.md`.

## Model families

Each separate model family gets its own mini-campaign folder in campaigns/0215-frontier-2026/model-families. Numbers are spaced two apart in case the work needs a second:

- [0216-houdini](model-families/0216-houdini) from American Pinball: 100th Anniversary **+ 2 older**: Master of Mystery, Master of Mystery (Deluxe)
- [0218-transformers](model-families/0218-transformers) from Stern: MTMTE Pro / Premium / LE **+ 5 older**: Transformers Pro & LE (2011), Autobot Crimson LE, Decepticon Violet LE, The Pin (2012)
- [0220-sonic-hedgehog](model-families/0220-sonic-hedgehog) from Jersey Jack: Collector's / Special / Arcade Edition
- [0222-galactic-tank-force](model-families/0222-galactic-tank-force) from American Pinball: Victory Edition **+ 4 older** (2023): Classic, Deluxe, Limited Edition, Signature
- [0224-cirqus-voltaire](model-families/0224-cirqus-voltaire) from American Pinball: Remake **+ 1 older**: Cirqus Voltaire (Bally, 1997)
- [0226-bon-jovi](model-families/0226-bon-jovi) from Barrels of Fun: Bon Jovi
- [0228-fish-tales](model-families/0228-fish-tales) from Cardona: Ultimate Fishing Challenge (Kit) **+ 1 older**: Fish Tales (Williams, 1992)
- [0230-arabian-nights](model-families/0230-arabian-nights) from Pedretti: Tales of the Arabian Nights 30th Anniversary + Legacy Edition **+ 1 older**: TOTAN (Williams, 1996)
- [0232-musketeers](model-families/0232-musketeers) from HEXA: The 3 Musketeers base + Elegance Edition
- [0234-p3-modules](model-families/0234-p3-modules) from Multimorphic: Dungeon Crawler Carl, Ender's Game
- [0236-yukon-yeti](model-families/0236-yukon-yeti) from Turner: Yukon Yeti
- [0238-ramps-pinball](model-families/0238-ramps-pinball) from Ramp's: Monster League Hockey **+ 2 siblings**: Road Trip, Little Shop of Horrors
- [0240-resident-evil](model-families/0240-resident-evil) from World Pinball: Resident Evil — mostly **corporate-entity** work, see below
- [0242-obsidian-high](model-families/0242-obsidian-high) from UP Pinball: The Fiery End of Obsidian High
- [0244-pokemon](model-families/0244-pokemon) from Stern: Pokémon Pro / Premium / Limited Edition — **not created by 0215**; all three were already in the catalog, and are just as bare as the rest

The data patch should be `patches/NNNN-<family-slug>.yaml`. The patch id is the filename stem — the YAML carries no id of its own — so renumbering is a rename the generator's `OUT` path must follow.

## Complete each model family's older siblings

Each per-family campaign fleshes out any missing data for **the whole family**, not just its 2026 member(s). This is because a family's primary documents mostly describe the _older_ machines -- for example, American Pinball's Houdini manual is 193 pages about the **2017** game; the GTF manual is the **2023** game; Cardona's kit documents install into Williams **1992** Fish Tales. An AI session holding those documents is already holding the evidence for the other models.

Don't overwrite data on existing models; only assert missing facts. If you think an existing fact is wrong you must get user approval to correct it.

## ModelPageExtractor?

We have an AI-based tool for extracting all the information from a model: [ModelPageExtractionAuthoring.md](../../docs/page_extractor/ModelPageExtractionAuthoring.md). It's never worked very well, but now would be the time to use it, and maybe now with PDFs it'll work better. We should at least do a little investigating.

## Research and fetch primary documents

This is new. We haven't done any patches like as follows before because we couldn't. We just revamped search, OCR and PDF handling in [Pinexplore's web cache](~/dev/pinexplore/docs/WebCache.md) and should now be able to source most facts from the manufacturer's own PDFs, at least for manufacturers that provide PDF flyers and manuals. This will be a bit of a test run of the new features in web cache, so LMK if there's any ways they could be improved.

Find as many primary documents for a model family as exist -- see `~/dev/flipcommons/docs/DataPatchAuthoring.md`#`Prefer primary sources`. Put them all in the [web cache](~/dev/pinexplore/docs/WebCache.md), even if you aren't sure they contain citable information. This makes the documents searchable and available to every later session; a document you looked at and did not fetch will probably be re-looked at by later sessions, so just get it.

`DataPatchAuthoring.md` is the authority on what a primary source is, but now that we're making a concerted effort to get more primary source, we are trying to get [crisper and more detailed as to what consitues a primary source](#primary-and-secondary-sources).

## PDF gotchas

- **PDFs over 100MB can't be `Read`** — Claude Code has a 100MB `Read` cap. Instead, extract the one sheet you need with `pypdf` to a scratch file first, then `Read` that. Or ask the user to get Pinexplore to provide a page extractor.
- **`outline` on a PDF is a flat page map.** It ignores the embedded bookmark tree. Most PDFs don't have one or they're useless garbage, but a few do. Read bookmarks with `pypdf` when you need a real table of contents.

## Each model family gets its own generator

Each family should have its own `gen.py`. Use [DataPatchKit.md](../../../flipcommons/docs/DataPatchKit.md) for the emitter; never hand-roll YAML escaping.

Whatever shape a family picks, `cite_kind` has to be recorded rather than inferred later: a `render` cite carries a visual observation in a `note` with no `quote:`, and the emitter writes the two differently. See [Quote-less cites](#quote-less-cites-and-the-trap-they-exist-to-stop).

**`draft-evidence-aggregator.csv` is not a generator input.** It is a **superseded draft**: 166 of its 181 cites are Pinside, not a primary source, and we'd rather use primary sources. Use it as a **research checklist**, naming people and roles worth going to look for in primary documents, and corroborating info from other places.

## Citation roots

A URL cite fails the apply unless its host resolves to a seeded citation root. Maker subdomains resolve for free by longest-label-boundary suffix (`wp.sternpinball.com` → Stern, `marketing.jerseyjackpinball.com` → Jersey Jack). CDN hosts do not.

The `sources:` block is **additive get-or-create**: a node matched to an existing root by recognition host has missing hosts backfilled and existing fields left alone, so re-declaring the same root in two patches is a no-op. **Do not modify 0215 and do not renumber.** Declare what you need:

```yaml
sources:
  - name: American Pinball
    source_type: web
    links:
      - { url: "https://americanpinball.com/", link_type: homepage }
    domains: # extra recognition hosts beyond the homepage
      - 48804760.fs1.hubspotusercontent-na1.net # AP's HubSpot portal — the account id is in the host
      - my.orbitgames.fun
```

Check what citation sources already resolve; most makers already do:

```sql
SELECT h.host, coalesce(cr.root_citation_source_name,'NO ROOT')
FROM (VALUES ('wp.sternpinball.com'), …) h(host)
LEFT JOIN citation_roots cr ON cr.root_citation_source_id = citation_root_for_host(h.host);
```

**Shared hosts must never be registered.** `cdn.shopify.com` and `img1.wsimg.com` carry many makers' files and their account id is not in the host, so registering either would resolve every unrelated URL on it to one maker. Prefer a maker-domain URL where one exists — the Sonic _manual_ is on `marketing.jerseyjackpinball.com`, and only the compare flyer is on Shopify — and otherwise treat the document as research-only: findable, not citable.

## Citing PDF evidence

We haven't cited a lot of PDFs before because Pinexplore web cache didn't have the OCR and search to find the information. Now that we do, we need to establish some ground rules.

**PDFs often have TWO page numbers**: the printed one and the sheet index. Locators should name both: `printed page 7, PDF document page 22`. Get the printed folio by rendering the sheet unless it's super super clear from the text.

**Some PDF evidence isn't quotable**. A checkmark in a feature matrix is vector art; the Bon Jovi flyer's text is outlined, so it has no text layer at all. The honest cite is `ref` + `locator` naming the sheet + `note` recording what was seen, with no `quote:`.

**Do not quote the row label to establish a column.** `"Megatron Pinball Firing Fusion Cannon."` is verbatim, but it establishes the _row_, not the Premium/LE column. The AI linter's `RULE_QUOTE_SUPPORTS_CLAIM` will reject it.

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

When you need the dev db rebuilt, ask user what to do.
