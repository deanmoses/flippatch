# External Data Source Identity

The [external data source layer](../scripts/analysis/external_data_sources.sql)'s job is to compare dumps of external systems -- IPDB and OPDB currently -- with the Flipcommons catalog.

The only way that we can compare deterministically via analytics is if we can deterministically link IPDB and OPDB records to Flipcommons records. Flipcommons records already have ID fields for the external records, like Model.opdb_id and Title.opdb_id (an OPDB Group). Flipcommons already links over 95% of IPDB and OPBD records. We need to link the remaining ones.

Process-wise, when using the external data source comparison layer, we should link records before doing any other comparison work.

This ID mapping must be [provably correct](#testing-the-rules); it's the foundation upon which everything else rests.

This doc is a draft of thinking through how the ID linking should work.

## Rules

In order of evaluation:

### Link by ID

#### Existing linkages

If an IPDB / OPDB record already has a Flipcommons record pointing at it, there's nothing to do; it's already linked.

Exception: when the external source itself retires the ID. See `opdb-id-moved` / `-deleted` / `-container` and `ipdb-id-retracted`.

#### OPDB's `ipdb_id`

More than 90% of OPDB listings have an `ipdb_id` that links it to an IPDB model. If an OPDB machine has an `ipdb_id`, link it except in the following cases:

- When OPDB's `ipdb_id` resolves to a catalog model that already carries a different `opdb_id`
- When the OPDB machine's group and the ipdb-resolved model's title disagree.
- When multiple OPDB listings point to the same IPDB ID. For example, both OPDB's `Metallica Road Case (Premium)`and `Metallica (Premium)` both point to IPDB 6029, `Metallica (Premium Road Case)`. OPDB splits variants finer than IPDB.

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

We must resolve Corporate Entity at the same time as Manufacturer.

Background:

In both IPDB and Flipcommons, the dependency runs Model -> Corporate Entity -> Manufacturer. Corporate Entity cannot exist in the Flipcommons DB without its Manufacturer; `CorporateEntity.manufacturer_id` is a required field. The Flipcommons field `CorporateEntity.ipdb_manufacturer_id` is a misnomer: it links to an IPDB Corporate Entity _not_ an IPDB Manufacturer. For _some_ Corporate Entities, IPDB also has a Trade Name or Short Name as part of the Corporate Entity's name, which Pinexplore parses out as a separate field; that Short Name is the name of a Flipcommons Manufacturer. For Short Name, IPDB just has the string name and not an ID.

OPDB does not have the concept of Corporate Entity. It links models to Manufacturer; Flipcommons links back with `Manufacturer.opdb_manufacturer_id`.

Titles can cross Manufacturers. For example, Eight Ball Deluxe (both an OPDB Group and a Flipcommons Title) holds models by multiple Manufacturers: Bally (original), Taito, Bell Games, LTD do Brasil (copies / bootlegs). For every cross-manufacturer Title, every model that's not in the original Manufacturer should have some sort of model-to-model relationship like `remake_of`, `copy_of`, `export_edition_of`. Any relationship except `variant_of`, which cannot cross Manufcturers; that'd be an error. And... should we check this Title - Manufacturer agreement when linking Manufacturers or Titles... or both?

Sequence:

- **Match OPDB first** because its Group structure helps us sanity check better:
  - [Match OPDB Manufacturer ID to `Manufacturer.opdb_manufacturer_id`](#existing-linkages). If there's a match, we're done.
  - For the OPDB manufacturers that don't match a `Manufacturer.opdb_manufacturer_id`, resolve by already-linked models.
    - If an OPDB manufacturer contains models that are already linked to Flipcommons Models, and those Flipcommons Models are linked to a Flipcommons Manufacturer, AND the name/alias matches, that's a link. If the name/alias doesn't match, it's a proposal.
  - For the OPDB manufacturers that don't match a `Manufacturer.opdb_manufacturer_id`, match by name + alias.
    - OPDB must have at least one sister model (in the same OPDB Group), and at least one of those sister models must have the same manufacturer.
      - If OPDB doesn't have any sister models, it's a proposal not a link.
    - Flipcommons must have at least one sister model (in the same Flipcommons Title), and at least one of those sister models must have the same manufacturer.
      - If Flipcommons doesn't have any sister models, it's a proposal not a link.
    - There must be exactly one match. If multiple records match, there's no link. Surface the candidates.
- **Then match IPDB Corporate Entity**:
  - [Match IPDB Corporate Entity ID to `CorporateEntity.ipdb_manufacturer_id`](#existing-linkages). If there's a match, we're done.
  - For the IPDB Corporate Entities that don't have a matching `CorporateEntity.ipdb_manufacturer_id`, match by name + alias.
    - There must be exactly one match. If multiple records match, there's no link. Surface the candidates.
    - If Flipcommons has sister models (in the same Flipcommons Title) in a DIFFERENT manufacturer, the system's in an inconsistent state. Surface that.
- **Then match IPDB Manufacturer aka Short Name, if it has one**:
  - At this point we'll have already matched Corporate Entities, so we'll have the Flipcommons Manufacturer and the IPDB Short Name aka Trade Name (if one exists). So we're only matching between that pair of names, NOT a whole population. Only do this check if the IPDB Corporate Entity actually has a Short Name.
  - The IPDB Short Name must match the name or an alias of the Flipcommons Manufacturer.
  - If it does, that's the expected state. There's no ID linking to be done because IPDB has no short name ID.
  - If it doesn't, that's an ERROR.

Known manufacturer disagreements:

- **Sega**. There are three separate Sega Corporate Entities. IPDB only gives one of them, the 1990's Sega, a short name ("Sega"), meaning it treats all three Corporate Entities as separate brands. OPDB (which doesn't do CE's) files Sega vs Sega Enterprises as separate manufacturers / brands. Flipcommons editorial decision was to lump all three Sega Corporate Entities under a single Sega brand. Flipcommons isn't changing. This is a true disagreement, the comparison layer will flag it, and it's exactly where we need the "don't show me this disagreement again" system.

#### Match Titles

OPDB only; IPDB doesn't have the concept of a Title/Group.

THIS HAS NOT YET BEEN VETTED BY THE DEVELOPER:

- [Match OPDB's group ID against `Title.opdb_id`](#existing-linkages). If Flipcommons already has linked to the record, we're done.
- Match by the OPDB group's own machines. Two tiers:
  - If another OPDB machine in the Group is ID-linked to a Flipcommons model in that Group's Title, it's a link.
  - an unlinked machine votes the Titles of its name-and-maker candidates (family grain — deliberately year-blind and plural-tolerant, because a family spans years and a candidate set confined to one Title is a clean family vote even while the model-grain question is open).
    Exactly one distinct Title across all votes: that is the link.
    More than one: split_across_titles — OPDB groups what the catalog splits (tournament combos, bootleg families). Adjudicate per group: a correct catalog split is dismissed, a misfiled model is fixed. Never a link.
- Match by name + year of first model. Titles don't have aliases, so I guess we're going to hand-curate mismatches.

#### Match Models

Rules:

- [Match by model ID](#existing-linkages). If Flipcommons already has linked to the record, we're done.
- Next we match by a combination of manufacturer, title, year and name. I think the pinball community thinks of model identity as a triangulation: (name, manufacturer, year), for the very good reason that it does accurately identify models:
  - **Manufacturer**. We already [linked manufacturers](#match-manufacturers), so this should be automatic.
  - **Title**. Every OPDB machine carries a group ID (`title_opdb_id`) that resolves against `Title.opdb_id`. We already [linked groups to titles](#match-titles), so this should be automatic. This only works for records coming from OPDB.
  - **Year**. The year must be ±1 from a Flipcommons year.
  - **Name**. Match on name. OPDB often spells models differently from Flipcommons or IPDB. Whereas OPDB abbreviates like `Godzilla LE` Flipcommons and IPDB spell out `Godzilla (Limited Edition)`. Models don't have aliases, so I guess we're going to hand-curate mismatches.

There must be exactly one match. If multiple models match, that's not a match.

NEVER attempt to link if either manufacturer, year or name is missing. That's called a GUESS and it's unacceptable. That's how bad data enters the system. This job is not to match every record, only PROVABLY CORRECT records.

**Match IPDB before OPDB**. Because OPDB models have IPDB IDs but the OPDB names are less likely to match than IPDB, we should match IPDB first, then match OPDB including by IPDB ID.

## Testing the rules

This must be a robust system that spits out 100% correct matches that we can bank on with absolute conviction, and for the ones that aren't 100%, instead spits out the judging evidence. It MUST NOT spit out confident wrong answers; if it must err, err on the side of putting the items in a to-be-adjudicated-manually bucket.

So the system must be tested. We have 95% of the corpus that's already linked; let's have a testing system that evaluates the linking rules against the known-good set of records, and ensure that it assigns the known good linkages perfectly.
