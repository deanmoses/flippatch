"""Tests for ai_page_extract — the cheap-model recall fan-out core.

Fully offline: a fake ``AiClient`` (satisfying ``common.ai``'s Protocol) returns
canned structured payloads keyed by which slice is asking, so these exercise the
three archetypes, union/dedup across samples, quote verification (keep-and-flag),
and the packet shape without any network, cache, or sibling checkout. Page text
is a fixture string; ``check_quote`` runs for real against it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from ai_page_extract.catalog import ChildTerm, VocabTerm
from ai_page_extract.extract import (
    STATE_CANDIDATES,
    STATE_CHECKED_ABSENT,
    STATE_NOT_CHECKED,
    PageMetadata,
    extract,
)
from ai_page_extract.fields import GAMEPLAY_FEATURE, LINEAGE, TECHNOLOGY_GENERATION
from ai_page_extract.framework import (
    Slice,
    TargetContext,
    dependency_pair_slice,
    multi_select_slice,
    scalar_slice,
    single_value_slice,
)
from common.ai.client import AiError

if TYPE_CHECKING:
    from collections.abc import Callable

    from common.ai.client import AiModelResult
    from common.types import JsonSchema

# A fixture page whose quotes below are all verbatim substrings — except where a
# test deliberately supplies a quote that is NOT present.
PAGE = (
    "Dogs Race is an electromechanical pinball machine. The score reel "
    "assemblies advance with each hit. It has three flippers, two ramps, and a "
    "set of drop targets. The cabinet reuses an earlier Gottlieb model's "
    "woodwork, converted with a new playfield."
)


class FakeAiClient:
    """Returns a canned payload per call, chosen by the responder from the user text."""

    def __init__(self, responder: Callable[[str], AiModelResult]) -> None:
        self._responder = responder
        self.calls: list[str] = []

    def structured(
        self,
        *,
        system: str,
        user: str,
        schema: JsonSchema,
        model: str,
        max_tokens: int = 512,
    ) -> AiModelResult:
        self.calls.append(user)
        return self._responder(user)


def _which(user: str) -> str:
    if "technology generation" in user:
        return "tech"
    if "gameplay feature" in user:
        return "gameplay"
    if "lineage relationship" in user:
        return "lineage"
    raise AssertionError("unrecognized slice prompt")


def _default_responder(user: str) -> AiModelResult:
    kind = _which(user)
    if kind == "tech":
        return {
            "value": "electromechanical",
            "quote": "Dogs Race is an electromechanical pinball machine.",
        }
    if kind == "gameplay":
        return {
            "items": [
                {"name": "flippers", "count": 3, "quote": "It has three flippers"},
                {"name": "ramps", "count": 2, "quote": "two ramps"},
            ]
        }
    return {
        "signals": [
            {
                "relation": "conversion",
                "related": "unnamed",
                "quote": "converted with a new playfield",
            }
        ]
    }


def test_single_value_field_yields_verified_candidate():
    ai = FakeAiClient(_default_responder)
    packet = extract(
        page_text=PAGE, source_ref="ipdb:1", slices=(TECHNOLOGY_GENERATION,), ai=ai
    )
    result = packet.fields["technology_generation"]
    assert result.state == STATE_CANDIDATES
    assert len(result.candidates) == 1
    cand = result.candidates[0].to_json()
    assert cand["value"] == "electromechanical"
    assert cand["quote_verified"] is True
    assert cand["source_ref"] == "ipdb:1"


def test_single_value_absent_is_checked_absent():
    def responder(user: str) -> AiModelResult:
        assert _which(user) == "tech"
        return {"value": "absent", "quote": ""}

    ai = FakeAiClient(responder)
    packet = extract(
        page_text=PAGE, source_ref="ipdb:1", slices=(TECHNOLOGY_GENERATION,), ai=ai
    )
    result = packet.fields["technology_generation"]
    assert result.state == STATE_CHECKED_ABSENT
    assert result.candidates == ()


def test_enumerative_unions_across_samples_and_merges_count():
    # Three samples (GAMEPLAY_FEATURE.samples == 3) each miss stochastically; the
    # union recovers the full set, and a count from any sample sticks.
    per_sample = [
        [{"name": "flippers", "count": None, "quote": "It has three flippers"}],
        [
            {"name": "flippers", "count": 3, "quote": "three flippers"},
            {"name": "drop targets", "count": None, "quote": "a set of drop targets"},
        ],
        [{"name": "ramps", "count": 2, "quote": "two ramps"}],
    ]
    calls = {"n": 0}

    def responder(user: str) -> AiModelResult:
        assert _which(user) == "gameplay"
        payload = {"items": per_sample[calls["n"]]}
        calls["n"] += 1
        return payload

    ai = FakeAiClient(responder)
    packet = extract(
        page_text=PAGE, source_ref="ipdb:1", slices=(GAMEPLAY_FEATURE,), ai=ai
    )
    result = packet.fields["gameplay_feature"]
    assert result.state == STATE_CANDIDATES
    assert ai.calls.__len__() == 3
    by_value = {c.candidate.value: c.to_json() for c in result.candidates}
    assert set(by_value) == {"flippers", "ramps", "drop targets"}
    # flippers surfaced first without a count, then with 3 — the count is kept.
    assert by_value["flippers"]["count"] == 3
    assert all(c["quote_verified"] for c in by_value.values())


def test_judgment_slice_flags_candidate_with_related():
    ai = FakeAiClient(_default_responder)
    packet = extract(page_text=PAGE, source_ref="ipdb:1", slices=(LINEAGE,), ai=ai)
    result = packet.fields["lineage"]
    assert result.state == STATE_CANDIDATES
    cand = result.candidates[0].to_json()
    assert cand["value"] == "conversion"
    assert cand["related"] == "unnamed"
    assert cand["quote_verified"] is True


def test_unverifiable_quote_is_kept_and_flagged_not_dropped():
    def responder(user: str) -> AiModelResult:
        return {
            "value": "solid-state",
            "quote": "this exact sentence is nowhere on the page",
        }

    ai = FakeAiClient(responder)
    packet = extract(
        page_text=PAGE, source_ref="ipdb:1", slices=(TECHNOLOGY_GENERATION,), ai=ai
    )
    result = packet.fields["technology_generation"]
    assert result.state == STATE_CANDIDATES  # kept, not silently dropped
    cand = result.candidates[0].to_json()
    assert cand["quote_verified"] is False
    assert "quote_unverified_reason" in cand


def test_elided_quote_with_ellipsis_verifies():
    # The prompt tells the model it may join two exact spans with `[...]`; the
    # verifier (check_quote) supports exactly that, so an elided quote must pass.
    def responder(user: str) -> AiModelResult:
        return {
            "items": [
                {
                    "name": "flippers and ramps",
                    "count": None,
                    "quote": "three flippers [...] two ramps",
                }
            ]
        }

    ai = FakeAiClient(responder)
    packet = extract(
        page_text=PAGE, source_ref="ipdb:1", slices=(GAMEPLAY_FEATURE,), ai=ai
    )
    cand = packet.fields["gameplay_feature"].candidates[0].to_json()
    assert cand["quote_verified"] is True


def test_slice_error_becomes_not_checked_and_others_proceed():
    def responder(user: str) -> AiModelResult:
        if _which(user) == "gameplay":
            raise AiError("model returned no tool_use block")
        return _default_responder(user)

    ai = FakeAiClient(responder)
    packet = extract(
        page_text=PAGE,
        source_ref="ipdb:1",
        slices=(TECHNOLOGY_GENERATION, GAMEPLAY_FEATURE, LINEAGE),
        ai=ai,
    )
    assert packet.fields["gameplay_feature"].state == STATE_NOT_CHECKED
    assert packet.fields["gameplay_feature"].note is not None
    # The erroring slice does not sink the run.
    assert packet.fields["technology_generation"].state == STATE_CANDIDATES
    assert packet.fields["lineage"].state == STATE_CANDIDATES


def test_expected_fields_preseed_not_checked_when_no_slice_covers():
    ai = FakeAiClient(_default_responder)
    packet = extract(
        page_text=PAGE,
        source_ref="ipdb:1",
        slices=(TECHNOLOGY_GENERATION,),
        ai=ai,
        expected_fields=("technology_generation", "year", "credits"),
    )
    # The covered field ran; the uncovered ones are reported, not omitted.
    assert packet.fields["technology_generation"].state == STATE_CANDIDATES
    assert packet.fields["year"].state == STATE_NOT_CHECKED
    assert packet.fields["year"].note is not None
    assert packet.fields["credits"].state == STATE_NOT_CHECKED


def test_partial_sample_failure_preserves_completed_candidates():
    # A union slice whose 2nd sample throws must keep sample 1's candidates, not
    # discard them as not-checked.
    calls = {"n": 0}

    def responder(user: str) -> AiModelResult:
        calls["n"] += 1
        if calls["n"] == 2:
            raise AiError("transient failure on sample 2")
        return {"items": [{"name": "ramps", "count": 2, "quote": "two ramps"}]}

    ai = FakeAiClient(responder)
    packet = extract(
        page_text=PAGE, source_ref="ipdb:1", slices=(GAMEPLAY_FEATURE,), ai=ai
    )
    result = packet.fields["gameplay_feature"]
    assert result.state == STATE_CANDIDATES
    assert [c.candidate.value for c in result.candidates] == ["ramps"]
    assert result.samples_completed == 2  # 2 of 3 completed
    assert result.note is not None  # partial failure recorded, not hidden


def test_count_and_quote_come_from_the_same_sample():
    # If sample 1 has no count and sample 2 supplies count=3, the merged item must
    # carry sample 2's quote (which supports the 3), not sample 1's.
    per_sample = [
        [{"name": "flippers", "count": None, "quote": "It has three flippers"}],
        [{"name": "flippers", "count": 3, "quote": "three flippers"}],
        [{"name": "flippers", "count": 3, "quote": "three flippers"}],
    ]
    calls = {"n": 0}

    def responder(user: str) -> AiModelResult:
        payload = {"items": per_sample[calls["n"]]}
        calls["n"] += 1
        return payload

    ai = FakeAiClient(responder)
    packet = extract(
        page_text=PAGE, source_ref="ipdb:1", slices=(GAMEPLAY_FEATURE,), ai=ai
    )
    cand = packet.fields["gameplay_feature"].candidates[0].to_json()
    assert cand["count"] == 3
    assert cand["quote"] == "three flippers"  # the quote that supports the count


def test_page_metadata_flows_into_packet():
    ai = FakeAiClient(_default_responder)
    metadata: PageMetadata = {
        "last_updated": "2026-03-22",
        "content_type": "text/html",
        "rendered": 0,
        "title": "Dogs Race",
    }
    packet = extract(
        page_text=PAGE,
        source_ref="ipdb:1",
        slices=(TECHNOLOGY_GENERATION,),
        ai=ai,
        page_metadata=metadata,
    )
    assert packet.to_json()["page_metadata"] == metadata


def test_packet_to_json_shape():
    ai = FakeAiClient(_default_responder)
    packet = extract(
        page_text=PAGE,
        source_ref="ipdb:5632",
        slices=(TECHNOLOGY_GENERATION, GAMEPLAY_FEATURE, LINEAGE),
        ai=ai,
    )
    blob = packet.to_json()
    assert blob["source_ref"] == "ipdb:5632"
    assert set(blob["fields"]) == {
        "technology_generation",
        "gameplay_feature",
        "lineage",
    }
    gameplay = blob["fields"]["gameplay_feature"]
    assert gameplay["state"] == STATE_CANDIDATES
    assert gameplay["aggregate"] == "union"
    assert gameplay["samples"] == 3
    for cand in gameplay["candidates"]:
        assert {"value", "quote", "source_ref", "quote_verified"} <= set(cand)


def test_core_makes_exactly_samples_calls_per_slice():
    slices: tuple[Slice, ...] = (TECHNOLOGY_GENERATION, GAMEPLAY_FEATURE, LINEAGE)
    ai = FakeAiClient(_default_responder)
    extract(page_text=PAGE, source_ref="ipdb:1", slices=slices, ai=ai)
    assert len(ai.calls) == sum(s.samples for s in slices)


@pytest.mark.parametrize("slice_", [TECHNOLOGY_GENERATION, GAMEPLAY_FEATURE, LINEAGE])
def test_user_prompt_delimits_the_page(slice_: Slice):
    prompt = slice_.user_prompt(PAGE)
    assert "SOURCE_PAGE" in prompt
    assert PAGE in prompt


# ── The archetypes added in the model-info batch ────────────────────────────

_PAIR_PAGE = "It uses a WPC CPU board and software."


def _pair_slice() -> Slice:
    return dependency_pair_slice(
        parent_key="technology_generation",
        child_key="technology_subgeneration",
        task="determine the generation and subgeneration",
        parent_terms=(VocabTerm("solid-state", "Solid State", "microprocessor"),),
        child_pairs=(
            ChildTerm(
                VocabTerm("ss-integrated", "Integrated", "WPC etc."), "solid-state"
            ),
        ),
        guidance="tells",
    )


def test_dependency_pair_routes_both_fields():
    def responder(user: str) -> AiModelResult:
        return {
            "value": "solid-state",
            "quote": "a WPC CPU board",
            "subvalue": "ss-integrated",
            "subquote": "WPC CPU board and software",
        }

    ai = FakeAiClient(responder)
    packet = extract(
        page_text=_PAIR_PAGE, source_ref="ipdb:1", slices=(_pair_slice(),), ai=ai
    )
    gen = packet.fields["technology_generation"].candidates[0].to_json()
    sub = packet.fields["technology_subgeneration"].candidates[0].to_json()
    assert gen["value"] == "solid-state"
    assert sub["value"] == "ss-integrated"
    assert gen["quote_verified"] is True
    assert sub["quote_verified"] is True
    # One call resolved two fields.
    assert len(ai.calls) == 1


def test_dependency_pair_child_na_is_checked_absent():
    def responder(user: str) -> AiModelResult:
        return {
            "value": "solid-state",
            "quote": "a WPC CPU board",
            "subvalue": "n-a",
            "subquote": "",
        }

    ai = FakeAiClient(responder)
    packet = extract(
        page_text=_PAIR_PAGE, source_ref="ipdb:1", slices=(_pair_slice(),), ai=ai
    )
    assert packet.fields["technology_generation"].state == STATE_CANDIDATES
    assert packet.fields["technology_subgeneration"].state == STATE_CHECKED_ABSENT


def test_multi_select_lists_each_applicable_value():
    terms = (
        VocabTerm("replay", "Replay", "free game"),
        VocabTerm("novelty", "Novelty", "no reward"),
    )
    slice_ = multi_select_slice(
        key="reward_type",
        task="which rewards",
        terms=terms,
        guidance="tells",
        samples=1,
    )
    ai = FakeAiClient(
        lambda _: {"items": [{"value": "replay", "quote": "awards a replay"}]}
    )
    packet = extract(
        page_text="Match feature awards a replay.",
        source_ref="ipdb:1",
        slices=(slice_,),
        ai=ai,
    )
    result = packet.fields["reward_type"]
    assert [c.candidate.value for c in result.candidates] == ["replay"]
    assert result.candidates[0].to_json()["quote_verified"] is True


def test_scalar_slice_captures_number_and_marks_null_absent():
    slice_ = scalar_slice(key="flipper_count", task="how many flippers")
    hit = FakeAiClient(lambda _: {"value": 3, "quote": "has 3 flippers"})
    packet = extract(
        page_text="The game has 3 flippers.",
        source_ref="ipdb:1",
        slices=(slice_,),
        ai=hit,
    )
    assert packet.fields["flipper_count"].candidates[0].to_json()["value"] == "3"

    miss = FakeAiClient(lambda _: {"value": None, "quote": ""})
    packet2 = extract(
        page_text="The game has 3 flippers.",
        source_ref="ipdb:1",
        slices=(slice_,),
        ai=miss,
    )
    assert packet2.fields["flipper_count"].state == STATE_CHECKED_ABSENT


# ── Target context — the maker-index over-surface fix ────────────────────────
# A run carries the model it is *about* so a multi-model page (a maker index, a
# whole-lineup marketing page) stops attributing a sibling machine's facts to the
# target. The context is stable across every slice, so it must reach each prompt.


def test_target_context_frames_every_slice_prompt():
    ai = FakeAiClient(_default_responder)
    target = TargetContext(name="Joker", maker="Manilamatic")
    extract(
        page_text=PAGE,
        source_ref="ipdb:1",
        slices=(TECHNOLOGY_GENERATION, GAMEPLAY_FEATURE, LINEAGE),
        ai=ai,
        target=target,
    )
    # Every slice call (including the 3 union samples of GAMEPLAY_FEATURE) is framed.
    assert ai.calls, "no slices ran"
    for prompt in ai.calls:
        assert "Joker" in prompt
        assert "Manilamatic" in prompt
        # The disambiguation discipline: a sibling's fact is not the target's.
        assert "NOT the target's fact" in prompt
        # The page still follows the framing (order: target → task → page).
        assert prompt.index("EXTRACTION TARGET") < prompt.index(PAGE[:20])


def test_no_target_leaves_prompt_unframed():
    ai = FakeAiClient(_default_responder)
    extract(page_text=PAGE, source_ref="ipdb:1", slices=(TECHNOLOGY_GENERATION,), ai=ai)
    assert ai.calls
    assert "EXTRACTION TARGET" not in ai.calls[0]


def test_target_note_reaches_prompt():
    ai = FakeAiClient(_default_responder)
    target = TargetContext(
        name="Joker",
        maker="Manilamatic",
        note="ignore the sidebar's related-games list",
    )
    extract(page_text=PAGE, source_ref="ipdb:1", slices=(TECHNOLOGY_GENERATION,), ai=ai)
    # Sanity: the note only appears when the target carries it.
    assert "related-games list" not in ai.calls[0]
    ai2 = FakeAiClient(_default_responder)
    extract(
        page_text=PAGE,
        source_ref="ipdb:1",
        slices=(TECHNOLOGY_GENERATION,),
        ai=ai2,
        target=target,
    )
    assert "ignore the sidebar's related-games list" in ai2.calls[0]


# ── Slice-guidance regression guards ─────────────────────────────────────────
# Behavioural fixes verified against the real corpus (a compact home machine that
# stands on legs was mis-read as `tabletop`; the catch-all emptied under target
# framing). These lock the guidance wording that addresses each so it can't be
# silently reverted; the behavioural proof is the recall-round re-run, not here.


def test_cabinet_guidance_treats_legs_as_floor_regardless_of_scale():
    from ai_page_extract.fields import CABINET_GUIDANCE

    lowered = CABINET_GUIDANCE.lower()
    assert "legs" in lowered
    # Size must not decide it: a compact/home machine on legs is still floor.
    assert "compact" in lowered
    assert "not tabletop" in lowered


def test_catch_all_scopes_between_field_enrichment():
    from ai_page_extract.fields import CATCH_ALL

    lowered = CATCH_ALL.instructions.lower()
    # The categories the target framing was suppressing are named as in-scope.
    assert "construction" in lowered
    assert "materials" in lowered
    # ...and explicitly wanted even when the other fields are already answered.
    assert "already answered" in lowered


def test_gameplay_guidance_flags_multi_level_and_forbids_locational_split():
    # A real run split "six flippers" into main/upper/outlane sub-counts (noise)
    # while missing the multi-level playfield the "upper transparent playfield"
    # phrasing implies. The structure is a feature; the locational split is not.
    from ai_page_extract.fields import GAMEPLAY_FEATURE

    lowered = GAMEPLAY_FEATURE.instructions.lower()
    assert "multi-level" in lowered
    assert "sub-count" in lowered


def test_credits_excludes_non_makers():
    # Ultra Attack surfaced four non-credits (a company rep, a researcher, a
    # collector who preserved a copy, an IPDB photographer) as credits. A credit
    # is for MAKING the game; other named people belong to entity discovery.
    from ai_page_extract.fields import CREDITS

    lowered = CREDITS.instructions.lower()
    assert "researcher" in lowered
    assert "collector" in lowered
    assert "not a credit" in lowered


def test_lineage_separates_conversion_from_variant_and_ignores_comparison():
    # An art-only re-skin (Ultra Attack = Jumbo Kick with new art) is a variant,
    # not a conversion; a bare look-alike comparison (World Series ~ Home Run) is
    # not a derivation at all.
    from ai_page_extract.fields import LINEAGE

    lowered = LINEAGE.instructions.lower()
    assert "not a conversion" in lowered
    assert "comparing" in lowered
    assert "derived" in lowered


def test_tag_guidance_scopes_retheme_and_export():
    # manufacturer-retheme fired cross-maker (Ultra Attack: NGK over Nihon Tenbo)
    # and export fired on a US game imported to Japan (Matador). Both are scoped.
    from ai_page_extract.fields import TAG_GUIDANCE

    lowered = TAG_GUIDANCE.lower()
    assert "its own" in lowered
    assert "different maker" in lowered
    assert "not export" in lowered


def test_tech_gen_guidance_treats_lighting_as_electricity():
    # Ultra Attack (backbox lamps / bulb lights) was misread as pure-mechanical;
    # electric lighting means electricity, which rules pure-mechanical out.
    from ai_page_extract.fields import TECH_GEN_GUIDANCE

    lowered = TECH_GEN_GUIDANCE.lower()
    assert "bulbs" in lowered
    assert "rules out pure-mechanical" in lowered


def test_enumerative_empty_object_is_checked_absent_not_lost_slice():
    # A cheap model that finds nothing sometimes returns a bare `{}` instead of
    # `{"items": []}`. The wrapper key is optional, so that benign empty validates
    # and the slice reports checked-absent — never not-checked (a lost slice).
    ai = FakeAiClient(lambda _: {})
    packet = extract(
        page_text=PAGE, source_ref="ipdb:1", slices=(GAMEPLAY_FEATURE,), ai=ai
    )
    result = packet.fields["gameplay_feature"]
    assert result.state == STATE_CHECKED_ABSENT
    assert result.candidates == ()
    assert result.samples_completed == GAMEPLAY_FEATURE.samples  # all samples ran


# ── Benign absence in the non-enumerative archetypes ─────────────────────────
# The twin of the empty-wrapper fix above: a cheap model expressing "nothing
# found" off-spec — the literal string "<null>", or omitting the required quote —
# must VALIDATE and degrade to checked-absent, never fail schema validation into
# an errored (not-checked) slice that the compact view then flags as a false gap.


def _validates(schema: JsonSchema, payload: object) -> None:
    """Assert ``payload`` passes the slice schema the real client validates against."""
    from jsonschema import Draft7Validator

    Draft7Validator(schema).validate(payload)


def test_year_null_sentinel_string_is_absent_not_error():
    from ai_page_extract.fields import YEAR

    payload = {"year": "<null>", "month": None, "quote": ""}
    _validates(YEAR.schema, payload)  # was: string fails the integer|null type
    assert YEAR.parser(payload) == []


def test_year_string_integer_is_coerced_to_a_candidate():
    from ai_page_extract.fields import YEAR

    payload = {"year": "1976", "month": None, "quote": "made in 1976"}
    _validates(YEAR.schema, payload)
    assert [item.value for item in YEAR.parser(payload)] == ["1976"]


def test_franchise_missing_quote_validates_and_sentinel_is_absent():
    from ai_page_extract.fields import FRANCHISE

    _validates(FRANCHISE.schema, {"value": None})  # was: missing quote fails required
    assert FRANCHISE.parser({"value": "<null>", "quote": ""}) == []


def test_single_value_missing_quote_and_sentinel_degrade():
    slice_ = single_value_slice(
        key="display_type",
        task="determine the display type",
        terms=(VocabTerm("score-reels", "Score reels", "mechanical reels"),),
        guidance="",
    )
    _validates(slice_.schema, {"value": "none"})  # sentinel + omitted quote
    assert slice_.parser({"value": "<null>", "quote": ""}) == []
    # A real value with a missing quote is kept-and-flagged, never errored away.
    _validates(slice_.schema, {"value": "score-reels"})
    assert [i.value for i in slice_.parser({"value": "score-reels"})] == ["score-reels"]


def test_scalar_sentinel_string_is_absent_and_string_int_coerces():
    slice_ = scalar_slice(key="player_count", task="max players")
    _validates(slice_.schema, {"value": "<null>"})
    assert slice_.parser({"value": "<null>", "quote": ""}) == []
    _validates(slice_.schema, {"value": "4", "quote": "up to 4 players"})
    assert [i.value for i in slice_.parser({"value": "4", "quote": "4 players"})] == [
        "4"
    ]


def test_pair_missing_subquote_validates_and_sentinel_child_is_absent():
    slice_ = _pair_slice()
    payload = {"value": "solid-state", "quote": "solid state", "subvalue": "<null>"}
    _validates(slice_.schema, payload)  # subquote omitted, child sentinel off-enum
    fields = {item.field for item in slice_.parser(payload)}
    assert "technology_generation" in fields  # parent kept
    assert "technology_subgeneration" not in fields  # sentinel child dropped
