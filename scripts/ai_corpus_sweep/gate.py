"""Layer 3 — deterministic gates: the script decides trust, not the model.

Two pure steps after the model's verdict:

- :func:`resolve_target` — the stated target name → catalog model(s), via
  ``EntityIndex.resolve`` (models + titles, titles expanded to their member
  models, the judged model itself excluded so a same-name copy can never
  resolve to itself), then narrowed deterministically by the year and maker
  the note stated. No model call: "1978" selecting the solid-state Mata Hari
  is a filter, not an opinion.
- :func:`dispose` — verdict × quote-verbatim × resolution × catalog diff ×
  hint diff → one disposition. Confidence is not a number the model reports;
  it is a verified quote plus a unique resolution plus catalog agreement.

Dispositions split green (never needs a human) from review (routed to the
coordinating session / the human table).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from common.catalog.entity_index import normalize_key

from ai_corpus_sweep.catalog import strip_parenthetical

if TYPE_CHECKING:
    from collections.abc import Callable

    from common.catalog.entity_index import EntityIndex
    from common.catalog.types import Slug

    from ai_corpus_sweep.catalog import ModelFacts, SweepCatalog
    from ai_corpus_sweep.fields import FieldSpec
    from ai_corpus_sweep.judge import JudgeAnswer

# ── Dispositions ─────────────────────────────────────────────────────────────
# Green — auto-audited, never surfaces by default:
AGREES = "agrees"  # catalog already holds the resolved value
FILL = "fill"  # catalog empty; quote verified; unique resolution
NO_CLAIM = "no-claim"  # net false positive: note supports nothing, catalog empty
# Review — the short queue a human actually reads:
CONFLICT = "conflict"  # catalog holds a DIFFERENT value than the note supports
SET_BUT_UNSUPPORTED = "set-but-unsupported"  # catalog set; note supports no claim
FACTS_MISMATCH = "facts-mismatch"  # sole resolution contradicts the note's stated facts
SAME_MAKER = "same-maker-target"  # licensed/bootleg target by the subject's own maker
QUOTE_UNSUPPORTED = "quote-unsupported"  # verbatim quote fails to establish the claim
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
        QUOTE_UNSUPPORTED,
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


def _maker_compatible(stated: str, candidate: ModelFacts) -> bool:
    """Is the note's stated maker consistent with the candidate's makers?

    Deliberately lenient — substring containment either way over both the
    Manufacturer (brand) and the corporate entity: notes say "Premier" for a
    Gottlieb-brand game built by Premier Technology, "Williams" for Williams
    Electronics Incorporated. A real contradiction (Bally vs Chicago Coin)
    shares no substring and still fails.
    """
    key = normalize_key(stated)
    if not key:
        return True  # nothing stated → nothing to contradict
    candidate_keys = [
        normalize_key(value)
        for value in (
            candidate.maker_slug,
            candidate.maker_name,
            candidate.ce_slug,
            candidate.ce_name,
        )
        if value
    ]
    return any(key in ck or ck in key for ck in candidate_keys if ck)


def _year_compatible(stated: int | None, candidate: ModelFacts) -> bool:
    """±1 year is data noise; an unknown candidate year can never contradict."""
    return stated is None or candidate.year is None or abs(candidate.year - stated) <= 1


def _fact_problems(answer: JudgeAnswer, chosen: ModelFacts) -> list[str]:
    """How the note's stated facts contradict the chosen candidate (if at all)."""
    problems = []
    if answer.target_maker and not _maker_compatible(answer.target_maker, chosen):
        problems.append(
            f"note says the target is by {answer.target_maker!r} but the only "
            f"catalog match is {chosen.describe()}"
        )
    if not _year_compatible(answer.target_year, chosen):
        problems.append(
            f"note says the target is from {answer.target_year} but the only "
            f"catalog match is {chosen.describe()}"
        )
    return problems


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


def resolve_target(
    answer: JudgeAnswer,
    *,
    index: EntityIndex,
    catalog: SweepCatalog,
    exclude_model_id: int,
) -> Resolution:
    """Resolve the note's stated target to catalog model(s); narrow by facts.

    Candidates are gathered from the name/alias/title index AND from the
    base-name map (both the stated title and the catalog names with any
    trailing "(...)" disambiguator stripped) — the campaign's "(Maker)" naming
    convention must not hide a target from its own note (TOOL-NOTES DEFECT 1).

    Filters are applied only while they keep at least one candidate: a stated
    year that matches nothing is recorded in ``how`` but never wipes the set —
    an over-eager filter would silently manufacture UNRESOLVED escalations. A
    candidate with an unknown year survives the year filter (it cannot be
    excluded by a fact it doesn't carry). And a unique survivor is only
    trusted if the note's stated facts don't contradict it (DEFECT 2 — the
    "Major League"/"Champion" false greens).
    """
    by_slug: dict[Slug, ModelFacts] = {}

    def collect(facts: ModelFacts | None) -> None:
        if facts is not None and facts.model_id != exclude_model_id:
            by_slug.setdefault(facts.slug, facts)

    names = {answer.target_title, strip_parenthetical(answer.target_title)}
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
        f"{len(candidates)} catalog match(es) for {answer.target_title!r}"
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
    if answer.target_maker:
        narrow(
            f"maker {answer.target_maker!r}",
            lambda c: _maker_compatible(answer.target_maker, c),
        )
    if answer.target_year and len(candidates) > 1:
        exact = tuple(c for c in candidates if c.year == answer.target_year)
        if exact:
            trail.append(f"year {answer.target_year} → {len(exact)}")
            candidates = exact
        else:
            narrow(
                f"year {answer.target_year}",
                lambda c: _year_compatible(answer.target_year, c),
            )

    # Exact-name tie-break (the King-of-Diamonds shape): title-group expansion
    # drags in same-maker/same-year siblings, but when exactly the candidates
    # NAMED as the note states remain distinguishable, prefer them. A true
    # same-name pair (two exact "Mata Hari"s) both match and stay ambiguous.
    if len(candidates) > 1:
        stated_key = normalize_key(strip_parenthetical(answer.target_title))
        exact = tuple(
            c
            for c in candidates
            if normalize_key(strip_parenthetical(c.name)) == stated_key
        )
        if exact and len(exact) < len(candidates):
            trail.append(f"exact name match → {len(exact)}")
            candidates = exact

    if len(candidates) > 1:
        return Resolution("ambiguous", None, candidates, "; ".join(trail))

    chosen = candidates[0]
    problems = _fact_problems(answer, chosen)
    if problems:
        trail.extend(problems)
        return Resolution("mismatch", None, candidates, "; ".join(trail))
    return Resolution("unique", chosen, candidates, "; ".join(trail))


def dispose(
    *,
    answer: JudgeAnswer,
    resolution: Resolution | None,
    catalog_now: Slug | None,
    quote_verified: bool,
    hint: Slug | None,
    subject: ModelFacts,
    spec: FieldSpec,
) -> tuple[str, list[str]]:
    """The disposition for one judged row, plus human-readable reasons.

    Pure and total over the post-judgment states; the pre-judgment ones
    (NO_MODEL / NO_EVIDENCE / AI_ERROR) are assigned by the pipeline before a
    verdict exists.
    """
    reasons: list[str] = []
    if answer.verdict == "uncertain":
        return UNCERTAIN, [answer.reason or "model could not decide from the note"]

    if answer.verdict == "no":
        if catalog_now is not None:
            reasons.append(
                f"catalog holds `{catalog_now}` but the note supports no claim"
            )
            if answer.reason:
                reasons.append(answer.reason)
            return SET_BUT_UNSUPPORTED, reasons
        return NO_CLAIM, [answer.reason] if answer.reason else []

    # verdict == "yes"
    if not quote_verified:
        return QUOTE_FAIL, ["grounding quote is not verbatim in any evidence source"]
    if resolution is None or resolution.status == "none":
        return UNRESOLVED, [
            f"stated target {answer.target_title!r} matches no catalog model "
            "(possible catalog gap, or a name the index cannot reach)"
        ]
    if resolution.status == "mismatch":
        return FACTS_MISMATCH, [resolution.how]
    if resolution.status == "ambiguous":
        # An ambiguous set that CONTAINS the catalog's current value is
        # consistency, not doubt: every survivor already fits the note's
        # stated facts, so the note cannot be contradicting the catalog.
        if catalog_now and any(c.slug == catalog_now for c in resolution.considered):
            return AGREES, [
                f"note consistent with existing `{catalog_now}` (resolution "
                f"ambiguous among {len(resolution.considered)}: {resolution.how})"
            ]
        return AMBIGUOUS, [resolution.how]

    resolved = resolution.chosen
    if resolved is None:  # unreachable given status == "unique"; keeps types honest
        return AMBIGUOUS, [resolution.how]

    # A machine cannot be a licensed build or bootleg of its own maker's game.
    # A same-maker "target" is a chain link — the maker's own variant the note
    # mentions on the way to the other maker's original (the Big Ben (Italy)
    # shape, TOOL-NOTES DEFECT 3) — never grounds to accuse the catalog or fill.
    if (
        spec.target_other_maker
        and subject.maker_slug is not None
        and resolved.maker_slug == subject.maker_slug
    ):
        return SAME_MAKER, [
            f"the note names `{resolved.slug}` — but a {spec.key} target by the "
            f"model's own maker (`{subject.maker_slug}`) is not valid; the note "
            "likely describes the maker's own variant, and the true target is "
            "the other maker's original the license/copy traces back to"
        ]

    if catalog_now is not None:
        if catalog_now == resolved.slug:
            if hint and hint != resolved.slug:
                reasons.append(
                    f"prior guess `{hint}` disagrees — catalog and this sweep "
                    f"both say `{resolved.slug}`; the prior guess looks wrong"
                )
            return AGREES, reasons
        return CONFLICT, [
            f"catalog holds `{catalog_now}` but the note supports `{resolved.slug}`"
        ]

    if hint and hint != resolved.slug:
        return HINT_MISMATCH, [
            f"prior guess `{hint}` vs this sweep's `{resolved.slug}` — "
            "two sessions disagree; decide from the quote and full note"
        ]
    return FILL, reasons
