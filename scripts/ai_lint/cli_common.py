"""Shared CLI plumbing for both entrypoints: rule selection and output.

Keeps the two ``cli.py`` scripts thin and their behavior identical — same
``--rules``/``--disable`` semantics, same human/JSON rendering, same exit-code
rule (non-zero iff any ``WARNING`` finding exists, so it can gate a pre-ingest
workflow later).
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

from common.ai.client import MAX_REQUESTS

from ai_lint.report import Severity

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ai_lint.report import Finding


def scope_error(patch_ids: Sequence[str], *, cost: str) -> str | None:
    """Refusal message when an AI-spending run names no patches, or None when scoped.

    These tools make a paid AI call per unit of work; a bare invocation would fan
    the whole patch corpus, unbidden — a forgotten ``ARGS=`` billing everything. So a
    run must name explicit patch ids. There is no run-everything option: the whole
    corpus exceeds the per-invocation ceiling anyway, so the only path is a scope
    small enough to fit. Call before the client is built, so a refusal is free.
    ``cost`` names what each unit costs, e.g. "one paid AI call per cite".
    """
    if patch_ids:
        return None
    return (
        f"refusing to run over the entire patch corpus without a scope — {cost}. "
        f"Pass patch ids to scope the run (a run may not exceed {MAX_REQUESTS} AI calls)."
    )


def oversize_error(call_count: int) -> str | None:
    """Refusal message when a scoped run would exceed the per-invocation ceiling.

    The ceiling (:data:`~common.ai.client.MAX_REQUESTS`) is a hard spend/time cap,
    sized just above the largest single patch. A scoped run whose known call count
    exceeds it is refused *before* spending — the caller narrows the scope to fewer
    patches and runs again (the auto-sizer aborts rather than silently sizing up).
    """
    if call_count <= MAX_REQUESTS:
        return None
    return (
        f"this run would make {call_count} AI calls, over the {MAX_REQUESTS}-call "
        f"per-invocation ceiling — scope to fewer patches and run again."
    )


def select_rules(
    all_rules: Sequence[str], rules_arg: str, disable_arg: str
) -> frozenset[str]:
    """Resolve ``--rules`` (allowlist) and ``--disable`` (denylist) against defaults.

    Unknown ids raise ``SystemExit`` with a clear message.
    """
    known = set(all_rules)

    def parse(raw: str) -> set[str]:
        ids = {item.strip() for item in raw.split(",") if item.strip()}
        unknown = ids - known
        if unknown:
            raise SystemExit(
                f"unknown rule(s): {sorted(unknown)} (known: {sorted(known)})"
            )
        return ids

    selected = parse(rules_arg) if rules_arg else set(all_rules)
    return frozenset(selected - parse(disable_arg) if disable_arg else selected)


def _severity_at_least(finding: Finding, minimum: Severity) -> bool:
    order = {Severity.INFO: 0, Severity.WARNING: 1}
    return order[finding.severity] >= order[minimum]


def emit(findings: list[Finding], *, as_json: bool, min_severity: Severity) -> int:
    """Print findings (human or JSON); return the process exit code."""
    shown = [f for f in findings if _severity_at_least(f, min_severity)]
    warnings = [f for f in findings if f.severity is Severity.WARNING]

    if as_json:
        print(json.dumps([f.as_dict() for f in shown], indent=2))
    else:
        _print_human(shown)
    print(
        f"\n{len(warnings)} warning(s), "
        f"{len(findings) - len(warnings)} info — "
        f"{len(findings)} finding(s) total",
        file=sys.stderr,
    )
    return 1 if warnings else 0


def _print_human(findings: list[Finding]) -> None:
    by_key: dict[tuple[str, str], list[Finding]] = {}
    for finding in findings:
        by_key.setdefault((finding.patch, finding.entity_ref), []).append(finding)
    for (patch, entity_ref), group in sorted(by_key.items()):
        print(f"\n{patch}  {entity_ref}")
        for finding in group:
            mark = "⚠" if finding.severity is Severity.WARNING else "·"
            print(f"  {mark} [{finding.rule}] {finding.message}")
            if finding.suggestion:
                print(f"      → {finding.suggestion}")
            if finding.reason:
                print(f"      reason: {finding.reason}")
