"""Tests for scripts/patch_validation/db_patch_state.py.

Unit-level, against the module directly — ``tests/test_audit_patches.py`` covers the
same logic once more through the shell wrapper, which is where the wiring can break.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from patch_validation.db_patch_state import (
    PatchState,
    State,
    patches_since,
    read_states,
    render_banner,
    render_status,
)

# The ledger instant every case is anchored to, as ingest_patches stores it: UTC,
# space-separated, microseconds. Displays are LOCAL, so the expected string is derived
# rather than hardcoded — otherwise the suite passes only where it was written.
APPLIED_UTC = "2026-08-15 23:37:40.179897"
APPLIED_EPOCH = int(datetime.fromisoformat(APPLIED_UTC).replace(tzinfo=UTC).timestamp())
# PatchState.applied_at is LOCAL — read_states() localises before handing it on and the
# renderers format it as given, so fixtures must match that contract or they test nothing.
# Built from the ISO string rather than APPLIED_EPOCH because read_states() carries the
# ledger's microseconds through untouched, and an int epoch drops them.
APPLIED_LOCAL = datetime.fromisoformat(APPLIED_UTC).replace(tzinfo=UTC).astimezone()
LOCAL_HHMM = APPLIED_LOCAL.strftime("%H:%M")


def _db(tmp_path: Path, applied: dict[str, str], *, table: bool = True) -> Path:
    path = tmp_path / "db.sqlite3"
    con = sqlite3.connect(path)
    if table:
        con.execute(
            "CREATE TABLE provenance_ingestrun ("
            "  patch_id VARCHAR(200) NULL,"
            "  status VARCHAR(10) NOT NULL,"
            "  finished_at DATETIME NULL)"
        )
        for patch_id, finished_at in applied.items():
            con.execute(
                "INSERT INTO provenance_ingestrun VALUES (?, 'success', ?)",
                (patch_id, finished_at),
            )
        # Noise the roster query must exclude.
        con.execute(
            "INSERT INTO provenance_ingestrun VALUES ('0299-failed', 'failed', ?)",
            (APPLIED_UTC,),
        )
        con.execute(
            "INSERT INTO provenance_ingestrun VALUES (NULL, 'success', ?)",
            (APPLIED_UTC,),
        )
    con.commit()
    con.close()
    return path


def _patch(tmp_path: Path, stem: str, mtime: int) -> Path:
    patches = tmp_path / "patches"
    patches.mkdir(exist_ok=True)
    path = patches / f"{stem}.yaml"
    path.write_text("claims: []\n", encoding="utf-8")
    os.utime(path, (mtime, mtime))
    return path


def _state(stem: str, state: State) -> PatchState:
    at = None if state is State.UNAPPLIED else APPLIED_LOCAL
    return PatchState(stem, state, at)


# ── read_states ──────────────────────────────────────────


def test_file_older_than_its_ingest_is_current(tmp_path: Path) -> None:
    db = _db(tmp_path, {"0251-gameplay": APPLIED_UTC})
    f = _patch(tmp_path, "0251-gameplay", APPLIED_EPOCH - 60)
    assert read_states([f], db) == [
        PatchState("0251-gameplay", State.CURRENT, APPLIED_LOCAL)
    ]


def test_file_newer_than_its_ingest_is_edited(tmp_path: Path) -> None:
    db = _db(tmp_path, {"0251-gameplay": APPLIED_UTC})
    f = _patch(tmp_path, "0251-gameplay", APPLIED_EPOCH + 60)
    states = read_states([f], db)
    assert states is not None
    assert states[0].state is State.EDITED


def test_file_absent_from_ledger_is_unapplied(tmp_path: Path) -> None:
    db = _db(tmp_path, {})
    f = _patch(tmp_path, "0253-manufacturers", APPLIED_EPOCH)
    states = read_states([f], db)
    assert states is not None
    assert states[0] == PatchState("0253-manufacturers", State.UNAPPLIED, None)


def test_failed_run_does_not_count_as_applied(tmp_path: Path) -> None:
    db = _db(tmp_path, {})
    f = _patch(tmp_path, "0299-failed", APPLIED_EPOCH - 60)
    states = read_states([f], db)
    assert states is not None
    assert states[0].state is State.UNAPPLIED


def test_latest_successful_run_wins(tmp_path: Path) -> None:
    """A re-ingested patch is judged against its most recent run, not its first.

    Hypothetical today: a partial unique index on the live table allows only one
    successful run per patch, so this row pair cannot occur there — the narrow fixture
    below carries no such index. It pins the max() as belt-and-braces, against the
    constraint ever relaxing.
    """
    db = _db(tmp_path, {"0251-gameplay": "2026-08-01 00:00:00.000000"})
    con = sqlite3.connect(db)
    con.execute(
        "INSERT INTO provenance_ingestrun VALUES ('0251-gameplay', 'success', ?)",
        (APPLIED_UTC,),
    )
    con.commit()
    con.close()
    # Newer than the first run, older than the second — current only if max() is used.
    f = _patch(tmp_path, "0251-gameplay", APPLIED_EPOCH - 60)
    states = read_states([f], db)
    assert states is not None
    assert states[0].state is State.CURRENT


def test_states_are_ordered_by_patch_number(tmp_path: Path) -> None:
    db = _db(tmp_path, {})
    late = _patch(tmp_path, "0253-b", APPLIED_EPOCH)
    early = _patch(tmp_path, "0239-a", APPLIED_EPOCH)
    states = read_states([late, early], db)
    assert states is not None
    assert [s.stem for s in states] == ["0239-a", "0253-b"]


def test_unreadable_ledger_is_unknown_not_all_unapplied(tmp_path: Path) -> None:
    """An older DB without the table must not read as every patch being missing."""
    db = _db(tmp_path, {}, table=False)
    f = _patch(tmp_path, "0251-gameplay", APPLIED_EPOCH)
    assert read_states([f], db) is None


# ── patches_since ────────────────────────────────────────


def test_patches_since_filters_by_number(tmp_path: Path) -> None:
    d = tmp_path / "patches"
    d.mkdir()
    for stem in ("0239-a", "0251-b", "0253-c"):
        (d / f"{stem}.yaml").write_text("claims: []\n", encoding="utf-8")
    (d / "README.md").write_text("not a patch\n", encoding="utf-8")
    assert [p.stem for p in patches_since(251, d)] == ["0251-b", "0253-c"]


def test_patches_since_is_inclusive_of_its_own_number(tmp_path: Path) -> None:
    d = tmp_path / "patches"
    d.mkdir()
    (d / "0251-b.yaml").write_text("claims: []\n", encoding="utf-8")
    assert [p.stem for p in patches_since(251, d)] == ["0251-b"]


# ── render_banner ────────────────────────────────────────


def test_banner_is_none_when_everything_is_current() -> None:
    assert render_banner([_state("0251-gameplay", State.CURRENT)]) is None


def test_banner_names_only_the_exceptions() -> None:
    out = render_banner(
        [
            _state("0251-gameplay", State.CURRENT),
            _state("0253-manufacturers", State.UNAPPLIED),
        ]
    )
    assert out is not None
    assert "0253-manufacturers" in out
    assert "0251-gameplay" not in out


def test_banner_wording_is_relative_to_the_report() -> None:
    out = render_banner([_state("0253-manufacturers", State.UNAPPLIED)])
    assert out is not None
    assert "STALE — database and patches/ do not match" in out
    assert "absent from the report below" in out


def test_banner_shows_the_applied_time_for_an_edited_patch() -> None:
    out = render_banner([_state("0251-gameplay", State.EDITED)])
    assert out is not None
    assert f"EDITED SINCE APPLIED — audited as of {LOCAL_HHMM}" in out


def test_banner_is_framed_by_matching_rules() -> None:
    out = render_banner([_state("0253-manufacturers", State.UNAPPLIED)])
    assert out is not None
    lines = out.splitlines()
    assert lines[0] == lines[-1]
    assert set(lines[0]) == {"═"}


# ── render_status ────────────────────────────────────────


def test_status_answers_affirmatively_when_current() -> None:
    """Standalone, silence is indistinguishable from a broken command."""
    out = render_status(
        [_state("0239-a", State.CURRENT), _state("0252-b", State.CURRENT)]
    )
    assert (
        out
        == "patches/ vs the dev DB — 2 patches (0239-0252), all applied and current."
    )


def test_status_expands_only_when_there_is_drift() -> None:
    out = render_status(
        [
            _state("0239-a", State.CURRENT),
            _state("0251-gameplay", State.EDITED),
            _state("0253-manufacturers", State.UNAPPLIED),
        ]
    )
    assert out.splitlines() == [
        "patches/ vs the dev DB — 3 patches (0239-0253):",
        "  1 applied and current",
        f"  0251-gameplay        EDITED SINCE APPLIED (applied {LOCAL_HHMM})",
        "  0253-manufacturers   NOT APPLIED",
    ]


def test_status_wording_is_not_report_relative() -> None:
    """There is no report below a standalone answer, so it must not claim one."""
    out = render_status([_state("0253-manufacturers", State.UNAPPLIED)])
    assert "report below" not in out


def test_status_singular_for_one_patch() -> None:
    assert "1 patch (" in render_status([_state("0239-a", State.CURRENT)])


def test_status_handles_an_empty_patch_dir() -> None:
    assert render_status([]) == "No patches in patches/."
