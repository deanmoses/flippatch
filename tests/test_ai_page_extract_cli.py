"""Tests for the CLI shell's pure logic — the ref/target cross-check banner.

Offline: ``_ref_target_banner`` is the pure comparison (resolved ref model vs. the
target name's catalog matches); the DB I/O that feeds it lives in the shell and is
not exercised here. Covers each divergence branch build order §8 calls for.
"""

from __future__ import annotations

from ai_page_extract.catalog import ModelRef
from ai_page_extract.cli import _ref_target_banner
from common.catalog.entity_index import EntityRef


def _model(slug: str, name: str = "Combat") -> EntityRef:
    return EntityRef("model", slug, name)


def test_ref_not_in_catalog_is_a_possible_gap_warning():
    banner = _ref_target_banner("ipdb:6682", "Combat", None, [_model("combat")])
    assert banner is not None
    assert "not in the catalog by its IPDB/OPDB id" in banner
    assert "possible gap" in banner


def test_target_name_resolves_to_nothing_warns_ref_is_the_anchor():
    banner = _ref_target_banner(
        "ipdb:6682", "Combat", ModelRef("combat-3", "Combat"), []
    )
    assert banner is not None
    assert "resolves to no catalog model" in banner
    assert "model:combat-3" in banner


def test_hard_disagreement_when_ref_model_not_among_name_matches():
    # The dangerous case: the ref denotes a record the target name doesn't reach.
    banner = _ref_target_banner(
        "ipdb:6682", "Combat", ModelRef("combat-3", "Combat"), [_model("combat")]
    )
    assert banner is not None
    assert "disagree" in banner
    assert "model:combat-3" in banner  # the ref's record
    assert "model:combat" in banner  # what the name reaches


def test_ambiguous_name_gets_a_disambiguation_note_not_a_warning():
    # The real Combat case: the name resolves to all three, the ref pins one.
    matches = [_model("combat"), _model("combat-2"), _model("combat-3")]
    banner = _ref_target_banner(
        "ipdb:6682", "Combat", ModelRef("combat-3", "Combat"), matches
    )
    assert banner is not None
    assert banner.startswith("note:")
    assert "ambiguous" in banner
    assert "pins it to model:combat-3" in banner


def test_single_agreeing_match_is_silent():
    banner = _ref_target_banner(
        "ipdb:3609", "Combat", ModelRef("combat", "Combat"), [_model("combat")]
    )
    assert banner is None
