"""Tests for ai_lint.patch_load — shaping patch YAML into rule inputs."""

from __future__ import annotations

from ai_lint.patch_load import iter_description_units, iter_scalar_claim_cites


def test_iter_description_units_reads_text_and_cites():
    data = {
        "claims": [
            {
                "franchise.battle-dome": {
                    "description": "Battle Dome is a ball game.[[cite:1]]",
                    "cites": {
                        1: {
                            "ref": "https://en.wikipedia.org/wiki/Battle_Dome",
                            "quote": "a ball game",
                        }
                    },
                }
            }
        ]
    }
    (unit,) = list(iter_description_units("0059-x.yaml", data))
    assert unit.entity_type == "franchise"
    assert unit.slug == "battle-dome"
    assert "1" in unit.cites
    assert unit.cites["1"].ref.endswith("Battle_Dome")
    assert unit.cites["1"].quote == "a ball game"


def test_iter_scalar_claim_cites_renders_claim_and_quote():
    data = {
        "claims": [
            {
                "model.american-battle-dome": {
                    "year": 1995,
                    "game_format": "pinball",
                    "cite": {
                        "ref": "ipdb:6069",
                        "quote": "Released by Sun Wise in 1995.",
                    },
                }
            }
        ]
    }
    (claim,) = list(iter_scalar_claim_cites("0059-x.yaml", data))
    assert "year = 1995" in claim.claim_text
    assert "game_format = 'pinball'" in claim.claim_text
    assert claim.cite.ref == "ipdb:6069"
    assert claim.cite.quote == "Released by Sun Wise in 1995."


def test_alias_only_unit_yields_no_scalar_claim():
    data = {
        "claims": [
            {"manufacturer.sunwise": {"manufacturer_alias": ["Sun Wise"], "note": "x"}}
        ]
    }
    assert list(iter_scalar_claim_cites("0059-x.yaml", data)) == []
