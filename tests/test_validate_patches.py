"""Tests for scripts/patch_validation/validate_patches.py.

Covers the structural patch gate run by ``make validate``: the strict YAML
loader (JSON-shaped values only) and the JSON-schema structural checks.
"""

from __future__ import annotations

import json

import patch_validation.validate_patches as vp
import pytest
import yaml
from jsonschema import Draft7Validator


def _load(doc: str):
    return yaml.load(doc, Loader=vp._StrictLoader)


# --- Strict loader: JSON-shaped implicit coercion ---------------------------


@pytest.mark.parametrize(
    ("doc", "key", "expected"),
    [
        ("a: 1990", "a", 1990),  # int stays int
        ("a: 3.14", "a", 3.14),  # finite float stays float
        ("a: true", "a", True),  # JSON bool
        ("a: null", "a", None),  # JSON null
        ("a: no", "a", "no"),  # YAML 1.1 bool -> string (JSON has no `no`)
        ("a: yes", "a", "yes"),
        ("a: 1996-01-01", "a", "1996-01-01"),  # bare date -> string
    ],
)
def test_implicit_coercion_is_json_shaped(doc, key, expected):
    assert _load(doc)[key] == expected


# --- Strict loader: explicit non-JSON tags are rejected ---------------------


@pytest.mark.parametrize(
    "doc",
    [
        "a: !!timestamp 2020-01-01",
        "a: !!float .nan",
        "a: !!float .inf",
        "a: !!float -.inf",
        "a: !!set {x, y}",
        "a: !!binary aGk=",
        "a: !!omap [{x: 1}]",
        "a: !!pairs [{x: 1}]",
    ],
)
def test_explicit_non_json_tags_rejected(doc):
    with pytest.raises(yaml.YAMLError):
        _load(doc)


def test_duplicate_keys_rejected():
    with pytest.raises(yaml.YAMLError):
        _load("a: 1\na: 2")


@pytest.mark.parametrize(
    "doc",
    [
        "1: foo",  # bare integer key (e.g. an unquoted cites handle)
        "true: foo",  # bool key
        "null: foo",  # null key
        "3.14: foo",  # float key
    ],
)
def test_non_string_mapping_keys_rejected(doc):
    # JSON object keys are always strings; a non-string key is non-JSON-shaped.
    # Notably this is the unquoted `1:` cites handle the patch format forbids.
    with pytest.raises(yaml.YAMLError):
        _load(doc)


# --- Schema: create + retract are mutually exclusive ------------------------


@pytest.fixture(scope="module")
def schema_validator():
    schema = json.loads(vp.SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft7Validator(schema)


def _has_error(validator, data) -> bool:
    return bool(list(validator.iter_errors(data)))


def test_create_and_retract_together_rejected(schema_validator):
    data = {
        "attribution": "ipdb",
        "claims": [{"manufacturer.foo": {"create": True, "retract": ["manufacturer"]}}],
    }
    assert _has_error(schema_validator, data)


def test_create_only_is_valid(schema_validator):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"manufacturer.foo": {"name": "Foo", "create": True}}],
    }
    assert not _has_error(schema_validator, data)


def test_retract_only_is_valid(schema_validator):
    data = {
        "attribution": "ipdb",
        "claims": [{"corporate-entity.foo": {"retract": ["manufacturer"]}}],
    }
    assert not _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "body",
    [
        # create is exclusive with delete and the edit-only directives.
        {"create": True, "delete": True},
        {"create": True, "remove": {"location": ["germany"]}, "name": "Foo"},
        # delete is footprint-exclusive — no retract/remove companions.
        {"delete": True, "retract": ["year"]},
        {"delete": True, "remove": {"location": ["germany"]}},
    ],
)
def test_illegal_directive_combinations_rejected(schema_validator, body):
    data = {"attribution": "ipdb", "claims": [{"model.foo": body}]}
    assert _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "body",
    [
        # delete carries provenance, plus a still-permitted (ignored) expect.
        {"delete": True, "expect": {"year": 1990}},
        {"delete": True, "note": "dup", "cite": "ipdb:4443"},
        # create carries fields and provenance, just not the edit-only directives.
        {"create": True, "name": "Foo", "note": "new", "cite": "ipdb:4443"},
        # the obsolete expect is still permitted anywhere, including on a create.
        {"create": True, "name": "Foo", "expect": {"year": 1990}},
    ],
)
def test_legal_directive_combinations_accepted(schema_validator, body):
    data = {"attribution": "ipdb", "claims": [{"model.foo": body}]}
    assert not _has_error(schema_validator, data)


# --- Schema: entity-reference key pattern -----------------------------------


@pytest.mark.parametrize(
    "ref",
    [
        "model.mazatron",  # slug
        "corporate-entity.western-products-incorporated",  # hyphenated type + slug
        "location.usa/il/chicago",  # location_path public-id
    ],
)
def test_valid_entity_refs_accepted(schema_validator, ref):
    data = {"attribution": "ipdb", "claims": [{ref: {"year": 1990}}]}
    assert not _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "ref",
    [
        "model.foo bar",  # space in public-id
        "manufacturer.Foo",  # uppercase in public-id
        "Model.foo",  # uppercase in type
        "model.",  # empty public-id
        "model.foo.bar",  # stray dot in public-id
        "modelfoo",  # no dot at all
    ],
)
def test_malformed_entity_refs_rejected(schema_validator, ref):
    data = {"attribution": "ipdb", "claims": [{ref: {"year": 1990}}]}
    assert _has_error(schema_validator, data)


# --- Schema: cite accepts scheme:identifier and http(s) URL -----------------


@pytest.mark.parametrize(
    "cite",
    [
        "ipdb:4443",
        "opdb:GRhX5",
        "https://en.wikipedia.org/wiki/Bally_Manufacturing",
        "http://example.com/a",
    ],
)
def test_cite_forms_accepted(schema_validator, cite):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"corporate-entity.foo": {"year_start": 1990, "cite": cite}}],
    }
    assert not _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "cite",
    [
        "ipdb",  # scheme without identifier
        "ftp://example.com",  # scheme://… is a URL shape, and only http(s) is legal
        "just some text",  # neither form
    ],
)
def test_malformed_cite_rejected(schema_validator, cite):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"corporate-entity.foo": {"year_start": 1990, "cite": cite}}],
    }
    assert _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "cite",
    [
        "billboard:1945-09-29",  # ISO-dated issue (also schemeIdentifier-shaped)
        "gameroom-magazine:vol-2",  # hyphenated left segment — the slug-only shape
    ],
)
def test_authored_source_cite_forms_accepted(schema_validator, cite):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"corporate-entity.foo": {"year_start": 1990, "cite": cite}}],
    }
    assert not _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "cite",
    [
        "Billboard:1945-09-29",  # uppercase — not the slug grammar
        "billboard:",  # empty child segment
        # Over-long segments in both spellings: hyphenated (only
        # authoredSourceRef could match) and plain (schemeIdentifier's prefix
        # is capped at the identifier_key column's 50, so it can't leak these
        # through the anyOf either).
        f"{'a-' * 100}a:vol-2",  # 201-char hyphenated root segment
        f"{'a' * 201}:vol-2",  # 201-char plain root segment
        f"billboard:{'a-' * 100}a",  # 201-char hyphenated child segment
        f"billboard:{'a' * 201}",  # 201-char plain child segment
        # A >50-char root with a NON-slug right segment matches neither form:
        # too long for a scheme key, not slug-shaped for an authored ref.
        f"{'a' * 60}:GRhX5",
        # NOT here: billboard:1945_09_29 and other bad-right-segment shapes
        # under a short root — schemeIdentifier deliberately shape-accepts any
        # plausible-key:free-form pair (the scheme list lives in the
        # flipcommons registry), so those pass local validation and fail at
        # ingest.
    ],
)
def test_malformed_authored_source_cite_rejected(schema_validator, cite):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"corporate-entity.foo": {"year_start": 1990, "cite": cite}}],
    }
    assert _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "cite",
    [
        "isbn:9781889933023",  # 13-digit
        "isbn:978-1-889933-02-3",  # hyphenated
        "isbn:0887404316",  # 10-digit
        "isbn:080442957X",  # 10-digit with an X check digit
    ],
)
def test_isbn_cite_forms_accepted(schema_validator, cite):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"corporate-entity.foo": {"year_start": 1990, "cite": cite}}],
    }
    assert not _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "cite",
    [
        "isbn:97818899330",  # too few digits
        "isbn:97818899330231",  # too many digits
        "isbn:not-an-isbn",  # not digits at all
        "isbn:",  # empty
    ],
)
def test_malformed_isbn_cite_rejected(schema_validator, cite):
    # The isbn form is shape-checked here (unlike a scheme identifier, whose
    # grammar lives in the flipcommons registry); the check digit itself is
    # ingest_patches' job.
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"corporate-entity.foo": {"year_start": 1990, "cite": cite}}],
    }
    assert _has_error(schema_validator, data)


def test_isbn_cite_with_locator_accepted(schema_validator):
    # The driving shape: the proximate source quotes, the book locates.
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [
            {
                "corporate-entity.foo": {
                    "year_start": 1990,
                    "cite": [
                        {"ref": "ipdb:3905", "quote": "According to the Encyclopedia"},
                        {"ref": "isbn:9781889933023", "locator": "Vol. 2, p. 107"},
                    ],
                }
            }
        ],
    }
    assert not _has_error(schema_validator, data)


def test_unknown_scheme_accepted_structurally(schema_validator):
    # Deliberate: the schema doesn't enumerate scheme prefixes (the
    # authoritative list lives in the flipcommons registry and drifts), so an
    # unknown scheme passes this structural pre-check and is rejected by
    # ingest_patches, which validates the actual key.
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [
            {"corporate-entity.foo": {"year_start": 1990, "cite": "bogus:4443"}}
        ],
    }
    assert not _has_error(schema_validator, data)


# --- Schema: cites inline-citation map --------------------------------------


def test_cites_map_forms_accepted(schema_validator):
    data = {
        "attribution": "flipcommons-ai-desc-model",
        "claims": [
            {
                "model.foo": {
                    "description": "A.[[cite:1]] B.[[cite:2]] C.[[cite:3]]",
                    "cites": {
                        "1": "ipdb:4443",
                        "2": "https://example.com/a",
                        "3": {
                            "ref": "https://example.com/b",
                            "archive": "https://web.archive.org/x",
                        },
                    },
                }
            }
        ],
    }
    assert not _has_error(schema_validator, data)


def test_cites_url_only_map_accepted(schema_validator):
    # The { ref } map with no archive is the common map form.
    data = {
        "attribution": "flipcommons-ai-desc-model",
        "claims": [
            {
                "model.foo": {
                    "description": "x[[cite:1]]",
                    "cites": {"1": {"ref": "https://example.com/a"}},
                }
            }
        ],
    }
    assert not _has_error(schema_validator, data)


def test_existing_slug_markers_need_no_cites(schema_validator):
    # The rehydrated re-edit shape: markers carry durable slugs, no cites map.
    data = {
        "attribution": "flipcommons-ai-desc-model",
        "claims": [
            {"model.foo": {"description": "A.[[cite:bqntvkrs]] B.[[cite:mwzfprhd]]"}}
        ],
    }
    assert not _has_error(schema_validator, data)


def test_entry_cite_mapping_with_locator_and_quote_accepted(schema_validator):
    # The entry-level cite: mapping widens the scalar ref with instance fields.
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [
            {
                "model.foo": {
                    "year": 1990,
                    "cite": {
                        "ref": "ipdb:4443",
                        "locator": "Notes section",
                        "quote": "This game was never produced.",
                    },
                }
            }
        ],
    }
    assert not _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "cite",
    [
        {"quote": "no ref"},  # mapping missing ref
        {"ref": "ipdb:4443", "bogus": 1},  # unknown key
        {"ref": "ipdb:4443", "quote": "x" * 2001},  # overlong quote
        {"ref": "ipdb:4443", "locator": "x" * 201},  # overlong locator
    ],
)
def test_malformed_entry_cite_mapping_rejected(schema_validator, cite):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"model.foo": {"year": 1990, "cite": cite}}],
    }
    assert _has_error(schema_validator, data)


def test_inline_cites_quote_and_locator_accepted(schema_validator):
    # Inline footnotes carry the same optional locator/quote as the entry cite.
    data = {
        "attribution": "flipcommons-ai-desc-model",
        "claims": [
            {
                "model.foo": {
                    "description": "x[[cite:1]]",
                    "cites": {
                        "1": {
                            "ref": "https://example.com/a",
                            "locator": "Notes section",
                            "quote": "Only two are known to survive.",
                        }
                    },
                }
            }
        ],
    }
    assert not _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "spec",
    [
        {"quote": "no ref"},  # mapping missing ref
        {"ref": "ipdb:4443", "bogus": 1},  # unknown key
        {"ref": "ipdb:4443", "quote": "x" * 2001},  # overlong quote
        {"ref": "ipdb:4443", "locator": "x" * 201},  # overlong locator
    ],
)
def test_malformed_inline_cites_mapping_rejected(schema_validator, spec):
    data = {
        "attribution": "flipcommons-ai-desc-model",
        "claims": [{"model.foo": {"description": "x[[cite:1]]", "cites": {"1": spec}}}],
    }
    assert _has_error(schema_validator, data)


def test_cite_and_cites_coexist(schema_validator):
    # A field-level cite: and inline cites: may ride the same entry.
    data = {
        "attribution": "flipcommons-ai-desc-model",
        "claims": [
            {
                "model.foo": {
                    "year": 1990,
                    "description": "x[[cite:1]]",
                    "cite": "ipdb:4443",
                    "cites": {"1": "https://example.com/a"},
                }
            }
        ],
    }
    assert not _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "cites",
    [
        {"1": "just text"},  # value neither scheme:id nor URL
        {"1": "ftp://example.com"},  # scheme://… is a URL shape, only http(s) legal
        {"abc": "ipdb:4443"},  # non-numeric handle
        {"1": {"archive": "https://web.archive.org/x"}},  # map missing ref
        {"1": {"ref": "https://x/", "bogus": 1}},  # unknown key in map
        {"1": {"ref": "ftp://x/"}},  # map ref not http(s)
        {},  # empty map
    ],
)
def test_malformed_cites_rejected(schema_validator, cites):
    data = {
        "attribution": "flipcommons-ai-desc-model",
        "claims": [{"model.foo": {"description": "x[[cite:1]]", "cites": cites}}],
    }
    assert _has_error(schema_validator, data)


# --- Schema: the sources: block ---------------------------------------------


def test_sources_only_patch_is_valid(schema_validator):
    data = {
        "attribution": "flipcommons-catalog",
        "sources": [
            {
                "name": "Wikipedia",
                "source_type": "web",
                "description": "Free encyclopedia.",
                "links": [
                    {"url": "https://en.wikipedia.org/", "link_type": "homepage"}
                ],
            }
        ],
    }
    assert not _has_error(schema_validator, data)


def test_patch_without_claims_or_sources_rejected(schema_validator):
    # Neither block, and an empty sources block, are both rejected.
    assert _has_error(schema_validator, {"attribution": "ipdb"})
    assert _has_error(schema_validator, {"attribution": "ipdb", "sources": []})


@pytest.mark.parametrize(
    "source",
    [
        {"source_type": "web"},  # missing name
        {"name": "X"},  # missing source_type
        {"name": "X", "source_type": "blog"},  # source_type not in enum
        {"name": "X", "source_type": "web", "bogus": 1},  # unknown key
        {  # nested children unsupported (v1 sources are flat)
            "name": "X",
            "source_type": "web",
            "children": [{"name": "Y", "source_type": "web"}],
        },
        {  # link_type not in enum
            "name": "X",
            "source_type": "web",
            "links": [{"url": "https://x/", "link_type": "bogus"}],
        },
        {  # link missing url
            "name": "X",
            "source_type": "web",
            "links": [{"link_type": "homepage"}],
        },
        {  # slug not in the slug grammar
            "name": "X",
            "source_type": "magazine",
            "slug": "Game_Room",
        },
        {  # slug past the 200-char column limit
            "name": "X",
            "source_type": "magazine",
            "slug": "a" * 201,
        },
        {  # parent past the 200-char column limit
            "name": "X",
            "source_type": "magazine",
            "slug": "x",
            "parent": "a" * 201,
        },
    ],
)
def test_malformed_source_rejected(schema_validator, source):
    data = {"attribution": "flipcommons-catalog", "sources": [source]}
    assert _has_error(schema_validator, data)


def test_magazine_issue_sources_valid(schema_validator):
    # The slug/parent verbs: a magazine root plus an issue nested by parent:.
    data = {
        "attribution": "flipcommons-catalog",
        "sources": [
            {"slug": "billboard", "name": "Billboard", "source_type": "magazine"},
            {
                "parent": "billboard",
                "slug": "1945-09-29",
                "name": "September 29, 1945",
                "source_type": "magazine",
                "year": 1945,
                "month": 9,
                "day": 29,
                "links": [
                    {
                        "url": "https://books.google.com/books?id=x",
                        "link_type": "archive",
                    }
                ],
            },
        ],
    }
    assert not _has_error(schema_validator, data)


# --- Schema: delete / remove directives -------------------------------------


def test_delete_and_remove_directives_valid(schema_validator):
    data = {
        "attribution": "flip-museum",
        "claims": [
            {"model.foo": {"delete": True}},
            {"corporate-entity.bar": {"remove": {"location": ["germany"]}}},
        ],
    }
    assert not _has_error(schema_validator, data)


def test_remove_credit_dict_member_valid(schema_validator):
    # Multi-key relationships (credit = person + role) remove via a one-key
    # 'person: role' mapping, alongside bare-string members for FK/alias namespaces.
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [
            {
                "model.medieval-madness": {
                    "remove": {"credit": [{"john-youssi": "art"}]}
                }
            },
            {
                "series.world-cup-soccer": {
                    "remove": {"credit": [{"pat-lawlor": "design"}]}
                }
            },
        ],
    }
    assert not _has_error(schema_validator, data)


def test_remove_empty_mapping_member_valid(schema_validator):
    # The empty mapping is the identity of a row whose every target slot is
    # absent — the `export_market` unknown-market row (flipcommons'
    # DataPatches.md -> Export editions and markets). It is the ONLY way to
    # remove that row, so the schema must not require a non-empty member.
    # Namespaces where `{}` is meaningless (credit's one-key person: role form)
    # reject it in ingest_patches, which is where that semantics lives.
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"model.dragon": {"remove": {"export_market": [{}]}}}],
    }
    assert not _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "member",
    [
        {"john-youssi": "art", "brian-eddy": "design"},  # >1 key
        {"john-youssi": ["art"]},  # non-string value
    ],
)
def test_remove_malformed_credit_member_rejected(schema_validator, member):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"model.foo": {"remove": {"credit": [member]}}}],
    }
    assert _has_error(schema_validator, data)


# --- Schema: grouped changesets: form ---------------------------------------


def test_grouped_pure_wrapper_valid(schema_validator):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [
            {
                "model.foo": {
                    "expect": {"ipdb_id": 4443},
                    "changesets": [
                        {"note": "first", "cite": "ipdb:4443", "year": 1970},
                        {"note": "second", "production_status": "unreleased"},
                    ],
                }
            }
        ],
    }
    assert not _has_error(schema_validator, data)


def test_grouped_create_header_plus_companions_valid(schema_validator):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [
            {
                "manufacturer.western-products": {
                    "create": True,
                    "name": "Western Products",
                    "changesets": [
                        {
                            "website": "https://westernproducts.example",
                            "cite": "ipdb:1234",
                        }
                    ],
                }
            }
        ],
    }
    assert not _has_error(schema_validator, data)


def test_delete_with_changesets_rejected(schema_validator):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"model.foo": {"delete": True, "changesets": [{"note": "orphan"}]}}],
    }
    assert _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "item",
    [
        {"create": True},
        {"delete": True},
        {"changesets": [{"note": "nested"}]},
    ],
)
def test_grouped_item_header_only_key_rejected(schema_validator, item):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"model.foo": {"changesets": [item]}}],
    }
    assert _has_error(schema_validator, data)


@pytest.mark.parametrize("changesets", [[], "not-a-list"])
def test_grouped_empty_or_nonlist_changesets_rejected(schema_validator, changesets):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"model.foo": {"expect": {"year": 1990}, "changesets": changesets}}],
    }
    assert _has_error(schema_validator, data)


@pytest.mark.parametrize(
    "item",
    [
        {"cite": "not-a-valid-cite", "year": 1970},
        {"cites": {"1": "not-a-valid-cite"}, "year": 1970},
        {"retract": "year"},
        {"remove": {"location": "germany"}},
    ],
)
def test_grouped_item_reuses_shared_subschemas(schema_validator, item):
    # The note/cite/cites/retract/remove sub-schemas are shared with the header
    # via $ref; a changeset item must enforce them, not silently accept garbage.
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"model.foo": {"expect": {"year": 1990}, "changesets": [item]}}],
    }
    assert _has_error(schema_validator, data)


# --- The shipped patches validate cleanly ----------------------------------


def test_shipped_patches_pass(schema_validator):
    for path in sorted(vp.PATCHES_DIR.glob("*.yaml")):
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=vp._StrictLoader)
        errors = list(schema_validator.iter_errors(data))
        assert not errors, f"{path.name}: {[e.message for e in errors]}"
