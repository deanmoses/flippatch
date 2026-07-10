"""Tests for the shared AI-lint CLI guards (scope + per-invocation ceiling).

Both AI-spending lint CLIs (verify-citations, lint-descriptions) route through
these: a run must name patch ids, and a scoped run's known call count must not
exceed the hard per-invocation ceiling — either refusal lands before the client is
built, so it costs nothing.
"""

from __future__ import annotations

from ai_lint.cli_common import oversize_error, scope_error
from common.ai.client import MAX_REQUESTS


def test_scope_error_refuses_a_bare_unscoped_run():
    msg = scope_error((), cost="one paid AI call per cite")
    assert msg is not None
    assert "Pass patch ids" in msg  # tells the caller how to scope
    assert "one paid AI call per cite" in msg  # the tool's cost phrase is threaded in


def test_scope_error_is_satisfied_by_explicit_ids():
    assert scope_error(("0114",), cost="x") is None  # scoped by id


def test_oversize_error_fires_only_above_the_ceiling():
    assert oversize_error(MAX_REQUESTS) is None  # exactly at the ceiling is allowed
    assert oversize_error(MAX_REQUESTS - 1) is None
    msg = oversize_error(MAX_REQUESTS + 1)
    assert msg is not None
    assert str(MAX_REQUESTS) in msg  # names the ceiling
    assert str(MAX_REQUESTS + 1) in msg  # and what the run would have made
    assert "fewer patches" in msg  # points at the fix: chunk the scope
