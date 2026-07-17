"""The model-info field catalog — the concrete slices and how they assemble.

``build_slices`` produces the full **model-info** field set (the machine's own
fields — not entity discovery, not related entities like the maker's location).
Each grounded slice's prompt composes two layers: the *derived data* (the field's
legal values and their real meanings, introspected live from the flipcommons
catalog by ``ai_page_extract.catalog``) and the *hand-crafted recognition
guidance* (the "tells" that help the model spot a value in messy prose). A
hardcoded fallback grounds technology_generation when the DB is absent.

The reusable machinery (the ``Slice`` type, the archetype builders, the model-
output readers) lives in ``ai_page_extract.framework``; this module is the part
that grows as fields are added or their prompts tuned.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai_page_extract.catalog import VocabTerm
from ai_page_extract.framework import (
    ExtractedItem,
    Slice,
    coerce_int,
    dependency_pair_slice,
    is_absent_token,
    multi_select_slice,
    read_int,
    read_objects,
    read_str,
    scalar_slice,
    single_value_slice,
)

if TYPE_CHECKING:
    from common.ai.client import AiModelResult
    from common.types import JsonSchema

    from ai_page_extract.catalog import CatalogDb


# ── technology_generation: hand-crafted tells + hardcoded fallback vocab ─────
# Layer 2 (hand-crafted tells) for the grounded fields — the DB never holds this.
TECH_GEN_GUIDANCE = (
    "Infer it from the machine's mechanisms and display — the page need not state "
    "the generation outright. Lean on the tells, not the date:\n"
    "- A screen or electronic display of any kind is a near-certain giveaway of "
    "solid-state.\n"
    "- Relays, solenoids, score reels or chimes with no CPU point to "
    "electromechanical.\n"
    "- Any electric lighting — bulbs, lamps, an illuminated backglass — or "
    "electrical wiring means the machine uses electricity, which rules out "
    "pure-mechanical (which has NO electricity at all) and points to at least "
    "electromechanical.\n"
    "- Do NOT infer solid-state from a recent date — electromechanical machines "
    "are still built today, so a late date rules nothing out."
)

GAME_FORMAT_GUIDANCE = (
    "Decide it explicitly — a non-pinball machine silently treated as pinball is "
    "a classic error. Tells:\n"
    "- Flippers, a plunger, bumpers and a tilted playfield point to pinball.\n"
    "- A pitch-and-bat baseball cabinet, a gun/target game, a bowling-style "
    "shuffle alley, or a coin-dispensing slot/reel machine each has its own "
    "format — do not fold them into pinball."
)

# Fallback vocab for when the flipcommons DB is unavailable (offline tests, or a
# checkout without the sibling). The live catalog is the real source (see
# ai_page_extract.catalog); these short definitions only stand in for it.
_TECH_GEN_FALLBACK_TERMS: tuple[VocabTerm, ...] = (
    VocabTerm(
        "pure-mechanical",
        "Pure Mechanical",
        "No electricity at all: gravity, springs, purely mechanical scoring.",
    ),
    VocabTerm(
        "electromechanical",
        "Electromechanical",
        "Relays, solenoids, stepping units, score motors, mechanical score reels, "
        "chimes or bells, backglass bulbs — and no CPU.",
    ),
    VocabTerm(
        "solid-state",
        "Solid State",
        "Microprocessor-controlled: an electronic or video display of any kind, or "
        "a CPU, circuit boards, ROMs, software, or a named electronic system.",
    ),
)

TECHNOLOGY_GENERATION = single_value_slice(
    key="technology_generation",
    task="determine this machine's technology generation",
    terms=_TECH_GEN_FALLBACK_TERMS,
    guidance=TECH_GEN_GUIDANCE,
    max_tokens=256,
)


# ── Enumerative collection — gameplay_feature ────────────────────────────────
GAMEPLAY_FEATURE_SCHEMA: JsonSchema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "count": {"type": ["integer", "null"]},
                    "quote": {"type": "string"},
                },
                "required": ["name", "count", "quote"],
            },
        }
    },
    # Wrapper key optional: a model that finds nothing may return `{}`; that is a
    # benign empty (checked-absent), not a malformed result that loses the slice.
    "required": [],
}

_GAMEPLAY_FEATURE_INSTRUCTIONS = (
    "ONE narrow extraction task from the source page below.\n"
    "Task: list every gameplay feature this machine has — the physical play "
    "mechanisms, such as multiball, ramps, drop targets, spinners, flippers, "
    "bumpers, and the like.\n"
    "Rules — this is a RECALL task:\n"
    "- Read the ENTIRE page, including prose and notes — not just any tidy "
    "feature list.\n"
    "- Do NOT restrict yourself to any predefined set; extract whatever the page "
    "describes, in its own words.\n"
    "- Over-include: surface anything that plausibly qualifies as a play "
    "mechanism. A false include is fine; a miss is not.\n"
    "- Count the playfield STRUCTURE as a feature, not only the mechanisms on "
    "it: an 'upper', 'second', 'lower', or 'split-level' playfield signals a "
    "multi-level playfield — surface that as its own feature.\n"
    "- Do not fragment ONE feature into locational sub-counts: flippers 'on the "
    "main playfield', 'on the upper playfield', and 'in the outlanes' are still "
    "just flippers — one feature, not three.\n"
    "- For each: a short name, a count if the page gives one (else null), and the "
    "verbatim quote it comes from."
)


def _parse_gameplay_feature(result: AiModelResult) -> list[ExtractedItem]:
    items: list[ExtractedItem] = []
    for row in read_objects(result, "items"):
        name = read_str(row, "name").strip()
        if not name:
            continue
        items.append(
            ExtractedItem(
                value=name,
                quote=read_str(row, "quote"),
                extra={"count": read_int(row, "count")},
            )
        )
    return items


GAMEPLAY_FEATURE = Slice(
    key="gameplay_feature",
    instructions=_GAMEPLAY_FEATURE_INSTRUCTIONS,
    schema=GAMEPLAY_FEATURE_SCHEMA,
    parser=_parse_gameplay_feature,
    samples=3,
    max_tokens=2048,
    aggregate="union",
)


# ── Judgment / candidate — lineage ───────────────────────────────────────────
_LINEAGE_KINDS = ["copy", "remake", "conversion", "variant"]

LINEAGE_SCHEMA: JsonSchema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "signals": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "relation": {"type": "string", "enum": _LINEAGE_KINDS},
                    "related": {"type": "string"},
                    "quote": {"type": "string"},
                },
                "required": ["relation", "related", "quote"],
            },
        }
    },
    # Wrapper key optional — a benign empty (`{}`) is checked-absent, not a lost slice.
    "required": [],
}

_LINEAGE_INSTRUCTIONS = (
    "ONE narrow task from the source page below.\n"
    "Task: surface every candidate lineage relationship for this machine. The "
    "kinds:\n"
    "- copy — a reproduction of another maker's design on newly built hardware "
    "(a copy, clone, or bootleg; licensed or not — the license is judged "
    "downstream).\n"
    "- remake — a newly manufactured recreation of an earlier title with new "
    "technology.\n"
    "- conversion — reuses another machine's physical cabinet but puts a "
    "DIFFERENT playfield in it (a new game inside an old cabinet).\n"
    "- variant — same gameplay and playfield, only the DRESS differs (art, "
    "plastics, toppers). If ONLY the artwork or theme changes and the playfield "
    "and gameplay are unchanged, it is a variant, NOT a conversion.\n"
    "Rules — RECALL / PROPOSE-ONLY:\n"
    "- Surface ANY candidate the page hints at, even weakly or indirectly, with "
    "the verbatim quote.\n"
    "- A page merely COMPARING this machine to another — a similar-looking "
    'playfield, "echoes", "reminiscent of", "appears nearly identical to" — is '
    "not a lineage relationship unless the page says this machine was DERIVED "
    "from the other (a copy, a re-theme, a reused cabinet, a remake). Comparison "
    "alone is not derivation.\n"
    '- Do NOT conclude "none" merely because the page does not state it '
    "outright — if there is suggestive language (a reused cabinet, an earlier "
    "game it is based on, a copy), flag it. The accept/reject judgment is made "
    "downstream, not by you. A false flag is cheap; a miss is unacceptable.\n"
    "- Watch the polarity trap: a statement about a DIFFERENT machine (its "
    "companion, sequel or donor) is not a claim about THIS one — flag it as "
    '"unnamed" only if it genuinely bears on this machine.\n'
    "- For each: which kind, the related machine if the page names it (else "
    '"unnamed"), and the verbatim quote.\n'
    "- If nothing on the page is suggestive, return an empty list."
)


def _parse_lineage(result: AiModelResult) -> list[ExtractedItem]:
    items: list[ExtractedItem] = []
    for row in read_objects(result, "signals"):
        relation = read_str(row, "relation").strip()
        if not relation:
            continue
        related = read_str(row, "related").strip() or "unnamed"
        items.append(
            ExtractedItem(
                value=relation,
                quote=read_str(row, "quote"),
                extra={"related": related},
            )
        )
    return items


LINEAGE = Slice(
    key="lineage",
    instructions=_LINEAGE_INSTRUCTIONS,
    schema=LINEAGE_SCHEMA,
    parser=_parse_lineage,
    samples=1,
    max_tokens=1024,
    aggregate="single-read",
)


# ── Scalar — year (+month), player/flipper count ─────────────────────────────
_YEAR_SCHEMA: JsonSchema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        # String tolerated so a stringified year or a "<null>" sentinel validates
        # (coerced / dropped in the parser) rather than erroring into a false gap.
        "year": {"type": ["integer", "string", "null"]},
        "month": {"type": ["integer", "string", "null"]},
        "quote": {"type": "string"},
    },
    "required": ["year"],
}


def _parse_year(result: AiModelResult) -> list[ExtractedItem]:
    year = coerce_int(result.get("year"))
    if year is None:
        return []
    return [
        ExtractedItem(
            value=str(year),
            quote=read_str(result, "quote"),
            extra={"month": coerce_int(result.get("month"))},
        )
    ]


YEAR = Slice(
    key="year",
    instructions=(
        "ONE narrow task from the source page below.\n"
        "Task: determine the machine's MANUFACTURE year (and month, if the page "
        "states one). Give the number(s) and a verbatim quote; null if the page "
        "states no year.\n"
        "Give the manufacture date, NOT a trade-show, reveal, announcement, or "
        "flyer date — those are not the year. If two sources give different dates, "
        "prefer the one describing manufacture."
    ),
    schema=_YEAR_SCHEMA,
    parser=_parse_year,
    samples=1,
    max_tokens=200,
    aggregate="single-read",
)

PLAYER_COUNT = scalar_slice(
    key="player_count",
    task="determine the maximum number of players the machine supports",
)
FLIPPER_COUNT = scalar_slice(
    key="flipper_count",
    task="determine how many flippers the machine has",
)


# ── Free-extract enumerative without a count — themes ────────────────────────
def _free_enum_schema() -> JsonSchema:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "quote": {"type": "string"},
                    },
                    "required": ["name", "quote"],
                },
            }
        },
        # Wrapper key optional — a benign empty (`{}`) is checked-absent, not a lost slice.
        "required": [],
    }


def _parse_free_enum(result: AiModelResult) -> list[ExtractedItem]:
    items: list[ExtractedItem] = []
    for row in read_objects(result, "items"):
        name = read_str(row, "name").strip()
        if name:
            items.append(ExtractedItem(value=name, quote=read_str(row, "quote")))
    return items


THEMES = Slice(
    key="themes",
    instructions=(
        "ONE narrow extraction task from the source page below.\n"
        "Task: list every theme this machine evokes — its subjects and settings "
        "(a sport, a place, an era, a character, a mood, a licensed property).\n"
        "Rules — this is a RECALL task:\n"
        "- Read the ENTIRE page, including prose and notes.\n"
        "- Do NOT restrict yourself to a predefined set; extract themes in the "
        "page's own words (they are mapped to the catalog's theme vocabulary "
        "later).\n"
        "- Over-include: a false include is cheap, a miss is not.\n"
        "- For each: a short theme name and the verbatim quote it comes from."
    ),
    schema=_free_enum_schema(),
    parser=_parse_free_enum,
    samples=3,
    max_tokens=1024,
    aggregate="union",
)


# ── Free single value — franchise ────────────────────────────────────────────
_FRANCHISE_SCHEMA: JsonSchema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "value": {"type": ["string", "null"]},
        "quote": {"type": "string"},
    },
    # Quote optional — a missing quote degrades, never errors into a false gap.
    "required": ["value"],
}


def _parse_franchise(result: AiModelResult) -> list[ExtractedItem]:
    value = result.get("value")
    if not isinstance(value, str) or is_absent_token(value):
        return []
    return [ExtractedItem(value=value.strip(), quote=read_str(result, "quote"))]


FRANCHISE = Slice(
    key="franchise",
    instructions=(
        "ONE narrow task from the source page below.\n"
        "Task: name the franchise, licensed property, or media brand this machine "
        "is based on (a film, TV show, band, video game, comic, etc.), if any. "
        "Give the name and a verbatim quote; null if it is based on no external "
        "property.\n"
        "Do NOT invent a franchise from a generic theme — 'medieval' or 'space' "
        "is a theme, not a franchise; 'Star Trek' or 'The Addams Family' is a "
        "franchise."
    ),
    schema=_FRANCHISE_SCHEMA,
    parser=_parse_franchise,
    samples=1,
    max_tokens=200,
    aggregate="single-read",
)


# ── Credits (person + role) ──────────────────────────────────────────────────
# A recognition task, not a field lookup. Free-extract person+role; resolving the
# person against the catalog is the (deferred) entity-discovery step.
_CREDITS_SCHEMA: JsonSchema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "person": {"type": "string"},
                    "role": {"type": "string"},
                    "quote": {"type": "string"},
                },
                "required": ["person", "role", "quote"],
            },
        }
    },
    # Wrapper key optional — a benign empty (`{}`) is checked-absent, not a lost slice.
    "required": [],
}


def _parse_credits(result: AiModelResult) -> list[ExtractedItem]:
    items: list[ExtractedItem] = []
    for row in read_objects(result, "items"):
        person = read_str(row, "person").strip()
        if not person:
            continue
        items.append(
            ExtractedItem(
                value=person,
                quote=read_str(row, "quote"),
                extra={"role": read_str(row, "role").strip() or "unspecified"},
            )
        )
    return items


CREDITS = Slice(
    key="credits",
    instructions=(
        "ONE narrow extraction task from the source page below.\n"
        "Task: list every person credited for work on this machine, each WITH the "
        "reason they are named (their role).\n"
        "Rules — this is a RECALL task:\n"
        "- Surface every named person and why — a bare name without a role is "
        "nearly useless.\n"
        "- Over-include: a false include is cheap, a missed designer is not.\n"
        "- Standard roles to map the reason to: Design, Concept, Art, "
        "Dots/Animation, Mechanics, Music, Sound, Voice, Software, Other. One "
        "person may hold several — each is a distinct credit.\n"
        "- A credit is for CREATING or PRODUCING this machine (design, art, "
        "music, software, mechanics, and the like). A person named only as a "
        "researcher, collector, photographer, preservationist, historian, the "
        "page's author, or a company owner or representative — named in a "
        "corporate or historical capacity, not as a maker of THIS game — is NOT "
        "a credit; leave them out (they belong to entity discovery, not "
        "credits).\n"
        "- For each: the person's name, the role/reason, and the verbatim quote."
    ),
    schema=_CREDITS_SCHEMA,
    parser=_parse_credits,
    samples=2,
    max_tokens=1024,
    aggregate="union",
)


# ── Open-ended catch-all — the between-slices safety net ─────────────────────
_CATCH_ALL_SCHEMA: JsonSchema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "fact": {"type": "string"},
                    "quote": {"type": "string"},
                },
                "required": ["fact", "quote"],
            },
        }
    },
    # Wrapper key optional — a benign empty (`{}`) is checked-absent, not a lost slice.
    "required": [],
}


def _parse_catch_all(result: AiModelResult) -> list[ExtractedItem]:
    items: list[ExtractedItem] = []
    for row in read_objects(result, "items"):
        fact = read_str(row, "fact").strip()
        if fact:
            items.append(
                ExtractedItem(value=fact, quote=read_str(row, "quote"), field="other")
            )
    return items


CATCH_ALL = Slice(
    key="other",
    instructions=(
        "ONE narrow extraction task from the source page below.\n"
        "Task: surface any catalog-relevant fact about THIS machine that a "
        "field-by-field pass might miss — anything about the machine itself that "
        "is not obviously a year, maker, theme, gameplay feature, display, "
        "cabinet, credit, reward, tag, or lineage relationship. Construction and "
        "materials, dimensions and weight, price, distribution and availability, "
        "connectivity and software, production quirks, and notable anecdotes about "
        "THIS machine all count — these between-field facts are exactly what this "
        "pass exists to surface, so include them even when the rest of the fields "
        "are already answered.\n"
        "Rules — this is a RECALL / catch-all task:\n"
        "- Over-include; the reviewer prunes. A miss is the failure this pass "
        "exists to catch.\n"
        "- Ignore facts about OTHER machines, the website, or navigation.\n"
        "- For each: a short statement of the fact and the verbatim quote."
    ),
    schema=_CATCH_ALL_SCHEMA,
    parser=_parse_catch_all,
    samples=1,
    max_tokens=1024,
    aggregate="union",
    fields=("other",),
)


# ── Hand-crafted tells (layer 2) for the remaining grounded fields ───────────
PRODUCTION_STATUS_GUIDANCE = (
    "Tells: commercially sold, even in tiny quantity → produced; announced but "
    "not yet shipped → announced; intended for production but cancelled → "
    "unreleased; a one/few-of-a-kind never meant for sale (gift, prop, test) → "
    "one-off; modified by someone other than the maker → aftermarket. A machine "
    "that clearly reached the market is produced."
)

CABINET_GUIDANCE = (
    "Decide by how the machine is SUPPORTED, not by its size or scale:\n"
    "- Stands on its own legs on the floor → floor. A reduced-scale, home, or "
    "'compact' machine that still stands on its own legs is floor, NOT tabletop — "
    "legs, leveling feet, or a stated standing/playing height are floor tells.\n"
    "- Built to sit on a table, bar, or counter → tabletop or countertop.\n"
    "- A horizontal flat-glass-top cabinet players sit around → cocktail."
)

REWARD_GUIDANCE = (
    "Tells: 'free game' / 'replay' / 'match' / 'special' → replay; 'extra ball' → "
    "add-a-ball (an extra ball, NOT a free game); 'for amusement only' or no "
    "reward described → novelty; coins paid out by scoring → cash-payout; "
    "redeemable tickets → ticket-payout; no coin needed to start → free-play."
)

TAG_GUIDANCE = (
    "These are independent yes/no labels — decide each on the page's evidence. "
    "Tells: a wider-than-standard body/playfield → widebody; built by its maker "
    "for a market outside the US → export (a US-made game merely imported, sold, "
    "or renamed abroad is NOT export); an engineering or pre-production sample → "
    "prototype; designed for home rather than coin-op routes → home-use; an "
    "official re-theme a manufacturer applied to ITS OWN earlier design → "
    "manufacturer-retheme (a re-theme involving a DIFFERENT maker, or a licensing "
    "or derivative relationship, is NOT manufacturer-retheme — that is a lineage "
    "relationship); a non-maker re-skin → unofficial-retheme."
)

TECH_PAIR_GUIDANCE = (
    TECH_GEN_GUIDANCE + "\n"
    "For the subgeneration (only if solid-state): early off-the-shelf CPU boards "
    "(late 1970s–1980s) → ss-discrete; purpose-built platforms like WPC → "
    "ss-integrated; commodity PC/ARM hardware (2010s onward) → ss-pc. Non-"
    "solid-state machines have no subgeneration (n-a)."
)

DISPLAY_PAIR_GUIDANCE = (
    "Tells for the display type: mechanical number drums → score-reels; fixed "
    "backglass bulbs → backglass-lights; segmented LED digits → alphanumeric; a "
    "dot-matrix (DMD) → dot-matrix; a color CRT → cga; a full video/LCD screen → "
    "lcd. Only alphanumeric and dot-matrix displays have subtypes; the others "
    "are n-a."
)

# Tags/relationships handled by the lineage slice, per the extraction checklist —
# keep them out of the plain tag slice. `bootleg` / `licensed-build` were retired
# (copies are the `copy` model relationship now), and `conversion-kit` is a
# relationship_type being retired as a tag; `remake` is still a tag.
_LINEAGE_PAIRED_TAGS = frozenset({"remake", "conversion-kit"})

# The full model-info field set the extractor aims to cover — INCLUDING fields no
# slice builds yet. The core pre-seeds every one as `not-checked`, so each packet
# lists all of them and coverage is explicit (the anti-satisficing receipt) rather
# than a field silently missing. `system` and `corporate_entity_location` are the
# deferred ones (see build_slices); they show `not-checked` every run until built.
MODEL_INFO_FIELDS: tuple[str, ...] = (
    "year",
    "technology_generation",
    "technology_subgeneration",
    "game_format",
    "production_status",
    "display_type",
    "display_subtype",
    "cabinet",
    "player_count",
    "flipper_count",
    "reward_type",
    "tag",
    "themes",
    "franchise",
    "gameplay_feature",
    "credits",
    "lineage",
    "system",
    "corporate_entity_location",
    "other",
)

# Field slices that carry no controlled vocab, so they are catalog-independent and
# identical whether or not the flipcommons DB is present.
_VOCAB_FREE_SLICES: tuple[Slice, ...] = (
    YEAR,
    PLAYER_COUNT,
    FLIPPER_COUNT,
    GAMEPLAY_FEATURE,
    THEMES,
    FRANCHISE,
    CREDITS,
    LINEAGE,
    CATCH_ALL,
)


def build_slices(catalog: CatalogDb | None = None) -> tuple[Slice, ...]:
    """Assemble the full model-info slice set, grounding controlled fields on the DB.

    With a ``catalog`` every controlled-vocab field is grounded on the live
    vocabulary and its real per-term descriptions (single-value, multi-select, and
    the dependency pairs). Without one, only the standalone technology-generation
    fallback is grounded and the rest of the vocab fields are skipped. The
    vocab-free field slices (year, counts, themes, credits, lineage, catch-all)
    run either way.

    Deferred (need machinery beyond this batch): ``system`` (conditional on the
    maker having catalogued systems; a large manufacturer-scoped vocab) and the
    corporate-entity ``location`` field (targets a related entity, not the model).
    Entity-discovery slices are also out of scope here by design.
    """
    if catalog is None:
        return (TECHNOLOGY_GENERATION, *_VOCAB_FREE_SLICES)

    tech_pair = dependency_pair_slice(
        parent_key="technology_generation",
        child_key="technology_subgeneration",
        task=(
            "determine this machine's technology generation and, if solid-state, "
            "its subgeneration"
        ),
        parent_terms=catalog.vocab_terms("technology_generation"),
        child_pairs=catalog.child_terms("technology_subgeneration"),
        guidance=TECH_PAIR_GUIDANCE,
    )
    display_pair = dependency_pair_slice(
        parent_key="display_type",
        child_key="display_subtype",
        task="determine this machine's display type and, if it has one, its subtype",
        parent_terms=catalog.vocab_terms("display_type"),
        child_pairs=catalog.child_terms("display_subtype"),
        guidance=DISPLAY_PAIR_GUIDANCE,
    )
    game_format = single_value_slice(
        key="game_format",
        task="determine this machine's game format",
        terms=catalog.vocab_terms("game_format"),
        guidance=GAME_FORMAT_GUIDANCE,
    )
    production_status = single_value_slice(
        key="production_status",
        task="determine this machine's production status",
        terms=catalog.vocab_terms("production_status"),
        guidance=PRODUCTION_STATUS_GUIDANCE,
    )
    cabinet = single_value_slice(
        key="cabinet",
        task="determine this machine's cabinet form factor",
        terms=catalog.vocab_terms("cabinet"),
        guidance=CABINET_GUIDANCE,
    )
    reward_type = multi_select_slice(
        key="reward_type",
        task="determine which reward mechanisms this machine has",
        terms=catalog.vocab_terms("reward_type"),
        guidance=REWARD_GUIDANCE,
    )
    tag = multi_select_slice(
        key="tag",
        task="determine which classification tags apply to this machine",
        terms=tuple(
            term
            for term in catalog.vocab_terms("tag")
            if term.slug not in _LINEAGE_PAIRED_TAGS
        ),
        guidance=TAG_GUIDANCE,
    )
    return (
        tech_pair,
        display_pair,
        game_format,
        production_status,
        cabinet,
        reward_type,
        tag,
        *_VOCAB_FREE_SLICES,
    )


# The offline default (no DB): the fallback-grounded field set.
FIRST_CUT_SLICES: tuple[Slice, ...] = build_slices(None)
