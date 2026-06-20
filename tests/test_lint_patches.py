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


# --- 9: a description must footnote at least one fact inline ----------------


def test_description_with_no_inline_cite_flagged():
    e = errs(
        [{"manufacturer.x": {"expect": {"name": "X"}, "description": "rests on data"}}],
        attribution="flipcommons-ai-desc-manufacturer",
    )
    assert has(e, "at least one inline")


def test_description_note_only_now_flagged():
    # A note: no longer excuses a missing footnote — every description must
    # footnote at least one fact inline.
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
    assert has(e, "at least one inline")


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
    assert not has(e, "at least one inline")


def test_description_no_inline_grandfathered_before_rule():
    e = errs(
        [{"manufacturer.x": {"note": "n", "description": "d"}}],
        attribution="flipcommons-ai-desc-manufacturer",
        filename="0010-x.yaml",
    )
    assert not has(e, "at least one inline")


def test_gameplay_feature_description_needs_no_inline_cite():
    # Taxonomy descriptions (gameplay features) are encyclopedic cross-references
    # — they define a concept and link related features/games via wikilinks
    # rather than footnoting sourced facts — so they're exempt from the
    # inline-cite requirement that binds real-world-entity descriptions.
    e = errs(
        [
            {
                "gameplay-feature.orbits": {
                    "description": "Loops past the [[gameplay-feature:spinners]]."
                }
            }
        ],
        attribution="flipcommons-ai-desc-gameplay-feature",
    )
    assert not has(e, "at least one inline")


def test_gameplay_feature_description_still_needs_attribution():
    # The exemption is narrow: only the inline-cite rule relaxes. A gameplay
    # feature description still must carry the desc attribution, and an
    # entry-level cite: is still rejected.
    e = errs(
        [
            {
                "gameplay-feature.orbits": {
                    "description": "A loop shot.",
                    "cite": "ipdb:1",
                }
            }
        ],
        attribution="flipcommons-catalog",
    )
    assert has(e, "must be attributed")
    assert has(e, "entry-level cite")


# --- patch-description-length: the Admin-only ingest-run note stays short ----
# This rule is whole-patch (the top-level description:), not per-unit, so the
# tests drive lint_patch directly rather than the per-claim errs() helper.


def _patch(description, filename="0040-x.yaml"):
    return lp.lint_patch(filename, {"description": description, "claims": []})


def test_long_patch_description_flagged():
    e = _patch("x" * 81)
    assert has(e, "max 80")


def test_short_patch_description_clean():
    e = _patch("Fix the maker name.")
    assert not has(e, "max 80")


def test_patch_description_exactly_80_clean():
    e = _patch("x" * 80)
    assert not has(e, "max 80")


def test_patch_description_counts_collapsed_length():
    # A folded scalar wraps across lines and may keep a trailing newline; the
    # limit measures the whitespace-collapsed text, so 80 chars + a newline is
    # still within budget.
    e = _patch("x" * 80 + "\n")
    assert not has(e, "max 80")

    # Content that only exceeds 80 once de-wrapped is still flagged.
    long = "\n".join(["a sentence fragment"] * 6)  # collapses to >80 chars
    assert has(_patch(long), "max 80")


def test_missing_patch_description_not_flagged():
    # The rule bounds length; it does not require a description to exist.
    e = lp.lint_patch("0040-x.yaml", {"claims": []})
    assert not has(e, "max 80")


def test_patch_description_length_grandfathered_before_rule():
    # 0038 is the last patch ingested on production and immutable — exempt.
    e = _patch("x" * 200, filename="0038-model-game-formats.yaml")
    assert not has(e, "max 80")


def test_patch_description_length_linted_at_0039():
    e = _patch("x" * 200, filename="0039-x.yaml")
    assert has(e, "max 80")


def test_rule_since_registry_has_patch_description_length():
    assert lp.RULE_SINCE["patch-description-length"] == 39


# --- per-rule introduction number / grandfathering --------------------------


def test_pre_baseline_patch_grandfathered():
    # A patch numbered below a rule's introduction is grandfathered for it: this
    # corporate-entity field assertion would need a note: at/after the baseline,
    # but a 0010 patch predates the ruleset and stays clean.
    e = errs(
        [{"corporate-entity.x": {"manufacturer": "y"}}],
        filename="0010-x.yaml",
    )
    assert e == []


def test_at_baseline_patch_linted():
    # The same fixture at/after the baseline IS linted.
    e = errs([{"corporate-entity.x": {"manufacturer": "y"}}], filename="0039-x.yaml")
    assert has(e, "needs a note")


def test_rule_since_registry_has_description_rules():
    # Both description footnote rules are registered with their own introduction
    # number (39, because 0039+ were retrofitted to comply).
    assert lp.RULE_SINCE["description-needs-inline-cite"] == 39
    assert lp.RULE_SINCE["description-no-entry-cite"] == 39


# --- a description must cite at least two distinct root sources --------------
# The description-two-sources enforcement is TEMPORARILY DISABLED in
# lint_patches.py; the tests asserting it fires are skipped until it's restored.
# Re-enable both together. The clean / grandfather / registry tests below stay
# active (they pass whether or not the rule fires).
_TWO_SOURCES_DISABLED = pytest.mark.skip(
    reason="description-two-sources rule temporarily disabled"
)


def _desc(description, cites, filename="0040-x.yaml"):
    return errs(
        [{"manufacturer.x": {"description": description, "cites": cites}}],
        attribution="flipcommons-ai-desc-manufacturer",
        filename=filename,
    )


@_TWO_SOURCES_DISABLED
def test_description_single_citation_flagged():
    e = _desc("one fact[[cite:1]]", {"1": "https://pinside.com/x"})
    assert has(e, "at least two sources")


@_TWO_SOURCES_DISABLED
def test_description_two_citations_same_root_flagged():
    # Both footnotes resolve to pawlowskipinball.com — one root, not two.
    e = _desc(
        "a[[cite:1]] b[[cite:2]]",
        {
            "1": "https://pawlowskipinball.com/",
            "2": "https://pawlowskipinball.com/eternal",
        },
    )
    assert has(e, "only one root source")


@_TWO_SOURCES_DISABLED
def test_description_subdomains_share_root_flagged():
    # twip.kineticist.com and www.kineticist.com collapse to one root domain.
    e = _desc(
        "a[[cite:1]] b[[cite:2]]",
        {
            "1": "https://twip.kineticist.com/p/x",
            "2": "https://www.kineticist.com/news/y",
        },
    )
    assert has(e, "only one root source")


@_TWO_SOURCES_DISABLED
def test_description_scheme_cites_same_scheme_flagged():
    e = _desc("a[[cite:1]] b[[cite:2]]", {"1": "ipdb:1", "2": "ipdb:2"})
    assert has(e, "only one root source")


def test_description_two_distinct_roots_clean():
    e = _desc(
        "a[[cite:1]] b[[cite:2]]",
        {"1": "https://pinside.com/x", "2": "https://www.kineticist.com/y"},
    )
    assert not has(e, "two sources")
    assert not has(e, "root source")


def test_description_url_and_scheme_distinct_clean():
    e = _desc(
        "a[[cite:1]] b[[cite:2]]", {"1": "https://pinside.com/x", "2": "youtube:abc"}
    )
    assert not has(e, "two sources")
    assert not has(e, "root source")


def test_description_two_sources_grandfathered_before_rule():
    e = _desc("one fact[[cite:1]]", {"1": "ipdb:1"}, filename="0010-x.yaml")
    assert not has(e, "two sources")


def test_rule_since_registry_has_two_sources_rule():
    assert lp.RULE_SINCE["description-two-sources"] == 39


# --- an entry-level cite: on a description is always an error ----------------


def test_description_entry_cite_forbidden():
    e = errs(
        [{"manufacturer.x": {"cite": "ipdb:1", "description": "d[[cite:1]]"}}],
        attribution="flipcommons-ai-desc-manufacturer",
        filename="0040-x.yaml",
    )
    assert has(e, "an entry-level cite: is not allowed")


def test_description_inline_cites_map_clean():
    e = errs(
        [
            {
                "manufacturer.x": {
                    "description": "a fact[[cite:1]]",
                    "cites": {"1": "ipdb:1"},
                }
            }
        ],
        attribution="flipcommons-ai-desc-manufacturer",
        filename="0040-x.yaml",
    )
    assert not has(e, "an entry-level cite: is not allowed")


def test_description_entry_cite_grandfathered_before_rule():
    e = errs(
        [{"manufacturer.x": {"cite": "ipdb:1", "description": "d"}}],
        attribution="flipcommons-ai-desc-manufacturer",
        filename="0036-manufacturer-descriptions.yaml",
    )
    assert not has(e, "an entry-level cite: is not allowed")
