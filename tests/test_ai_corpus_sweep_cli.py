"""Shell tests for the sweep CLI — the offline-safe paths only.

The judging path needs an API key + sibling stores and is not exercised here;
these cover the free ``--no-ai`` reconcile, the artifact locations, and the
refuse-before-spending guards.
"""

from __future__ import annotations

import pytest
from ai_corpus_sweep import cli

from tests.test_ai_corpus_sweep import db_path  # noqa: F401  # fixture reuse


@pytest.fixture
def candidates_file(tmp_path):
    path = tmp_path / "candidates.jsonl"
    path.write_text('{"ipdb_id": 5555, "hint": "hurdy-gurdy"}\n{"ipdb_id": 7777}\n')
    return path


def test_no_ai_writes_reconcile_artifact(monkeypatch, capsys, candidates_file, db_path):  # noqa: F811
    monkeypatch.setattr(cli, "FLIPCOMMONS_DB", db_path)
    assert cli.main([str(candidates_file), "--no-ai"]) == 0
    report = (candidates_file.parent / cli.RECONCILE_NAME).read_text()
    assert "| set | 1 |" in report
    assert "reconcile" in capsys.readouterr().out.lower()


def test_bad_candidates_file_is_a_clean_error(monkeypatch, capsys, tmp_path, db_path):  # noqa: F811
    monkeypatch.setattr(cli, "FLIPCOMMONS_DB", db_path)
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"ipdb_id": 5555, "field": "widebody"}\n')
    assert cli.main([str(bad), "--no-ai"]) == 2
    assert "unknown field" in capsys.readouterr().err


def test_pending_beyond_cap_refuses_before_spending(
    monkeypatch,
    capsys,
    candidates_file,
    db_path,  # noqa: F811
):
    monkeypatch.setattr(cli, "FLIPCOMMONS_DB", db_path)
    assert cli.main([str(candidates_file), "--max-requests", "1"]) == 2
    err = capsys.readouterr().err
    assert "exceed the AI-call ceiling" in err
    assert "--max-requests 2" in err


def test_missing_dev_db_is_a_clean_error(
    monkeypatch, capsys, candidates_file, tmp_path
):
    monkeypatch.setattr(cli, "FLIPCOMMONS_DB", tmp_path / "absent.sqlite3")
    assert cli.main([str(candidates_file), "--no-ai"]) == 2
    assert "dev DB not found" in capsys.readouterr().err


def _seed_results(out_dir, rows):
    import json

    payload = {"rows": [row.to_json() for row in rows]}
    (out_dir / cli.RESULTS_NAME).write_text(json.dumps(payload))


def test_status_reads_the_artifact_without_db_or_ai(capsys, candidates_file):
    from ai_corpus_sweep import gate
    from ai_corpus_sweep.sweep import SweepRow

    _seed_results(
        candidates_file.parent,
        [SweepRow(ipdb_id=5555, disposition=gate.CONFLICT)],
    )
    assert cli.main([str(candidates_file), "--status"]) == 0
    out = capsys.readouterr().out
    assert "judged 1/2 models" in out
    assert "1 pending" in out
    assert "needs review: 1" in out
    assert "conflict 1" in out


def test_status_without_results_is_a_clean_error(capsys, candidates_file):
    assert cli.main([str(candidates_file), "--status"]) == 2
    assert "no results yet" in capsys.readouterr().err


def test_regate_rebuckets_stored_rows_offline(
    monkeypatch,
    capsys,
    candidates_file,
    db_path,  # noqa: F811
):
    from ai_corpus_sweep import gate
    from ai_corpus_sweep.sweep import SweepRow

    monkeypatch.setattr(cli, "FLIPCOMMONS_DB", db_path)
    stale = SweepRow(
        ipdb_id=109,
        disposition=gate.UNRESOLVED,
        relationship_type="conversion_kit",
        verdict="yes",
        quote="Conversion kit for Bally's 1979 'Supersonic'.",
        target_title="Supersonic",
        target_maker="Bally",
        target_year=1979,
        evidence=(("ipdb:109", "Conversion kit for Bally's 1979 'Supersonic'."),),
    )
    _seed_results(candidates_file.parent, [stale])
    assert cli.main([str(candidates_file), "--regate"]) == 0
    captured = capsys.readouterr()
    assert "1 changed disposition" in captured.err
    assert "fill 1" in captured.out
    review = (candidates_file.parent / cli.REVIEW_NAME).read_text()
    assert "`supersonic`" in review
