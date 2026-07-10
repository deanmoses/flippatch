"""Load descriptions, cites, and scalar-claim units from flippatch patch YAML.

Reuses ``patch_validation.lint_patches`` for the patch-walking primitives
(``_units`` yields the entry header plus each ``changesets:`` item; the ``is_*``
guards narrow untrusted YAML), so this stays a thin adapter that shapes those
units into the carriers the two entrypoints consume.

Only the ``cites:`` map (new inline footnotes declared in this patch, keyed by a
numeric handle) carries a ``ref``/``quote`` here; an existing-slug marker
(``[[cite:<slug>]]``) points at a citation already in flipcommons and is left to
the deterministic ``verify-quotes`` and the live catalog — the AI tools focus on
the new evidence a patch introduces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import yaml
from patch_validation.lint_patches import (
    ALIAS_KEYS,
    RESERVED,
    PatchUnit,
    _units,
    is_cite_map,
    is_mapping,
)

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class CiteRef:
    """A patch-declared inline citation: its source ref plus verbatim quote."""

    handle: str
    ref: str
    quote: str = ""
    locator: str = ""


@dataclass(frozen=True, slots=True)
class DescriptionUnit:
    """One ``description:`` field and the inline cites declared alongside it."""

    patch: str
    entity_ref: str  # e.g. "franchise.battle-dome"
    entity_type: str  # e.g. "franchise"
    slug: str  # e.g. "battle-dome"
    text: str  # the description markdown, authoring form
    cites: dict[str, CiteRef] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ScalarClaim:
    """A non-description assertion (field→value cluster) and one supporting cite.

    The citation verifier renders ``claim_text`` for the model; each distinct
    ``(ref, quote)`` on the unit becomes its own :class:`ScalarClaim` so a
    quote is judged against exactly the fields its unit asserts.
    """

    patch: str
    entity_ref: str
    claim_text: str  # e.g. "game_format = pinball; year = 1994"
    cite: CiteRef


def load_patches(
    patches_dir: Path, patch_ids: tuple[str, ...] = ()
) -> Iterator[tuple[str, object]]:
    """Yield ``(filename, parsed_yaml)`` for each ``NNNN-*.yaml`` patch.

    ``patch_ids`` (bare numbers or stems) restricts the set; empty means all.
    Parse errors are skipped — structural validity is ``validate_patches.py``'s job.
    """
    wanted = {pid.removesuffix(".yaml") for pid in patch_ids}
    for path in sorted(patches_dir.glob("[0-9]*.yaml")):
        stem = path.stem
        if wanted and stem not in wanted and stem.split("-", 1)[0] not in wanted:
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        yield path.name, data


def _entries(data: object) -> Iterator[tuple[str, PatchUnit]]:
    """Yield ``(entity_ref, body)`` for each claim entry in a parsed patch."""
    if not is_mapping(data):
        return
    claims = data.get("claims")
    if not isinstance(claims, list):
        return
    for entry in claims:
        if not is_mapping(entry):
            continue
        for ref, body in entry.items():
            if is_mapping(body):
                yield ref, body


def _cites_of(unit: PatchUnit) -> dict[str, CiteRef]:
    """The unit's ``cites:`` map, normalized to :class:`CiteRef` by handle."""
    cites = unit.get("cites")
    out: dict[str, CiteRef] = {}
    if not is_mapping(cites):
        return out
    for handle, spec in cites.items():
        key = str(handle)
        if isinstance(spec, str):
            out[key] = CiteRef(handle=key, ref=spec)
        elif is_cite_map(spec):
            quote = spec.get("quote")
            locator = spec.get("locator")
            out[key] = CiteRef(
                handle=key,
                ref=spec["ref"],
                quote=quote if isinstance(quote, str) else "",
                locator=locator if isinstance(locator, str) else "",
            )
    return out


def iter_description_units(filename: str, data: object) -> Iterator[DescriptionUnit]:
    """Yield every unit carrying a ``description:`` string, with its cites."""
    for entity_ref, body in _entries(data):
        entity_type, _, slug = entity_ref.partition(".")
        for _label, unit in _units(body):
            text = unit.get("description")
            if isinstance(text, str) and text.strip():
                yield DescriptionUnit(
                    patch=filename,
                    entity_ref=entity_ref,
                    entity_type=entity_type,
                    slug=slug,
                    text=text,
                    cites=_cites_of(unit),
                )


def _scalar_claim_text(unit: PatchUnit) -> str:
    """A human rendering of the non-reserved, non-alias fields a unit asserts."""
    parts: list[str] = []
    for key, value in unit.items():
        if key in RESERVED or key in ALIAS_KEYS or key == "description":
            continue
        parts.append(f"{key} = {value!r}")
    return "; ".join(parts)


def iter_scalar_claim_cites(filename: str, data: object) -> Iterator[ScalarClaim]:
    """Yield ``(scalar field cluster, supporting cite)`` pairs for the verifier.

    Only units that assert a substantive non-description field *and* carry a
    quote-bearing entry-level ``cite:`` are yielded — a description's inline
    footnotes are handled separately (sentence ↔ footnote), and an alias-only or
    quoteless unit has nothing for the support check to weigh.
    """
    for entity_ref, body in _entries(data):
        for _label, unit in _units(body):
            claim_text = _scalar_claim_text(unit)
            if not claim_text:
                continue
            cite = unit.get("cite")
            # cite: may be one spec or a list of them (both schema-legal, as
            # verify_quotes handles) — check every quote-bearing spec.
            specs = cite if isinstance(cite, list) else [cite]
            for spec in specs:
                if is_cite_map(spec):
                    quote = spec.get("quote")
                    if isinstance(quote, str) and quote.strip():
                        yield ScalarClaim(
                            patch=filename,
                            entity_ref=entity_ref,
                            claim_text=claim_text,
                            cite=CiteRef(handle="cite", ref=spec["ref"], quote=quote),
                        )
