"""Deterministic catalog-domain shared code — the flipcommons-specific layer.

The middle tier of the ``common`` layering its own modules name: domain-neutral
primitives (``Json``) live in :mod:`common.types`; the AI-judgment tooling lives
in :mod:`common.ai`; this package sits between them with the catalog vocabulary
and lookups both depend on, and neither of those is AI. It holds the catalog
string :mod:`~common.catalog.types` (``EntityType``/``TableName``/``Slug``/…) and
:mod:`~common.catalog.entity_index` — the name/alias → entity index read straight
from flipcommons' dev SQLite (no Django), used by the lint's mention rules and by
the extraction tool's target resolution.
"""
