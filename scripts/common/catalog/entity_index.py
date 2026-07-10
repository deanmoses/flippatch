"""Catalog entity index, read directly from flipcommons' dev SQLite.

flipcommons is the source of truth for what exists / what is linkable. Its dev
DB (``backend/db.sqlite3``, a near-clone of prod) carries the resolved (winning)
``slug``/``name`` on each catalog row and per-type ``*alias`` rows. We read those
tables directly by sibling path — flippatch can't import flipcommons' Django.

Two access patterns, because the tools enter the index from opposite ends:

- :meth:`EntityIndex.find_mentions` — n-gram scan of prose for unlinked catalog
  surface forms (the lint's missing-wikilink / unknown-model rules).
- :meth:`EntityIndex.resolve` — single-name lookup (the extraction tool's
  entity-discovery cross-check and the sweep's ``target_title`` → ref step).

Which entity types populate the index is the **caller's** choice: pass the type
profile to :meth:`EntityIndex.build`. :data:`DEFAULT_TYPES` is tuned for the
proper-noun entities prose links and is the wikilink default, *not* a universal
one — target resolution wants its own profile (e.g. ``model`` + ``title``).

The entity-type → table and alias-table map below is a **generated mirror** of
flipcommons' wikilinkable-model registry (``apps/catalog/_walks.py``). Regenerate
it if flipcommons adds an entity type:

    cd ../flipcommons/backend && uv run python manage.py shell -c \\
      "from apps.catalog._walks import wikilinkable_models, alias_models; ..."

Matching is dash/space/punctuation- and case-insensitive (via
:func:`normalize_key`) so prose "F-14" / "Twilight Zone" reaches slug
``f14-tomcat`` / name "The Twilight Zone".
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from common.catalog.types import EntityType, Label, Slug, TableName

# The shared catalog string vocabulary (EntityType, TableName, Slug, Label) lives
# in common.catalog.types now that more than one tool reads the same DB (imported
# above). These two stay here — the mention scanner's own working types, used
# nowhere else:
type NormKey = str  # a folded lookup key produced by normalize_key()
type Surface = str  # a raw surface form as it appears in prose or the DB


class AliasSpec(NamedTuple):
    """One alias table and how it joins back to the parent catalog row it aliases.

    Generated mirror of flipcommons' alias registry; see the module docstring.
    """

    alias_table: TableName
    fk_id_column: str
    parent_table: TableName
    value_column: str


class RefKey(NamedTuple):
    """The (entity_type, slug) identity of an :class:`EntityRef` — its dict-key form."""

    entity_type: EntityType
    slug: Slug


class Span(NamedTuple):
    """A half-open character range ``[start, end)`` into the source text."""

    start: int
    end: int


# entity_type -> flipcommons catalog table. Generated mirror; see module docstring.
WIKILINKABLE: dict[EntityType, TableName] = {
    "gameplay-feature": "catalog_gameplayfeature",
    "manufacturer": "catalog_manufacturer",
    "corporate-entity": "catalog_corporateentity",
    "model": "catalog_machinemodel",
    "person": "catalog_person",
    "franchise": "catalog_franchise",
    "series": "catalog_series",
    "system": "catalog_system",
    "technology-generation": "catalog_technologygeneration",
    "technology-subgeneration": "catalog_technologysubgeneration",
    "display-type": "catalog_displaytype",
    "display-subtype": "catalog_displaysubtype",
    "cabinet": "catalog_cabinet",
    "game-format": "catalog_gameformat",
    "production-status": "catalog_productionstatus",
    "reward-type": "catalog_rewardtype",
    "tag": "catalog_tag",
    "credit-role": "catalog_creditrole",
    "theme": "catalog_theme",
    "title": "catalog_title",
}
_TABLE_TO_TYPE: dict[TableName, EntityType] = {
    table: etype for etype, table in WIKILINKABLE.items()
}

_ALIAS_SPECS: tuple[AliasSpec, ...] = (
    AliasSpec(
        "catalog_gameplayfeaturealias", "feature_id", "catalog_gameplayfeature", "value"
    ),
    AliasSpec(
        "catalog_manufactureralias", "manufacturer_id", "catalog_manufacturer", "value"
    ),
    AliasSpec(
        "catalog_corporateentityalias",
        "corporate_entity_id",
        "catalog_corporateentity",
        "value",
    ),
    AliasSpec("catalog_personalias", "person_id", "catalog_person", "value"),
    AliasSpec(
        "catalog_rewardtypealias", "reward_type_id", "catalog_rewardtype", "value"
    ),
    AliasSpec("catalog_themealias", "theme_id", "catalog_theme", "value"),
)

# Default match set: proper-noun-ish entities prose actually names and should
# link. Abstract taxonomy (game-format "pinball", production-status, tags, …) is
# excluded — its "names" are common descriptive words that would flood findings.
DEFAULT_TYPES: tuple[EntityType, ...] = (
    "manufacturer",
    "corporate-entity",
    "model",
    "title",
    "person",
    "franchise",
    "series",
)

# Longest catalog names run ~4-5 words ("Nihon Goraku Ki Kabushikigaisha").
MAX_WINDOW = 6
# Below this normalized length a key is too generic to match on ("f1", initials).
MIN_KEY_LEN = 3

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_LEADING_THE = re.compile(r"^the\s+")
_TOKEN = re.compile(r"\S+")

# Normalized keys too generic to be a useful catalog reference on their own.
_STOP_KEYS: frozenset[NormKey] = frozenset(
    {"pinball", "game", "machine", "model", "series", "company", "the", "and"}
)


def normalize_key(text: str) -> NormKey:
    """Fold a surface form to a dash/space/punctuation/case-insensitive key.

    Lowercases, drops a leading "the", and removes every non-alphanumeric char
    (so "F-14 Tomcat", "f14 tomcat", and slug "f14-tomcat" all fold to the same
    ``f14tomcat``).
    """
    folded = _LEADING_THE.sub("", text.casefold().strip())
    return _NON_ALNUM.sub("", folded)


@dataclass(frozen=True, slots=True)
class EntityRef:
    """A linkable catalog entity: its type, slug, and display label."""

    entity_type: EntityType
    slug: Slug
    label: Label

    @property
    def wikilink(self) -> str:
        """The authoring-form marker that would link this entity."""
        return f"[[{self.entity_type}:{self.slug}]]"


@dataclass(frozen=True, slots=True)
class Mention:
    """An entity surface form found unlinked in prose.

    ``exact`` is ``True`` when the prose surface case-folds to a stored name/alias
    verbatim; ``False`` when only normalization (dropped dashes/spaces) matched —
    a lower-confidence candidate for the AI rule to confirm.
    """

    surface: Surface
    start: int
    end: int
    refs: tuple[EntityRef, ...]
    exact: bool


class EntityIndex:
    """Name/alias → catalog entity lookup, with n-gram prose mention finding."""

    def __init__(
        self,
        by_norm: dict[NormKey, list[EntityRef]],
        surfaces: dict[NormKey, set[Surface]],
        nkeys_by_ref: dict[RefKey, set[NormKey]],
    ) -> None:
        self._by_norm = by_norm
        self._surfaces = surfaces
        self._nkeys_by_ref = nkeys_by_ref

    @classmethod
    def build(
        cls, db_path: Path, types: Iterable[EntityType] = DEFAULT_TYPES
    ) -> EntityIndex:
        """Read the catalog + alias tables for ``types`` from the dev SQLite."""
        type_set = tuple(types)
        by_norm: dict[NormKey, list[EntityRef]] = {}
        surfaces: dict[NormKey, set[Surface]] = {}
        nkeys_by_ref: dict[RefKey, set[NormKey]] = {}

        def add(surface: Surface, ref: EntityRef) -> None:
            nkey = normalize_key(surface)
            if len(nkey) < MIN_KEY_LEN or nkey in _STOP_KEYS:
                return
            refs = by_norm.setdefault(nkey, [])
            if ref not in refs:
                refs.append(ref)
            surfaces.setdefault(nkey, set()).add(surface.casefold())
            nkeys_by_ref.setdefault(RefKey(ref.entity_type, ref.slug), set()).add(nkey)

        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            existing: set[TableName] = {
                str(row[0])
                for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            refs_by_id: dict[TableName, dict[int, EntityRef]] = {}
            for etype in type_set:
                table = WIKILINKABLE.get(etype)
                if table is None or table not in existing:
                    continue
                rows = con.execute(f"SELECT id, slug, name FROM {table}")  # noqa: S608
                id_map = refs_by_id.setdefault(table, {})
                for row_id, slug, name in rows:
                    ref = EntityRef(etype, str(slug), str(name))
                    id_map[int(row_id)] = ref
                    add(str(name), ref)
            for alias_table, fk_col, parent_table, value_col in _ALIAS_SPECS:
                parent_type = _TABLE_TO_TYPE.get(parent_table)
                if (
                    alias_table not in existing
                    or parent_type is None
                    or parent_type not in type_set
                ):
                    continue
                parents = refs_by_id.get(parent_table, {})
                query = f"SELECT {fk_col}, {value_col} FROM {alias_table}"  # noqa: S608
                for parent_id, value in con.execute(query):
                    alias_ref = parents.get(int(parent_id))
                    if alias_ref is not None and isinstance(value, str):
                        add(value, alias_ref)
        finally:
            con.close()
        return cls(by_norm, surfaces, nkeys_by_ref)

    def resolve(
        self, name: str, *, types: Iterable[EntityType] | None = None
    ) -> list[EntityRef]:
        """Resolve one name to the catalog entities it matches.

        A single-name lookup (not a prose scan): the extraction tool's
        entity-discovery cross-check and the sweep's ``target_title`` → ref step
        both call this. An empty list means "not in the catalog" (a possible
        gap); more than one means an ambiguous name for the caller to
        disambiguate. ``types`` narrows the result to those entity types (the
        index must have been built with them).
        """
        nkey = normalize_key(name)
        if len(nkey) < MIN_KEY_LEN or nkey in _STOP_KEYS:
            return []
        refs = self._by_norm.get(nkey, [])
        if types is not None:
            wanted = set(types)
            refs = [ref for ref in refs if ref.entity_type in wanted]
        return list(refs)

    def _self_nkeys(self, entity_type: EntityType, slug: Slug) -> set[NormKey]:
        """The normalized keys that resolve to this (subject) entity."""
        return self._nkeys_by_ref.get(RefKey(entity_type, slug), set())

    def find_mentions(
        self, text: str, *, exclude_type: EntityType = "", exclude_slug: Slug = ""
    ) -> list[Mention]:
        """Find unlinked catalog-entity surface forms in ``text``.

        Longest match wins at any position; the subject entity's own names are
        excluded so a maker's description isn't told to link itself. Callers
        should first blank out any existing ``[[…]]`` markers so link syntax
        isn't matched as prose.
        """
        own = self._self_nkeys(exclude_type, exclude_slug)
        spans = [Span(m.start(), m.end()) for m in _TOKEN.finditer(text)]
        found: list[Mention] = []
        for i in range(len(spans)):
            # normalize_key drops a leading "the", so don't let a window start on
            # one — otherwise "The F-14 Tomcat" swallows the article. The core
            # name is matched from the next token instead.
            first = text[spans[i].start : spans[i].end].strip(".,;:!?").casefold()
            if first == "the":
                continue
            for width in range(min(MAX_WINDOW, len(spans) - i), 0, -1):
                nkey = normalize_key(text[spans[i].start : spans[i + width - 1].end])
                if nkey in own:
                    break
                refs = self._by_norm.get(nkey)
                if refs:
                    span = _trim(text, spans[i].start, spans[i + width - 1].end)
                    surface = text[span.start : span.end]
                    exact = surface.casefold() in self._surfaces.get(nkey, set())
                    found.append(
                        Mention(surface, span.start, span.end, tuple(refs), exact)
                    )
                    break  # longest window at this start wins
        return _dedupe_overlaps(found)


def _trim(text: str, start: int, end: int) -> Span:
    """Shrink a span to its alphanumeric bounds (drop leading/trailing punctuation)."""
    while start < end and not text[start].isalnum():
        start += 1
    while end > start and not text[end - 1].isalnum():
        end -= 1
    return Span(start, end)


def _dedupe_overlaps(mentions: list[Mention]) -> list[Mention]:
    """Keep non-overlapping mentions, preferring longer spans, then earlier."""
    ordered = sorted(mentions, key=lambda m: (-(m.end - m.start), m.start))
    taken: list[Mention] = []
    for mention in ordered:
        if all(mention.end <= t.start or mention.start >= t.end for t in taken):
            taken.append(mention)
    return sorted(taken, key=lambda m: m.start)
