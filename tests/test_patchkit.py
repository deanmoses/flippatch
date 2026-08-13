"""Tests for patchkit — the shared patch-authoring helpers.

patchkit lives at scripts/patchkit.py and is on the pytest pythonpath via
pyproject (`pythonpath = ["scripts"]`). Its whole purpose is to centralize the
escaping / guard / emission logic that kept being re-derived (subtly wrong) in each
authoring session, so it earns real coverage. These tests are the authoritative
checks; the module's __main__ block is now just a runnable demo.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import patchkit
import pytest
import yaml
from patchkit import (
    _check_cites,
    _cite_spec_flow,
    _scalar,
    check_resolved,
    clean_ipdb_quote,
    clean_text,
    entry,
    read_view,
    render_patch,
    sentence_with,
    sentences,
    source_root,
    write_patch,
    yamlq,
)

# --------------------------------------------------------------------------- #
# text / escaping                                                             #
# --------------------------------------------------------------------------- #


def test_yamlq_prefers_double_quotes() -> None:
    """Prettier's default quote style: double, apostrophes need no escaping."""
    assert yamlq("plain") == '"plain"'
    assert yamlq("a'b") == '"a\'b"'


@pytest.mark.parametrize(
    "raw",
    [
        "plain",
        "it's",
        'says "x"',
        'both "x" and it\'s',
        "back\\slash",
        "\\n not a newline",
        "\\u00e9 not an e-acute",
        "tab\tchar",
        "trailing space ",
        "404",
        "ipdb:4443",
        "# not a comment",
    ],
)
def test_yamlq_round_trips_the_exact_string(raw: str) -> None:
    """Whichever quote style is chosen, the value must survive unchanged — a
    double-quoted YAML scalar interprets backslash escapes, which is exactly why
    anything containing a backslash falls back to single quotes."""
    assert yaml.safe_load("v: " + yamlq(raw)) == {"v": raw}


def test_yamlq_falls_back_to_single_quotes_when_double_would_escape() -> None:
    """A `"` or `\\` would need backslash-escaping in a double-quoted scalar, so
    Prettier switches the whole scalar to single quotes (doubling apostrophes)."""
    assert yamlq('says "x"') == "'says \"x\"'"
    assert yamlq('it\'s a "x"') == "'it''s a \"x\"'"
    assert yamlq("back\\slash") == "'back\\slash'"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("“flasher” — ok", '"flasher" - ok'),  # smart quotes + em dash normalized
        ("Günter Wulff — gegründet", "Günter Wulff - gegründet"),  # keeps umlauts
        ("bad�char", "badchar"),  # drops only the U+FFFD mojibake
        ("a…b", "a...b"),  # ellipsis
    ],
)
def test_clean_text(raw: str, expected: str) -> None:
    assert clean_text(raw) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, "true"),  # bool before int (bool is an int subclass)
        (False, "false"),
        (5, "5"),
        (3.5, "3.5"),
        ("simple", "simple"),  # safe bare scalar
        ("with space", "with space"),
        ("404", '"404"'),  # numeric-looking string stays quoted
        ("true", '"true"'),  # bool-looking string stays quoted
        ("ipdb:4443", '"ipdb:4443"'),  # colon forces quoting
    ],
)
def test_scalar(value: object, expected: str) -> None:
    assert _scalar(value) == expected


# --------------------------------------------------------------------------- #
# source-text extraction                                                       #
# --------------------------------------------------------------------------- #


def test_sentences_splits_on_terminal_punctuation() -> None:
    assert sentences("One. Two? Three!") == ["One.", "Two?", "Three!"]
    assert sentences("Has\nnewlines\r\nhere.") == ["Has newlines here."]


def test_sentence_with_finds_first_case_insensitive() -> None:
    assert sentence_with("Foo bar. Baz qux.", "baz") == "Baz qux."
    assert sentence_with("Foo bar.", "nope") == ""


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "6022 / 1946 / 1 Player This is a bagatelle.",
            "This is a bagatelle.",
        ),  # strips IPDB header
        ("“Plain” quote.", '"Plain" quote.'),  # normalizes typography
        (
            'The backglass translates as follows: "Win a prize."',
            "Win a prize.",
        ),  # drops framing intro
    ],
)
def test_clean_ipdb_quote(raw: str, expected: str) -> None:
    assert clean_ipdb_quote(raw) == expected


def test_clean_ipdb_quote_marks_truncation() -> None:
    limit = 20
    out = clean_ipdb_quote("a " * 200, limit=limit)
    assert out.endswith(" [...]")
    assert len(out) <= limit + len(
        " [...]"
    )  # trimmed to the limit, plus the omission marker


# --------------------------------------------------------------------------- #
# resolution                                                                   #
# --------------------------------------------------------------------------- #


def test_check_resolved() -> None:
    check_resolved(["a", "b"], ["a", "b", "c"])  # all present → no raise
    with pytest.raises(SystemExit, match="UNRESOLVED"):
        check_resolved(["a", "missing"], ["a"])


# --------------------------------------------------------------------------- #
# entry() emission                                                             #
# --------------------------------------------------------------------------- #


def test_entry_assert_block() -> None:
    e = entry(
        "model.mazatron",
        cite={"ref": "ipdb:4443", "quote": 'exists only as a "prototype" machine'},
        fields={"production_status": "unreleased"},
        tags=["prototype"],
    )
    assert "- model.mazatron:" in e
    assert 'ref: "ipdb:4443"' in e
    assert """quote: 'exists only as a "prototype" machine'""" in e
    assert "production_status: unreleased" in e
    assert "tag: [prototype]" in e


def test_entry_create_block() -> None:
    v = entry(
        "game-format.slot-machine",
        create=True,
        fields={"name": "Slot Machine", "display_order": 5},
        description="Coin-operated   gambling machines.",
    )
    assert "create: true" in v
    assert "description: >" in v
    assert "Coin-operated gambling machines." in v  # whitespace collapsed by the fold


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        (
            {"game_format": "404"},
            'game_format: "404"',
        ),  # numeric-looking string stays a string
        ({"v": "true"}, 'v: "true"'),  # bool-looking string stays a string
    ],
)
def test_entry_quotes_json_literal_strings(
    fields: dict[str, object], expected: str
) -> None:
    assert expected in entry("model.x", fields=fields)


def test_entry_cite_mapping_emits_block_map_with_verbatim_quote() -> None:
    e = entry(
        "model.five-martians",
        create=True,
        cite={
            "ref": "https://www.tilt.it/flipper_pinball/ipdb/ceff",
            "quote": "esistono almeno due versioni di questo flipper",
        },
        fields={"name": "Five Martians"},
    )
    parsed = yaml.safe_load("claims:\n" + e)["claims"][0]["model.five-martians"]
    assert parsed["cite"] == {
        "ref": "https://www.tilt.it/flipper_pinball/ipdb/ceff",
        "quote": "esistono almeno due versioni di questo flipper",
    }


def test_entry_cite_mapping_normalizes_smart_typography_in_quote() -> None:
    e = entry(
        "model.marte",
        cite={"ref": "https://x.example/pc", "quote": "Marte (“Electra Pool”)"},
        fields={"corporate_entity": "pc"},
    )
    parsed = yaml.safe_load("claims:\n" + e)["claims"][0]["model.marte"]
    assert parsed["cite"]["quote"] == 'Marte ("Electra Pool")'


def test_entry_changesets_emit_fields_with_own_provenance() -> None:
    e = entry(
        "model.home-run",
        create=True,
        cite={"ref": "https://x.example/page", "quote": "Home Run"},
        fields={"name": "Home Run", "year": 1967},
        changesets=[
            {
                "fields": {"game_format": "pinball"},
                "note": "the page's category line",
                "cite": {"ref": "https://x.example/page", "quote": "flipper pinball"},
            },
            {"relationships": {"theme": ["baseball"]}, "cite": "ipdb:123"},
        ],
    )
    parsed = yaml.safe_load("claims:\n" + e)["claims"][0]["model.home-run"]
    cs = parsed["changesets"]
    assert cs[0]["game_format"] == "pinball"
    assert cs[0]["note"] == "the page's category line"
    assert cs[0]["cite"]["quote"] == "flipper pinball"
    assert cs[1]["theme"] == ["baseball"]
    assert cs[1]["cite"] == "ipdb:123"


def test_entry_relationships_and_remove() -> None:
    e = entry(
        "model.x",
        relationships={"theme": ["medieval"], "manufacturer_alias": ["Stern Inc"]},
        remove={"location": ["germany"]},
        retract=["year"],
    )
    assert "theme: [medieval]" in e
    assert "manufacturer_alias: [Stern Inc]" in e
    assert "remove: { location: [germany] }" in e
    assert "retract: [year]" in e


def test_entry_relationship_member_carries_a_count() -> None:
    """`gameplay_feature` is the one namespace whose members take a count
    (DataPatches.md -> Counted members). The count is authored as a one-key
    `{public_id: count}` mapping in place of the bare slug, and the two forms mix
    freely in one list."""
    e = entry(
        "model.x", relationships={"gameplay_feature": ["multiball", {"ramps": 4}]}
    )
    assert "gameplay_feature: [multiball, { ramps: 4 }]" in e


def test_entry_relationship_count_must_be_a_positive_int() -> None:
    """A count of 0, a negative, or a non-int is rejected at authoring time rather
    than at apply time — the backend enforces `>= 1`."""
    # Deliberately ill-typed values — the guard exists for authoring mistakes the
    # annotation cannot catch (a count read from a source, a stray string).
    bad_counts: list[Any] = [{"ramps": 0}, {"ramps": -1}, {"ramps": "lots"}]
    for bad in bad_counts:
        with pytest.raises(ValueError, match="positive integer"):
            entry("model.x", relationships={"gameplay_feature": [bad]})
    with pytest.raises(ValueError, match="exactly one key"):
        entry("model.x", relationships={"gameplay_feature": [{"a": 1, "b": 2}]})


def test_entry_model_relationship_emits_block_list() -> None:
    """A typed lineage edge is a list of MAPPINGS, not scalars — it needs a block
    list, which neither `fields` (scalars) nor `relationships` (flow list of
    strings) can express."""
    e = entry(
        "model.spin-out-maresa",
        cite={
            "ref": "ipdb:5801",
            "quote": "This is a copy of Gottlieb's 1975 'Spin Out'.",
        },
        model_relationship=[
            {
                "target_machine": "spin-out-gottlieb",
                "relationship_type": "copy",
                "license_status": "unlicensed",
            }
        ],
    )
    parsed = yaml.safe_load("claims:\n" + e)
    edges = parsed["claims"][0]["model.spin-out-maresa"]["model_relationship"]
    assert edges == [
        {
            "target_machine": "spin-out-gottlieb",
            "relationship_type": "copy",
            "license_status": "unlicensed",
        }
    ]


def test_entry_model_relationship_supports_label_target_and_multiple_edges() -> None:
    """A conversion kit's donor may be plural/unnamed — a `target_label` free-text
    target instead of a slug — and a model may carry several edges."""
    e = entry(
        "model.sky-warrior",
        model_relationship=[
            {
                "target_machine": "fast-draw",
                "relationship_type": "copy",
                "license_status": "unknown",
            },
            {
                "target_label": "many late 1970s solid state Gottliebs",
                "relationship_type": "conversion_kit",
                "license_status": "unknown",
            },
        ],
    )
    edges = yaml.safe_load("claims:\n" + e)["claims"][0]["model.sky-warrior"][
        "model_relationship"
    ]
    assert len(edges) == 2
    assert edges[1]["target_label"] == "many late 1970s solid state Gottliebs"


def test_entry_model_relationship_escapes_apostrophes_in_label() -> None:
    e = entry(
        "model.x",
        model_relationship=[
            {
                "target_label": "an unidentified O'Brien game",
                "relationship_type": "conversion",
            }
        ],
    )
    edges = yaml.safe_load("claims:\n" + e)["claims"][0]["model.x"][
        "model_relationship"
    ]
    assert edges[0]["target_label"] == "an unidentified O'Brien game"


def test_entry_export_market_emits_country_rows() -> None:
    """A country market is a `target_market_location` member — a block list of
    mappings, like `model_relationship` (DataPatches.md → Export editions and
    markets). `export_edition_of` rides along as a plain scalar FK field."""
    e = entry(
        "model.big-ben-segasa-italy",
        cite={
            "ref": "ipdb:1234",
            "quote": "made for export to Italy.",
        },
        fields={"export_edition_of": "big-ben"},
        export_market=[{"target_market_location": "italy"}],
    )
    claim = yaml.safe_load("claims:\n" + e)["claims"][0]["model.big-ben-segasa-italy"]
    assert claim["export_edition_of"] == "big-ben"
    assert claim["export_market"] == [{"target_market_location": "italy"}]


def test_entry_export_market_emits_multiple_countries() -> None:
    """The rare multi-country build is the join table's reason for being."""
    e = entry(
        "model.galaxie",
        export_market=[
            {"target_market_location": "brazil"},
            {"target_market_location": "italy"},
        ],
    )
    rows = yaml.safe_load("claims:\n" + e)["claims"][0]["model.galaxie"][
        "export_market"
    ]
    assert rows == [
        {"target_market_location": "brazil"},
        {"target_market_location": "italy"},
    ]


def test_entry_export_market_emits_empty_mapping_for_unknown_destination() -> None:
    """`- {}` is the UNKNOWN-market row: a positive claim that the model was built
    for export with no known destination. It must survive as an empty mapping, not
    become a null list item — an explicit `target_market_label: null` is rejected by
    ingest, so the absent slot has to be written by omitting the key entirely."""
    e = entry("model.jackpot", export_market=[{}])
    rows = yaml.safe_load("claims:\n" + e)["claims"][0]["model.jackpot"][
        "export_market"
    ]
    assert rows == [{}]
    assert "null" not in e


def test_entry_export_market_emits_region_label() -> None:
    e = entry("model.phantom-haus", export_market=[{"target_market_label": "Europe"}])
    rows = yaml.safe_load("claims:\n" + e)["claims"][0]["model.phantom-haus"][
        "export_market"
    ]
    assert rows == [{"target_market_label": "Europe"}]


def test_entry_export_market_rejects_both_target_keys() -> None:
    """At most one target key per member — flipcommons rejects the pair at apply
    time, so catch it while authoring rather than after a snapshot restore."""
    with pytest.raises(ValueError, match="at most one"):
        entry(
            "model.x",
            export_market=[
                {"target_market_location": "italy", "target_market_label": "Europe"}
            ],
        )


def test_entry_export_market_rejects_mixed_row_shapes() -> None:
    """A null-location row must be the model's ONLY row. Ingest does not enforce
    this (DataPatches.md: "author discipline, not a validated rule") and the illegal
    mix applies silently, so patchkit is the only place it can be caught."""
    with pytest.raises(ValueError, match="only row"):
        entry(
            "model.x",
            export_market=[{"target_market_location": "italy"}, {}],
        )


def test_entry_export_market_rejects_null_valued_target() -> None:
    """Write the absent slot by OMITTING the key; an explicit null is rejected."""
    with pytest.raises(ValueError, match="omit the key"):
        entry("model.x", export_market=[{"target_market_label": None}])


def test_entry_commented_prefixes_every_line() -> None:
    e = entry("model.x", fields={"year": 1990}, commented=True)
    assert all(line.startswith("  #") for line in e.splitlines())


def test_entry_create_with_retract_raises() -> None:
    # create + retract is invalid — nothing to retract on a new entity.
    with pytest.raises(ValueError):
        entry("model.x", create=True, retract=["x"])


# --------------------------------------------------------------------------- #
# inline citations: _cite_spec, _check_cites, and entry(cites=…)              #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        (
            {"ref": "https://x.test/p", "archive": "https://web.archive.org/y"},
            '{ ref: "https://x.test/p", archive: "https://web.archive.org/y" }',
        ),
        (
            {"ref": "ipdb:4443", "locator": "Notes section"},
            '{ ref: "ipdb:4443", locator: Notes section }',
        ),
    ],
)
def test_cite_spec_flow(spec: dict[str, str], expected: str) -> None:
    assert _cite_spec_flow(spec) == expected


def test_check_cites_accepts_valid_correspondence() -> None:
    # numeric marker with a matching entry
    _check_cites("ref", ["a[[cite:1]] b[[cite:2]]"], {"1": "ipdb:1", "2": "ipdb:2"})
    # existing-slug marker needs no entry
    _check_cites("ref", ["a[[cite:bqntvkrs]]"], None)
    # mixed: a new numeric handle alongside an existing slug
    _check_cites("ref", ["a[[cite:1]] b[[cite:wxyz]]"], {"1": "ipdb:1"})
    # repeated handle is fine (renders deduped)
    _check_cites("ref", ["a[[cite:1]] b[[cite:1]]"], {"1": "ipdb:1"})
    # markers in a string field value are scanned too
    _check_cites("ref", ["desc", "field text[[cite:1]]"], {"1": "ipdb:1"})


@pytest.mark.parametrize(
    ("texts", "cites", "match"),
    [
        (["a[[cite:1]]"], None, "no cites: entry"),  # numeric marker, no map
        (["a[[cite:1]]"], {}, "no cites: entry"),
        (["plain"], {"1": "ipdb:1"}, "not referenced"),  # entry with no marker
        (
            ["a[[cite:1]]"],
            {"foo": "ipdb:1"},
            "numeric handle",
        ),  # slug-keyed cites entry
        (["a[[cite:id:1]]"], None, "malformed"),  # raw-pk handle
        (["a[[cite:1a]]"], None, "malformed"),  # letter+digit mix
        (["a[[cite:Foo]]"], None, "malformed"),  # uppercase
        (
            ["a[[cite:1]]"],
            {"1": {"url": "https://x.test/p"}},
            "unknown key",
        ),  # backend grammar takes 'ref', not 'url'
        (
            ["a[[cite:1]]"],
            {"1": {"quote": "no ref"}},
            "non-empty 'ref'",
        ),  # mapping form requires ref
    ],
)
def test_check_cites_rejects(
    texts: list[str], cites: dict[str, object] | None, match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        _check_cites("ref", texts, cites)  # type: ignore[arg-type]


def test_check_cites_error_sorts_handles_numerically() -> None:
    with pytest.raises(ValueError, match=r"\['2', '10'\]"):
        _check_cites("ref", ["a[[cite:2]] b[[cite:10]]"], None)


def test_entry_emits_cites_block() -> None:
    e = entry(
        "model.mazatron",
        description="A 1990 solid-state prototype by Mac Pinball.[[cite:1]] "
        "Only two units are known to survive.[[cite:2]]",
        cites={
            "1": "ipdb:4443",
            "2": {
                "ref": "https://pinside.com/thread",
                "archive": "https://web.archive.org/x",
            },
        },
        note="Narrative compiled from IPDB and Pinside.",
    )
    assert "cites:" in e
    assert '"1": "ipdb:4443"' in e
    # Too long for one line, so Prettier's exploded flow map: one field per line.
    assert (
        '        "2":\n'
        "          {\n"
        '            ref: "https://pinside.com/thread",\n'
        '            archive: "https://web.archive.org/x",\n'
        "          }"
    ) in e
    # the block is emitted after the description it annotates
    assert e.index("description:") < e.index("cites:")


def test_entry_emits_quote_bearing_cite_as_block_map() -> None:
    e = entry(
        "model.mazatron",
        description="Only two units are known to survive.[[cite:1]]",
        cites={
            "1": {
                "ref": "ipdb:4443",
                "locator": "Notes section",
                "quote": "It doesn't work; only two are known to survive.",
            },
        },
    )
    # A quote-bearing spec goes block-form: handle line, then one line per field.
    assert '"1":\n' in e
    assert '\n          ref: "ipdb:4443"' in e
    assert "\n          locator: Notes section" in e
    # An apostrophe needs no escaping inside a double-quoted scalar.
    assert 'quote: "It doesn\'t work; only two are known to survive."' in e
    # Round-trips as YAML with the fields intact.
    doc = yaml.safe_load("claims:\n" + e)
    spec = doc["claims"][0]["model.mazatron"]["cites"]["1"]
    assert spec == {
        "ref": "ipdb:4443",
        "locator": "Notes section",
        "quote": "It doesn't work; only two are known to survive.",
    }


def test_entry_cite_markers_survive_folding() -> None:
    # a description long enough to wrap must keep its space-free markers intact
    e = entry(
        "model.x",
        description="A 1990 solid-state prototype by Mac Pinball.[[cite:1]] "
        "Only two units are known to survive.[[cite:2]]",
        cites={"1": "ipdb:1", "2": "ipdb:2"},
    )
    body = e[e.index("description:") : e.index("cites:")]
    assert "\n" in body  # actually wrapped
    assert "[[cite:1]]" in e
    assert "[[cite:2]]" in e


def test_entry_re_edit_existing_slugs_need_no_cites() -> None:
    e = entry(
        "model.mazatron", description="Reworded the first sentence.[[cite:bqntvkrs]]"
    )
    assert "[[cite:bqntvkrs]]" in e
    assert "cites:" not in e


@pytest.mark.parametrize(
    "kwargs",
    [
        {"description": "x[[cite:1]]"},  # numeric marker in description, no cites
        {"description": "x[[cite:id:1]]"},  # malformed handle rejected
        {
            "fields": {"summary": "x[[cite:1]]"}
        },  # markers in a string field value are scanned too
    ],
)
def test_entry_enforces_cite_guard(kwargs: dict[str, object]) -> None:
    # entry() delegates to _check_cites (the rejection matrix lives in
    # test_check_cites_rejects); this pins that the guard runs and that string
    # field values — not just description — are scanned.
    with pytest.raises(ValueError):
        entry("model.x", **kwargs)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# source_root / write_patch                                                    #
# --------------------------------------------------------------------------- #


def test_source_root_emits_header_and_escaped_links() -> None:
    sr = source_root(
        "Arcade Heroes",
        description="Arcade & amusement industry news.",
        links=[("https://arcadeheroes.com/", "Arcade Heroes", "homepage")],
    )
    assert "  - name: Arcade Heroes" in sr
    assert "    source_type: web" in sr
    # Over 80 columns, so the flow map breaks with the bracket hugging the dash.
    assert (
        "      - {\n"
        '          url: "https://arcadeheroes.com/",\n'
        "          label: Arcade Heroes,\n"
        "          link_type: homepage,\n"
        "        }"
    ) in sr


def test_source_root_emits_domains_verbatim() -> None:
    """A `domains:` entry may carry a path (a path-scoped slice of a shared CDN
    host — DataPatches.md → Citation sources); prefixes are stored verbatim, so
    the emitter must not round or escape them into unrecognizability."""
    sr = source_root(
        "Cardona Pinball Designs",
        links=[("https://cardonapinball.com/", "Cardona Pinball", "homepage")],
        domains=["img1.wsimg.com/blobby/go/4bd466e8-edb0-49f6-afcc-31250ba5b0f3"],
    )
    assert "    domains:" in sr
    assert "      - img1.wsimg.com/blobby/go/4bd466e8-edb0-49f6-afcc-31250ba5b0f3" in sr
    parsed = yaml.safe_load(sr)
    assert parsed[0]["domains"] == [
        "img1.wsimg.com/blobby/go/4bd466e8-edb0-49f6-afcc-31250ba5b0f3"
    ]
    # domains sit between the header and links, matching the docs' example order
    assert sr.index("source_type") < sr.index("domains:") < sr.index("links:")


def test_source_root_without_domains_emits_no_domains_key() -> None:
    sr = source_root(
        "Arcade Heroes",
        links=[("https://arcadeheroes.com/", "Arcade Heroes", "homepage")],
    )
    assert "domains" not in sr


def test_source_root_slug_addressed_document_root() -> None:
    """A document publisher root is slug-addressed and linkless: the slug is the
    cite handle (williams:...), and the root is an abstract container with no
    homepage to recognize (DataPatches.md → Citation sources)."""
    sr = source_root(
        "Williams",
        source_type="document",
        slug="williams",
        description="First-party manuals, schematics and service bulletins.",
    )
    parsed = yaml.safe_load(sr)[0]
    assert parsed["slug"] == "williams"
    assert parsed["source_type"] == "document"
    assert "links" not in parsed
    assert sr.index("name:") < sr.index("slug:") < sr.index("source_type:")


def test_source_root_web_requires_homepage_link() -> None:
    """A web root's homepage is its recognition host: without one, no URL cite
    can ever nest under it, and nothing downstream catches the omission."""
    with pytest.raises(ValueError):
        source_root("Example")  # web by default, no links at all
    with pytest.raises(ValueError):
        source_root(  # links, but none of them a homepage
            "Example",
            links=[("https://example.com/about", "About", "reference")],
        )


def test_source_root_rejects_malformed_slug() -> None:
    with pytest.raises(ValueError):
        source_root("Williams", source_type="document", slug="Not_A_Slug")


def test_source_child_emits_document_node() -> None:
    sc = patchkit.source_child(
        "Tales of the Arabian Nights Operations Manual (May 1996)",
        parent="williams",
        slug="tales-of-the-arabian-nights-operations-manual-1996",
        year=1996,
        month=5,
        links=[
            (
                "https://www.ipdb.org/files/3824/manual.pdf",
                "IPDB copy",
                "catalog",
            ),
            (
                "https://archive.org/download/x/manual.pdf",
                "Internet Archive copy",
                "archive",
            ),
        ],
    )
    parsed = yaml.safe_load(sc)[0]
    assert parsed["parent"] == "williams"
    assert parsed["slug"] == "tales-of-the-arabian-nights-operations-manual-1996"
    assert parsed["source_type"] == "document"
    assert parsed["year"] == 1996
    assert parsed["month"] == 5
    assert [link["link_type"] for link in parsed["links"]] == ["catalog", "archive"]
    assert sc.index("name:") < sc.index("slug:") < sc.index("parent:")


def test_source_child_rejects_malformed_handles() -> None:
    with pytest.raises(ValueError):
        patchkit.source_child("M", parent="Williams!", slug="ok-slug")
    with pytest.raises(ValueError):
        patchkit.source_child("M", parent="williams", slug="Not_A_Slug")


def test_source_child_rejects_non_slug_addressed_type() -> None:
    """A web or book child is never declared as a node — web children are minted
    by URL cites, book editions are ISBN rows — so a generator asking for one is
    confused, and ingest would reject it later and less legibly."""
    with pytest.raises(ValueError):
        patchkit.source_child("M", parent="example", slug="m", source_type="web")


def test_source_child_rejects_homepage_link() -> None:
    """homepage is a web root's recognition anchor; on a slug-addressed child it
    would silently widen URL recognition to the child's host."""
    with pytest.raises(ValueError):
        patchkit.source_child(
            "M",
            parent="williams",
            slug="m",
            links=[("https://example.com/", "Example", "homepage")],
        )


def test_render_patch_sources_only_omits_claims_key() -> None:
    """A roots-only patch carries no claims: key at all — a bare 'claims:'
    would load as null and fail the schema's minItems arm."""
    text = render_patch(
        attribution="flipcommons-catalog",
        description="Publisher roots.",
        entries=[],
        sources=[source_root("Williams", source_type="document", slug="williams")],
    )
    data = yaml.safe_load(text)
    assert "claims" not in data
    assert data["sources"][0]["slug"] == "williams"


def test_render_patch_returns_exactly_what_write_patch_writes(tmp_path: Path) -> None:
    """Rendering is split from writing so a caller can regenerate a patch and
    BYTE-COMPARE it without touching the file — the freeze check that stops an
    already-applied patch being silently rewritten."""
    kwargs = {
        "attribution": "flipcommons-catalog",
        "description": "A test patch.",
        "entries": [entry("model.mazatron", fields={"year": 1979})],
    }
    written = write_patch(tmp_path / "0001-test.yaml", **kwargs)  # type: ignore[arg-type]
    assert render_patch(**kwargs) == written.read_text()  # type: ignore[arg-type]


def test_write_patch_orders_blocks_and_parses(tmp_path: Path) -> None:
    e = entry(
        "model.mazatron",
        fields={"production_status": "unreleased"},
    )
    sr = source_root(
        "Arcade Heroes",
        links=[("https://arcadeheroes.com/", "Arcade Heroes", "homepage")],
    )
    p = write_patch(
        tmp_path / "0001-test.yaml",
        attribution="flipcommons-catalog",
        description="A test patch.",
        entries=[e],
        sources=[sr],
    )
    body = p.read_text()
    assert (
        body.index("sources:") < body.index("claims:") < body.index("- model.mazatron")
    )
    # the emitted file is valid, loadable YAML
    data = yaml.safe_load(body)
    assert data["attribution"] == "flipcommons-catalog"
    assert isinstance(data["claims"], list)
    assert isinstance(data["sources"], list)


def test_entry_cite_list_emits_yaml_list_of_specs() -> None:
    e = entry(
        "model.rugby",
        create=True,
        cite=[
            {
                "ref": "https://www.tilt.it/flipper_pinball/ipdb/sidam",
                "quote": 'l\'altra "versione": Rugby (video-pinball)',
            },
            "ipdb:3340",
        ],
        fields={"name": "Rugby"},
    )
    parsed = yaml.safe_load("claims:\n" + e)["claims"][0]["model.rugby"]
    assert parsed["cite"] == [
        {
            "ref": "https://www.tilt.it/flipper_pinball/ipdb/sidam",
            "quote": 'l\'altra "versione": Rugby (video-pinball)',
        },
        "ipdb:3340",
    ]


def test_clean_quote_keeps_dashes_verbatim() -> None:
    # A quote's dashes are part of the exact source text the verifier ctrl-Fs;
    # only smart quotes and the ellipsis are normalized.
    from patchkit import clean_quote

    assert clean_quote("Fly Man – ss – 1p") == "Fly Man – ss – 1p"
    assert clean_quote("la “versione” … fine") == 'la "versione" [...] fine'


def test_entry_cite_quote_preserves_source_dashes() -> None:
    e = entry(
        "model.fly-man",
        create=True,
        cite={"ref": "https://x.test/cea", "quote": "Fly Man – ss – 1p"},
        fields={"name": "Fly Man"},
    )
    parsed = yaml.safe_load("claims:\n" + e)["claims"][0]["model.fly-man"]
    assert parsed["cite"]["quote"] == "Fly Man – ss – 1p"


def test_entry_credits_emit_block_mapping_members() -> None:
    e = entry(
        "model.golf",
        credits=[("cortez", "art")],
        cite={"ref": "https://x.test/dama", "quote": "Golf (grafica di Cortez)"},
    )
    parsed = yaml.safe_load("claims:\n" + e)["claims"][0]["model.golf"]
    assert parsed["credit"] == [{"cortez": "art"}]


def test_changeset_credits_emit_block_mapping_members() -> None:
    e = entry(
        "model.golf",
        create=True,
        cite={"ref": "https://x.test/dama", "quote": "Golf"},
        fields={"name": "Golf"},
        changesets=[
            {
                "credits": [("cortez", "art")],
                "cite": {"ref": "https://x.test/dama", "quote": "grafica di Cortez"},
            }
        ],
    )
    cs = yaml.safe_load("claims:\n" + e)["claims"][0]["model.golf"]["changesets"][0]
    assert cs["credit"] == [{"cortez": "art"}]
    assert cs["cite"]["quote"] == "grafica di Cortez"


# --------------------------------------------------------------------------- #
# read_view — the gated plan read                                             #
# --------------------------------------------------------------------------- #
#
# read_view shells out to flipcommons' analysis runner, so these tests stub
# subprocess.run and assert on the COMMAND SHAPE. That is the whole contract: a
# generator that reads its plan through a subtly wrong invocation still emits
# perfectly well-formed YAML, so the invocation is the thing worth pinning down.


class _FakeRunner:
    """Stands in for subprocess.run, recording how read_view invoked the runner."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.stdout: str = "[]"
        self.returncode: int = 0

    def __call__(self, cmd: list[str], **kw: Any) -> SimpleNamespace:
        self.calls.append({"cmd": cmd, **kw})
        if self.returncode != 0:
            raise subprocess.CalledProcessError(self.returncode, cmd, self.stdout)
        return SimpleNamespace(stdout=self.stdout, stderr="", returncode=0)

    @property
    def cmd(self) -> list[str]:
        argv: list[str] = self.calls[0]["cmd"]
        return argv

    def opt(self, flag: str) -> str:
        """The value following `flag` in the recorded argv."""
        return self.cmd[self.cmd.index(flag) + 1]


@pytest.fixture
def plan(tmp_path: Path) -> Path:
    """A real plan file — read_view rejects a path that doesn't exist."""
    p = tmp_path / "years.sql"
    p.write_text(".read scripts/analysis/catalog.sql\n")
    return p


@pytest.fixture
def runner(monkeypatch: pytest.MonkeyPatch) -> _FakeRunner:
    fake = _FakeRunner()
    # patchkit does a plain `import subprocess`, so patching the module attribute
    # is what it resolves at call time.
    monkeypatch.setattr(subprocess, "run", fake)
    monkeypatch.setattr(patchkit, "_flipcommons_dir", lambda: Path("/fc"))
    return fake


def test_read_view_invokes_the_runner_and_parses_json(
    plan: Path, runner: _FakeRunner
) -> None:
    runner.stdout = '[{"slug":"acapulco","year":1961}]'
    rows = read_view(plan, "year_patch_rows", prefix="year")

    assert runner.cmd[:2] == ["/fc/scripts/analysis/analysis", "query"]
    assert runner.cmd[2] == str(plan)
    assert runner.cmd[3] == "FROM year_patch_rows;"
    assert runner.opt("--format") == "json"
    assert rows == [{"slug": "acapulco", "year": 1961}]


def test_read_view_gates_on_the_plans_checks(plan: Path, runner: _FakeRunner) -> None:
    """The gate is the point of the helper.

    Without it a generator can emit a patch from a plan whose detectors have gone
    dark — and the YAML looks exactly the same either way.
    """
    read_view(plan, "year_patch_rows", prefix="year")
    assert "--check" in runner.cmd
    assert runner.opt("--check") == "year"


def test_read_view_prefix_is_explicit_not_inferred(
    plan: Path, runner: _FakeRunner
) -> None:
    """exports.sql gates on `export_checks`, features.sql on `gpf_checks`.

    Inferring the prefix from the plan filename is wrong for most real campaigns,
    which is why the argument is required rather than defaulted.
    """
    read_view(plan, "export_patch_rows", prefix="export")
    assert runner.opt("--check") == "export"


def test_read_view_check_false_omits_the_gate(plan: Path, runner: _FakeRunner) -> None:
    """The escape hatch, for a plan whose checks aren't written yet."""
    read_view(plan, "year_patch_rows", prefix="year", check=False)
    assert "--check" not in runner.cmd


def test_read_view_exports_flippatch_dir(plan: Path, runner: _FakeRunner) -> None:
    """A plan reading a checked-in authoring artifact locates this repo through it.

    The plans fall back to the sibling layout when it is unset, so a missing var
    reads another checkout's artifact instead of failing — hence setting it here
    rather than trusting the caller's shell.
    """
    read_view(plan, "year_patch_rows", prefix="year")
    expected = str(patchkit.REPO_ROOT)
    assert runner.calls[0]["env"]["FLIPPATCH_DIR"] == expected


def test_read_view_returns_empty_list_for_an_empty_view(
    plan: Path, runner: _FakeRunner
) -> None:
    """An empty candidate set is the caller's call, not an error here.

    A campaign whose patch has already been applied legitimately reads back zero
    rows; the generator's own "nothing to emit" guard is where that turns fatal.
    """
    runner.stdout = "[]"
    assert read_view(plan, "year_patch_rows", prefix="year") == []


def test_read_view_propagates_a_failing_gate(plan: Path, runner: _FakeRunner) -> None:
    """A nonzero exit must not be swallowed into an empty row set."""
    runner.returncode = 1
    with pytest.raises(subprocess.CalledProcessError):
        read_view(plan, "year_patch_rows", prefix="year")


@pytest.mark.parametrize("bad", ["year_patch_rows; DROP TABLE x", "a-b", "", "1x"])
def test_read_view_rejects_a_non_identifier_view(
    plan: Path, runner: _FakeRunner, bad: str
) -> None:
    with pytest.raises(ValueError, match="bare SQL identifier"):
        read_view(plan, bad, prefix="year")


def test_read_view_rejects_a_missing_plan(runner: _FakeRunner, tmp_path: Path) -> None:
    """A typo'd plan path must fail here, not as an empty result set."""
    with pytest.raises(FileNotFoundError):
        read_view(tmp_path / "nope.sql", "year_patch_rows", prefix="year")


# --------------------------------------------------------------------------- #
# Prettier compatibility (flow collections, printWidth 80)                     #
# --------------------------------------------------------------------------- #
#
# patches/*.yaml is reformatted by Prettier at commit time and by the IDE on
# save, so any construct patchkit emits differently comes back as diff noise on
# every generated patch. These pin the three places the two used to disagree:
# quote style (above), bracket spacing, and over-long flow collections.


def test_counted_member_gets_prettier_bracket_spacing() -> None:
    e = entry("model.x", relationships={"gameplay_feature": [{"ramp": 4}, "spinner"]})
    assert "gameplay_feature: [{ ramp: 4 }, spinner]" in e


def test_long_flow_list_moves_to_its_own_line() -> None:
    """Over 80 columns, Prettier drops the value to the next line, indented +2 --
    still inline, as long as it fits there."""
    e = entry(
        "gameplay-feature.x",
        relationships={
            "gameplay_feature_alias": [
                "Mini-Post Screw Between Flippers",
                "Stationary Post Between Flippers",
            ]
        },
    )
    assert (
        "      gameplay_feature_alias:\n"
        "        [Mini-Post Screw Between Flippers, Stationary Post Between Flippers]"
    ) in e


def test_flow_list_too_long_for_its_own_line_explodes() -> None:
    """Beyond that, one member per line inside the brackets, trailing comma and
    all -- Prettier never fills a flow collection."""
    e = entry(
        "gameplay-feature.x",
        relationships={
            "gameplay_feature_alias": [
                "Mini-Post Screw Between The Flippers On The Lower Playfield",
                "Stationary Center Post Between The Flippers",
                "Center Post",
            ]
        },
    )
    assert (
        "      gameplay_feature_alias:\n"
        "        [\n"
        "          Mini-Post Screw Between The Flippers On The Lower Playfield,\n"
        "          Stationary Center Post Between The Flippers,\n"
        "          Center Post,\n"
        "        ]"
    ) in e


def test_long_source_link_explodes_with_the_bracket_hugging_the_dash() -> None:
    """A block-sequence item can't move its bracket to the next line, so Prettier
    keeps `- {` together and indents the members under it."""
    sr = source_root(
        "Internet Pinball Machine Database",
        links=[
            (
                "https://www.ipdb.org/search.pl?any=quite+a+long+query+string",
                "IPDB search",
                "homepage",
            )
        ],
    )
    assert (
        "      - {\n"
        '          url: "https://www.ipdb.org/search.pl?any=quite+a+long+query+string",\n'
        "          label: IPDB search,\n"
        "          link_type: homepage,\n"
        "        }"
    ) in sr


def test_empty_export_market_row_stays_an_inline_flow_map() -> None:
    e = entry("model.x", export_market=[{}])
    assert "      - {}" in e
