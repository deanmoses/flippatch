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
    _cite_spec,
    _scalar,
    check_resolved,
    clean_ipdb_quote,
    clean_text,
    entry,
    guard,
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
# guards / resolution                                                          #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ({"year": None, "ipdb_id": 42}, {"ipdb_id": 42}),  # ipdb_id most specific
        ({"year": 1990, "ipdb_id": None}, {"year": 1990}),  # falls back to year
        (
            {"corporate_entity__slug": "bally", "year": None, "ipdb_id": None},
            {"corporate_entity": "bally"},
        ),
        ({"year": None, "ipdb_id": None}, {}),  # nothing available
        ({"year": "", "ipdb_id": None}, {}),  # empty string is treated as absent
    ],
)
def test_guard(row: dict[str, object], expected: dict[str, object]) -> None:
    assert guard(row) == expected


def test_guard_respects_prefer_order() -> None:
    row = {"year": 1990, "ipdb_id": 42}
    assert guard(row, prefer=("year", "ipdb_id")) == {"year": 1990}


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
        expect={"ipdb_id": 4443},
        note=source_note("IPDB", 'exists only as a "prototype" machine'),
        cite="ipdb:4443",
        fields={"production_status": "unreleased"},
        tags=["prototype"],
    )
    assert "- model.mazatron:" in e
    assert "expect: { ipdb_id: 4443 }" in e
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


def test_entry_commented_prefixes_every_line() -> None:
    e = entry("model.x", fields={"year": 1990}, commented=True)
    assert all(line.startswith("  #") for line in e.splitlines())


@pytest.mark.parametrize(
    "kwargs",
    [
        {"create": True, "expect": {"year": 1}},  # create + expect contradictory
        {"create": True, "retract": ["x"]},  # create + retract invalid
    ],
)
def test_entry_contradictory_kwargs_raise(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        entry("model.x", **kwargs)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# inline citations: _cite_spec, _check_cites, and entry(cites=…)              #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        ("ipdb:4443", "'ipdb:4443'"),  # scheme:id quoted (colon)
        ("https://x.test/p", "'https://x.test/p'"),  # url quoted
        (
            {"url": "https://x.test/p", "archive": "https://web.archive.org/y"},
            "{ url: 'https://x.test/p', archive: 'https://web.archive.org/y' }",
        ),
    ],
)
def test_cite_spec(spec: object, expected: str) -> None:
    assert _cite_spec(spec) == expected  # type: ignore[arg-type]


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
        expect={"ipdb_id": 4443},
        description="A 1990 solid-state prototype by Mac Pinball.[[cite:1]] "
        "Only two units are known to survive.[[cite:2]]",
        cites={
            "1": "ipdb:4443",
            "2": {
                "url": "https://pinside.com/thread",
                "archive": "https://web.archive.org/x",
            },
        },
        note="Narrative compiled from IPDB and Pinside.",
    )
    assert "cites:" in e
    assert "'1': 'ipdb:4443'" in e
    assert (
        "'2': { url: 'https://pinside.com/thread', archive: 'https://web.archive.org/x' }"
        in e
    )
    # the block is emitted after the description it annotates
    assert e.index("description:") < e.index("cites:")


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
        expect={"ipdb_id": 4443},
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
