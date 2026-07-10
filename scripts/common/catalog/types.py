"""Shared type vocabulary for the catalog-domain AI tooling.

Transparent aliases that name *which* string a value holds, so a ``dict[str, str]``
becomes a ``dict[EntityType, TableName]`` that says what it actually maps. They are
all ``str`` at runtime and interchange freely with it — the job is reasoning
clarity at call sites, not nominal enforcement (mixing two of them is not a type
error, and deliberately so: these strings get casefolded, sliced, and read
straight from SQLite, so ``NewType`` would only add wrapping ceremony).

Layering: domain-neutral primitives (e.g. ``Json``) live in ``common.types``; this
is the catalog/flipcommons-specific layer above it. And a type only lands here once
*more than one* consumer shares it — module-internal working types (e.g.
entity_index's normalized-key / surface-form types) stay in that module.
"""

from __future__ import annotations

type EntityType = str  # a catalog entity-type slug: "manufacturer", "model", …
type TableName = str  # a flipcommons SQLite table: "catalog_machinemodel", …
type Slug = str  # a catalog row's resolved (winning) slug
type Label = str  # a catalog row's display name
# An extractor field id ("technology_generation", "display_subtype"): the tools'
# own underscored field identifiers. Distinct from an EntityType's dash-cased slug
# ("technology-generation", the wikilink form) — separate types keep the two
# registries from being read as one.
type FieldKey = str
