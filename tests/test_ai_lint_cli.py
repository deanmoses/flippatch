"""Tests for CLI plumbing: rule selection, exit codes, and the no-key gate."""

from __future__ import annotations

import pytest
from ai_lint.cli_common import emit, select_rules
from ai_lint.report import DESCRIPTION_RULES, Finding, Severity


def test_select_rules_defaults_and_disable():
    assert select_rules(DESCRIPTION_RULES, "", "") == frozenset(DESCRIPTION_RULES)
    kept = select_rules(DESCRIPTION_RULES, "", "plagiarism")
    assert "plagiarism" not in kept
    assert "unknown-model" in kept


def test_select_rules_allowlist():
    assert select_rules(DESCRIPTION_RULES, "plagiarism", "") == frozenset(
        {"plagiarism"}
    )


def test_select_rules_unknown_raises():
    with pytest.raises(SystemExit):
        select_rules(DESCRIPTION_RULES, "no-such-rule", "")


def test_emit_exit_code_is_nonzero_only_for_warnings(capsys):
    info = Finding("unknown-model", Severity.INFO, "p", "e", "an info")
    assert emit([info], as_json=False, min_severity=Severity.INFO) == 0
    warn = Finding("plagiarism", Severity.WARNING, "p", "e", "a warning")
    assert emit([warn], as_json=False, min_severity=Severity.INFO) == 1


def test_description_cli_fatal_without_key(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from ai_lint.description_check import cli

    # Neutralize the .env load so the test controls the environment: we are
    # asserting the no-key gate, not whether the dev machine has a .env.
    monkeypatch.setattr(cli, "load_env", lambda: None)
    assert cli.main(["--patches-dir", str(tmp_path)]) == 2


def test_citation_cli_fatal_without_key(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from ai_lint.citation_verify import cli

    monkeypatch.setattr(cli, "load_env", lambda: None)
    assert cli.main(["--patches-dir", str(tmp_path)]) == 2
