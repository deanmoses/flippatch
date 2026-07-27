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


def test_seed_in_patch_description_flagged():
    e = desc_errs("Seed the remaining video platform roots.")
    assert has(e, "'Seed'")


def test_seed_in_record_description_allowed():
    # The horticultural/figurative sense is legitimate prose in a public
    # record description ("seeded dozens of small local manufacturers").
    e = perrs(desc_unit("Prize laws seeded dozens of small local manufacturers."))
    assert not has(e, "seed")


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


def test_link_density_flagged():
    links = " ".join(f"[[theme:id:{i}]]" for i in range(9))
    e = perrs(desc_unit(f"A machine of many themes: {links}."))
    assert has(e, "cross-reference links")


def test_link_density_cite_links_not_counted():
    body = " ".join(f"[[cite:{i}]]" for i in range(12))
    e = perrs(desc_unit(f"A well-footnoted machine. {body}"))
    assert not has(e, "cross-reference links")


def test_link_density_at_limit_clean():
    links = " ".join(f"[[theme:id:{i}]]" for i in range(8))
    e = perrs(desc_unit(f"A machine of many themes: {links}."))
    assert not has(e, "cross-reference links")


def test_prose_rules_grandfathered_before_0189():
    e = perrs(note_unit("The seed derived this month."), filename="0188-x.yaml")
    assert e == []


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
        "description-link-density",
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
