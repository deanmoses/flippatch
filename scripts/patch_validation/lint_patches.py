#!/usr/bin/env python3
"""Editorial lint for data patches — pindata authoring standards.

Distinct from ``validate_patches.py`` (the structural gate that mirrors
flipcommons' apply-time loader and JSON schema): this enforces the *authoring*
conventions in flipcommons' ``docs/DataPatchAuthoring.md`` that the schema does
not — public-note discipline, citation hygiene, and drift-guard coverage. Run by
``make validate``.

A "unit" below is one provenance carrier: the entry header itself, plus each
``changesets:`` item. A ``note:``/``cite:`` rides the claims of its own unit, so
most checks run per unit.

Checks (each is tagged at its implementation site with a matching ``# name`` comment)
------
- ``note-patch-number`` — Notes must not reference a data patch by number (the
  world has no concept of ingest runs; bookkeeping belongs in the Admin-only
  ``description:``).
- ``note-typography`` — Notes must not contain smart typography — straight quotes
  only, ``…`` as ``[...]`` (DataPatchAuthoring "Note every entry").
- ``expect-guard`` — Every non-``create`` entry must carry an ``expect:`` drift
  guard ("Guard every entry").
- ``alias-duplicates`` — Alias / abbreviation lists carry no duplicate members
  (aliases case-fold; abbreviations are verbatim) — flipcommons rejects these at
  apply.
- ``alias-length`` — Alias members ≤ 200 chars, abbreviation members ≤ 50 —
  flipcommons rejects over-long members at build.
- ``cite-scheme-form`` — An IPDB/OPDB record cited by URL must use the
  ``scheme:identifier`` form — flipcommons rejects a scheme-pattern URL.
- ``description-attribution`` — A ``description:`` field must be attributed to
  ``flipcommons-ai-desc-<type>`` matching the entity type, not the generic
  ``flipcommons-catalog``.
- ``note-required`` — A unit needs a ``note:`` when it cites, deletes,
  retracts/removes, or asserts a substantive (non-alias) field — except a
  description-only unit and create-scaffolding.
- ``description-citation`` — A ``description:`` unit needs a citation (``cite:``,
  ``cites:``, or an inline ``[[cite:…]]`` marker) **or** a ``note:`` stating it
  rests on catalogued data — the "are you sure you don't need a cite?" guard.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import TypeGuard

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PATCHES_DIR = REPO_ROOT / "patches"

# Patches 0001-0038 were applied to production before this lint existed, and an
# applied patch is immutable (the ledger rejects any content change), so their
# bodies can no longer be edited — they're grandfathered. Only 0039+ — the
# still-editable frontier — are linted. This floor only ever moves forward.
EDITABLE_FLOOR = 39
_PREFIX_RE = re.compile(r"^(\d{4})-")

# Reserved keys are directives/provenance, not claim fields.
RESERVED = {
    "create",
    "delete",
    "expect",
    "retract",
    "remove",
    "note",
    "cite",
    "cites",
    "changesets",
}
# Relationship namespaces whose members are bare strings (no note/cite needed).
ALIAS_KEYS = {
    "manufacturer_alias",
    "corporate_entity_alias",
    "person_alias",
    "title_alias",
    "theme_alias",
    "gameplay_feature_alias",
    "location_alias",
    "reward_type_alias",
    "series_alias",
    "abbreviation",
}

# A zero-padded 4-digit token (0001-0999) is how patches are numbered/referenced
# — bare ("0067") or as a stem prefix ("0067-slug", \b on the hyphen). Years
# (19xx/20xx) and IPDB/OPDB ids (6069, 5572) never lead with a zero.
PATCH_NUM_RE = re.compile(r"\b0\d{3}\b")
# Smart quotes and the ellipsis character (copy-paste typography to straighten).
SMART_RE = re.compile(r"[“”‘’…]")
# An IPDB/OPDB URL cite that should instead be scheme:identifier.
SCHEME_DOMAIN_RE = re.compile(r"https?://(?:www\.)?(?:ipdb|opdb)\.org", re.IGNORECASE)
INLINE_CITE = "[[cite:"
ALIAS_MAX, ABBREV_MAX = 200, 50


# Patch YAML is untrusted until validate_patches.py (and, authoritatively,
# flipcommons' ingest_patches) accept it, so a parsed unit is just an open
# string-keyed mapping; reserved fields are narrowed at the use site with the
# guards below. A closed TypedDict can't model a unit — it carries arbitrary
# authored-field keys (year, manufacturer_alias, …) beside the reserved ones.
PatchUnit = Mapping[str, object]  # a provenance carrier: entity body OR changeset


class CiteMap(TypedDict):
    """A cite given as a map; we read its ``url`` (any ``archive`` is ignored)."""

    url: str


def is_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    """Narrow an untrusted YAML value to a string-keyed mapping."""
    return isinstance(value, Mapping)


def is_cite_map(value: object) -> TypeGuard[CiteMap]:
    """Narrow a cite value to the ``{url, …}`` map form (not a bare string)."""
    return isinstance(value, Mapping) and isinstance(value.get("url"), str)


def _units(body: PatchUnit) -> Iterator[tuple[str, PatchUnit]]:
    """Yield ``(label, unit)`` for the entry header and each changesets item."""
    yield "", body
    changesets = body.get("changesets")
    if isinstance(changesets, list):
        for i, changeset in enumerate(changesets):
            if is_mapping(changeset):
                yield f" changesets[{i}]", changeset


def _cite_strings(unit: PatchUnit) -> Iterator[str]:
    """Yield every cite URL/identifier on a unit (cite: and the cites: map)."""
    cite = unit.get("cite")
    if isinstance(cite, str):
        yield cite
    cites = unit.get("cites")
    if is_mapping(cites):
        for value in cites.values():
            if isinstance(value, str):
                yield value
            elif is_cite_map(value):
                yield value["url"]


def _check_unit(
    ref: str, ref_type: str, attribution: str, label: str, unit: PatchUnit
) -> list[str]:
    where = f"{ref}{label}"
    errors: list[str] = []

    authored = {k for k in unit if k not in RESERVED}
    nonalias_field = authored - ALIAS_KEYS - {"description"}
    description_only = bool(authored) and authored <= {"description"}
    has_note = isinstance(unit.get("note"), str)
    has_cite = ("cite" in unit) or ("cites" in unit)
    is_create = unit.get("create") is True
    is_delete = unit.get("delete") is True
    has_retract_remove = ("retract" in unit) or ("remove" in unit)
    has_description = "description" in authored
    description = unit.get("description") if has_description else None
    inline_cite = isinstance(description, str) and INLINE_CITE in description

    # note-patch-number + note-typography: note content
    note = unit.get("note")
    if isinstance(note, str):
        errors.extend(
            f"{where}: note references patch number {token!r} — notes are "
            f"public; move cross-patch bookkeeping to the description:"
            for token in dict.fromkeys(PATCH_NUM_RE.findall(note))
        )
        smart = sorted(set(SMART_RE.findall(note)))
        if smart:
            errors.append(
                f"{where}: note contains smart typography {smart} — use straight "
                f"quotes and write an ellipsis as [...]"
            )

    # cite-scheme-form
    errors.extend(
        f"{where}: cite {cite!r} is an IPDB/OPDB URL — use the "
        f"scheme:identifier form (ipdb:<id> / opdb:<id>)"
        for cite in _cite_strings(unit)
        if SCHEME_DOMAIN_RE.search(cite)
    )

    # note-required: note presence
    needs_note = (
        (has_cite and not description_only)
        or is_delete
        or has_retract_remove
        or (bool(nonalias_field) and not is_create)
    )
    if needs_note and not has_note:
        errors.append(f"{where}: this change needs a note: explaining it")

    # description-attribution + description-citation: description rules
    if has_description:
        want = f"flipcommons-ai-desc-{ref_type}"
        if attribution != want:
            errors.append(
                f"{where}: a description: field must be attributed {want!r}, "
                f"not {attribution!r}"
            )
        if not (has_cite or inline_cite or has_note):
            errors.append(
                f"{where}: description has no citation and no note — descriptions "
                f"almost always cite non-catalog facts; add a cite, or a note "
                f"stating it rests on catalogued data"
            )

    # alias-duplicates + alias-length: aliases / abbreviations
    for key in authored & ALIAS_KEYS:
        members = unit.get(key)
        if not isinstance(members, list):
            continue
        casefold = key != "abbreviation"
        seen: set[str] = set()
        dups: set[str] = set()
        for member in members:
            ident = str(member).casefold() if casefold else str(member)
            (dups if ident in seen else seen).add(ident)
        if dups:
            errors.append(
                f"{where}: {key} has duplicate members "
                f"{sorted(dups)} ({'aliases case-fold' if casefold else 'verbatim'})"
            )
        limit = ABBREV_MAX if key == "abbreviation" else ALIAS_MAX
        errors.extend(
            f"{where}: {key} member {member!r} exceeds {limit} chars"
            for member in members
            if len(str(member)) > limit
        )

    return errors


def lint_patch(filename: str, data: object) -> list[str]:
    """Lint one parsed patch; return a list of ``filename: …`` error strings."""
    if not is_mapping(data):
        return []
    attribution = data.get("attribution", "")
    if not isinstance(attribution, str):
        attribution = ""
    errors: list[str] = []
    claims = data.get("claims")
    if isinstance(claims, list):
        for entry in claims:
            if not is_mapping(entry):
                continue
            for ref, body in entry.items():
                if not is_mapping(body):
                    continue
                ref_type = ref.split(".", 1)[0]
                # expect-guard: guard every non-create entry with expect:
                if body.get("create") is not True and "expect" not in body:
                    errors.append(f"{ref}: entry has no expect: drift guard")
                for label, unit in _units(body):
                    errors.extend(_check_unit(ref, ref_type, attribution, label, unit))
    return [f"{filename}: {e}" for e in errors]


def main() -> int:
    if not PATCHES_DIR.is_dir():
        print("No patches/ directory; nothing to lint.")
        return 0

    errors: list[str] = []
    for path in sorted(PATCHES_DIR.glob("*.yaml")):
        prefix = _PREFIX_RE.match(path.name)
        if prefix and int(prefix.group(1)) < EDITABLE_FLOOR:
            continue  # grandfathered immutable history (see EDITABLE_FLOOR)
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue  # parse/structural validity is validate_patches.py's job
        errors.extend(lint_patch(path.name, data))

    if errors:
        print(f"{len(errors)} patch lint error(s):", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    print("All patches pass authoring lint.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
