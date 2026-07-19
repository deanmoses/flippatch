"""Tests for patchkit — the shared patch-authoring helpers.

patchkit lives at patches/authoring/patchkit.py (excluded from the R2 upload) and
is on the pytest pythonpath via pyproject. Its whole purpose is to centralize the
escaping / guard / emission logic that kept being re-derived (subtly wrong) in each
authoring session, so it earns real coverage. These tests are the authoritative
checks; the module's __main__ block is now just a runnable demo.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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
    sentence_with,
    sentences,
    source_note,
    source_root,
    write_patch,
    yamlq,
)

if TYPE_CHECKING:
    from pathlib import Path

# --------------------------------------------------------------------------- #
# text / escaping                                                             #
# --------------------------------------------------------------------------- #


def test_yamlq_doubles_single_quotes() -> None:
    assert yamlq("a'b") == "'a''b'"
    assert yamlq("plain") == "'plain'"


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


def test_source_note_wraps_verbatim_and_normalizes() -> None:
    note = source_note("IPDB", 'exists only as a "prototype" machine')
    assert note == 'IPDB says "exists only as a "prototype" machine"'


def test_source_note_tail() -> None:
    assert (
        source_note("IPDB", "x", tail=" (translated)") == 'IPDB says "x" (translated)'
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, "true"),  # bool before int (bool is an int subclass)
        (False, "false"),
        (5, "5"),
        (3.5, "3.5"),
        ("simple", "simple"),  # safe bare scalar
        ("with space", "with space"),
        ("404", "'404'"),  # numeric-looking string stays quoted
        ("true", "'true'"),  # bool-looking string stays quoted
        ("ipdb:4443", "'ipdb:4443'"),  # colon forces quoting
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
        note=source_note("IPDB", 'exists only as a "prototype" machine'),
        cite="ipdb:4443",
        fields={"production_status": "unreleased"},
        tags=["prototype"],
    )
    assert "- model.mazatron:" in e
    assert """note: 'IPDB says "exists only as a "prototype" machine"\'""" in e
    assert "cite: ipdb:4443" in e
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
            "game_format: '404'",
        ),  # numeric-looking string stays a string
        ({"v": "true"}, "v: 'true'"),  # bool-looking string stays a string
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
            "{ ref: 'https://x.test/p', archive: 'https://web.archive.org/y' }",
        ),
        (
            {"ref": "ipdb:4443", "locator": "Notes section"},
            "{ ref: 'ipdb:4443', locator: Notes section }",
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
    assert "'1': 'ipdb:4443'" in e
    assert (
        "'2': { ref: 'https://pinside.com/thread', archive: 'https://web.archive.org/x' }"
        in e
    )
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
    assert "'1':\n" in e
    assert "\n          ref: 'ipdb:4443'" in e
    assert "\n          locator: Notes section" in e
    # The apostrophe survives via single-quote doubling.
    assert "quote: 'It doesn''t work; only two are known to survive.'" in e
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
    assert "url: 'https://arcadeheroes.com/'" in sr  # url quoted (has ':')
    assert "label: Arcade Heroes, link_type: homepage" in sr


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
