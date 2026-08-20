# Missing years

We have a lot of models that are missing years. This is a very basic and important piece of identifying a model: `Godzilla (Stern 2021)`. You basically triangulate on name, mfr, year.

Anyway, for plenty of our missing-year models, plenty of OTHER catalog sites have years. We need not and should not rely solely on IPDB.

We need years for as many machines as possible and I'm okay mining catalog sites.

## Xantari IPDB dump was incomplete

IPDB's website shows years for many machines for which we do NOT have years. An example: we have no year for `models/ice-castle` but IPDB does. This means that our baseline ingest from IPDB was incomplete. We did some research and figured out what happened. There's two causes:

1. our original baseline IPDB dump was missing data
2. we incompletely extracted data from that dump

We got our original baseline IPDB info from a JSON dump, `~/dev/pinexplore/ingest_sources/ipdb_xantari.json` . It's still accessible via the pinexplore DuckDB. Most of the information has already been incorporated into the Flipcommons database.

`ipdb_xantari.json` has **two** date carriers:

- `DateOfManufacture` — the structured field, present on 5,265 of 6,664 records. **This is the only one our ingest read.**
- `AdditionalDetails` — present on **all 6,664**, and it is verbatim the header line IPDB renders on the machine page: `IPD No. 3711 / May, 1989 / 4 Players`. **zero** records contain a year the parser fails to extract (no unparsed remainder), and where both fields exist the parse **agrees with `DateOfManufacture` 5,265 / 5,265 — no disagreements**. The regex is not guessing; it is reading a fixed-format field. We realized that the Xantari dump missed a concept in IPDB: Project Date, which is distinct from Production Date. `AdditionalDetails`'s date is the production date if it exists, else project date. Pinexplore now has the `AdditionalDetails` date information parsed out in a new `ipdb_machine_additional_details` view, added in `04_staging.sql`.

In addition, the dump contains other fields that we simply didn't notice, such as:

- Specialty
- PhotosIn
- Source
- ConceptBy
- EasterEggs

In addition, the dump did not contain other information, such as:

- `Production:` when it wasn't a quantity but a status like `Never Produced`.

## Catalog site sweep options

Options to sweep missing data from catalog sites. This is unfinished.

## Option 1: Table

Build a CSV or SQLite DB or DuckDB with data from multiple sites. Maybe a table with columns something like

model_id ⬅️ Flipcommons ID
model_slug ⬅️ Flipcommons model slug
year ⬅️ Flipcommons year
month ⬅️ Flipcommons month
manufacturer ⬅️ Flipcommons manufacturer

ipdb year / month manufactured
ipdb year / month of project
ipdb specialty
ipdb additional_details
ipdb photos_in
ipdb source
ipdb concept_by
ipdb easter_eggs

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
