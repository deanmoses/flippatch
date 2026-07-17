"""Read-only model facts from flipcommons' dev SQLite, keyed on ``ipdb_id``.

The sweep's deterministic side of "judge the delta": what the catalog holds
*now* for a model's lineage field, plus the structured facts (year, maker,
technology) that disambiguate a resolved target name. Reads the same dev DB as
:mod:`common.catalog.entity_index`, by sibling path — flippatch can't import
flipcommons' Django.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING

from common.catalog.entity_index import normalize_key

if TYPE_CHECKING:
    from pathlib import Path

    from common.catalog.types import Slug

_FACTS_SELECT = """
SELECT m.id, m.slug, m.name, m.year, m.ipdb_id, mf.slug, mf.name, tg.name,
       ce.slug, ce.name
FROM catalog_machinemodel m
LEFT JOIN catalog_corporateentity ce ON m.corporate_entity_id = ce.id
LEFT JOIN catalog_manufacturer mf ON ce.manufacturer_id = mf.id
LEFT JOIN catalog_technologygeneration tg ON m.technology_generation_id = tg.id
"""

# A trailing parenthetical disambiguator on a display name — the campaign's
# "(Maker)" suffix ("Supersonic (Bally)") or IPDB's locale tag ("Hurdy Gurdy
# (Italy)"). Stripping it recovers the base name both sides actually share.
_PAREN_SUFFIX = re.compile(r"\s*\([^)]*\)\s*$")


def strip_parenthetical(name: str) -> str:
    """The name with one trailing "(...)" disambiguator removed."""
    return _PAREN_SUFFIX.sub("", name).strip()


@dataclass(frozen=True, slots=True)
class CatalogEdge:
    """One `catalog_modelrelationship` row the sweep reconciles a claim against.

    ``target_slug`` is the resolved slug of the machine target, or None for a
    text-target edge (a model holds at most one of those); ``target_label`` is
    the free text for a text target, or "" for a machine target. ``rel_type`` /
    ``license`` are the edge's ``relationship_type`` / ``license_status``.
    """

    rel_type: str
    license: str
    target_slug: Slug | None
    target_label: str

    def describe(self) -> str:
        """A one-line human rendering: ``copy/unlicensed → aquarius``."""
        target = (
            f"`{self.target_slug}`" if self.target_slug else f"“{self.target_label}”"
        )
        return f"{self.rel_type}/{self.license} → {target}"


@dataclass(frozen=True, slots=True)
class ModelFacts:
    """One model's identity and the structured facts disambiguation needs."""

    model_id: int
    slug: Slug
    name: str
    year: int | None
    ipdb_id: int | None
    maker_slug: Slug | None
    maker_name: str | None
    technology: str | None
    ce_slug: Slug | None = None
    ce_name: str | None = None

    def describe(self) -> str:
        """A one-line human rendering for review tables and prompts."""
        bits = [
            self.maker_name or self.maker_slug or "maker unknown",
            str(self.year) if self.year else "year unknown",
        ]
        if self.technology:
            bits.append(self.technology)
        return f"{self.slug} — {self.name} ({', '.join(bits)})"


def _opt_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _facts(
    row: tuple[int, str, str, object, object, object, object, object, object, object],
) -> ModelFacts:
    model_id, slug, name, year, ipdb_id, maker_slug, maker_name, tech, ce_s, ce_n = row
    return ModelFacts(
        model_id=model_id,
        slug=slug,
        name=name,
        year=int(year) if isinstance(year, int) else None,
        ipdb_id=int(ipdb_id) if isinstance(ipdb_id, int) else None,
        maker_slug=_opt_str(maker_slug),
        maker_name=_opt_str(maker_name),
        technology=_opt_str(tech),
        ce_slug=_opt_str(ce_s),
        ce_name=_opt_str(ce_n),
    )


class SweepCatalog:
    """Read-only lookups over the dev DB the sweep reconciles against."""

    def __init__(self, db_path: Path) -> None:
        self._con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self._base_names: dict[str, list[ModelFacts]] | None = None
        self._brand_keys: frozenset[str] | None = None
        self._brand_years: dict[str, tuple[int, int]] | None = None

    def close(self) -> None:
        self._con.close()

    def by_base_name(self, name: str) -> list[ModelFacts]:
        """Models whose display name matches ``name`` once "(...)" suffixes go.

        Catalog names carry parenthetical disambiguators the sources they are
        judged against do not: a note's bare "Gottlieb's 1978 'Dragon'" has to
        reach the model named "Dragon (EM)", and the name/alias index only sees
        the full string. Each model is keyed under both its full and its
        suffix-stripped normalized name; look up the stated title (and its own
        stripped form) against it.

        (This was built for a since-retired campaign convention that suffixed
        names with the *maker* — "Supersonic (Bally)" — hence TOOL-NOTES DEFECT
        1. Those names are bare again, but edition and technology suffixes are
        not going anywhere, so the lookup stays load-bearing.)
        """
        if self._base_names is None:
            index: dict[str, list[ModelFacts]] = {}
            for row in self._con.execute(_FACTS_SELECT).fetchall():
                facts = _facts(row)
                keys = {normalize_key(facts.name)}
                keys.add(normalize_key(strip_parenthetical(facts.name)))
                for key in keys:
                    if key:
                        index.setdefault(key, []).append(facts)
            self._base_names = index
        key = normalize_key(name)
        return list(self._base_names.get(key, [])) if key else []

    def brand_keys(self) -> frozenset[str]:
        """Every Manufacturer record's slug and name, normalized.

        The vocabulary that tells a *brand* from a longer legal name (DEFECT
        6): a stated maker found here names a real, distinct brand, so it must
        match one exactly rather than by substring — "Bally" is in here and so
        is "Bally Wulff", and the two are different makers. A stated maker that
        is absent (a corporate entity like "Premier") keeps the lenient
        containment match that reaches its brand.
        """
        if self._brand_keys is None:
            keys: set[str] = set()
            for slug, name in self._con.execute(
                "SELECT slug, name FROM catalog_manufacturer"
            ):
                for value in (slug, name):
                    key = normalize_key(value) if isinstance(value, str) else ""
                    if key:
                        keys.add(key)
            self._brand_keys = frozenset(keys)
        return self._brand_keys

    def brand_active_in(self, key: str, year: int) -> bool:
        """Did the brand named by ``key`` make anything around ``year`` (±1)?

        DEFECT 9. ``brand_keys`` says a stated maker names *a* real brand; it
        cannot say it names a *plausible* one. "Stern" is the full name of
        Stern Pinball (founded 1999) as well as the token every Stern
        Electronics note from 1979 uses, so the exact-brand veto of DEFECT 6
        was binding 1970s notes to a company that did not exist and rejecting
        the correct target. A brand with no models anywhere near the stated
        year cannot be the referent, so that binding is vacuous.

        Unknown-year models never count toward a brand's span — the same rule
        the year filter uses, for the same reason: a fact a record doesn't
        carry can't establish one.
        """
        if self._brand_years is None:
            spans: dict[str, list[int]] = {}
            for slug, name, model_year in self._con.execute(
                "SELECT mf.slug, mf.name, m.year FROM catalog_machinemodel m "
                "JOIN catalog_corporateentity ce ON m.corporate_entity_id = ce.id "
                "JOIN catalog_manufacturer mf ON ce.manufacturer_id = mf.id "
                "WHERE m.year IS NOT NULL"
            ):
                for value in (slug, name):
                    brand = normalize_key(value) if isinstance(value, str) else ""
                    if brand and isinstance(model_year, int):
                        spans.setdefault(brand, []).append(model_year)
            self._brand_years = {k: (min(v), max(v)) for k, v in spans.items()}
        span = self._brand_years.get(key)
        if span is None:
            return False  # a brand that made nothing dated can vouch for no year
        low, high = span
        return low - 1 <= year <= high + 1

    def by_ipdb(self, ipdb_id: int) -> ModelFacts | None:
        row = self._con.execute(
            f"{_FACTS_SELECT} WHERE m.ipdb_id = ?", (ipdb_id,)
        ).fetchone()
        return _facts(row) if row else None

    def by_slug(self, slug: Slug) -> ModelFacts | None:
        row = self._con.execute(f"{_FACTS_SELECT} WHERE m.slug = ?", (slug,)).fetchone()
        return _facts(row) if row else None

    def title_models(self, title_slug: Slug) -> list[ModelFacts]:
        """Every model grouped under a title — the title→model expansion step."""
        rows = self._con.execute(
            f"{_FACTS_SELECT} JOIN catalog_title t ON m.title_id = t.id "
            "WHERE t.slug = ?",
            (title_slug,),
        ).fetchall()
        return [_facts(row) for row in rows]

    def current_relationships(self, model_id: int) -> tuple[CatalogEdge, ...]:
        """Every `catalog_modelrelationship` edge this model holds now.

        The reconciler's deterministic side: a model may carry several
        machine-target edges (a copy of two designs, a kit fitting several
        donors) and at most one text-target edge, so the sweep diffs a claim
        against the whole set, not a single column value.
        """
        rows = self._con.execute(
            "SELECT r.relationship_type, r.license_status, t.slug, r.target_label "
            "FROM catalog_modelrelationship r "
            "LEFT JOIN catalog_machinemodel t ON r.target_machine_id = t.id "
            "WHERE r.machine_model_id = ?",
            (model_id,),
        ).fetchall()
        return tuple(
            CatalogEdge(
                rel_type=str(rel_type),
                license=str(license_status),
                target_slug=str(slug) if slug is not None else None,
                target_label=label or "",
            )
            for rel_type, license_status, slug, label in rows
        )
