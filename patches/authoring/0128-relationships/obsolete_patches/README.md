# Parked patches

Patches in this directory are **not** part of the active patch set: `patches/` discovery (validation, ingest, and `make push`) is a non-recursive `patches/*.yaml` glob, so nothing here is validated, ingested, or published. They are held here — with their prose and citations intact — until a feature they depend on ships.

## `0126-tag-descriptions.yaml`

Parked as part of step 8 of the [Model Relationships](../../../flipcommons/docs/plans/catalog_data_model/ModelRelationships.md) plan. It described the `bootleg` and `licensed-build` composite tags, but the Model Relationships design has no vocabulary rows for those concepts (bootleg = `copy` × `unlicensed` and licensed-build = `copy` × `licensed` are cross-axis composites with no first-class representation), and patch 0039 no longer creates the tags. Its two composite descriptions are Page-shaped content: when the Articles/Page feature lands, they seed the bootleg / licensed-build page articles, citations intact, and the remaining `[[tag:...]]` links inside them get relinked as `[[page:...]]`.
