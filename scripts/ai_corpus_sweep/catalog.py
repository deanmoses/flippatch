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

    def close(self) -> None:
        self._con.close()

    def by_base_name(self, name: str) -> list[ModelFacts]:
        """Models whose display name matches ``name`` once "(...)" suffixes go.

        The resolver supplement for the campaign's "(Maker)" naming convention:
        a note's bare "Supersonic" must reach the model renamed "Supersonic
        (Bally)", which the name/alias index cannot see. Each model is keyed
        under both its full and suffix-stripped normalized name; look up the
        stated title (and its own stripped form) against it.
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

    def current_target(self, model_id: int, column: str) -> Slug | None:
        """The slug the model's lineage ``column`` points at now, or None.

        ``column`` comes from the trusted :mod:`ai_corpus_sweep.fields`
        registry, never from user input, so interpolating it is safe.
        """
        row = self._con.execute(
            "SELECT t.slug FROM catalog_machinemodel m "  # noqa: S608
            f"JOIN catalog_machinemodel t ON m.{column} = t.id WHERE m.id = ?",
            (model_id,),
        ).fetchone()
        return str(row[0]) if row else None

    def tags(self, model_id: int) -> frozenset[str]:
        rows = self._con.execute(
            "SELECT t.slug FROM catalog_machinemodel_tags mt "
            "JOIN catalog_tag t ON mt.tag_id = t.id WHERE mt.machinemodel_id = ?",
            (model_id,),
        ).fetchall()
        return frozenset(str(row[0]) for row in rows)
