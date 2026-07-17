"""Tests for the DB-grounding layer — catalog introspection + grounded slices.

Offline: a temp SQLite fixture mirrors the shape of flipcommons' vocab + entity
tables (no sibling checkout), so these exercise vocab reading, display-order,
``[[type:id:N]]`` wikilink flattening, parent-grouped child vocab, and that
``build_slices`` grounds the full model-info field set on the DB.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from ai_page_extract.catalog import CatalogDb, ModelRef, VocabTerm
from ai_page_extract.fields import build_slices
from ai_page_extract.framework import Slice, single_value_slice

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


def _enum(slice_: Slice) -> object:
    """The value enum out of a slice's (loosely-typed) forced-tool schema."""
    props = slice_.schema["properties"]
    assert isinstance(props, dict)
    value_spec = props["value"]
    assert isinstance(value_spec, dict)
    return value_spec["enum"]


def _covered_fields(slices: Sequence[Slice]) -> list[str]:
    fields: list[str] = []
    for slice_ in slices:
        fields.extend(slice_.fields or (slice_.key,))
    return fields


def _make_db(path: Path) -> None:
    """A fixture with the flipcommons vocab tables build_slices reads."""
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE catalog_manufacturer (id INTEGER PRIMARY KEY, name TEXT, slug TEXT);
        INSERT INTO catalog_manufacturer (id, name, slug) VALUES (86, 'Mirco Games', 'mirco');
        CREATE TABLE catalog_title (id INTEGER PRIMARY KEY, name TEXT, slug TEXT);

        CREATE TABLE catalog_technologygeneration
            (id INTEGER PRIMARY KEY, slug TEXT, name TEXT, description TEXT, display_order INTEGER);
        INSERT INTO catalog_technologygeneration VALUES
            (1, 'pure-mechanical', 'Pure Mechanical', 'No electricity at all.', 1),
            (2, 'electromechanical', 'Electromechanical', 'Relays and score reels, no CPU.', 2),
            (3, 'solid-state', 'Solid State',
             'Arrived when [[manufacturer:id:86]] shipped the first microprocessor game.', 3);

        CREATE TABLE catalog_technologysubgeneration
            (id INTEGER PRIMARY KEY, slug TEXT, name TEXT, description TEXT, display_order INTEGER,
             technology_generation_id INTEGER);
        INSERT INTO catalog_technologysubgeneration VALUES
            (1, 'ss-integrated', 'Integrated', 'Purpose-built platforms like WPC.', 1, 3);

        CREATE TABLE catalog_displaytype
            (id INTEGER PRIMARY KEY, slug TEXT, name TEXT, description TEXT, display_order INTEGER);
        INSERT INTO catalog_displaytype VALUES
            (1, 'score-reels', 'Score Reels', 'Mechanical number drums.', 1),
            (2, 'alphanumeric', 'Alpha-Numeric', 'Segmented LED digits.', 2);

        CREATE TABLE catalog_displaysubtype
            (id INTEGER PRIMARY KEY, slug TEXT, name TEXT, description TEXT, display_order INTEGER,
             display_type_id INTEGER);
        INSERT INTO catalog_displaysubtype VALUES
            (1, '7-segment', '7-Segment', 'Seven-segment digits.', 1, 2);

        CREATE TABLE catalog_gameformat
            (id INTEGER PRIMARY KEY, slug TEXT, name TEXT, description TEXT, display_order INTEGER);
        INSERT INTO catalog_gameformat VALUES
            (1, 'pinball', 'Pinball', 'A tilted playfield with flippers.', 1),
            (2, 'shuffle', 'Shuffle', 'A bowling-style alley.', 2);

        CREATE TABLE catalog_productionstatus
            (id INTEGER PRIMARY KEY, slug TEXT, name TEXT, description TEXT, display_order INTEGER);
        INSERT INTO catalog_productionstatus VALUES
            (1, 'produced', 'Produced', 'Commercially sold.', 1);

        CREATE TABLE catalog_cabinet
            (id INTEGER PRIMARY KEY, slug TEXT, name TEXT, description TEXT, display_order INTEGER);
        INSERT INTO catalog_cabinet VALUES (1, 'floor', 'Floor', 'Free-standing upright.', 1);

        CREATE TABLE catalog_rewardtype
            (id INTEGER PRIMARY KEY, slug TEXT, name TEXT, description TEXT, display_order INTEGER);
        INSERT INTO catalog_rewardtype VALUES
            (1, 'replay', 'Replay', 'A free game.', 1),
            (2, 'novelty', 'Novelty', 'No reward.', 2);

        CREATE TABLE catalog_tag
            (id INTEGER PRIMARY KEY, slug TEXT, name TEXT, description TEXT, display_order INTEGER);
        INSERT INTO catalog_tag VALUES
            (1, 'widebody', 'Widebody', 'A wider cabinet.', 1),
            (2, 'remake', 'Remake', 'A newly manufactured recreation.', 2);

        CREATE TABLE catalog_machinemodel
            (id INTEGER PRIMARY KEY, slug TEXT, name TEXT, ipdb_id INTEGER, opdb_id TEXT);
        INSERT INTO catalog_machinemodel (id, slug, name, ipdb_id, opdb_id) VALUES
            (1352, 'combat-2', 'Combat', 3858, NULL),
            (1353, 'combat-3', 'Combat', 6682, NULL),
            (1354, 'combat', 'Combat', 3609, 'GryPZ-ML07x');
        """
    )
    conn.commit()
    conn.close()


def _catalog(tmp_path: Path) -> CatalogDb:
    db_path = tmp_path / "db.sqlite3"
    _make_db(db_path)
    return CatalogDb(db_path)


def test_vocab_terms_reads_slug_name_description_in_display_order(tmp_path: Path):
    terms = _catalog(tmp_path).vocab_terms("technology_generation")
    assert [t.slug for t in terms] == [
        "pure-mechanical",
        "electromechanical",
        "solid-state",
    ]
    assert terms[1].name == "Electromechanical"
    assert terms[1].description == "Relays and score reels, no CPU."


def test_wikilink_markup_is_flattened_to_entity_name(tmp_path: Path):
    solid_state = _catalog(tmp_path).vocab_terms("technology_generation")[2]
    assert "[[" not in solid_state.description
    assert "Mirco Games" in solid_state.description


def test_unresolvable_wikilink_degrades_to_humanized_type(tmp_path: Path):
    db_path = tmp_path / "db.sqlite3"
    _make_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE catalog_gameformat SET description = 'Similar to a [[title:id:9999]].' "
        "WHERE slug = 'shuffle'"
    )
    conn.commit()
    conn.close()
    shuffle = next(
        t for t in CatalogDb(db_path).vocab_terms("game_format") if t.slug == "shuffle"
    )
    # No such title id; the marker degrades to a readable token, never leaks the id.
    assert "[[" not in shuffle.description
    assert "9999" not in shuffle.description


def test_child_terms_are_grouped_by_parent(tmp_path: Path):
    children = _catalog(tmp_path).child_terms("technology_subgeneration")
    assert len(children) == 1
    term, parent_slug = children[0]
    assert term.slug == "ss-integrated"
    assert parent_slug == "solid-state"


def test_grounded_single_value_slice_carries_enum_and_meanings():
    terms = (
        VocabTerm("pinball", "Pinball", "A tilted playfield with flippers."),
        VocabTerm("shuffle", "Shuffle", "A bowling-style alley."),
    )
    slice_ = single_value_slice(
        key="game_format",
        task="determine this machine's game format",
        terms=terms,
        guidance="Tells: flippers point to pinball.",
    )
    # The legal slugs lead the enum; "absent" and the tolerated null-ish sentinels
    # (normalized to absence in the parser) follow — a benign off-spec "nothing"
    # validates instead of erroring into a false gap.
    enum = _enum(slice_)
    assert enum[:2] == ["pinball", "shuffle"]
    assert "absent" in enum
    prompt = slice_.user_prompt("PAGE TEXT")
    assert "pinball (Pinball): A tilted playfield with flippers." in prompt
    assert "Tells: flippers point to pinball." in prompt


def test_build_slices_grounds_the_full_model_info_field_set(tmp_path: Path):
    slices = build_slices(_catalog(tmp_path))
    covered = _covered_fields(slices)
    for field in [
        "technology_generation",
        "technology_subgeneration",
        "display_type",
        "display_subtype",
        "game_format",
        "production_status",
        "cabinet",
        "reward_type",
        "tag",
        "year",
        "player_count",
        "flipper_count",
        "gameplay_feature",
        "themes",
        "franchise",
        "credits",
        "lineage",
        "other",
    ]:
        assert field in covered


def test_tag_slice_excludes_lineage_paired_tags(tmp_path: Path):
    tag_slice = next(s for s in build_slices(_catalog(tmp_path)) if s.key == "tag")
    props = tag_slice.schema["properties"]
    assert isinstance(props, dict)
    item_spec = props["items"]
    assert isinstance(item_spec, dict)
    inner = item_spec["items"]
    assert isinstance(inner, dict)
    enum = inner["properties"]["value"]["enum"]
    assert "widebody" in enum
    assert "remake" not in enum  # decided by the lineage slice instead


def test_build_slices_without_catalog_uses_fallback_field_set():
    keys = [s.key for s in build_slices(None)]
    assert keys[0] == "technology_generation"
    assert "gameplay_feature" in keys
    assert "credits" in keys
    # No DB → the controlled-vocab fields that need grounding are skipped.
    assert "game_format" not in keys
    assert "reward_type" not in keys


# ── Ref → model resolution (the ref side of the ref/target cross-check) ──────


def test_model_for_ipdb_ref_resolves_by_stored_id(tmp_path: Path):
    # ipdb:6682 is the SS split (combat-3), a *different* record than ipdb:3609.
    catalog = _catalog(tmp_path)
    assert catalog.model_for_external_ref("ipdb:6682") == ModelRef("combat-3", "Combat")
    assert catalog.model_for_external_ref("ipdb:3609") == ModelRef("combat", "Combat")


def test_model_for_opdb_ref_resolves_by_string_id(tmp_path: Path):
    catalog = _catalog(tmp_path)
    assert catalog.model_for_external_ref("opdb:GryPZ-ML07x") == ModelRef(
        "combat", "Combat"
    )


def test_model_for_ref_returns_none_for_unknown_id(tmp_path: Path):
    # A scheme ref the catalog doesn't hold — the caller reads None as a possible gap.
    assert _catalog(tmp_path).model_for_external_ref("ipdb:99999") is None


def test_model_for_ref_returns_none_for_non_id_ref(tmp_path: Path):
    # http / youtube carry no external id to key on.
    catalog = _catalog(tmp_path)
    assert catalog.model_for_external_ref("https://example.com/combat") is None
    assert catalog.model_for_external_ref("youtube:abc123") is None
