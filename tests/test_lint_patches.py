"""Tests for scripts/patch_validation/lint_patches.py.

Covers the editorial authoring lint run by ``make validate`` — public-note
discipline, citation hygiene, drift-guard coverage, and the description rules.
Each test asserts on a specific error substring so unrelated incidental errors
in the crafted fixture don't make it brittle.
"""

from __future__ import annotations

import patch_validation.lint_patches as lp
import pytest


def errs(claims, attribution="flipcommons-catalog", filename="0040-x.yaml"):
    return lp.lint_patch(filename, {"attribution": attribution, "claims": claims})


def has(errors, needle):
    return any(needle in e for e in errors)


# --- 1: patch numbers in notes ----------------------------------------------


def test_note_patch_number_flagged():
    e = errs(
        [{"manufacturer.x": {"expect": {"name": "X"}, "note": "see 0042", "name": "X"}}]
    )
    assert has(e, "references patch number '0042'")


def test_note_year_and_ids_clean():
    e = errs(
        [
            {
                "manufacturer.x": {
                    "expect": {"name": "X"},
                    "note": "made 1972, ipdb 6069",
                    "name": "X",
                }
            }
        ]
    )
    assert not has(e, "patch number")


# --- 2: smart typography in notes -------------------------------------------


@pytest.mark.parametrize("note", ["IPDB “quote”", "it’s here", "a … gap"])
def test_smart_typography_flagged(note):
    e = errs([{"manufacturer.x": {"expect": {"name": "X"}, "note": note, "name": "X"}}])
    assert has(e, "smart typography")


def test_straight_typography_clean():
    e = errs(
        [
            {
                "manufacturer.x": {
                    "expect": {"name": "X"},
                    "note": 'IPDB "quote" [...]',
                    "name": "X",
                }
            }
        ]
    )
    assert not has(e, "smart typography")


# --- 4 + 5: aliases / abbreviations -----------------------------------------


def test_alias_casefold_duplicate_flagged():
    e = errs(
        [
            {
                "manufacturer.x": {
                    "expect": {"name": "X"},
                    "manufacturer_alias": ["Stern", "stern"],
                }
            }
        ]
    )
    assert has(e, "duplicate members")


def test_abbreviation_is_verbatim_not_casefolded():
    # MM vs mm are distinct abbreviations (verbatim identity), so no dup.
    e = errs([{"model.x": {"expect": {"year": 1990}, "abbreviation": ["MM", "mm"]}}])
    assert not has(e, "duplicate members")


def test_alias_too_long_flagged():
    e = errs(
        [
            {
                "manufacturer.x": {
                    "expect": {"name": "X"},
                    "manufacturer_alias": ["a" * 201],
                }
            }
        ]
    )
    assert has(e, "exceeds 200 chars")


def test_abbreviation_too_long_flagged():
    e = errs([{"model.x": {"expect": {"year": 1990}, "abbreviation": ["a" * 51]}}])
    assert has(e, "exceeds 50 chars")


# --- 6: IPDB/OPDB URL cites must use scheme form -----------------------------


def test_ipdb_url_cite_flagged():
    e = errs(
        [
            {
                "model.x": {
                    "expect": {"year": 1990},
                    "note": "n",
                    "year": 1990,
                    "cite": "https://www.ipdb.org/machine.cgi?id=6069",
                }
            }
        ]
    )
    assert has(e, "use the scheme:identifier form")


def test_scheme_cite_clean():
    e = errs(
        [
            {
                "model.x": {
                    "expect": {"year": 1990},
                    "note": "n",
                    "year": 1990,
                    "cite": "ipdb:6069",
                }
            }
        ]
    )
    assert not has(e, "scheme:identifier")


# --- 7: description attribution ---------------------------------------------


def test_description_wrong_attribution_flagged():
    e = errs(
        [
            {
                "manufacturer.x": {
                    "expect": {"name": "X"},
                    "cite": "ipdb:1",
                    "description": "d",
                }
            }
        ],
        attribution="flipcommons-catalog",
    )
    assert has(e, "flipcommons-ai-desc-manufacturer")


def test_description_right_attribution_clean():
    e = errs(
        [
            {
                "manufacturer.x": {
                    "expect": {"name": "X"},
                    "cite": "ipdb:1",
                    "description": "d",
                }
            }
        ],
        attribution="flipcommons-ai-desc-manufacturer",
    )
    assert not has(e, "must be attributed")


# --- 8: note presence -------------------------------------------------------


def test_cited_entry_without_note_flagged():
    e = errs(
        [{"manufacturer.x": {"expect": {"name": "X"}, "cite": "ipdb:1", "year": 1970}}]
    )
    assert has(e, "needs a note")


def test_create_scaffolding_needs_no_note():
    e = errs([{"title.x": {"create": True, "name": "X"}}])
    assert not has(e, "needs a note")


def test_substantive_assert_without_note_flagged():
    e = errs([{"model.x": {"expect": {"year": 1990}, "production_status": "produced"}}])
    assert has(e, "needs a note")


# --- 9: description needs a citation or a note ------------------------------


def test_description_without_cite_or_note_flagged():
    e = errs(
        [{"manufacturer.x": {"expect": {"name": "X"}, "description": "rests on data"}}],
        attribution="flipcommons-ai-desc-manufacturer",
    )
    assert has(e, "no citation and no note")


def test_description_with_entry_cite_clean():
    e = errs(
        [
            {
                "manufacturer.x": {
                    "expect": {"name": "X"},
                    "cite": "ipdb:1",
                    "description": "d",
                }
            }
        ],
        attribution="flipcommons-ai-desc-manufacturer",
    )
    assert not has(e, "no citation and no note")


def test_description_with_only_note_clean():
    e = errs(
        [
            {
                "manufacturer.x": {
                    "expect": {"name": "X"},
                    "note": "Rests on catalogued data.",
                    "description": "d",
                }
            }
        ],
        attribution="flipcommons-ai-desc-manufacturer",
    )
    assert not has(e, "no citation and no note")


def test_description_with_inline_marker_clean():
    e = errs(
        [
            {
                "manufacturer.x": {
                    "expect": {"name": "X"},
                    "description": "a fact[[cite:1]]",
                    "cites": {"1": "ipdb:1"},
                }
            }
        ],
        attribution="flipcommons-ai-desc-manufacturer",
    )
    assert not has(e, "no citation and no note")


# --- floor ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("filename", "linted"),
    [
        ("0038-x.yaml", False),
        ("0039-x.yaml", True),
        ("0067-x.yaml", True),
    ],
)
def test_editable_floor(filename, linted):
    prefix = lp._PREFIX_RE.match(filename)
    assert (int(prefix.group(1)) >= lp.EDITABLE_FLOOR) is linted
