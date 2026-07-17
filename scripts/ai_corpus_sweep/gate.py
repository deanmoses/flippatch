"""Layer 3 — deterministic gates: the script decides trust, not the model.

Two pure steps after the model's verdict:

- :func:`resolve_target` — the stated target name → catalog model(s), via
  ``EntityIndex.resolve`` (models + titles, titles expanded to their member
  models, the judged model itself excluded so a same-name copy can never
  resolve to itself), then narrowed deterministically by the year and maker
  the note stated. No model call: "1978" selecting the solid-state Mata Hari
  is a filter, not an opinion.
- :func:`dispose_claim` — one relationship claim × quote-verbatim × resolution
  × catalog edge-set diff × hint diff → one disposition, plus the catalog edge
  it addressed (so the pipeline can surface unaddressed edges as
  set-but-unsupported). Confidence is not a number the model reports; it is a
  verified quote plus a unique resolution plus catalog agreement.

Dispositions split green (never needs a human) from review (routed to the
coordinating session / the human table).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from common.catalog.entity_index import normalize_key

from ai_corpus_sweep.catalog import strip_parenthetical
from ai_corpus_sweep.fields import requires_machine_target, requires_other_maker

if TYPE_CHECKING:
    from collections.abc import Callable

    from common.catalog.entity_index import EntityIndex
    from common.catalog.types import Slug

    from ai_corpus_sweep.catalog import CatalogEdge, ModelFacts, SweepCatalog
    from ai_corpus_sweep.judge import JudgeClaim

# ── Dispositions ─────────────────────────────────────────────────────────────
# Green — auto-audited, never surfaces by default:
AGREES = "agrees"  # catalog already holds the resolved value
FILL = "fill"  # catalog empty; quote verified; unique resolution
NO_CLAIM = "no-claim"  # net false positive: note supports nothing, catalog empty
# Review — the short queue a human actually reads:
CONFLICT = "conflict"  # catalog holds a DIFFERENT value than the note supports
SET_BUT_UNSUPPORTED = "set-but-unsupported"  # catalog set; note supports no claim
FACTS_MISMATCH = "facts-mismatch"  # sole resolution contradicts the note's stated facts
SAME_MAKER = "same-maker-target"  # a copy target by the subject's own maker
LABEL_TARGET_INVALID = "label-target-invalid"  # a text label on a machine-only type
QUOTE_UNSUPPORTED = "quote-unsupported"  # verbatim quote fails to establish the claim
ASSET_SCOPED = (
    "asset-scoped-quote"  # the quote copies an ASSET (art, cabinet), not a design
)
MULTI_TARGET = "multi-target-quote"  # the quote names a second candidate target
UNCERTAIN = "uncertain"  # the model could not decide from the note
UNRESOLVED = "unresolved-target"  # stated target matches no catalog model
AMBIGUOUS = "ambiguous-target"  # >1 catalog model even after year/maker filters
QUOTE_FAIL = "quote-unverified"  # the grounding quote is not verbatim in a source
HINT_MISMATCH = "hint-mismatch"  # fill disagrees with the prior guess (two AIs differ)
NO_MODEL = "no-model"  # ipdb_id not in the catalog
NO_EVIDENCE = "no-evidence"  # no source text found for any evidence ref
AI_ERROR = "ai-error"  # the model call failed for this row

GREEN = frozenset({AGREES, FILL, NO_CLAIM})
REVIEW = frozenset(
    {
        CONFLICT,
        SET_BUT_UNSUPPORTED,
        FACTS_MISMATCH,
        SAME_MAKER,
        LABEL_TARGET_INVALID,
        QUOTE_UNSUPPORTED,
        ASSET_SCOPED,
        MULTI_TARGET,
        UNCERTAIN,
        UNRESOLVED,
        AMBIGUOUS,
        QUOTE_FAIL,
        HINT_MISMATCH,
        NO_MODEL,
        NO_EVIDENCE,
        AI_ERROR,
    }
)


@dataclass(frozen=True, slots=True)
class Resolution:
    """The stated target name resolved against the catalog, deterministically."""

    status: str  # "none" | "unique" | "ambiguous"
    chosen: ModelFacts | None
    considered: tuple[ModelFacts, ...]
    how: str  # human-readable trail, e.g. "2 name matches; year 1978 → 1"


def _maker_compatible(
    stated: str,
    candidate: ModelFacts,
    brands: frozenset[str],
    *,
    catalog: SweepCatalog | None = None,
    stated_year: int | None = None,
) -> bool:
    """Is the note's stated maker consistent with the candidate's makers?

    Deliberately lenient — substring containment either way over both the
    Manufacturer (brand) and the corporate entity: notes say "Premier" for a
    Gottlieb-brand game built by Premier Technology, "Williams" for Williams
    Electronics Incorporated. A real contradiction (Bally vs Chicago Coin)
    shares no substring and still fails.

    That leniency has one hole (DEFECT 6): a brand whose slug merely *starts
    with* another brand's — "Bally" ⊂ "bally-wulff", "Taito" ⊂
    "taito-do-brasil" — satisfied a note naming the shorter one, both hiding
    the true target behind a false tie and (worse) able to green a wrong-brand
    sole survivor. So when ``stated`` names a real Manufacturer record
    (``brands``), the candidate's own brand must match it **exactly**; the
    containment fallback is kept for makers that name no brand ("Premier"),
    which is the case the leniency exists for.

    That exactness has its own hole (DEFECT 9): it checks that ``stated`` names
    *a* brand, never that it names a *possible* one. "Stern" is Stern Pinball's
    whole name and also what every Stern Electronics note says, so a 1979 note
    bound to a company founded in 1999 and vetoed its own correct target. So the
    veto is gated on the stated brand being plausible at the stated year: if it
    made nothing near then, the binding is vacuous and containment resumes —
    which reaches "Stern Electronics" exactly as it reaches "Premier". Bally was
    alive in 1979, so Bally-vs-Bally-Wulff still vetoes and DEFECT 6 holds.
    """
    key = normalize_key(stated)
    if not key:
        return True  # nothing stated → nothing to contradict
    brand_keys = [
        normalize_key(value)
        for value in (candidate.maker_slug, candidate.maker_name)
        if value
    ]
    binding = key in brands and bool(brand_keys)
    if binding and catalog is not None and stated_year is not None:
        binding = catalog.brand_active_in(key, stated_year)
    if binding:
        return key in brand_keys
    candidate_keys = brand_keys + [
        normalize_key(value)
        for value in (candidate.ce_slug, candidate.ce_name)
        if value
    ]
    return any(key in ck or ck in key for ck in candidate_keys if ck)


def _year_compatible(stated: int | None, candidate: ModelFacts) -> bool:
    """±1 year is data noise; an unknown candidate year can never contradict."""
    return stated is None or candidate.year is None or abs(candidate.year - stated) <= 1


def _fact_problems(
    claim: JudgeClaim,
    chosen: ModelFacts,
    brands: frozenset[str],
    catalog: SweepCatalog | None = None,
) -> list[str]:
    """How the note's stated facts contradict the chosen candidate (if at all)."""
    problems = []
    if claim.target_maker and not _maker_compatible(
        claim.target_maker,
        chosen,
        brands,
        catalog=catalog,
        stated_year=claim.target_year,
    ):
        problems.append(
            f"note says the target is by {claim.target_maker!r} but the only "
            f"catalog match is {chosen.describe()}"
        )
    if not _year_compatible(claim.target_year, chosen):
        problems.append(
            f"note says the target is from {claim.target_year} but the only "
            f"catalog match is {chosen.describe()}"
        )
    return problems


# The parts a machine is ASSEMBLED FROM or DECORATED WITH. Sharing one of these
# with another game is not a lineage relationship: pinball artwork, cabinets and
# sound hardware travel between otherwise unrelated machines all the time.
_ASSET_NOUNS = (
    "artwork",
    "art",
    "backglass",
    "translite",
    "backbox",
    "playfield",
    "cabinet",
    "marquee",
    "apron",
    "plastics",
    "decals",
    "theme",
    "sound card",
    "sound board",
    "soundboard",
)
_ASSET_RE = re.compile(
    r"\b(" + "|".join(re.escape(noun) for noun in _ASSET_NOUNS) + r")\b", re.IGNORECASE
)
# The words that carry a lineage claim. Everything before the FIRST of these is
# what the claim is being made ABOUT.
_REL_VERB_RE = re.compile(
    r"\b(copy|copies|copied|clone|cloned|conversion|converted|convert|"
    r"re-?theme|re-?themed|re-?skin|re-?skinned)\b",
    re.IGNORECASE,
)


def asset_scoped_quote(quote: str) -> str:
    """The asset noun a quote scopes its copy/conversion claim to, or "".

    TOOL-NOTES DEFECT 7. "Backglass artwork is in part a copy of Gottlieb's
    1970 'Scuba'" says the ARTWORK was copied — Jaws is a conversion of some
    other Gottlieb entirely, and the same note adds that the art "was also used
    again on AMI's 1976 'The Shark'". That row resolved uniquely and quoted
    verbatim, so nothing but the Worklist's (differently wrong) hint stopped it
    greening as a machine copy.

    Position is the whole test, because an asset noun is perfectly normal in a
    genuine copy's quote — "a copy of [...] 'Vulcan' except the backglass
    depicts a woman" (0158) and "a converted [...] game with a digital display
    and sound card added" (0160) are both real shipped fills. What distinguishes
    the false one is that the asset is the SUBJECT of the copy verb: it sits
    *before* it. So we look only at the text preceding the first lineage verb.
    """
    verb = _REL_VERB_RE.search(quote)
    if verb is None:
        return ""
    asset = _ASSET_RE.search(quote[: verb.start()])
    return asset.group(1).lower() if asset else ""


def other_models_in_quote(
    quote: str,
    *,
    index: EntityIndex,
    subject: ModelFacts,
    target: ModelFacts,
) -> list[str]:
    """Catalog models the quote names BESIDES the subject and resolved target.

    The and-joined-donors gate (TOOL-NOTES DEFECT 5): "conversion kit for X and
    Y" greens as a single fill on whichever donor the model reported, unless
    something notices the quote itself names another candidate. Deterministic —
    an n-gram scan of the quote against the model/title index; a mention counts
    only when NONE of its readings is the subject or the target, so same-name
    pairs and ambiguous mentions of the target itself never trip it. Quote-
    scoped on purpose: the full note legitimately mentions companion machines.
    """
    # A mention is "own" when any reading resolves to the subject/target slug,
    # OR its surface text is the subject/target's name (base-name aware): the
    # mention index resolves a bare "Supersonic" to the sibling still named
    # exactly that, not to the "(Bally)"-suffixed target — the same suffix
    # blind spot DEFECT 1 fixed for resolution, filtered here by surface.
    # And a mention only counts when the note QUOTES it as a title ('Rock'):
    # IPDB writes machine names in quotes, and without that requirement every
    # common-word model name ("colors", "round", "add-a-ball") fires on
    # ordinary prose.
    own_slugs = {subject.slug, target.slug}
    own_keys = {
        normalize_key(text)
        for facts in (subject, target)
        for text in (facts.slug, facts.name, strip_parenthetical(facts.name))
    }
    text = quote.replace("[...]", " ")
    named: list[str] = []
    for mention in index.find_mentions(text):
        slugs = {ref.slug for ref in mention.refs}
        if slugs & own_slugs or normalize_key(mention.surface) in own_keys:
            continue
        if not _quoted_as_title(text, mention.start, mention.end):
            continue
        named.extend(sorted(slugs - set(named)))
    return named


_QUOTE_MARKS = frozenset("'\"‘’“”")


def _quoted_as_title(text: str, start: int, end: int) -> bool:
    """Is the span written as a quoted title ('Rock') rather than bare prose?"""
    return (
        start > 0
        and end < len(text)
        and text[start - 1] in _QUOTE_MARKS
        and text[end] in _QUOTE_MARKS
    )


def _technology_tiebreak(
    candidates: tuple[ModelFacts, ...],
    subject: ModelFacts | None,
    trail: list[str],
) -> tuple[ModelFacts, ...]:
    """Prefer the candidate built on the subject's own technology generation.

    Gottlieb (and others) shipped EM and SS twins of the same game in the same
    year — "Gottlieb's 1978 'Dragon'" narrows by maker and year to exactly two
    and stops, because the note names a fact neither twin owns alone. The
    subject settles it: a derivative rides its donor's hardware generation, so
    an EM copy is not built from an SS design (every Fipermatic copy is EM and
    every one of its targets is the EM twin).

    A tie-break, never a filter, and only among candidates that all carry a
    technology: a candidate with none can't be excluded by a fact it doesn't
    carry (DEFECT 2's lesson), and guessing against missing data is how a
    false green happens.
    """
    if subject is None or not subject.technology:
        return candidates
    if not all(c.technology for c in candidates):
        trail.append("technology tie-break skipped (a candidate has none)")
        return candidates
    matching = tuple(c for c in candidates if c.technology == subject.technology)
    if not matching or len(matching) == len(candidates):
        return candidates
    trail.append(f"technology {subject.technology!r} → {len(matching)}")
    return matching


def resolve_target(
    claim: JudgeClaim,
    *,
    index: EntityIndex,
    catalog: SweepCatalog,
    exclude_model_id: int,
    subject: ModelFacts | None = None,
) -> Resolution:
    """Resolve the note's stated target to catalog model(s); narrow by facts.

    Candidates are gathered from the name/alias/title index AND from the
    base-name map (both the stated title and the catalog names with any
    trailing "(...)" disambiguator stripped) — a parenthetical the catalog adds
    and the source does not ("Dragon (EM)") must not hide a target from its own
    note (TOOL-NOTES DEFECT 1).

    Filters are applied only while they keep at least one candidate: a stated
    year that matches nothing is recorded in ``how`` but never wipes the set —
    an over-eager filter would silently manufacture UNRESOLVED escalations. A
    candidate with an unknown year survives the year filter (it cannot be
    excluded by a fact it doesn't carry). And a unique survivor is only
    trusted if the note's stated facts don't contradict it (DEFECT 2 — the
    "Major League"/"Champion" false greens).

    ``subject`` is the model being judged; its own technology breaks the
    same-year EM/SS twin tie its note cannot (see ``_technology_tiebreak``).
    """
    brands = catalog.brand_keys()
    by_slug: dict[Slug, ModelFacts] = {}

    def collect(facts: ModelFacts | None) -> None:
        if facts is not None and facts.model_id != exclude_model_id:
            by_slug.setdefault(facts.slug, facts)

    names = {claim.target_title, strip_parenthetical(claim.target_title)}
    for name in names:
        if not name:
            continue
        for ref in index.resolve(name, types=("model", "title")):
            if ref.entity_type == "model":
                collect(catalog.by_slug(ref.slug))
            else:
                for facts in catalog.title_models(ref.slug):
                    collect(facts)
        for facts in catalog.by_base_name(name):
            collect(facts)

    candidates = tuple(by_slug.values())
    # Name the pre-narrow matches in the trail: the artifact must show what
    # narrowing dropped, or a silently-wrong pick is invisible after the fact.
    matched = sorted(c.slug for c in candidates)
    shown = ", ".join(matched[:8]) + ("…" if len(matched) > 8 else "")
    trail = [
        f"{len(candidates)} catalog match(es) for {claim.target_title!r}"
        + (f" [{shown}]" if matched else "")
    ]
    if not candidates:
        return Resolution("none", None, (), "; ".join(trail))

    def narrow(label: str, matches: Callable[[ModelFacts], bool]) -> None:
        nonlocal candidates
        if len(candidates) == 1:
            return
        narrowed = tuple(c for c in candidates if matches(c))
        if narrowed:
            trail.append(f"{label} → {len(narrowed)}")
            candidates = narrowed
        else:
            trail.append(f"{label} matches none (filter skipped)")

    # Maker first: a maker contradiction is a harder fact than a year (years
    # drift ±1 between sources; brands don't) — narrowing by year first let
    # "Bally's 1949 Champion" resolve to Chicago Coin's. Year then narrows
    # exact-first (that is what splits an EM/SS same-name pair one year apart),
    # falling back to ±1-with-unknown only when nothing matches exactly.
    if claim.target_maker:
        narrow(
            f"maker {claim.target_maker!r}",
            lambda c: _maker_compatible(
                claim.target_maker,
                c,
                brands,
                catalog=catalog,
                stated_year=claim.target_year,
            ),
        )
    if claim.target_year and len(candidates) > 1:
        exact = tuple(c for c in candidates if c.year == claim.target_year)
        if exact:
            trail.append(f"year {claim.target_year} → {len(exact)}")
            candidates = exact
        else:
            narrow(
                f"year {claim.target_year}",
                lambda c: _year_compatible(claim.target_year, c),
            )

    # Exact-name tie-break (the King-of-Diamonds shape): title-group expansion
    # drags in same-maker/same-year siblings, but when exactly the candidates
    # NAMED as the note states remain distinguishable, prefer them. A true
    # same-name pair (two exact "Mata Hari"s) both match and stay ambiguous.
    if len(candidates) > 1:
        stated_key = normalize_key(strip_parenthetical(claim.target_title))
        exact = tuple(
            c
            for c in candidates
            if normalize_key(strip_parenthetical(c.name)) == stated_key
        )
        if exact and len(exact) < len(candidates):
            trail.append(f"exact name match → {len(exact)}")
            candidates = exact

    if len(candidates) > 1:
        candidates = _technology_tiebreak(candidates, subject, trail)

    if len(candidates) > 1:
        return Resolution("ambiguous", None, candidates, "; ".join(trail))

    chosen = candidates[0]
    problems = _fact_problems(claim, chosen, brands, catalog)
    if problems:
        trail.extend(problems)
        return Resolution("mismatch", None, candidates, "; ".join(trail))
    return Resolution("unique", chosen, candidates, "; ".join(trail))


def _edge_for(slug: Slug, edges: tuple[CatalogEdge, ...]) -> CatalogEdge | None:
    """The catalog edge whose machine target is ``slug`` (or None)."""
    return next((e for e in edges if e.target_slug == slug), None)


def _label_edge(edges: tuple[CatalogEdge, ...]) -> CatalogEdge | None:
    """The model's single text-target edge, if any (a model holds at most one)."""
    return next((e for e in edges if e.target_slug is None), None)


def _label_key(label: str) -> str:
    """A label's comparison key: normalized, with any leading article dropped.

    DEFECT 12. A label is prose, and prose the sweep re-derives will never match
    an authored wording character-for-character; a leading "a"/"an"/"the" is
    the difference between a phrase and the same phrase, not between two claims.
    Only the LEADING article goes — an article inside the phrase ("parts for a
    Gottlieb donor") is ordinary wording, and stripping every one of them would
    start blunting real differences. It must come off the RAW text: normalize_key
    removes every non-alphanumeric char, so by then "an electromechanical" has
    folded to "anelectromechanical" with no word boundary left to match on.
    (normalize_key already drops a leading "the"; "a"/"an" is the actual gap.)
    """
    return normalize_key(re.sub(r"^\s*(?:an?|the)\s+", "", label, flags=re.IGNORECASE))


def _same_label(claim: JudgeClaim, edge: CatalogEdge) -> bool:
    """Do a label edge and a label claim say the same thing, modulo formatting?

    Compared on ``_label_key`` (case / punctuation / whitespace collapsed, and
    a leading article dropped), so "Many late-1970s solid-state Gottliebs." and
    "many late 1970s solid state Gottliebs" are one wording, not two. What
    survives that is a real word-level difference — a rewording a human should
    rule on, or a contradiction.
    """
    return _label_key(edge.target_label) == _label_key(claim.target_label)


def _axis_diff(claim: JudgeClaim, edge: CatalogEdge) -> str:
    """Which axis of an existing edge disagrees with the claim — for the reason."""
    bits = []
    if edge.rel_type != claim.relationship_type:
        bits.append(f"relationship_type ({edge.rel_type} vs {claim.relationship_type})")
    if edge.license != claim.license_status:
        bits.append(f"license_status ({edge.license} vs {claim.license_status})")
    # The label's wording is not part of edge identity, but it IS payload a
    # patch rewords in place — so a differing label is a real disagreement, not
    # a matter of taste. Only for label edges; a machine edge has no wording.
    if edge.target_slug is None and not _same_label(claim, edge):
        bits.append(
            f"target_label wording ({edge.target_label!r} vs {claim.target_label!r})"
        )
    return " and ".join(bits) if bits else "no field"


def _hint_note(resolved: Slug, hints: frozenset[Slug]) -> list[str]:
    """A note when the resolution disagrees with every prior guess."""
    if hints and resolved not in hints:
        listed = ", ".join(f"`{h}`" for h in sorted(hints))
        return [f"prior guess(es) {listed} disagree with this sweep's `{resolved}`"]
    return []


def dispose_claim(
    *,
    claim: JudgeClaim,
    resolution: Resolution | None,
    catalog_edges: tuple[CatalogEdge, ...],
    quote_verified: bool,
    hints: frozenset[Slug],
    subject: ModelFacts,
) -> tuple[str, list[str], CatalogEdge | None]:
    """Disposition for one judged relationship claim vs the catalog edge set.

    Returns ``(disposition, reasons, matched_edge)``. ``matched_edge`` is the
    catalog edge this claim addresses (AGREES or CONFLICT to that target),
    so the pipeline can tell which existing edges the note accounts for and
    surface the rest as SET_BUT_UNSUPPORTED. Pure and total over the
    post-judgment states.
    """
    if claim.hedged:
        return UNCERTAIN, [claim.reason or "note is hedged/tentative"], None
    if not quote_verified:
        msg = "grounding quote is not verbatim in any evidence source"
        return QUOTE_FAIL, [msg], None

    # Scoped to an asset, not the machine (DEFECT 7) — this is not a lineage
    # claim in ANY disposition, so it is checked before the hint and the catalog
    # are consulted. Gating it at the fill step alone was too late: the `jaws`
    # specimen reached HINT_MISMATCH first (its stale hint was a *differently*
    # wrong target) and sailed past. Worse, an already-seeded artwork edge would
    # have been confirmed as AGREES by a note that never claimed it.
    asset = asset_scoped_quote(claim.quote)
    if asset:
        return (
            ASSET_SCOPED,
            [
                f"the quote claims the {asset} was copied, not that this machine "
                "reproduces the target's design — shared art, cabinets and sound "
                "hardware are not a lineage relationship"
            ],
            None,
        )

    # ── Text-label target: never resolved to a slug; matched against the
    # model's single label edge on type + license + the label's own wording.
    # Agreeing without examining the target would make "same target" a claim the
    # gate never checked — and would suppress the edge from surfacing as
    # set-but-unsupported, hiding a contradiction twice.
    if claim.is_label:
        # Some types admit no label target at all (a re-theme's donor is always
        # a specific seeded machine). Such an edge is rejected by the patch
        # planner and a DB CHECK, so greening it would hand the author a patch
        # that cannot ingest — the note likely names the donor, or the type is
        # wrong. Either way it is a human call.
        if requires_machine_target(claim.relationship_type):
            return (
                LABEL_TARGET_INVALID,
                [
                    f"the note supports {claim.relationship_type} → "
                    f"“{claim.target_label}”, but a {claim.relationship_type} "
                    "edge must name a seeded machine — a text label is rejected "
                    "by the planner and the DB. Identify the donor the note "
                    "means, or reconsider the relationship type"
                ],
                None,
            )
        edge = _label_edge(catalog_edges)
        if edge is None:
            return FILL, [], None
        if (
            edge.rel_type == claim.relationship_type
            and edge.license == claim.license_status
            and _same_label(claim, edge)
        ):
            return (
                AGREES,
                [f"note consistent with existing label edge {edge.describe()}"],
                edge,
            )
        return (
            CONFLICT,
            [
                f"catalog holds label edge {edge.describe()} but the note supports "
                f"{claim.relationship_type}/{claim.license_status} → “{claim.target_label}”"
                f" — {_axis_diff(claim, edge)} differs"
            ],
            edge,
        )

    # ── Machine target: resolve, then diff against any edge to that slug.
    if resolution is None or resolution.status == "none":
        return (
            UNRESOLVED,
            [
                f"stated target {claim.target_title!r} matches no catalog model "
                "(possible catalog gap, or a name the index cannot reach)"
            ],
            None,
        )
    if resolution.status == "mismatch":
        return FACTS_MISMATCH, [resolution.how], None
    if resolution.status == "ambiguous":
        # An ambiguous set that CONTAINS a matching catalog edge is consistency,
        # not doubt: every survivor fits the note's stated facts. The edge must
        # match on BOTH axes, exactly as the unique-target path below — a note
        # supporting copy/unlicensed does not confirm a copy/licensed edge.
        for cand in resolution.considered:
            edge = _edge_for(cand.slug, catalog_edges)
            if (
                edge
                and edge.rel_type == claim.relationship_type
                and edge.license == claim.license_status
            ):
                return (
                    AGREES,
                    [
                        f"note consistent with existing {edge.describe()} (resolution "
                        f"ambiguous among {len(resolution.considered)}: {resolution.how})"
                    ],
                    edge,
                )
        return AMBIGUOUS, [resolution.how], None

    resolved = resolution.chosen
    if resolved is None:  # unreachable given status == "unique"; keeps types honest
        return AMBIGUOUS, [resolution.how], None

    # A copy reproduces ANOTHER maker's design. A same-maker copy target is a
    # chain link — the maker's own variant the note mentions on the way to the
    # real original (the Big Ben (Italy) shape, TOOL-NOTES DEFECT 3).
    if (
        requires_other_maker(claim.relationship_type)
        and subject.maker_slug is not None
        and resolved.maker_slug == subject.maker_slug
    ):
        return (
            SAME_MAKER,
            [
                f"the note names `{resolved.slug}` — but a {claim.relationship_type} "
                f"target by the model's own maker (`{subject.maker_slug}`) is not "
                "valid; the note likely describes the maker's own variant, and the "
                "true target is the other maker's original the copy traces back to"
            ],
            None,
        )

    edge = _edge_for(resolved.slug, catalog_edges)
    if edge is not None:
        if (
            edge.rel_type == claim.relationship_type
            and edge.license == claim.license_status
        ):
            return AGREES, _hint_note(resolved.slug, hints), edge
        return (
            CONFLICT,
            [
                f"catalog holds {edge.describe()} but the note supports "
                f"{claim.relationship_type}/{claim.license_status} → `{resolved.slug}`"
                f" — {_axis_diff(claim, edge)} differs"
            ],
            edge,
        )

    # No catalog edge to this target — a new relationship.
    if hints and resolved.slug not in hints:
        listed = ", ".join(f"`{h}`" for h in sorted(hints))
        return (
            HINT_MISMATCH,
            [
                f"prior guess(es) {listed} vs this sweep's `{resolved.slug}` — "
                "two sessions disagree; decide from the quote and full note"
            ],
            None,
        )
    return FILL, [], None
