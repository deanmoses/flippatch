"""Tests for common.catalog.entity_index — registry read, mention finding, resolve."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from common.catalog.entity_index import EntityIndex, normalize_key


@pytest.fixture
def catalog_db(tmp_path: Path) -> Path:
    db = tmp_path / "db.sqlite3"
    con = sqlite3.connect(db)
    con.executescript(
        """
        CREATE TABLE catalog_manufacturer (id INTEGER PRIMARY KEY, slug TEXT, name TEXT);
        CREATE TABLE catalog_machinemodel (id INTEGER PRIMARY KEY, slug TEXT, name TEXT);
        CREATE TABLE catalog_manufactureralias (
            id INTEGER PRIMARY KEY, manufacturer_id INTEGER, value TEXT
        );
        """
    )
    con.execute("INSERT INTO catalog_manufacturer VALUES (1, 'bally', 'Bally')")
    con.execute(
        "INSERT INTO catalog_machinemodel VALUES (2, 'f14-tomcat', 'F-14 Tomcat')"
    )
    con.execute("INSERT INTO catalog_manufactureralias VALUES (1, 1, 'Bally Midway')")
    con.commit()
    con.close()
    return db


def test_normalize_key_folds_dashes_spaces_case_and_the():
    assert normalize_key("F-14 Tomcat") == "f14tomcat"
    assert normalize_key("f14 tomcat") == "f14tomcat"
    assert normalize_key("The Twilight Zone") == "twilightzone"


def test_finds_exact_name_and_alias(catalog_db: Path):
    index = EntityIndex.build(catalog_db, types=("manufacturer", "model"))
    mentions = index.find_mentions("The F-14 Tomcat was made by Bally Midway.")
    surfaces = {m.surface for m in mentions}
    assert "F-14 Tomcat" in surfaces
    assert "Bally Midway" in surfaces
    by_surface = {m.surface: m for m in mentions}
    assert by_surface["F-14 Tomcat"].refs[0].entity_type == "model"
    assert by_surface["F-14 Tomcat"].exact is True
    assert by_surface["Bally Midway"].refs[0].wikilink == "[[manufacturer:bally]]"


def test_fuzzy_match_on_dash_number_variant_is_not_exact(catalog_db: Path):
    index = EntityIndex.build(catalog_db, types=("manufacturer", "model"))
    (mention,) = [
        m
        for m in index.find_mentions("Loved the F14 Tomcat cabinet.")
        if m.refs[0].entity_type == "model"
    ]
    assert mention.refs[0].slug == "f14-tomcat"
    assert mention.exact is False  # matched only after normalization


def test_subject_self_mention_excluded(catalog_db: Path):
    index = EntityIndex.build(catalog_db, types=("manufacturer", "model"))
    mentions = index.find_mentions(
        "The F-14 Tomcat is a Bally machine.",
        exclude_type="model",
        exclude_slug="f14-tomcat",
    )
    assert all(m.refs[0].slug != "f14-tomcat" for m in mentions)
    assert any(m.refs[0].slug == "bally" for m in mentions)


# --- resolve: single-name lookup (extraction/sweep target resolution) -------
def test_resolve_matches_name_alias_and_fuzzy_variant(catalog_db: Path):
    index = EntityIndex.build(catalog_db, types=("manufacturer", "model"))
    assert index.resolve("F-14 Tomcat")[0].slug == "f14-tomcat"
    assert index.resolve("f14 tomcat")[0].slug == "f14-tomcat"  # normalization
    assert index.resolve("Bally Midway")[0].slug == "bally"  # alias


def test_resolve_unknown_name_is_empty_possible_gap(catalog_db: Path):
    index = EntityIndex.build(catalog_db, types=("manufacturer", "model"))
    assert index.resolve("Some Machine Not In Catalog") == []


def test_resolve_type_profile_filters_results(catalog_db: Path):
    index = EntityIndex.build(catalog_db, types=("manufacturer", "model"))
    assert index.resolve("F-14 Tomcat", types=("manufacturer",)) == []
    assert index.resolve("F-14 Tomcat", types=("model",))[0].slug == "f14-tomcat"


def test_resolve_ignores_too_generic_and_stop_keys(catalog_db: Path):
    index = EntityIndex.build(catalog_db, types=("manufacturer", "model"))
    assert index.resolve("pinball") == []  # stop key
    assert index.resolve("a") == []  # below MIN_KEY_LEN
