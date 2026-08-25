# External Data Source Identity

The [external data source layer](../scripts/analysis/external_data_sources.sql)'s job is to compare dumps of external systems -- IPDB and OPDB currently -- with the Flipcommons catalog.

The only way that we can compare deterministically via analytics is if we can deterministically link IPDB and OPDB records to Flipcommons records. Flipcommons records already have ID fields for the external records, like Model.opdb_id and Title.opdb_id (an OPDB Group). Over 95% of the catalog is already linked. We need to link the remaining ones.

Process-wise, when using the external data source comparison layer, we should link records before doing any other comparison work.

There's already a draft of the ID matching in the external data source layer, but it's not complete. The ID mapping must be provably correct; it's the foundation upon which everything else rests.

This doc is a draft of thinking through how the provably correct ID linking should work.

## Rules

In priority order:

### Link by ID

#### Existing linkages

If an IPDB / OPDB record already has a Flipcommons record pointing at it, there's nothing to do; it's already linked.

Exception: when the external source itself retires the ID. See `opdb-id-moved` / `-deleted` / `-container` and `ipdb-id-retracted`.

#### OPDB's `ipdb_id`

More than 90% of OPDB listings have an `ipdb_id` that links it to an IPDB model. If an OPDB machine has an `ipdb_id`, link it except in the following cases:

- When OPDB's `ipdb_id` resolves to a catalog model that already carries a different `opdb_id`
- When the OPDB machine's group and the ipdb-resolved model's title disagree.
- When multiple IPDB listings point to the same IPDB ID. For example, both OPDB's `Metallica Road Case (Premium)`and `Metallica (Premium)` both point to IPDB 6029, `Metallica (Premium Road Case)`. OPDB splits variants finer than IPDB.

If the transitive chain contradicts, it's a finding, never a link.

### Entity type tiers

After linking what we can by ID, there's a tier order in which we should resolve identities. Each stage's links rely on the links of the prior stages.

- **[Match Manufacturers](#match-manufacturers)**. And Corporate Entities (IPDB only).
- **[Match Titles](#match-titles) (OPDB only)**
- **[Match Models](#match-models)**

We shouldn't move on from one tier until we've fully resolved prior tiers.

I'd imagine we'd create a data patch for Manufacturers, matching Manufacturer IDs and creating new Corporate Entities & Manufacturers. Then resolve Titles and create a Title data patch. Then resolve Models.

Note this isn't a strict DAG: Title matching partly depends on looking at what Models have already been ID-linked. But we can do that because we've already ID-linked so many Models.

#### Match Manufacturers

We must resolve Corporate Entity at the same time as Manufacturer. In both Flipcommons and IPDB, the actual dependency runs model -> Corporate Entity -> Manufacturer. Corporate Entity cannot exist in the Flipcommons DB without its Manufacturer; `CorporateEntity.manufacturer_id` is a required field.

- [Match by manufacturer ID](#existing-linkages). If Flipcommons already has linked to the record, we're done.

#### Match Titles

- [Match by title ID](#existing-linkages). If Flipcommons already has linked to the record, we're done.
- Mactch by name + year of first model

#### Match Models

Rules:

- [Match by model ID](#existing-linkages). If Flipcommons already has linked to the record, we're done.
- Next we match by a combination of manufacturer, title, year and name. I think the pinball community thinks of model identity as a triangulation: (name, manufacturer, year), for the very good reason that it does accurately identify models:
  - **Manufacturer**. We already [linked manufacturers](#match-manufacturers), so this should be automatic.
  - **Title**. Every OPDB machine carries a group ID (`title_opdb_id`) that resolves against `Title.opdb_id`. We already [linked groups to titles](#match-titles), so this should be automatic. This only works for records coming from OPDB.
  - **Year**. The year must be ±1 from a Flipcommons year.
  - **Name**. OPDB often spells models differently from Flipcommons or IPDB. Whereas OPDB abbreviates like `Godzilla LE` Flipcommons and IPDB spell out `Godzilla (Limited Edition)`. Fixing these mismatches is a job for aliases.

There must be exactly one match. If multiple models match, that's not a match.

NEVER attempt to link if either manufacturer, year or name is missing. That's called a GUESS and it's unacceptable. That's how bad data enters the system. This job is not to match every record, only PROVABLY CORRECT records.

**Match IPDB before OPDB**. Because OPDB models have IPDB IDs but the OPDB names are less likely to match than IPDB, we should match IPDB first, then match OPDB including by IPDB ID.
