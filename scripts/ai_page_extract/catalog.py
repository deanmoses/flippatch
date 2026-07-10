"""DB introspection — the *derived grounding layer* (legal vocab + real meanings).

The anti-duplication rule of AiPageDataExtractor.md: the tool must not hardcode a
field's legal values or their meanings. Both live in flipcommons, so a controlled
field's slice is grounded on the LIVE vocabulary and its real per-term
``description`` — when flipcommons adds a term, the slice covers it for free.

Read directly from flipcommons' dev SQLite (``backend/db.sqlite3``), the same way
``common.catalog.entity_index`` does, rather than booting the Django ORM: it keeps the
offline test seam (unit tests point at a tiny fixture DB, no sibling checkout) and
reuses ``entity_index.WIKILINKABLE`` as the type→table map. The localhost audit
that motivated this confirmed every small controlled vocab carries a populated
description; **themes** (hundreds of terms, no descriptions) and **credit roles**
(self-descriptive) are deliberately *not* grounded here — they use free-extract →
map and hand-crafted guidance respectively.

Descriptions carry flipcommons ``[[type:id:N]]`` wikilink markup; it is flattened
to the referenced entity's plain name before the text reaches a model, so the
grounding reads as prose rather than leaking internal ids.

``FIELD_VOCAB_TABLES`` is a generated mirror (same discipline as
``entity_index.WIKILINKABLE``); regenerate when flipcommons adds a vocab field.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

from common.catalog.entity_index import WIKILINKABLE

if TYPE_CHECKING:
    from pathlib import Path

    from common.catalog.types import EntityType, FieldKey, Label, Slug, TableName


class ParentLink(NamedTuple):
    """How a child vocab hangs off its parent: the parent value's field key and
    the FK column on the child table that joins to it."""

    parent_field: FieldKey
    fk_column: str


# Extraction field key → flipcommons vocab table. Controlled single-value / small
# enum vocab only (each term carries a real description). Large free-extract
# collections (themes) and tiny self-descriptive sets (credit roles) are handled
# elsewhere, not grounded here. Generated mirror; see the module docstring.
FIELD_VOCAB_TABLES: dict[FieldKey, TableName] = {
    "technology_generation": "catalog_technologygeneration",
    "technology_subgeneration": "catalog_technologysubgeneration",
    "display_type": "catalog_displaytype",
    "display_subtype": "catalog_displaysubtype",
    "cabinet": "catalog_cabinet",
    "game_format": "catalog_gameformat",
    "production_status": "catalog_productionstatus",
    "reward_type": "catalog_rewardtype",
    "tag": "catalog_tag",
}

# Each child vocab and the parent it refines. The dependency pairs the extractor
# resolves in one call. Generated mirror; see the module docstring.
CHILD_PARENT: dict[FieldKey, ParentLink] = {
    "technology_subgeneration": ParentLink(
        "technology_generation", "technology_generation_id"
    ),
    "display_subtype": ParentLink("display_type", "display_type_id"),
}

_WIKILINK = re.compile(r"\[\[([a-z-]+):id:(\d+)\]\]")


@dataclass(frozen=True, slots=True)
class VocabTerm:
    """One legal value of a controlled field: its slug, name, and real meaning.

    ``slug`` is the enum value a slice constrains the model to; ``description`` is
    the flipcommons prose (wikilinks already flattened), the grounding that tells
    the model what the term *means*.
    """

    slug: Slug
    name: Label
    description: str


class ChildTerm(NamedTuple):
    """A child vocab term paired with the slug of the parent value it refines.

    The shape a dependency-pair slice consumes (subgeneration under generation,
    display subtype under display type).
    """

    term: VocabTerm
    parent_slug: Slug


@dataclass(frozen=True, slots=True)
class ModelRef:
    """The catalog model an external-id source ref denotes: its slug and name.

    The result of resolving an ``ipdb:``/``opdb:`` ref through the model's stored
    external id — the ref side of the ref/target cross-check (the CLI shell diffs
    it against what ``--target`` resolves to by name).
    """

    slug: Slug
    name: Label


class CatalogDb:
    """Read-only introspection over flipcommons' dev SQLite.

    Constructed from the DB path (default ``common.related_projects.FLIPCOMMONS_DB``);
    unit-tested against a temp fixture DB, so it never needs a sibling checkout.
    """

    def __init__(self, path: Path) -> None:
        self._conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        self._name_cache: dict[TableName, dict[int, Label]] = {}

    def close(self) -> None:
        self._conn.close()

    def vocab_terms(self, field_key: FieldKey) -> tuple[VocabTerm, ...]:
        """The legal terms for a controlled field, in display order, descriptions flattened."""
        table = FIELD_VOCAB_TABLES[field_key]
        columns = {row[1] for row in self._conn.execute(f"PRAGMA table_info({table})")}
        order_by = "display_order" if "display_order" in columns else "name"
        rows = self._conn.execute(
            f"SELECT slug, name, description FROM {table} ORDER BY {order_by}"  # noqa: S608 — table from trusted constant map
        ).fetchall()
        return tuple(
            VocabTerm(
                slug=slug, name=name, description=self._flatten(description or "")
            )
            for slug, name, description in rows
        )

    def model_for_external_ref(self, source_ref: str) -> ModelRef | None:
        """The catalog model an ``ipdb:``/``opdb:`` ref denotes, keyed on its stored
        external id.

        None for a non-id ref (``http`` / ``youtube`` — nothing to key on) *and* for
        an id the catalog doesn't hold — the caller distinguishes the two by the
        scheme, and a scheme ref that resolves to None is itself a signal (the ref
        may name a model missing from the catalog). Structured id → model is a
        deterministic lookup, never an AI question.
        """
        scheme, _, ident = source_ref.partition(":")
        if scheme == "ipdb" and ident.isdigit():
            row = self._conn.execute(
                "SELECT slug, name FROM catalog_machinemodel WHERE ipdb_id = ?",
                (int(ident),),
            ).fetchone()
        elif scheme == "opdb" and ident:
            row = self._conn.execute(
                "SELECT slug, name FROM catalog_machinemodel WHERE opdb_id = ?",
                (ident,),
            ).fetchone()
        else:
            return None
        return ModelRef(slug=str(row[0]), name=str(row[1])) if row else None

    def child_terms(self, child_field: FieldKey) -> tuple[ChildTerm, ...]:
        """A child vocab's terms, each paired with its parent term's slug.

        For the dependency pairs (subgeneration under generation, display subtype
        under display type): lets one slice present the legal children grouped by
        which parent value they refine.
        """
        parent_field, fk_col = CHILD_PARENT[child_field]
        child_table = FIELD_VOCAB_TABLES[child_field]
        parent_table = FIELD_VOCAB_TABLES[parent_field]
        columns = {
            row[1] for row in self._conn.execute(f"PRAGMA table_info({child_table})")
        }
        order_by = "c.display_order" if "display_order" in columns else "c.name"
        rows = self._conn.execute(
            f"SELECT c.slug, c.name, c.description, p.slug "  # noqa: S608 — tables from trusted constant maps
            f"FROM {child_table} c JOIN {parent_table} p ON c.{fk_col} = p.id "
            f"ORDER BY {order_by}"
        ).fetchall()
        return tuple(
            ChildTerm(
                VocabTerm(slug, name, self._flatten(description or "")), parent_slug
            )
            for slug, name, description, parent_slug in rows
        )

    def _flatten(self, text: str) -> str:
        """Replace ``[[type:id:N]]`` markup with the referenced entity's plain name."""
        return _WIKILINK.sub(
            lambda m: self._name_for(m.group(1), int(m.group(2))), text
        )

    def _name_for(self, entity_type: EntityType, entity_id: int) -> Label:
        table = WIKILINKABLE.get(entity_type)
        if table is None:
            return entity_type.replace("-", " ")
        cache = self._name_cache.get(table)
        if cache is None:
            try:
                cache = {
                    int(row[0]): str(row[1])
                    for row in self._conn.execute(f"SELECT id, name FROM {table}")  # noqa: S608 — table from trusted constant map
                }
            except sqlite3.OperationalError:
                # A referenced table absent from this DB shape: degrade rather than
                # crash a run over one stray marker.
                cache = {}
            self._name_cache[table] = cache
        return cache.get(entity_id, entity_type.replace("-", " "))
