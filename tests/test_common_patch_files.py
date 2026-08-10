"""Unit tests for patch-file selection (common.patch_files).

The scope vocabulary the verbatim gate and both AI checkers share, so these pin
what an id may look like and the one refusal all three print for a bad one.
"""

from common.patch_files import patch_paths, unmatched_ids, unmatched_scope_error


def _corpus(tmp_path):
    for name in (
        "0001-first.yaml",
        "0042-japanese-maker-years.yaml",
        "0223-cirqus-voltaire.yaml",
        "README.md",  # not a patch
        "draft-notes.yaml",  # no numeric prefix — not a patch
    ):
        (tmp_path / name).write_text("claims: []\n")
    return tmp_path


def test_no_ids_selects_every_patch_in_filename_order(tmp_path):
    assert [path.name for path in patch_paths(_corpus(tmp_path))] == [
        "0001-first.yaml",
        "0042-japanese-maker-years.yaml",
        "0223-cirqus-voltaire.yaml",
    ]


def test_bare_number_selects_that_patch(tmp_path):
    assert [path.name for path in patch_paths(_corpus(tmp_path), ["0223"])] == [
        "0223-cirqus-voltaire.yaml"
    ]


def test_full_stem_and_filename_select_that_patch(tmp_path):
    corpus = _corpus(tmp_path)
    for spelling in ("0223-cirqus-voltaire", "0223-cirqus-voltaire.yaml", "0223.yaml"):
        assert [path.name for path in patch_paths(corpus, [spelling])] == [
            "0223-cirqus-voltaire.yaml"
        ], spelling


def test_several_ids_select_the_union_in_filename_order(tmp_path):
    assert [path.name for path in patch_paths(_corpus(tmp_path), ["0223", "0001"])] == [
        "0001-first.yaml",
        "0223-cirqus-voltaire.yaml",
    ]


def test_unmatched_id_selects_nothing(tmp_path):
    # Nothing, rather than everything — an unmatched scope must not widen to all.
    assert patch_paths(_corpus(tmp_path), ["9999"]) == []


def test_a_number_never_matches_another_patchs_slug(tmp_path):
    # "0001" must not select 0042-...-0001-... style names by substring; the
    # match is on the whole stem or the whole numeric prefix.
    (tmp_path / "0500-sequel-to-0001.yaml").write_text("claims: []\n")
    assert [path.name for path in patch_paths(_corpus(tmp_path), ["0001"])] == [
        "0001-first.yaml"
    ]


# ── unmatched_ids ────────────────────────────────────────────────────────────


def test_every_id_that_matches_a_patch_is_matched(tmp_path):
    corpus = _corpus(tmp_path)
    assert unmatched_ids(corpus, ["0223", "0001-first", "0042.yaml"]) == []


def test_an_id_matching_no_patch_is_reported(tmp_path):
    assert unmatched_ids(_corpus(tmp_path), ["9999"]) == ["9999"]


def test_only_the_unmatched_ids_are_reported_in_the_order_given(tmp_path):
    assert unmatched_ids(_corpus(tmp_path), ["9999", "0223", "0007"]) == [
        "9999",
        "0007",
    ]


def test_an_empty_scope_has_nothing_unmatched(tmp_path):
    # A bare run is the whole corpus, not a scope naming zero patches.
    assert unmatched_ids(_corpus(tmp_path), []) == []


# ── unmatched_scope_error ────────────────────────────────────────────────────


def test_no_error_when_every_id_matches(tmp_path):
    assert unmatched_scope_error(_corpus(tmp_path), ["0223", "0001"]) is None


def test_no_error_for_a_bare_run(tmp_path):
    # Whether a bare run is allowed at all is each tool's own policy, not this
    # guard's: the verbatim gate runs the corpus, the AI checkers refuse.
    assert unmatched_scope_error(_corpus(tmp_path), []) is None


def test_the_error_names_only_the_unmatched_ids(tmp_path):
    msg = unmatched_scope_error(_corpus(tmp_path), ["0223", "9999"])
    assert msg is not None
    assert "9999" in msg  # the typo, so the fix is one edit
    assert "0223" not in msg
    assert "nothing ran" in msg  # refused whole, not narrowed to what matched
