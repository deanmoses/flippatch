#!/usr/bin/env python3
"""Editorial authoring standards linting for data patches.

This enforces the authoring quality conventions like public-note discipline and
citation hygiene.  The data patch schema does NOT enforce this stuff.

Much of this is also guidance in flipcommons' ``docs/DataPatchAuthoring.md``.

Run by ``make validate``.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
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
# patches numbered below that are grandfathered for that rule. A number never
# moves once set — a rule introduced later simply gets a higher one.
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
    "expect-obsolete": 130,
    "prose-seed": 189,
    "prose-node": 189,
    "prose-edge": 189,
    "prose-code-identifier": 189,
    "prose-bare-entity": 189,
    "prose-the-record": 189,
    "prose-the-catalog": 189,
    "prose-catalogs": 189,
    "prose-pinball-record": 189,
    "prose-authoring-process": 215,
    "prose-prior-state": 215,
    "prose-absence-claim": 215,
    "prose-vocabulary": 215,
    "prose-namespace": 215,
    "prose-taxonomy": 215,
    "prose-search-effort": 215,
    "prose-temporal-filler": 215,
    "prose-classification": 215,
    "locator-pagination-absence": 215,
    "locator-document-length": 215,
    "feature-grouping-node": 219,
    "description-dating-phrases": 239,
    "description-repeat-link": 239,
}

# Gameplay-feature nodes that exist only to group their children (the toy
# classification tree and the interactive-lighting DAG); a model attaches the
# leaves, never these. See flipcommons docs/plans/catalog_data_model/
# unique_features/UniqueFeatures.md. Grown as taxonomies are added.
GROUPING_FEATURE_SLUGS = frozenset(
    {
        "toys",
        "interactive-toys",
        "interactive-lighting",
        "expression-lighting-system",
    }
)
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
# An IPDB/OPDB URL cite that should instead be scheme:identifier. Matched on the
# RECORD path, not the bare domain: these mirror the url_shapes flipcommons'
# schemes declare (ipdb `/machine.cgi?id=`, opdb `/machines/<id>`), and only a
# URL a scheme can represent has a scheme form to be rewritten to. Other pages on
# those sites — an image page such as `/showpic.pl?id=…&picno=…` holding a flyer
# scan — classify as ordinary web children of the root, so demanding
# `scheme:identifier` for one would leave it with no citable form at all.
SCHEME_DOMAIN_RE = re.compile(
    r"https?://(?:www\.)?(?:ipdb\.org/machine\.cgi|opdb\.org/machines/)", re.IGNORECASE
)
# A locator describing what the document does NOT print — "the sheet carries no
# printed folio". The absence of a page number locates nothing.
LOCATOR_NO_FOLIO_RE = re.compile(
    r"no (?:printed )?(?:folios?|foliation|page numbers?|pagination)"
    r"|unpaginated|unnumbered pages?",
    re.IGNORECASE,
)
# "page 2 of 2" / "sheet 1 of 4" — the total is document length, not a location.
LOCATOR_PAGE_OF_RE = re.compile(
    r"\b(?:pages?|sheets?|pp?\.)\s*\d+\s+of\s+\d+\b", re.IGNORECASE
)
INLINE_CITE = "[[cite:"
# The key inside an inline footnote, e.g. the "2" in [[cite:2]].
INLINE_CITE_KEY_RE = re.compile(r"\[\[cite:([^\]]+)\]\]")
# A cross-reference wikilink in a description, captured as "type:public-id" so
# the same record under two types (title vs model) keys apart. [[cite:N]] is
# excluded: a footnote handle is *meant* to carry several markers.
DESC_LINK_RE = re.compile(r"\[\[(?!cite:)([^\]]+)\]\]")
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
# flipcommons rejects duplicate members at apply and over-long ones at build;
# catching both here keeps the failure in authoring, where it is fixable.
ALIAS_MAX, ABBREV_MAX = 200, 50
# The top-level patch description maps to the Admin-only IngestRun note; keep it
# to a commit-title-style summary rather than a paragraph of changeset detail.
PATCH_DESC_MAX = 80

# --- prose word-choice rules ------------------------------------------------
# Prose written for the site's nontechnical readers must not use internal
# programming vocabulary. The three prose corpora a rule can apply to. Record descriptions are public
# encyclopedia text where several of these words have a legitimate
# physical/trade sense, so some rules exclude them.
PATCH_DESC, NOTE, RECORD_DESC = "patch description", "note", "description"
_ALL_PROSE = frozenset({PATCH_DESC, NOTE, RECORD_DESC})
_AUTHORING_PROSE = frozenset({PATCH_DESC, NOTE})
# Notes only. The top-level patch description is the Admin-only IngestRun note,
# so internal bookkeeping vocabulary is correct there and wrong in a note.
_NOTE_ONLY = frozenset({NOTE})
_RECORD_DESC_ONLY = frozenset({RECORD_DESC})

# Internal CamelCase model names. A general CamelCase pattern can't work —
# TiltBob, WhizBang, MarsaPlay and other brand names are legitimate CamelCase —
# so code names are denylisted explicitly.
_INTERNAL_CAMEL = (
    "ChangeSet",
    "CitationSource",
    "CorporateEntity",
    "DateOfManufacture",
    "IngestRun",
    "MachineModel",
    "ModelRelationship",
    "ProductionStatus",
)

# (rule, corpora it applies to, pattern, guidance). Each match is reported with
# the offending token, so guidance stays generic.
PROSE_RULES: tuple[tuple[str, frozenset[str], re.Pattern[str], str], ...] = (
    (
        # A member of the prose-authoring-process family below, kept separate
        # because a rule's RULE_SINCE number never moves once it ships.
        "prose-seed",
        _AUTHORING_PROSE,
        re.compile(r"\bseed(?:s|ed|ing)?\b", re.IGNORECASE),
        "contributors don't know our pipeline — cut the reference, don't rename it",
    ),
    # A note renders publicly and must read standalone decades on, naming
    # neither how it was authored nor what the data used to be. The next two
    # split by what a word *names*, not by what the sentence uses it to say:
    # "seed" and "ingest" name our own pipeline, so they are process words even
    # in a sentence about a prior value, while "supersedes" and "the prior
    # value" describe the data's history in ordinary English.
    (
        "prose-authoring-process",
        _AUTHORING_PROSE,
        re.compile(
            r"\bingest(?:s|ed|ing)?\b"
            r"|\bREADME\b"
            r"|\bcampaign (?:README|dir(?:ectory)?)\b"
            r"|\bper the campaign\b"
            r"|\buser[-\s]approv\w*"
            r"|\bapproved by the (?:user|operator)\b"
            r"|\bas discussed\b"
            r"|\b(?:flagged|held|caught) in review\b",
            re.IGNORECASE,
        ),
        "how the patch got authored, and who took part, is invisible to the "
        "reader — cut it",
    ),
    (
        "prose-prior-state",
        _AUTHORING_PROSE,
        re.compile(
            r"\bsupersed\w*"
            r"|\b(?:prior|previous|former|old) value\b",
            re.IGNORECASE,
        ),
        "what the data used to be is on the Edit History page already — cut "
        "it, or say plainly what makes the prior state load-bearing",
    ),
    (
        # Not a word-choice rule like its neighbours: the defect is the claim's
        # shape, not its register. It reaches record descriptions because an
        # ageing absolute is worse in public encyclopedia prose than in a note.
        "prose-absence-claim",
        _ALL_PROSE,
        re.compile(
            # Naming the silent source does not rescue the claim, so 'no
            # record' and a bare 'nowhere' are in scope: a gap in one source is
            # not evidence, and "OPDB has no record of it" writes that source
            # up as an oracle that owed us an answer.
            r"\bno (?:other |known )*(?:sources?|records?|evidence|documentation)\b"
            r"|\bnowhere\b"
            r"|\bnothing else (?:documents|records|states|mentions)\b"
            r"|\bonly (?:known|surviving|documented|recorded)\b"
            r"|\bsole (?:known|surviving|documented)\b",
            re.IGNORECASE,
        ),
        "the next source to surface falsifies an absence claim — cut it and "
        "let the cite stand for what is supported",
    ),
    (
        # 'sought-after' is the collector's-market sense and stays clean.
        "prose-search-effort",
        _AUTHORING_PROSE,
        re.compile(
            r"\bsought\b(?!-after)|\bnone (?:were )?found\b",
            re.IGNORECASE,
        ),
        "the fact of looking is not evidence — cut it",
    ),
    (
        # 'at the time' is excluded: it points at a moment in the past, which
        # is the opposite defect. 'still' and 'today' read as natural prose and
        # stay out of scope.
        "prose-temporal-filler",
        _ALL_PROSE,
        re.compile(
            r"\bat authoring time\b"
            r"|\bat (?:the moment|this time|this point|present)\b"
            r"|\bcurrently\b|\bpresently\b"
            r"|\bas of (?:now|today|this writing)\b"
            r"|\bto date\b|\bso far\b",
            re.IGNORECASE,
        ),
        "the reader already assumes now — cut it or name the date if timing matters",
    ),
    (
        # Superlatives and recency words pin an ongoing maker's description to
        # the year it was written. 'still' and 'today' are excluded despite
        # ageing the same way: they are the settled wording in ten shipped
        # descriptions ("it survives in Turin today"), and a rule that fires on
        # correct prose gets ignored.
        "description-dating-phrases",
        _RECORD_DESC_ONLY,
        re.compile(
            r"\blatest\b|\bnewest\b|\bmost recent\b|\brecently\b"
            r"|\bupcoming\b|\bforthcoming\b"
            r"|\b(?:their|its)\s+(?:one|only|sole)\s+(?:machine|game|title|model)\b",
            re.IGNORECASE,
        ),
        "dates the prose — the next machine falsifies it; name the year instead",
    ),
    (
        # Active voice only. Passive 'recorded as' is ordinary prose about what
        # a source documents ("BEM is recorded as building"), or rationale for
        # a deliberate omission — 30 distinct legitimate uses in the corpus.
        "prose-classification",
        _NOTE_ONLY,
        re.compile(r"\bmap(?:s|ped|ping) to\b|\brecords as\b", re.IGNORECASE),
        "the quote shows the match — cut the reasoning",
    ),
    (
        # Notes only: unlike its namespace/taxonomy neighbours, this word does
        # honest work in the Admin-only patch description ("create the four
        # production-status vocabulary values").
        "prose-vocabulary",
        _NOTE_ONLY,
        re.compile(r"\bvocabular(?:y|ies)\b", re.IGNORECASE),
        "internal term — you can probably delete talking about it",
    ),
    (
        "prose-namespace",
        _ALL_PROSE,
        re.compile(r"\bnamespaces?\b", re.IGNORECASE),
        "internal term — name the kind of record in plain words",
    ),
    (
        "prose-taxonomy",
        _ALL_PROSE,
        re.compile(r"\btaxonom(?:y|ies|ic)\b", re.IGNORECASE),
        "internal term — name the set of values in plain words",
    ),
    (
        "prose-node",
        _ALL_PROSE,
        re.compile(r"\bnodes?\b", re.IGNORECASE),
        "internal term — describe the record in plain words",
    ),
    (
        "prose-edge",
        _AUTHORING_PROSE,
        re.compile(r"\bedges?\b", re.IGNORECASE),
        "internal term — describe the relationship in plain words",
    ),
    (
        "prose-code-identifier",
        _ALL_PROSE,
        re.compile(
            r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b"
            r"|\b(?:" + "|".join(_INTERNAL_CAMEL) + r")s?\b"
        ),
        "code identifier — write it in plain words ('conversion kit', "
        "'relationship type')",
    ),
    (
        "prose-bare-entity",
        _ALL_PROSE,
        re.compile(
            r"(?<!corporate )(?<!corporate-)(?<!legal )(?<!legal-)"
            r"\bentit(?:y|ies)\b",
            re.IGNORECASE,
        ),
        "internal jargon — name the thing (the firm, the maker, the record) "
        "or write 'corporate entity' in full",
    ),
    (
        "prose-the-record",
        _ALL_PROSE,
        re.compile(
            r"\b(?:the|this|that|these|those|each|every|its|their|both|all|per)"
            r"\s+records?\b",
            re.IGNORECASE,
        ),
        "database phrasing — name what it is (the machine, the maker, the entry)",
    ),
    # 'catalog' is two different problems, so two rules with different fixes.
    # Determiner + singular ("the catalog", "this catalog", "the eremeka
    # catalog"): the READER CAN'T RESOLVE THE REFERENT — they don't know
    # "catalog" means a website, this one or another. The fix is to name the
    # site. Possessives ("SIRMO's catalog", a maker's product line) are
    # legitimate trade English and don't match.
    (
        "prose-the-catalog",
        _ALL_PROSE,
        re.compile(
            r"\b(?:the|this|our)\s+(?:\w+\s+)?catalog(?:ue)?\b",
            re.IGNORECASE,
        ),
        "the reader can't tell what site 'catalog' refers to — name the site: "
        "this one by name, another by its name or domain ('eremeka.net dates "
        "this to 1974')",
    ),
    # Bare plural or verb ("Catalogs list them", "the community catalogues
    # these machines"): the referent is clear — the problem is the PEDANTIC
    # REGISTER. The fix is plain wording, not naming a site.
    (
        "prose-catalogs",
        _ALL_PROSE,
        re.compile(r"(?<!-)\bcatalog(?:ue)?s\b", re.IGNORECASE),
        "pedantic — these are sites and lists: write 'sites like IPDB', "
        "'IPDB lists it', 'other pinball sites put it under that name'",
    ),
    (
        "prose-pinball-record",
        _ALL_PROSE,
        re.compile(r"\bthe pinball record\b", re.IGNORECASE),
        "drop the phrase — 'known in the pinball record for X' is just 'known for X'",
    ),
)


def _prose_errors(corpus: str, text: str, patch_num: int) -> Iterator[str]:
    """Word-choice findings for one prose field, without the location prefix."""
    for rule, corpora, pattern, guidance in PROSE_RULES:
        if corpus not in corpora or not _active(rule, patch_num):
            continue
        for token in dict.fromkeys(m.group(0) for m in pattern.finditer(text)):
            yield f"{corpus} uses {token!r} — {guidance}"


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
    """A cite given as a map; we read these keys (others are ignored)."""

    ref: str
    quote: NotRequired[str]
    locator: NotRequired[str]


def is_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    """Narrow an untrusted YAML value to a string-keyed mapping."""
    return isinstance(value, Mapping)


def is_cite_map(value: object) -> TypeGuard[CiteMap]:
    """Narrow a cite value to the ``{ref, …}`` map form (not a bare string)."""
    return isinstance(value, Mapping) and isinstance(value.get("ref"), str)


def _units(body: PatchUnit) -> Iterator[tuple[str, PatchUnit]]:
    """Yield ``(label, unit)`` for the entry header and each changesets item.

    A ``note:``/``cite:`` rides the claims of its own unit, which is why the
    checks run per unit rather than once per entry.
    """
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


def _cite_maps(unit: PatchUnit) -> Iterator[tuple[str, CiteMap]]:
    """Yield ``(label, cite)`` for every map-form cite on a unit.

    Walks the entry-level ``cite:`` spec(s) — including each element of a
    list-valued ``cite:`` — and each inline ``cites:`` entry, so rules reading
    a cite's fields treat every carrier identically.
    """
    listed = isinstance(unit.get("cite"), list)
    for i, spec in enumerate(_cite_specs(unit)):
        if is_cite_map(spec):
            yield (f"cite[{i}]" if listed else "cite"), spec
    cites = unit.get("cites")
    if is_mapping(cites):
        for handle, value in cites.items():
            if is_cite_map(value):
                yield f"cites[{handle!r}]", value


def _quote_values(unit: PatchUnit) -> Iterator[tuple[str, str]]:
    """Every verbatim quote on a unit — drives ``quote-typography`` and the
    ``note-required`` exemption."""
    for label, cite in _cite_maps(unit):
        quote = cite.get("quote")
        if isinstance(quote, str):
            yield label, quote


def _locator_values(unit: PatchUnit) -> Iterator[tuple[str, str]]:
    """Every locator on a unit — drives the ``locator-*`` rules."""
    for label, cite in _cite_maps(unit):
        locator = cite.get("locator")
        if isinstance(locator, str):
            yield label, locator


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

    # expect-obsolete: the drift guard flipcommons' apply engine now ignores.
    # Grandfathered on older patches; rejected going forward so it stops being
    # copied out of recent patches.
    if "expect" in unit and on("expect-obsolete"):
        errors.append(
            f"{where}: expect: is obsolete — the apply engine ignores it; remove "
            f"it and do not copy it from older patches"
        )

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

    # feature-grouping-node: a model never attaches a grouping vocab node
    if on("feature-grouping-node"):
        members = unit.get("gameplay_feature")
        if isinstance(members, list):
            for member in members:
                # A member is either a bare slug or a one-key {slug: count}
                # mapping, whose single key is the slug.
                slug: str | None = None
                if isinstance(member, str):
                    slug = member
                elif is_mapping(member) and len(member) == 1:
                    slug = next(iter(member))
                if slug in GROUPING_FEATURE_SLUGS:
                    errors.append(
                        f"{where}: gameplay_feature member {slug!r} is a "
                        f"grouping node — it exists to organize the vocabulary; "
                        f"attach the specific leaf (e.g. bash-toys, "
                        f"Speaker Expression Lighting System) instead"
                    )

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
        # prose-*: word choice — notes are public
        errors.extend(f"{where}: {e}" for e in _prose_errors(NOTE, note, patch_num))

    # quote-typography: every quote on the unit (entry-level cite and inline cites)
    for quote_label, quote in unit_quotes:
        smart = sorted(set(SMART_RE.findall(quote)))
        if smart and on("quote-typography"):
            errors.append(
                f"{where}: {quote_label} quote contains smart typography {smart} — "
                f"use straight quotes and write an ellipsis as [...]"
            )

    # locator-pagination-absence + locator-document-length: a locator points at
    # where the evidence sits; it is not prose about the document.
    for locator_label, locator in _locator_values(unit):
        if on("locator-pagination-absence"):
            errors.extend(
                f"{where}: {locator_label} locator notes {token!r} — a locator "
                f"points at where the evidence is, not at what the page lacks"
                for token in dict.fromkeys(LOCATOR_NO_FOLIO_RE.findall(locator))
            )
        if on("locator-document-length"):
            errors.extend(
                f"{where}: {locator_label} locator gives the document length "
                f"({token!r}) — the total does not help anyone find the page"
                for token in dict.fromkeys(LOCATOR_PAGE_OF_RE.findall(locator))
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
        # prose-*: word choice — record descriptions are the site's public text
        if isinstance(description, str):
            errors.extend(
                f"{where}: {e}"
                for e in _prose_errors(RECORD_DESC, description, patch_num)
            )
            # description-repeat-link: the first mention carries the link. A
            # second marker for the same record adds no edge to the reference
            # graph (it is unique on the pair) and only thins the prose.
            if on("description-repeat-link"):
                counts = Counter(DESC_LINK_RE.findall(description))
                errors.extend(
                    f"{where}: description links {target!r} {n} times — "
                    f"link the first mention only"
                    for target, n in counts.items()
                    if n > 1
                )
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


def lint_patch(
    filename: str, data: object, *, ignore_grandfather: bool = False
) -> list[str]:
    """Lint one parsed patch; return a list of ``filename: …`` error strings.

    ``ignore_grandfather`` lints the patch under every rule regardless of
    ``RULE_SINCE`` — the ``--all`` review mode for seeing what a rule would
    have caught in immutable history.
    """
    if not is_mapping(data):
        return []
    attribution = data.get("attribution", "")
    if not isinstance(attribution, str):
        attribution = ""
    patch_num = 10**9 if ignore_grandfather else _patch_number(filename)
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
    # prose-*: word choice on the patch description
    if isinstance(description, str):
        errors.extend(_prose_errors(PATCH_DESC, description, patch_num))

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


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    ignore_grandfather = "--all" in args
    if not PATCHES_DIR.is_dir():
        print("No patches/ directory; nothing to lint.")
        return 0

    errors: list[str] = []
    for path in sorted(PATCHES_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue  # parse/structural validity is validate_patches.py's job
        errors.extend(
            lint_patch(path.name, data, ignore_grandfather=ignore_grandfather)
        )

    if errors:
        print(f"{len(errors)} patch lint error(s):", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    print("All patches pass authoring lint.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
