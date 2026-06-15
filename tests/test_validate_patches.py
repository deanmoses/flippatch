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
        # create is exclusive with delete and the edit-only guards.
        {"create": True, "delete": True},
        {"create": True, "expect": {"year": 1990}, "name": "Foo"},
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
        # delete keeps its drift guard and provenance.
        {"delete": True, "expect": {"year": 1990}},
        {"delete": True, "note": "dup", "cite": "ipdb:4443"},
        # create carries fields and provenance, just not the edit-only guards.
        {"create": True, "name": "Foo", "note": "new", "cite": "ipdb:4443"},
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
        "bogus:4443",  # unknown scheme
        "ftp://example.com",  # non-http(s) URL
        "just some text",  # neither form
    ],
)
def test_malformed_cite_rejected(schema_validator, cite):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"corporate-entity.foo": {"year_start": 1990, "cite": cite}}],
    }
    assert _has_error(schema_validator, data)


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
                            "url": "https://example.com/b",
                            "archive": "https://web.archive.org/x",
                        },
                    },
                }
            }
        ],
    }
    assert not _has_error(schema_validator, data)


def test_cites_url_only_map_accepted(schema_validator):
    # The { url } map with no archive is the common map form.
    data = {
        "attribution": "flipcommons-ai-desc-model",
        "claims": [
            {
                "model.foo": {
                    "description": "x[[cite:1]]",
                    "cites": {"1": {"url": "https://example.com/a"}},
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
        {"1": "ftp://example.com"},  # non-http(s) URL
        {"1": "bogus:4443"},  # unknown scheme
        {"abc": "ipdb:4443"},  # non-numeric handle
        {"1": {"archive": "https://web.archive.org/x"}},  # map missing url
        {"1": {"url": "https://x/", "bogus": 1}},  # unknown key in map
        {"1": {"url": "ftp://x/"}},  # map url not http(s)
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
    ],
)
def test_malformed_source_rejected(schema_validator, source):
    data = {"attribution": "flipcommons-catalog", "sources": [source]}
    assert _has_error(schema_validator, data)


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
        {"expect": {"year": 1990}},
        {"changesets": [{"note": "nested"}]},
    ],
)
def test_grouped_item_header_only_key_rejected(schema_validator, item):
    data = {
        "attribution": "flipcommons-catalog",
        "claims": [{"model.foo": {"expect": {"year": 1990}, "changesets": [item]}}],
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
