"""Tests for scripts/cloud_store/push_to_r2.py patch collection.

Patches ship verbatim under ``flippatch/patches/``. Only the top-level
``NNNN-slug.yaml`` files are shipped; subdirectories under ``patches/``
(e.g. ``authoring/`` scratch tooling) must NOT be uploaded.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import cloud_store.push_to_r2 as p2r

if TYPE_CHECKING:
    from pathlib import Path


def _make_patches(tmp_path: Path) -> Path:
    patches = tmp_path / "patches"
    patches.mkdir()
    (patches / "0001-foo.yaml").write_text("patch: foo\n", encoding="utf-8")
    (patches / "0002-bar.yaml").write_text("patch: bar\n", encoding="utf-8")
    # Scratch authoring tooling that must never ship.
    authoring = patches / "authoring" / "0001-foo"
    authoring.mkdir(parents=True)
    (authoring / "gen.py").write_text("print('hi')\n", encoding="utf-8")
    (authoring / "worksheet.csv").write_text("a,b\n", encoding="utf-8")
    (patches / "authoring" / "patchkit.py").write_text("x = 1\n", encoding="utf-8")
    return patches


def test_collect_patch_files_only_top_level_yaml(tmp_path: Path) -> None:
    patches = _make_patches(tmp_path)
    entries = p2r._collect_patch_files(patches, path_prefix="patches/")
    paths = {e["path"] for e in entries}
    assert paths == {"patches/0001-foo.yaml", "patches/0002-bar.yaml"}


def test_collect_patch_files_excludes_authoring(tmp_path: Path) -> None:
    patches = _make_patches(tmp_path)
    entries = p2r._collect_patch_files(patches, path_prefix="patches/")
    assert not any("authoring" in e["path"] for e in entries)
    assert not any(e["path"].endswith(".py") for e in entries)
    assert not any(e["path"].endswith(".csv") for e in entries)
