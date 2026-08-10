"""Load descriptions, cites, and scalar-claim units from flippatch patch YAML.

Reuses ``patch_validation.lint_patches`` for the patch-walking primitives
(``_units`` yields the entry header plus each ``changesets:`` item; the ``is_*``
guards narrow untrusted YAML), so this stays a thin adapter that shapes those
units into the carriers the two entrypoints consume.

Only the ``cites:`` map (new inline footnotes declared in this patch, keyed by a
numeric handle) carries a ``ref``/``quote`` here; an existing-slug marker
(``[[cite:<slug>]]``) points at a citation already in flipcommons and is left to
the deterministic ``verify-quote-verbatim`` and the live catalog — the AI tools focus on
the new evidence a patch introduces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import yaml
from common.patch_files import patch_paths
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
    archive: str = ""  # Wayback snapshot, when the cite names one


@dataclass(frozen=True, slots=True)
class DescriptionUnit:
    """One ``description:`` field and the inline cites declared alongside it."""

    patch: str
    entity_ref: str  # e.g. "franchise.battle-dome"
    entity_type: str  # e.g. "franchise"
    slug: str  # e.g. "battle-dome"
    text: str  # the description markdown, authoring form
    cites: dict[str, CiteRef] = field(default_factory=dict)
    note: str = ""


@dataclass(frozen=True, slots=True)
class ScalarClaim:
    """A non-description assertion (field→value cluster) and its whole evidence.

    The schema directs authors to put reconciliation in ``note:`` rather than in
    a quote, so a quote read without it is half the record.
    """

    patch: str
    entity_ref: str
    claim_text: str  # e.g. "game_format = pinball; year = 1994"
    cites: tuple[CiteRef, ...]
    note: str = ""


def load_patches(
    patches_dir: Path, patch_ids: tuple[str, ...] = ()
) -> Iterator[tuple[str, object]]:
    """Yield ``(filename, parsed_yaml)`` for each ``NNNN-*.yaml`` patch.

    ``patch_ids`` (bare numbers or stems) restricts the set; empty means all —
    selection is :func:`~common.patch_files.patch_paths`.
    Parse errors are skipped — structural validity is ``validate_patches.py``'s job.
    """
    for path in patch_paths(patches_dir, patch_ids):
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
            archive = spec.get("archive")
            out[key] = CiteRef(
                handle=key,
                ref=spec["ref"],
                quote=quote if isinstance(quote, str) else "",
                locator=locator if isinstance(locator, str) else "",
                archive=archive if isinstance(archive, str) else "",
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
                    note=_note_of(unit),
                )


def _scalar_claim_text(unit: PatchUnit) -> str:
    """A human rendering of the non-reserved, non-alias fields a unit asserts."""
    parts: list[str] = []
    for key, value in unit.items():
        if key in RESERVED or key in ALIAS_KEYS or key == "description":
            continue
        parts.append(f"{key} = {value!r}")
    return "; ".join(parts)


def _note_of(unit: PatchUnit) -> str:
    note = unit.get("note")
    return note if isinstance(note, str) else ""


def _entry_cites_of(unit: PatchUnit) -> tuple[CiteRef, ...]:
    """The unit's entry-level ``cite:`` specs — one, or a list of them, per schema."""
    cite = unit.get("cite")
    specs = cite if isinstance(cite, list) else [cite]
    out: list[CiteRef] = []
    for spec in specs:
        if isinstance(spec, str):  # a bare cite-ref, quote-less by construction
            out.append(CiteRef(handle="cite", ref=spec))
            continue
        if not is_cite_map(spec):
            continue
        quote, locator, archive = (
            spec.get("quote"),
            spec.get("locator"),
            spec.get("archive"),
        )
        out.append(
            CiteRef(
                handle="cite",
                ref=spec["ref"],
                quote=quote if isinstance(quote, str) else "",
                locator=locator if isinstance(locator, str) else "",
                archive=archive if isinstance(archive, str) else "",
            )
        )
    return tuple(out)


def iter_scalar_claims(filename: str, data: object) -> Iterator[ScalarClaim]:
    """Yield one claim per non-description unit, with all of its evidence.

    A unit whose every cite is a quote-less mark is not yielded: its only
    readable evidence would be the note, and weighing an author's reasoning
    against their own claim decides nothing.
    """
    for entity_ref, body in _entries(data):
        for _label, unit in _units(body):
            claim_text = _scalar_claim_text(unit)
            if not claim_text:
                continue
            cites = _entry_cites_of(unit)
            if any(cite.quote.strip() for cite in cites):
                yield ScalarClaim(
                    patch=filename,
                    entity_ref=entity_ref,
                    claim_text=claim_text,
                    cites=cites,
                    note=_note_of(unit),
                )
