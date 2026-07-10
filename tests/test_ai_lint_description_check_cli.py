"""CLI guard test for lint-descriptions — the same scope requirement as the verifier."""

from __future__ import annotations


def test_cli_main_refuses_bare_run_without_spending(capsys):
    # A bare `make lint-descriptions` used to fan AI calls across every description
    # in the corpus. Now it refuses before the client is built when no ids are given.
    from ai_lint.description_check.cli import main

    assert main([]) == 2
    err = capsys.readouterr().err
    assert "without a scope" in err
    assert "model call" not in err  # the run announcement never printed — nothing ran
