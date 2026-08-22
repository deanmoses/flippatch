"""Tests for scripts/analysis/audit-patches — the catalog-audit wrapper.

The wrapper's own job is the staleness banner: the audit reports on what the
local flipcommons DB *ingested*, while the patch range is derived from the
files on disk, so a file the DB has not seen — or has seen in an older form —
makes the report quietly wrong about its own scope. Everything here drives the
real ``/bin/sh`` script against a hermetic fake flipcommons: a stub ``audit``
that prints a recognisable report, a real SQLite ledger, and a fake ``duckdb``
on PATH so the availability probe passes without the binary installed.

The patch set is planted too, under ``FLIPPATCH_PATCHES_DIR``. Reading the repo's
own ``patches/`` instead looks tempting — the wrapper hands the banner a patch
NUMBER, so the set it checks is a directory rather than a list of filenames — but
that directory empties completely every time a series is archived to
``patches/shipped/``, and a suite whose every fixture is derived from it then has
nothing to assert on and no way to say why.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path

WRAPPER = (
    Path(__file__).resolve().parent.parent / "scripts" / "analysis" / "audit-patches"
)

# The planted mutable set. Deliberately uneven in length: the banner pads stems to a
# common width, and a set of equal-length stems would let a missing pad pass unnoticed.
PATCHES = ["0239-first-of-the-mutable-set", "0244-middle", "0252-last"]

# Ledger instants as ingest_patches stores them: UTC, space-separated, microseconds.
# Anchored either side of the planted files' mtime so a case is decided by the fixture:
# FUTURE reads as current, PAST as edited-since. The banner renders LOCAL time, so the
# expected string is derived rather than hardcoded; otherwise the suite passes only in
# the timezone it was written in.
FUTURE_UTC = "2099-01-01 12:00:00.000000"
PAST_UTC = "2020-01-01 12:00:00.000000"
PAST_LOCAL_HHMM = (
    datetime.fromisoformat(PAST_UTC).replace(tzinfo=UTC).astimezone().strftime("%H:%M")
)
# Every planted file's mtime, fixed between the two instants above so that "edited since
# applied" is a property of the ledger row rather than of when the test happened to run.
PLANTED_MTIME = int(
    datetime.fromisoformat("2026-08-15 23:37:40.179897").replace(tzinfo=UTC).timestamp()
)

REPORT_FIRST_LINE = "Auditing 55 records touched by 3 patches, 0239-0252."
# The stub echoes the patch number it was invoked with, so a test can assert the scope
# the wrapper derived — the difference between "audited nothing" and "audited from N".
SINCE_PREFIX = "stub-audit since="


def _number(stem: str) -> str:
    """The patch number as the wrapper renders it — leading zeros stripped."""
    return str(int(stem.split("-")[0]))


def _current(*, omit: str = "", aged: str = "") -> dict[str, str]:
    """A ledger in which every planted patch is applied and current, bar the named."""
    return {
        stem: (PAST_UTC if stem == aged else FUTURE_UTC)
        for stem in PATCHES
        if stem != omit
    }


def _fake_flipcommons(tmp_path: Path, applied: dict[str, str]) -> Path:
    """A flipcommons checkout holding just what the wrapper touches.

    ``applied`` maps patch id to the UTC ``finished_at`` of its successful run.
    """
    fc = tmp_path / "flipcommons"
    (fc / "backend").mkdir(parents=True)
    (fc / "scripts" / "analysis").mkdir(parents=True)

    db = fc / "backend" / "db.sqlite3"
    con = sqlite3.connect(db)
    # Only the columns the staleness query reads. The real table is far wider;
    # a narrow stand-in keeps the fixture honest about what the wrapper depends on.
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
    # Noise the query must exclude: a failed run, and a non-patch ingest.
    con.execute(
        "INSERT INTO provenance_ingestrun VALUES ('0299-failed', 'failed', ?)",
        (FUTURE_UTC,),
    )
    con.execute(
        "INSERT INTO provenance_ingestrun VALUES (NULL, 'success', ?)", (FUTURE_UTC,)
    )
    con.commit()
    con.close()

    audit = fc / "scripts" / "analysis" / "audit"
    audit.write_text(
        f'#!/bin/sh\necho "{SINCE_PREFIX}$1"\necho "{REPORT_FIRST_LINE}"\n',
        encoding="utf-8",
    )
    audit.chmod(0o755)
    return fc


def _patches_dir(tmp_path: Path) -> Path:
    """The directory the wrapper will audit as the mutable set. Empty until planted."""
    patches = tmp_path / "patches"
    patches.mkdir(exist_ok=True)
    return patches


def _patch_file(tmp_path: Path, stem: str, mtime: int = PLANTED_MTIME) -> Path:
    path = _patches_dir(tmp_path) / f"{stem}.yaml"
    path.write_text("claims: []\n", encoding="utf-8")
    os.utime(path, (mtime, mtime))
    return path


def _plant(tmp_path: Path, stems: list[str] = PATCHES) -> list[Path]:
    """The mutable set on disk. What the ledger says about it is the test's business."""
    return [_patch_file(tmp_path, stem) for stem in stems]


def _env(tmp_path: Path, fc: Path) -> dict[str, str]:
    """Environment with a fake ``duckdb`` on PATH, so the probe passes without it."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    duckdb = bin_dir / "duckdb"
    duckdb.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    duckdb.chmod(0o755)
    return {
        **os.environ,
        "FLIPCOMMONS_DIR": str(fc),
        "FLIPPATCH_PATCHES_DIR": str(_patches_dir(tmp_path)),
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
    }


def _run(tmp_path: Path, fc: Path, *files: Path) -> str:
    """Run the wrapper with a fake ``duckdb`` on PATH; return combined output."""
    env = _env(tmp_path, fc)
    proc = subprocess.run(
        [str(WRAPPER), *(str(f) for f in files)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    # The wrapper must never fail the commit, whatever it finds.
    assert proc.returncode == 0, proc.stderr
    return proc.stdout + proc.stderr


def test_in_sync_prints_no_banner(tmp_path: Path) -> None:
    _plant(tmp_path)
    fc = _fake_flipcommons(tmp_path, _current())
    out = _run(tmp_path, fc)
    assert "STALE" not in out
    assert REPORT_FIRST_LINE in out


def test_never_applied_is_reported(tmp_path: Path) -> None:
    _plant(tmp_path)
    missing = PATCHES[-1]
    fc = _fake_flipcommons(tmp_path, _current(omit=missing))
    out = _run(tmp_path, fc)
    assert "STALE — database and patches/ do not match" in out
    assert f"{missing} " in out
    assert "NOT APPLIED" in out
    # Every other patch is current, so none of them may be named.
    assert not [stem for stem in PATCHES if stem != missing and stem in out]


def test_edited_since_applied_is_reported_with_local_time(tmp_path: Path) -> None:
    _plant(tmp_path)
    aged = PATCHES[0]
    fc = _fake_flipcommons(tmp_path, _current(aged=aged))
    out = _run(tmp_path, fc)
    assert "EDITED SINCE APPLIED" in out
    assert f"audited as of {PAST_LOCAL_HHMM}" in out


def test_banner_covers_patches_nobody_named(tmp_path: Path) -> None:
    """The report spans `since` onward, so the banner must too.

    Handing the wrapper only the earliest patch used to leave a later unapplied one
    inside the report's range and outside the freshness check — the report silently
    omitted it and the banner, whose whole job is to say so, said nothing.
    """
    named, *_ = _plant(tmp_path)
    unnamed = PATCHES[-1]
    fc = _fake_flipcommons(tmp_path, _current(omit=unnamed))
    out = _run(tmp_path, fc, named)
    assert unnamed in out
    assert "NOT APPLIED" in out


def test_banner_precedes_the_report(tmp_path: Path) -> None:
    """The banner says how far to trust the report, so it must arrive first."""
    _plant(tmp_path)
    fc = _fake_flipcommons(tmp_path, {})
    out = _run(tmp_path, fc)
    assert out.index("STALE") < out.index(REPORT_FIRST_LINE)


def test_both_conditions_render_together(tmp_path: Path) -> None:
    _plant(tmp_path)
    aged, missing = PATCHES[0], PATCHES[-1]
    fc = _fake_flipcommons(tmp_path, _current(aged=aged, omit=missing))
    out = _run(tmp_path, fc)
    edited_line = next(ln for ln in out.splitlines() if aged in ln)
    missing_line = next(ln for ln in out.splitlines() if missing in ln)
    # Stems are padded to a common width so the labels line up.
    assert edited_line.index("EDITED SINCE APPLIED") == missing_line.index(
        "NOT APPLIED"
    )


def test_banner_is_framed_by_matching_rules(tmp_path: Path) -> None:
    _plant(tmp_path)
    fc = _fake_flipcommons(tmp_path, {})
    lines = _run(tmp_path, fc).splitlines()
    rules = [i for i, ln in enumerate(lines) if ln.startswith("═")]
    assert len(rules) == 2
    assert lines[rules[0]] == lines[rules[1]]


# ── scope derivation ─────────────────────────────────────


def test_scope_starts_at_the_lowest_patch_given(tmp_path: Path) -> None:
    fc = _fake_flipcommons(tmp_path, {})
    late = _patch_file(tmp_path, "0253-b")
    early = _patch_file(tmp_path, "0251-a")
    out = _run(tmp_path, fc, late, early)
    assert f"{SINCE_PREFIX}251" in out


def test_a_bare_filename_still_derives_its_number(tmp_path: Path) -> None:
    """A path with no directory component must not read as "no patches given".

    pre-commit passes repo-relative paths, but `make` and a hand-run do not have to,
    and deriving nothing is indistinguishable in the output from a clean catalog.
    """
    fc = _fake_flipcommons(tmp_path, {})
    f = _patch_file(tmp_path, "0251-a")
    proc = subprocess.run(
        [str(WRAPPER), f.name],
        capture_output=True,
        text=True,
        cwd=f.parent,
        env=_env(tmp_path, fc),
        check=False,
    )
    assert f"{SINCE_PREFIX}251" in proc.stdout + proc.stderr


def test_non_patch_arguments_audit_the_whole_mutable_set(tmp_path: Path) -> None:
    """The hook fires on a change to its own implementation, which names no patch.

    Firing and silently doing nothing would be worse than not firing: the run reports
    "Passed" either way, so the gate would look like it had checked something.
    """
    _plant(tmp_path)
    fc = _fake_flipcommons(tmp_path, {})
    out = _run(tmp_path, fc, WRAPPER)
    assert f"{SINCE_PREFIX}{_number(PATCHES[0])}" in out


def test_no_arguments_audit_the_whole_mutable_set(tmp_path: Path) -> None:
    _plant(tmp_path)
    fc = _fake_flipcommons(tmp_path, {})
    out = _run(tmp_path, fc)
    assert f"{SINCE_PREFIX}{_number(PATCHES[0])}" in out


def test_an_empty_mutable_set_says_so_instead_of_exiting_silently(
    tmp_path: Path,
) -> None:
    """Between ships every patch is archived and patches/ holds nothing.

    There is no scope to audit, so this is a skip — but it has to SAY so. pre-commit
    and `make validate-in-db` both report success on no output at all, so exiting
    silently reads as an audit that ran and approved, which is the very failure the
    whole-mutable-set fallback above it exists to prevent.
    """
    _patches_dir(tmp_path)  # exists, empty — nothing planted
    fc = _fake_flipcommons(tmp_path, _current())
    out = _run(tmp_path, fc)
    assert "catalog audit: skipped" in out
    assert "no mutable patches" in out
    assert SINCE_PREFIX not in out


def test_no_database_still_skips_quietly(tmp_path: Path) -> None:
    """Pre-existing behaviour: no dev DB is a skip, not a staleness banner."""
    fc = _fake_flipcommons(tmp_path, {})
    (fc / "backend" / "db.sqlite3").unlink()
    f = _patch_file(tmp_path, "0251-gameplay")
    out = _run(tmp_path, fc, f)
    assert "skipped" in out
    assert "STALE" not in out
