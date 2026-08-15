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


def test_opdb_machine_url_cite_flagged():
    e = errs(
        [
            {
                "model.x": {
                    "note": "n",
                    "year": 1990,
                    "cite": "https://opdb.org/machines/G4q3L-MKN50",
                }
            }
        ]
    )
    assert has(e, "use the scheme:identifier form")


def test_ipdb_non_record_url_cite_clean():
    # Only a MACHINE RECORD has a scheme form. An image page (a flyer scan) is
    # an ordinary page on the site, matching no scheme URL shape — flipcommons
    # classifies it SiteOf, not SchemeRecord — so there is no ipdb:<id> to
    # rewrite it to, and demanding one would make the page uncitable.
    e = errs(
        [
            {
                "model.x": {
                    "note": "n",
                    "year": 1990,
                    "cite": "https://www.ipdb.org/showpic.pl?id=4583&picno=6433",
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


def test_quoted_cite_satisfies_note_requirement():
    # A cite carrying a verbatim quote explains the change by itself.
    e = errs(
        [
            {
                "model.x": {
                    "cite": {"ref": "ipdb:1", "quote": "never produced"},
                    "production_status": "unreleased",
                }
            }
        ]
    )
    assert not has(e, "needs a note")


def test_note_quote_scaffolding_flagged():
    e = errs(
        [
            {
                "model.x": {
                    "note": 'IPDB says "This game was never produced."',
                    "cite": "ipdb:1",
                    "year": 1970,
                }
            }
        ],
        filename="0076-x.yaml",
    )
    assert has(e, "scaffolding")


def test_note_quote_scaffolding_grandfathered_before_rule():
    e = errs(
        [
            {
                "model.x": {
                    "note": 'IPDB says "This game was never produced."',
                    "cite": "ipdb:1",
                    "year": 1970,
                }
            }
        ],
        filename="0040-x.yaml",
    )
    assert not has(e, "scaffolding")


def test_expect_obsolete_flagged():
    e = errs(
        [{"model.x": {"expect": {"ipdb_id": 6454}, "note": "n", "year": 1970}}],
        filename="0130-x.yaml",
    )
    assert has(e, "expect: is obsolete")


def test_expect_grandfathered_before_rule():
    e = errs(
        [{"model.x": {"expect": {"ipdb_id": 6454}, "note": "n", "year": 1970}}],
        filename="0129-x.yaml",
    )
    assert not has(e, "obsolete")


def test_own_data_quote_note_not_scaffolding():
    e = errs(
        [
            {
                "model.x": {
                    "note": 'The name includes "Prototype", indicating a prototype.',
                    "year": 1970,
                }
            }
        ],
        filename="0076-x.yaml",
    )
    assert not has(e, "scaffolding")


def test_quote_smart_typography_flagged():
    e = errs(
        [
            {
                "model.x": {
                    "cite": {"ref": "ipdb:1", "quote": "never “produced”"},
                    "year": 1970,
                }
            }
        ],
        filename="0076-x.yaml",
    )
    assert has(e, "cite quote contains smart typography")


def test_quote_straight_typography_clean():
    e = errs(
        [
            {
                "model.x": {
                    "cite": {"ref": "ipdb:1", "quote": 'never "produced" [...]'},
                    "year": 1970,
                }
            }
        ],
        filename="0076-x.yaml",
    )
    assert not has(e, "cite quote contains smart typography")


# --- locator hygiene (introduced at 0215) -----------------------------------
# A locator points at where the evidence sits. It is not prose about the
# document: what isn't printed on the page, and how long the document runs,
# help nobody find anything.


def locerrs(locator, filename="0215-x.yaml"):
    # The note satisfies note-required so the clean cases isolate locator rules.
    return errs(
        [
            {
                "model.x": {
                    "note": "Why.",
                    "cite": {"ref": "ipdb:1", "locator": locator},
                    "year": 1970,
                }
            }
        ],
        filename=filename,
    )


def test_locator_missing_pagination_flagged():
    e = locerrs("PDF document page 1; the sheet carries no printed folio")
    assert has(e, "cite locator")
    assert has(e, "no printed folio")


def test_locator_document_length_flagged():
    e = locerrs("PDF document page 2 of 2")
    assert has(e, "'page 2 of 2'")


def test_locator_sheet_of_n_flagged():
    # 0219 counts sheets rather than pages; same defect.
    assert has(locerrs("PDF sheet 2 of 2"), "'sheet 2 of 2'")


def test_locator_both_defects_flagged():
    # The corpus's most common locator, 23 uses, trips both rules at once.
    e = locerrs("PDF document page 2 of 2; the flyer carries no printed folios")
    assert has(e, "'page 2 of 2'")
    assert has(e, "no printed folios")


def test_locator_plain_clean():
    assert locerrs("PDF document page 1") == []
    assert locerrs("back sheet; in the PLAYFIELD FEATURES list") == []
    assert locerrs("in the manufacturer's press release reprinted in the article") == []


def test_locator_rules_grandfathered_before_0215():
    assert (
        locerrs(
            "PDF document page 1 of 1; the sheet carries no printed folio",
            filename="0214-x.yaml",
        )
        == []
    )


def test_inline_cites_locator_flagged():
    e = errs(
        [
            {
                "model.x": {
                    "description": "A game.[[cite:1]]",
                    "cites": {"1": {"ref": "ipdb:1", "locator": "page 1 of 4"}},
                }
            }
        ],
        attribution="flipcommons-ai-desc-model",
        filename="0215-x.yaml",
    )
    assert has(e, "cites['1'] locator")


def test_quoted_inline_cite_satisfies_note_requirement():
    # An inline cites: entry carrying a quote counts as the explanation, same
    # as the entry-level cite: mapping.
    e = errs(
        [
            {
                "model.x": {
                    "production_status": "unreleased",
                    "description": "Never produced.[[cite:1]]",
                    "cites": {"1": {"ref": "ipdb:1", "quote": "never produced"}},
                }
            }
        ]
    )
    assert not has(e, "needs a note")


def test_inline_quote_smart_typography_flagged():
    e = errs(
        [
            {
                "model.x": {
                    "description": "Never produced.[[cite:1]]",
                    "cites": {"1": {"ref": "ipdb:1", "quote": "never “produced”"}},
                }
            }
        ],
        filename="0076-x.yaml",
    )
    assert has(e, "cites['1'] quote contains smart typography")


def test_inline_quote_straight_typography_clean():
    e = errs(
        [
            {
                "model.x": {
                    "description": "Never produced.[[cite:1]]",
                    "cites": {
                        "1": {"ref": "ipdb:1", "quote": 'never "produced" [...]'}
                    },
                }
            }
        ],
        filename="0076-x.yaml",
    )
    assert not has(e, "quote contains smart typography")


def test_quoteless_cite_mapping_still_needs_note():
    e = errs(
        [
            {
                "model.x": {
                    "cite": {"ref": "ipdb:1"},
                    "production_status": "unreleased",
                }
            }
        ]
    )
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


# --- cite lists (multi-source evidence) --------------------------------------


def test_cite_list_quotes_get_typography_checked():
    e = errs(
        [
            {
                "model.x": {
                    "cite": [
                        {"ref": "ipdb:1", "quote": "clean quote"},
                        {"ref": "https://a.test/p", "quote": "smart “quote”"},
                    ],
                    "year": 1980,
                }
            }
        ],
        filename="0090-x.yaml",
    )
    assert has(e, "smart")


def test_cite_list_members_get_scheme_form_checked():
    e = errs(
        [
            {
                "model.x": {
                    "cite": ["https://www.ipdb.org/machine.cgi?id=4443"],
                    "year": 1980,
                }
            }
        ]
    )
    assert has(e, "scheme")


def test_cite_list_with_quote_satisfies_note_requirement():
    e = errs(
        [
            {
                "model.x": {
                    "cite": ["ipdb:1", {"ref": "ipdb:2", "quote": "never produced"}],
                    "production_status": "unreleased",
                }
            }
        ]
    )
    assert not has(e, "needs a note")


# --- prose word-choice rules (introduced at 0189) ----------------------------
# Three prose corpora: the top-level patch description:, unit note:, and the
# record description: field. Scopes differ per rule because some words have a
# legitimate physical/trade sense in record descriptions ("the cabinet's
# edges", "seeded dozens of manufacturers", "SIRMO's catalog of bingo games").


def perrs(claims, filename="0189-x.yaml"):
    return lp.lint_patch(
        filename, {"attribution": "flipcommons-catalog", "claims": claims}
    )


def note_unit(note):
    return [{"manufacturer.x": {"note": note, "name": "X"}}]


def desc_unit(description):
    return [{"manufacturer.x": {"description": description}}]


def desc_errs(text, filename="0189-x.yaml"):
    return lp.lint_patch(
        filename,
        {"attribution": "flipcommons-catalog", "description": text, "claims": []},
    )


def test_seed_in_note_flagged():
    e = perrs(note_unit("The seed derived this month from OPDB's date."))
    assert has(e, "'seed'")


def test_seed_guidance_does_not_offer_a_replacement_name():
    # The rule used to answer "say 'an earlier ingest'", and that phrase then
    # spread through the notes it was fixing. Where a prior value came from is
    # not the note's business under any name, so the guidance says cut, not
    # rename.
    e = perrs(note_unit("The seed derived this month from OPDB's date."))
    assert has(e, "'seed'")
    assert not has(e, "earlier ingest")


def test_seed_in_patch_description_flagged():
    e = desc_errs("Seed the remaining video platform roots.")
    assert has(e, "'Seed'")


def test_seed_in_record_description_allowed():
    # The horticultural/figurative sense is legitimate prose in a public
    # record description ("seeded dozens of small local manufacturers").
    e = perrs(desc_unit("Prize laws seeded dozens of small local manufacturers."))
    assert not has(e, "seed")


# --- the note's durability rules (introduced at 0215) -----------------------
# A note renders publicly and must read standalone decades on: it may name
# neither the authoring process that produced it nor what the data used to be.
# The split is by what the word names, not by what it's used to say: 'seed' and
# 'ingest' name our own pipeline, so they're process words even when the
# sentence around them is about a prior value. prose-seed is the 0189-era
# member of that family; its number is fixed, so the rest lands at 0215.
#
# The rule name isn't in the error text, so a test pins the categorization by
# asserting on the guidance the author is shown.
PROCESS_GUIDANCE = "how the patch got authored"
PRIOR_STATE_GUIDANCE = "what the data used to be"


def nerrs(note):
    return perrs(note_unit(note), filename="0215-x.yaml")


def test_user_approval_flagged():
    assert has(
        nerrs("The base model takes the maker's edition name (user-approved)."),
        "'user-approved'",
    )
    assert has(nerrs("Asserted after user approval on the rename."), "'user approval'")


def test_authoring_artifacts_flagged():
    assert has(nerrs("See the README for the full family breakdown."), "'README'")
    # Two alternatives fire here; either token names the problem.
    assert has(
        nerrs("Per the campaign README, the count follows the maker."),
        "'Per the campaign'",
    )
    assert has(
        nerrs("As discussed, the count follows the maker's own heading."),
        "'As discussed'",
    )
    assert has(
        nerrs("Flagged in review as a duplicate of the 1974 run."),
        "'Flagged in review'",
    )


def test_user_manual_clean():
    # 'user' alone is legitimate: the machine's own documentation.
    assert nerrs("The user manual lists four flippers and two ramps.") == []


def test_trade_senses_clean():
    # The words the authoring-process rule must never reach: each is normal
    # note prose about the machine or its sources.
    assert nerrs("The manual documents an operator adjustment for the diverter.") == []
    assert nerrs("A Pinside review states the ramp was rebuilt for the reissue.") == []
    assert nerrs("IPDB confirms the 1974 manufacture year.") == []
    assert nerrs("Bally's advertising campaign ran through 1974.") == []


def test_pipeline_words_are_authoring_process():
    # 'ingest' and 'seed' name our pipeline. The sentence they sit in is
    # usually about a prior value, but the word itself is process vocabulary,
    # so the author gets the process guidance, not the prior-state one.
    e = nerrs("The date arrived via an earlier ingest.")
    assert has(e, "'ingest'")
    assert has(e, PROCESS_GUIDANCE)
    assert not has(e, PRIOR_STATE_GUIDANCE)

    # prose-seed predates the split and carries its own message, so all that's
    # pinnable here is that 'seed' is not treated as a prior-state word.
    e = nerrs("The seed derived this month from OPDB's date.")
    assert has(e, "'seed'")
    assert not has(e, PRIOR_STATE_GUIDANCE)


def test_prior_state_flagged():
    e = nerrs("This supersedes the coarser Germany location.")
    assert has(e, "'supersedes'")
    assert has(e, PRIOR_STATE_GUIDANCE)

    e = nerrs("The prior value of 4 arrived uncited.")
    assert has(e, "'prior value'")
    assert has(e, PRIOR_STATE_GUIDANCE)


def test_prior_state_about_the_world_clean():
    # Prior state of the machines, not of the catalog's own field values.
    assert nerrs("An earlier machine of the same name used this cabinet.") == []
    assert nerrs("The firm's earlier games were all bingos.") == []


def test_superseded_in_record_description_clean():
    # Record descriptions are public encyclopedia prose, where one product
    # superseding another is the plain English sense.
    e = perrs(
        desc_unit("The solid-state version superseded the electromechanical run."),
        filename="0215-x.yaml",
    )
    assert not has(e, "supersed")


def test_absence_claim_flagged():
    # Present tense, asserted about the world: the next source to surface
    # falsifies it.
    assert has(
        nerrs("No source states a release year, so none is asserted."), "'No source'"
    )
    assert has(nerrs("Documented nowhere else in the pinball press."), "'nowhere'")
    assert has(nerrs("There is no evidence the machine ever shipped."), "'no evidence'")
    assert has(
        nerrs("Nothing else documents the 1974 run."), "'Nothing else documents'"
    )


def test_uniqueness_claim_flagged_in_record_description():
    # Unlike the other two durability rules, this one reaches record
    # descriptions: an ageing absolute is worse in public encyclopedia prose
    # than in a note, and descriptions are generated at volume.
    e = perrs(
        desc_unit("The only known surviving example sits in a private collection."),
        filename="0215-x.yaml",
    )
    assert has(e, "'only known'")


def test_first_person_clean():
    # The contributor's name rides the change forever, so 'I' resolves for a
    # reader where a third-party 'the user' would not.
    #
    # NB this sentence is still effort narration, which prose-search-effort
    # bans in its 'sought'/'none found' forms; the phrasing is spared only
    # because no pattern reaches it.
    assert nerrs("I was not able to find a second source for the year.") == []


def test_bounded_absolutes_clean():
    # Sourced claims about the machines, not about the state of the evidence.
    assert nerrs("The firm made no bingos after 1974.") == []
    assert nerrs("It was the first pinball to use a magnet under the playfield.") == []


def test_absence_bounded_to_a_named_source_flagged():
    # Naming the silent source does not rescue the claim: a gap in one source
    # is not evidence, and writing it up as though it were treats that source
    # as an oracle that owed us an answer. Both of these are real notes from
    # the shipped corpus, and both should have been caught before they froze.
    assert has(nerrs("OPDB has no record of the Bally Wulff build."), "'no record'")
    assert has(
        nerrs("The header graphic is one word, with Taito nowhere on the sheet."),
        "'nowhere'",
    )


def test_search_effort_flagged():
    # How hard someone looked is not evidence. The cite carries what supports
    # the value; a hunt that came up empty leaves nothing to say.
    e = nerrs("Corroborating sources were sought at authoring time and none found.")
    assert has(e, "'sought'")
    assert has(e, "'at authoring time'")
    assert has(e, "'none found'")


FILLER_GUIDANCE = "the reader already assumes now"


def test_authoring_time_is_filler_not_search_effort():
    # 'at authoring time' rides along with effort narration but is a separate
    # defect: the change is timestamped, so it dates what is already dated.
    # It fires on a sentence with no hunt in it at all.
    e = nerrs("Shipping had not begun at authoring time, so the machine is announced.")
    assert has(e, "'at authoring time'")
    assert has(e, FILLER_GUIDANCE)


def test_temporal_filler_siblings_flagged():
    assert has(nerrs("The maker's site currently expects late 2026."), "'currently'")
    assert has(nerrs("No shipping date at the moment."), "'at the moment'")
    assert has(nerrs("At this time the machine has no year."), "'At this time'")
    assert has(nerrs("Two examples are known to date."), "'to date'")


def test_historical_at_the_time_clean():
    # 'at the time' points at a moment in the past — 1934, in 0112's case —
    # which is the opposite of asserting the default frame.
    e = perrs(
        desc_unit("Gridiron football had scarcely any following in Italy at the time."),
        filename="0215-x.yaml",
    )
    assert not has(e, "at the time")


def test_still_and_today_clean():
    # Natural encyclopedia prose, not filler: deliberately out of scope.
    assert nerrs("The firm is still in business, so no end year is asserted.") == []
    assert nerrs("The company remains active today.") == []


def test_sought_after_clean():
    # The collector's-market sense, and a real record description from 0111.
    e = perrs(
        desc_unit("They became among the most sought-after games of their era."),
        filename="0215-x.yaml",
    )
    assert not has(e, "sought")
    assert nerrs("The machine is sought-after among collectors.") == []


def test_classification_rationale_flagged():
    # The note documents the author working out which of our values to use.
    # The cite's quote shows the source's own label, and the claim shows what
    # it became; the deliberation between them is not the reader's business.
    assert has(nerrs("'Lead LCD Artist' maps to the animation role."), "'maps to'")
    assert has(nerrs("Produced and sold, so it records as produced."), "'records as'")


def test_recorded_as_clean():
    # Passive 'recorded as' is mostly ordinary prose about what a source
    # documents, or real rationale for a deliberate omission — 30 distinct
    # uses in the corpus, so the rule stops at the active voice.
    assert (
        nerrs("Troubadour is not recorded as a second donor, pending a source.") == []
    )
    e = perrs(
        desc_unit("Among the last tables BEM is recorded as building."),
        filename="0215-x.yaml",
    )
    assert not has(e, "recorded as")


def test_vocabulary_in_note_flagged():
    # The reader has never heard of the credit-role vocabulary, and the quote
    # on the cite already shows the specialized role doesn't exist.
    e = nerrs("The credit vocabulary has no sculptor role; sculpting records as art.")
    assert has(e, "'vocabulary'")


def test_taxonomy_siblings_in_note_flagged():
    assert has(nerrs("Titles and models are separate namespaces."), "'namespaces'")
    assert has(nerrs("The theme taxonomy has no entry for this."), "'taxonomy'")


def test_taxonomy_siblings_flagged_in_every_corpus():
    # 'namespace' and 'taxonomy' are pure internal jargon, like node and edge:
    # no physical or trade sense anywhere, so no corpus is spared. This is what
    # separates them from 'vocabulary', which does honest work in the
    # Admin-only patch description.
    e = perrs(
        desc_unit("The theme taxonomy groups it under pirates."), filename="0215-x.yaml"
    )
    assert has(e, "'taxonomy'")
    assert has(desc_errs("Seed the theme namespace.", "0215-x.yaml"), "'namespace'")


def test_vocabulary_in_patch_description_allowed():
    # The top-level description is the Admin-only IngestRun note, which is
    # where taxonomy bookkeeping belongs — "Create the four ProductionStatus
    # vocabulary values" is an accurate summary for the one audience that has
    # the concept.
    e = desc_errs("Create the four production-status vocabulary values.", "0215-x.yaml")
    assert not has(e, "vocabulary")


def test_note_durability_rules_grandfathered_before_0215():
    assert (
        perrs(
            note_unit("Supersedes an earlier ingest (user-approved)."),
            filename="0214-x.yaml",
        )
        == []
    )


def test_rule_since_registry_has_note_durability_rules():
    for rule in ("prose-authoring-process", "prose-prior-state"):
        assert lp.RULE_SINCE[rule] == 215, rule


def test_node_in_record_description_flagged():
    e = perrs(desc_unit("This node sits under the parent theme."))
    assert has(e, "'node'")


def test_edge_in_note_flagged():
    e = perrs(note_unit("The fact now lives on the conversion kit edge."))
    assert has(e, "'edge'")


def test_edge_in_record_description_allowed():
    # Physical sense: rails run along the cabinet's edges.
    e = perrs(desc_unit("Rails run along the cabinet's edges outside the lanes."))
    assert not has(e, "'edge")


def test_snake_case_identifier_flagged():
    e = perrs(note_unit("The conversion_kit relationship duplicates the tag."))
    assert has(e, "'conversion_kit'")


def test_camelcase_internal_name_flagged():
    e = perrs(note_unit("The fact now lives on the ModelRelationship."))
    assert has(e, "'ModelRelationship'")


def test_brand_camelcase_clean():
    # CamelCase brand names are real names, not code identifiers.
    e = perrs(note_unit("Built by TiltBob and WhizBang under the MarsaPlay badge."))
    assert e == []


def test_slug_allowed():
    # Contributors edit slugs in the site's own UI — it's vocabulary they know.
    e = perrs(note_unit("Merged under the lady-luck title with the slug renamed."))
    assert e == []


def test_bare_entity_flagged():
    e = perrs(note_unit("This game is reattributed to the canonical entity."))
    assert has(e, "'entity'")


def test_corporate_entity_allowed():
    e = perrs(note_unit("The corporate entity below it keeps the full name."))
    assert not has(e, "entity")


def test_corporate_entity_markup_allowed():
    e = perrs(desc_unit("Trading as [[corporate-entity:id:449]], it built tables."))
    assert not has(e, "entity")


def test_determiner_record_flagged():
    e = perrs(note_unit("The duplicate gold-star-5 is merged into this record."))
    assert has(e, "'this record'")


def test_record_as_verb_clean():
    e = perrs(note_unit("German Wikipedia records that the firm was founded in 1950."))
    assert e == []


def test_the_catalog_flagged():
    # Self-reference: the reader can't know 'the catalog' means this site.
    e = perrs(
        note_unit("The machine had not shipped, so the catalog dates it to 2026.")
    )
    assert has(e, "'the catalog'")
    assert has(e, "name the site")


def test_named_catalog_flagged():
    # Referring to another site as "the <name> catalog" is the same referent
    # problem — name the site or its domain instead.
    e = perrs(note_unit("The eremeka catalog dates this baseball game to 1974."))
    assert has(e, "'The eremeka catalog'")
    assert has(e, "name the site")


def test_possessive_catalog_clean():
    # A maker's product line is the legitimate trade sense.
    e = perrs(
        note_unit("SIRMO Games S.A.'s catalog is entirely in-line bingo machines.")
    )
    assert e == []


def test_flipcommons_catalog_slug_clean():
    # The hyphen-joined attribution slug is not the word 'catalog'.
    e = desc_errs("Retract flipcommons-catalog's OPDB-derived bad January months.")
    assert not has(e, "catalog")


def test_bare_plural_catalogs_flagged():
    # Plural noun without determiner: the referent is clear, the register is
    # the problem — these are just sites.
    e = perrs(desc_unit("Catalogs list them beside pinball for the shared cabinet."))
    assert has(e, "'Catalogs'")
    assert has(e, "pedantic")


def test_catalogues_as_verb_flagged():
    # The verb is the same register problem, and gets the same plain-words
    # guidance — NOT the name-the-site guidance, which would misdirect the fix.
    e = perrs(
        note_unit("The pinball community catalogues these two machines as Mecatronics.")
    )
    assert has(e, "'catalogues'")
    assert has(e, "pedantic")
    assert not has(e, "name the site")


def test_pinball_record_phrase_flagged():
    e = perrs(desc_unit("It is known in the pinball record for its artwork."))
    assert has(e, "'the pinball record'")


def test_prose_rules_grandfathered_before_0189():
    e = perrs(note_unit("The seed derived this month."), filename="0188-x.yaml")
    assert e == []


def ddesc(description, filename="0239-x.yaml"):
    """A record description linted under the dating-phrase rule's own number."""
    return perrs(desc_unit(description), filename=filename)


def test_dating_superlative_flagged():
    e = ddesc("Their latest machine is a widebody with a magnet.")
    assert has(e, "'latest'")


def test_dating_newest_flagged():
    e = ddesc("The newest table in the range uses a colour display.")
    assert has(e, "'newest'")


def test_dating_most_recent_flagged():
    e = ddesc("Its most recent release returned to solid-state hardware.")
    assert has(e, "'most recent'")


def test_dating_recently_flagged():
    e = ddesc("The firm recently returned to making flipper games.")
    assert has(e, "'recently'")


def test_dating_upcoming_flagged():
    e = ddesc("An upcoming machine will use the same platform.")
    assert has(e, "'upcoming'")


def test_dating_sole_output_flagged():
    e = ddesc("Its only machine was a two-player woodrail.")
    assert has(e, "'Its only machine'")


def test_dating_sole_output_needs_the_possessive():
    # "the only machine on the line" is a fact about a factory, not a count of
    # a maker's output — the possessive is what makes it the dating shape.
    e = ddesc("The only machine on the line that year used a rubber belt.")
    assert not has(e, "dates the prose")


def test_dating_still_clean():
    # 'still' and 'today' read as ordinary prose and are the settled wording in
    # shipped descriptions ("It is still an active company", "it survives in
    # Turin today"); flagging them would fire on 10 correct passages.
    e = ddesc("It is still an active company, and survives in Turin today.")
    assert not has(e, "dates the prose")


def test_dating_a_named_year_clean():
    # Naming the date is the fix the guidance asks for, not a violation.
    e = ddesc("As of 2019 the firm had built eleven machines.")
    assert not has(e, "dates the prose")


def test_dating_phrase_not_flagged_in_notes():
    # Scoped to public record descriptions: the note corpus has its own
    # temporal rule, and 'latest' in a note is authoring context.
    e = perrs(note_unit("Their latest machine is a widebody."), filename="0239-x.yaml")
    assert not has(e, "dates the prose")


def test_dating_phrase_grandfathered_before_0239():
    e = ddesc("Their latest machine is a widebody.", filename="0238-x.yaml")
    assert not has(e, "dates the prose")


def test_repeat_link_flagged():
    e = ddesc("[[manufacturer:bally]] built it, and [[manufacturer:bally]] sold it.")
    assert has(e, "'manufacturer:bally'")


def test_repeat_link_reported_once_per_target():
    e = ddesc(
        "[[manufacturer:bally]] built it, [[manufacturer:bally]] sold it, "
        "and [[manufacturer:bally]] serviced it."
    )
    assert len([x for x in e if "link the first mention" in x]) == 1


def test_repeat_link_cite_markers_not_counted():
    # A handle is meant to be referenced from several markers.
    e = ddesc("A machine.[[cite:1]] Built in Chicago.[[cite:1]]")
    assert not has(e, "link the first mention")


def test_repeat_link_distinct_targets_clean():
    e = ddesc("[[manufacturer:bally]] and [[manufacturer:williams]] both built one.")
    assert not has(e, "link the first mention")


def test_repeat_link_same_slug_different_type_clean():
    # A title and a model sharing a slug are different records.
    e = ddesc("*[[title:cosmic]]* covers the build *[[model:cosmic]]*.")
    assert not has(e, "link the first mention")


def test_repeat_link_not_flagged_in_notes():
    # Scoped to public record descriptions; a note is not encyclopedia prose.
    e = perrs(
        note_unit("[[manufacturer:bally]] and [[manufacturer:bally]] again."),
        filename="0239-x.yaml",
    )
    assert not has(e, "link the first mention")


def test_repeat_link_grandfathered_before_0239():
    e = ddesc(
        "[[manufacturer:bally]] built it, and [[manufacturer:bally]] sold it.",
        filename="0238-x.yaml",
    )
    assert not has(e, "link the first mention")


def test_rule_since_registry_has_prose_rules():
    for rule in (
        "prose-seed",
        "prose-node",
        "prose-edge",
        "prose-code-identifier",
        "prose-bare-entity",
        "prose-the-record",
        "prose-the-catalog",
        "prose-catalogs",
        "prose-pinball-record",
    ):
        assert lp.RULE_SINCE[rule] == 189, rule


def test_ignore_grandfather_runs_rules_on_old_patches():
    # The review escape hatch: lint an old patch as if every rule applied.
    data = {
        "attribution": "flipcommons-catalog",
        "claims": note_unit("The seed derived this month."),
    }
    assert not lp.lint_patch("0002-x.yaml", data)
    e = lp.lint_patch("0002-x.yaml", data, ignore_grandfather=True)
    assert has(e, "'seed'")


# --- grouping gameplay-feature nodes are never attached to models -----------


def test_grouping_feature_attach_flagged():
    e = errs(
        [
            {
                "model.some-machine": {
                    "note": "why",
                    "gameplay_feature": ["toys", "flippers"],
                }
            }
        ],
        filename="0220-x.yaml",
    )
    assert has(e, "grouping node")
    assert has(e, "'toys'")


def test_grouping_feature_counted_member_flagged():
    e = errs(
        [
            {
                "model.some-machine": {
                    "note": "why",
                    "gameplay_feature": [{"interactive-toys": 2}],
                }
            }
        ],
        filename="0220-x.yaml",
    )
    assert has(e, "grouping node")


def test_grouping_feature_leaf_attach_clean():
    e = errs(
        [
            {
                "model.some-machine": {
                    "note": "why",
                    "gameplay_feature": ["bash-toys", {"flippers": 3}],
                }
            }
        ],
        filename="0220-x.yaml",
    )
    assert not has(e, "grouping node")


def test_grouping_feature_parent_reference_clean():
    # Parenting a new node under a grouping node is the tree's whole point;
    # only model attaches are barred.
    e = errs(
        [
            {
                "gameplay-feature.pop-up-toys": {
                    "create": True,
                    "name": "Pop-Up Toys",
                    "gameplay_feature_parent": ["interactive-toys"],
                }
            }
        ],
        filename="0220-x.yaml",
    )
    assert not has(e, "grouping node")


def test_grouping_feature_grandfathered_before_0219():
    e = errs(
        [
            {
                "model.some-machine": {
                    "note": "why",
                    "gameplay_feature": ["toys"],
                }
            }
        ],
        filename="0100-x.yaml",
    )
    assert not has(e, "grouping node")
