# Missing IPDB data

We are realizing that our extraction of facts from IPDB was incomplete.

We noticed this because IPDB's website shows years for many machines for which we do NOT have years. An example: we have no year for `models/ice-castle` but IPDB does. This means that our baseline ingest from IPDB was incomplete.

We did some research and figured out what happened. There's two causes:

1. our original baseline IPDB dump was missing data
2. we incompletely extracted data from that dump

We got our original baseline IPDB info from a JSON dump, `~/dev/pinexplore/ingest_sources/ipdb_xantari.json` . It's still accessible via the pinexplore DuckDB. Most of the information has already been incorporated into the Flipcommons database.

Here's an example. `ipdb_xantari.json` has **two** date carriers:

- `DateOfManufacture`: the structured field, present on 5,265 of 6,664 records. **This is the only one our ingest read.**
- `AdditionalDetails`: present on **all 6,664**, and it is verbatim the header line IPDB renders on the machine page: `IPD No. 3711 / May, 1989 / 4 Players`.
  - **zero** records contain a year the parser fails to extract, and where both fields exist the parse **agrees with `DateOfManufacture` 100%: 5,265 / 5,265**. The regex is reading a generated, fixed-format field.
  - We realized that the Xantari dump missed a concept in IPDB: Project Date, which is distinct from Production Date. `AdditionalDetails`'s date is the production date if it exists, else project date. This explains the delta of models that have a `AdditionalDetails` date but no `DateOfManufacture`.
  - Pinexplore now has the `AdditionalDetails` date information parsed out in a new `ipdb_machine_additional_details` view, added in `04_staging.sql`.

In addition, the dump contains other fields that we simply didn't notice, such as:

- `PhotosIn`: `Pinball Ad Catalog Volume 2, 1934-1935, pages 285-286`
- `Source`: `pictures`

In addition, from looking at IPDB web pages rather than the dump, we can see the dump did not contain other fields, such as:

- `Production`: when it isn't a quantity but a status like `Never Produced`.
- `ConceptBy`:
- `EasterEggs`:
- `Specialty`:
- `Serial Number Database`:
- `Project Date`: as discussed

## Updates

### Flipcommons now supports Project Date

We added project date to Flipcommons. Flipcommons now has THREE date fields:

- **Project year/month**: date the machine was sent to manufacturer
- **Production year/month**: same as before, but renamed from year/month
- **year/month**: now derived, read-only. It's derived from production date, else fall back to project date, else none.

### We extracted the extractable Project Date info from xantari

We created a data patch (0268) that sets Project Date on all models that had no date at all. The Project Date was extracted from the xantari dump's `AdditionalDetails` field. The only way we knew it was a Project date was that these were the xantari records with no date field.

That's as much as we can do with the current xantari dump. For the rest of the models, the `AdditionalDetails` date matches `DateOfManufacture` and thus isn't the Project Date.

## Pulling IPDB from Archive.org

**⚠️ WARNING**: Archive.org does NOT have recent pages for IPDB; many are 2018 era. The Xantari dump is newer and more correct. **We must NEVER replace recent Xantari data with stale Archive.org data**.

### Fetching IPDB pages

Pinexplore's web cache now fetches IPDB pages better:

- I think the correct tool is `--from-file` batch mode plus `have` verification. This will handle Archive.org's rate limiting.
- Archive.org holds one machine's IPDB page under several spellings (?id=N, ?gid=N, bare ?N). Make sure to regularize: construct every URL from Flipcommons' ipdb_id as <https://www.ipdb.org/machine.cgi?id=><ipdb_id> . The live fetch will 403, the fetcher falls back to archive.org on its own, and the stored row is keyed under the IPDB URL. Read the "Fetching IPDB pages" section of ~/dev/pinexplore/docs/WebCache.md

### Extracting structured data

We now have a tool that takes an IPDB page (say from archive.org) and turns it into structured data: `~/dev/pinexplore/scripts/web_scrape/parse_ipdb.py`. It explicitly gets the fields we've noticed as missing.

### Saving structured data as JSONL

Then, `~/dev/pinexplore/scripts/web_scrape/extract_ipdb_to_jsonl.py` runs that parser over every IPDB machine page in pinexplore's web cache and writes `~/dev/pinexplore/ingest_sources/ipdb_archive/models.jsonl`, one object per model.

### Using the structured IPDB JSONL in Flippatch campaigns

Flippatch campaigns can use it with the Flipcommons analytics layer, something like `SELECT * FROM read_json_auto('../pinexplore/ingest_sources/ipdb_archive/models.jsonl', sample_size = -1)`, similar to how [../../scripts/analysis/evidence.sql](../../scripts/analysis/evidence.sql) gets web cache. Why `sample_size = -1`: the rarest fields are on a handful of models, and a sampled read types a real struct as NULL and loses it silently.
