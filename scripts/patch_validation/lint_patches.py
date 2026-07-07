#!/usr/bin/env python3
"""Editorial lint for data patches — pindata authoring standards.

Distinct from ``validate_patches.py`` (the structural gate that mirrors
flipcommons' apply-time loader and JSON schema): this enforces the *authoring*
conventions in flipcommons' ``docs/DataPatchAuthoring.md`` that the schema does
not — public-note discipline and citation hygiene. Run by
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
  description-only unit and create-scaffolding. A ``cite:`` mapping (or any
  inline ``cites:`` entry) carrying a ``quote:`` satisfies it: the verbatim
  evidence is the explanation.
- ``description-needs-inline-cite`` — A ``description:`` unit must carry at least
  one inline ``[[cite:N]]`` footnote; a ``note:`` no longer excuses its absence.
  Exempt for the abstract-taxonomy entity types in
  ``DESCRIPTION_CITE_EXEMPT_TYPES`` (e.g. ``gameplay-feature``), whose
  descriptions are definitional cross-references, not sourced claims.
- ``description-no-entry-cite`` — A ``description:`` unit may not carry an
  entry-level ``cite:`` covering the whole field opaquely — footnote each fact
  inline instead.
- ``description-two-sources`` — A ``description:`` unit must cite at least two
  distinct sources, resolving to at least two different root sources (registrable
  domain for a URL, scheme for an ``ipdb:``/``opdb:``/``youtube:`` identifier) —
  a single source, or several footnotes from one root, is not corroboration.
- ``note-no-quote-scaffolding`` — A note must not carry the legacy
  ``<source> says "<quote>"`` scaffolding — the verbatim excerpt belongs in
  ``quote:`` on the ``cite:`` mapping, where the citation already names the
  source. (Shipped patches keep their historical notes as-authored; their DB
  rows were fixed by flipcommons' backfill migration, not the files.)
- ``quote-typography`` — ``quote:`` values — on the entry-level ``cite:``
  mapping and on inline ``cites:`` entries alike — must use straight quotes and
  write an ellipsis as ``[...]`` — the same normalization ``note-typography``
  enforces on notes.
- ``patch-description-length`` — The *top-level* patch ``description:`` (→ the
  Admin-only ``IngestRun`` note) must be ≤ 80 chars after whitespace collapse: a
  commit-title-style summary, not a paragraph. Per-change detail belongs in
  ``note:`` fields, not here. This is the one whole-patch check (the others run
  per unit); the per-record ``description-*`` rules above target a different
  field — the narrative ``description:`` inside a claim unit.

Each rule is enforced from the patch number at which it was introduced
(``RULE_SINCE``); patches below that are grandfathered for it.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, TypedDict

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import TypeGuard

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PATCHES_DIR = REPO_ROOT / "patches"

# Each rule is enforced only from the patch number at which it was introduced;
# patches numbered below that are grandfathered for that rule. This is FIXED
# history, not a moving "editable floor": a patch authored at/after a rule's
# introduction complies by construction, so it keeps passing once it becomes
# immutable — the number never moves as production advances. A rule added once
# more patches are already immutable simply gets a higher number.
#
# Each rule carries its own literal number. They coincide at 39 today — the
# original ruleset shipped after patches 0001-0038 were already immutable, and
# the inline-citation rule rides the same line because 0039+ were retrofitted to
# comply — but this is NOT one shared constant: an existing rule's number must
# never change, and a new rule's is independent. Do not factor these into a
# constant; that re-invites bumping them together, the very bug this removes.
RULE_SINCE: dict[str, int] = {
    "note-patch-number": 39,
    "note-typography": 39,
    "cite-scheme-form": 39,
    "note-required": 39,
    "description-attribution": 39,
    "description-needs-inline-cite": 39,
    "description-no-entry-cite": 39,
    "description-two-sources": 39,
    "alias-duplicates": 39,
    "note-no-quote-scaffolding": 76,
    "quote-typography": 76,
    "alias-length": 39,
    "patch-description-length": 39,
}
_PREFIX_RE = re.compile(r"^(\d{4})-")


def _patch_number(filename: str) -> int:
    """The patch's numeric prefix; un-numbered input lints under every rule."""
    match = _PREFIX_RE.match(filename)
    return int(match.group(1)) if match else 10**9


def _active(rule: str, patch_num: int) -> bool:
    """Whether ``rule`` is enforced on a patch of this number."""
    return patch_num >= RULE_SINCE[rule]


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

# Entity types whose ``description:`` is exempt from the citation rules
# (``description-needs-inline-cite`` and ``description-two-sources``). These are
# abstract taxonomy concepts, not specific real-world entities: their
# descriptions *define* the concept and cross-reference related features and
# notable games via ``[[…]]`` wikilinks rather than footnoting sourced facts, so
# an inline ``[[cite:N]]`` requirement does not fit them. The desc attribution
# and no-entry-cite rules still apply.
DESCRIPTION_CITE_EXEMPT_TYPES = {
    "gameplay-feature",
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
# The key inside an inline footnote, e.g. the "2" in [[cite:2]].
INLINE_CITE_KEY_RE = re.compile(r"\[\[cite:([^\]]+)\]\]")
# The legacy note-as-quote scaffolding shape: a short source phrase, a
# quote-introducing verb (or a colon), then a quoted span. Verbs mirror the
# migration recognizer's; own-data notes ('The name includes "Prototype"')
# use none of them and stay legal.
NOTE_QUOTE_SCAFFOLDING_RE = re.compile(
    r'^[^"]{1,60}?(?:\s+(?:says|lists|states|reports|reported|dates this)'
    r"(?:\s+that)?\s+|:\s+)\""
)
# The host of a URL cite, with any leading www. stripped.
URL_HOST_RE = re.compile(r"^https?://(?:www\.)?([^/?#]+)", re.IGNORECASE)
ALIAS_MAX, ABBREV_MAX = 200, 50
# The top-level patch description maps to the Admin-only IngestRun note; keep it
# to a commit-title-style summary rather than a paragraph of changeset detail.
PATCH_DESC_MAX = 80


def _cite_root(cite: str) -> str | None:
    """The root source of a cite, for the two-distinct-sources check.

    A URL collapses to its registrable domain — the last two host labels, www.
    stripped — so ``twip.kineticist.com`` and ``www.kineticist.com`` share the
    root ``kineticist.com``. A ``scheme:identifier`` cite (``ipdb:6069``,
    ``youtube:abc``) collapses to its scheme. ``None`` if neither form parses.
    """
    match = URL_HOST_RE.match(cite.strip())
    if match:
        labels = match.group(1).lower().split(".")
        return ".".join(labels[-2:]) if len(labels) >= 2 else labels[0]
    scheme, sep, _ = cite.partition(":")
    return scheme.strip().lower() or None if sep else None


# Patch YAML is untrusted until validate_patches.py (and, authoritatively,
# flipcommons' ingest_patches) accept it, so a parsed unit is just an open
# string-keyed mapping; reserved fields are narrowed at the use site with the
# guards below. A closed TypedDict can't model a unit — it carries arbitrary
# authored-field keys (year, manufacturer_alias, …) beside the reserved ones.
PatchUnit = Mapping[str, object]  # a provenance carrier: entity body OR changeset


class CiteMap(TypedDict):
    """A cite given as a map; we read its ``ref`` and ``quote`` (other keys are ignored)."""

    ref: str
    quote: NotRequired[str]


def is_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    """Narrow an untrusted YAML value to a string-keyed mapping."""
    return isinstance(value, Mapping)


def is_cite_map(value: object) -> TypeGuard[CiteMap]:
    """Narrow a cite value to the ``{ref, …}`` map form (not a bare string)."""
    return isinstance(value, Mapping) and isinstance(value.get("ref"), str)


def _units(body: PatchUnit) -> Iterator[tuple[str, PatchUnit]]:
    """Yield ``(label, unit)`` for the entry header and each changesets item."""
    yield "", body
    changesets = body.get("changesets")
    if isinstance(changesets, list):
        for i, changeset in enumerate(changesets):
            if is_mapping(changeset):
                yield f" changesets[{i}]", changeset


def _cite_specs(unit: PatchUnit) -> Iterator[object]:
    """Yield each entry-level cite spec — ``cite:`` takes one bare-string/mapping
    spec or a non-empty list of them (multi-source evidence)."""
    cite = unit.get("cite")
    if isinstance(cite, list):
        yield from cite
    elif cite is not None:
        yield cite


def _cite_strings(unit: PatchUnit) -> Iterator[str]:
    """Yield every cite URL/identifier on a unit (cite: and the cites: map)."""
    for spec in _cite_specs(unit):
        if isinstance(spec, str):
            yield spec
        elif is_cite_map(spec):
            yield spec["ref"]
    cites = unit.get("cites")
    if is_mapping(cites):
        for value in cites.values():
            if isinstance(value, str):
                yield value
            elif is_cite_map(value):
                yield value["ref"]


def _quote_values(unit: PatchUnit) -> Iterator[tuple[str, str]]:
    """Yield ``(label, quote)`` for every verbatim quote on a unit.

    Walks the entry-level ``cite:`` spec(s) — including each element of a
    list-valued ``cite:`` — and each inline ``cites:`` entry, so quote-driven
    rules (``quote-typography``, the ``note-required`` exemption) treat every
    carrier identically.
    """
    listed = isinstance(unit.get("cite"), list)
    for i, spec in enumerate(_cite_specs(unit)):
        if is_cite_map(spec) and isinstance(spec.get("quote"), str):
            yield (f"cite[{i}]" if listed else "cite"), spec["quote"]
    cites = unit.get("cites")
    if is_mapping(cites):
        for handle, value in cites.items():
            if is_cite_map(value) and isinstance(value.get("quote"), str):
                yield f"cites[{handle!r}]", value["quote"]


def _check_unit(
    ref: str,
    ref_type: str,
    attribution: str,
    label: str,
    unit: PatchUnit,
    patch_num: int,
) -> list[str]:
    where = f"{ref}{label}"
    errors: list[str] = []

    def on(rule: str) -> bool:
        return _active(rule, patch_num)

    authored = {k for k in unit if k not in RESERVED}
    nonalias_field = authored - ALIAS_KEYS - {"description"}
    description_only = bool(authored) and authored <= {"description"}
    has_note = isinstance(unit.get("note"), str)
    has_cite = ("cite" in unit) or ("cites" in unit)
    # A cite carrying a verbatim quote — entry-level or inline — explains the
    # change by itself; the note is for editorial rationale beyond the
    # evidence, so it may be absent.
    unit_quotes = list(_quote_values(unit))
    has_quoted_cite = bool(unit_quotes)
    is_create = unit.get("create") is True
    is_delete = unit.get("delete") is True
    has_retract_remove = ("retract" in unit) or ("remove" in unit)
    has_description = "description" in authored
    description = unit.get("description") if has_description else None
    inline_cite = isinstance(description, str) and INLINE_CITE in description

    # note-patch-number + note-typography: note content
    note = unit.get("note")
    if isinstance(note, str):
        if on("note-patch-number"):
            errors.extend(
                f"{where}: note references patch number {token!r} — notes are "
                f"public; move cross-patch bookkeeping to the description:"
                for token in dict.fromkeys(PATCH_NUM_RE.findall(note))
            )
        smart = sorted(set(SMART_RE.findall(note)))
        if smart and on("note-typography"):
            errors.append(
                f"{where}: note contains smart typography {smart} — use straight "
                f"quotes and write an ellipsis as [...]"
            )
        if NOTE_QUOTE_SCAFFOLDING_RE.match(note) and on("note-no-quote-scaffolding"):
            errors.append(
                f"{where}: note carries '<source> says \"...\"' scaffolding — "
                f"put the verbatim excerpt in quote: on the cite: mapping and "
                f"keep the note for rationale"
            )

    # quote-typography: every quote on the unit (entry-level cite and inline cites)
    for quote_label, quote in unit_quotes:
        smart = sorted(set(SMART_RE.findall(quote)))
        if smart and on("quote-typography"):
            errors.append(
                f"{where}: {quote_label} quote contains smart typography {smart} — "
                f"use straight quotes and write an ellipsis as [...]"
            )

    # cite-scheme-form
    if on("cite-scheme-form"):
        errors.extend(
            f"{where}: cite {cite!r} is an IPDB/OPDB URL — use the "
            f"scheme:identifier form (ipdb:<id> / opdb:<id>)"
            for cite in _cite_strings(unit)
            if SCHEME_DOMAIN_RE.search(cite)
        )

    # note-required: note presence (a quote-bearing cite counts as the
    # explanation — see has_quoted_cite above)
    needs_note = (
        (has_cite and not description_only)
        or is_delete
        or has_retract_remove
        or (bool(nonalias_field) and not is_create)
    )
    if needs_note and not has_note and not has_quoted_cite and on("note-required"):
        errors.append(f"{where}: this change needs a note: explaining it")

    # description-attribution + description-needs-inline-cite + description-no-entry-cite
    if has_description:
        want = f"flipcommons-ai-desc-{ref_type}"
        if attribution != want and on("description-attribution"):
            errors.append(
                f"{where}: a description: field must be attributed {want!r}, "
                f"not {attribution!r}"
            )
        # A record description footnotes its facts inline; it must carry at least
        # one [[cite:N]] marker. A note: no longer excuses a missing footnote.
        # Taxonomy descriptions (DESCRIPTION_CITE_EXEMPT_TYPES) are exempt — they
        # are definitional cross-references, not sourced claims.
        cite_exempt = ref_type in DESCRIPTION_CITE_EXEMPT_TYPES
        if not inline_cite and not cite_exempt and on("description-needs-inline-cite"):
            errors.append(
                f"{where}: a description: needs at least one inline [[cite:N]] "
                f"footnote (declare new ones in a cites: map)"
            )
        # The whole-field cite: covers the description opaquely; footnote each
        # fact inline instead. (Predates inline footnotes in descriptions.)
        if "cite" in unit and on("description-no-entry-cite"):
            errors.append(
                f"{where}: an entry-level cite: is not allowed on a description: "
                f"— footnote facts inline with [[cite:N]]"
            )
        # A description must rest on at least two distinct sources, and those must
        # come from at least two different roots — one source, or several
        # footnotes off one root, is not corroboration.
        # TEMPORARILY DISABLED — re-enable by uncommenting this block (and the
        # skipped flagging tests in tests/test_lint_patches.py). Keep the
        # description-two-sources entry in RULE_SINCE while disabled.
        # if on("description-two-sources") and not cite_exempt and isinstance(description, str):
        #     cites = unit.get("cites")
        #     keys = dict.fromkeys(INLINE_CITE_KEY_RE.findall(description))
        #     roots: set[str] = set()
        #     for key in keys:
        #         value = cites.get(key) if is_mapping(cites) else None
        #         url = value["ref"] if is_cite_map(value) else value
        #         if isinstance(url, str) and (root := _cite_root(url)):
        #             roots.add(root)
        #     if len(keys) < 2:
        #         errors.append(
        #             f"{where}: a description: must cite at least two sources "
        #             f"(found {len(keys)})"
        #         )
        #     elif len(roots) < 2:
        #         only = next(iter(roots), "?")
        #         errors.append(
        #             f"{where}: a description: cites only one root source "
        #             f"({only!r}) — cite at least two different sources"
        #         )

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
        if dups and on("alias-duplicates"):
            errors.append(
                f"{where}: {key} has duplicate members "
                f"{sorted(dups)} ({'aliases case-fold' if casefold else 'verbatim'})"
            )
        limit = ABBREV_MAX if key == "abbreviation" else ALIAS_MAX
        if on("alias-length"):
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
    patch_num = _patch_number(filename)
    errors: list[str] = []

    # patch-description-length: the whole-patch description (→ IngestRun.note) is
    # an Admin-only summary, not a place for changeset detail. Measure the
    # whitespace-collapsed text so a folded scalar's wrapping/trailing newline
    # doesn't count against the budget.
    description = data.get("description")
    if isinstance(description, str) and _active("patch-description-length", patch_num):
        collapsed = " ".join(description.split())
        if len(collapsed) > PATCH_DESC_MAX:
            errors.append(
                f"patch description is {len(collapsed)} chars (max "
                f"{PATCH_DESC_MAX}) — keep it to a single short summary; per-change "
                f"detail belongs in note: fields, not the Admin-only description:"
            )

    claims = data.get("claims")
    if isinstance(claims, list):
        for entry in claims:
            if not is_mapping(entry):
                continue
            for ref, body in entry.items():
                if not is_mapping(body):
                    continue
                ref_type = ref.split(".", 1)[0]
                for label, unit in _units(body):
                    errors.extend(
                        _check_unit(ref, ref_type, attribution, label, unit, patch_num)
                    )
    return [f"{filename}: {e}" for e in errors]


def main() -> int:
    if not PATCHES_DIR.is_dir():
        print("No patches/ directory; nothing to lint.")
        return 0

    errors: list[str] = []
    for path in sorted(PATCHES_DIR.glob("*.yaml")):
        # Every patch is linted; each rule grandfathers patches below its own
        # introduction number (see RULE_SINCE), so immutable history stays clean.
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
