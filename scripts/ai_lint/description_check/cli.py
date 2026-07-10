"""CLI entrypoint for the description checker.

Run via the opt-in ``make lint-descriptions`` target (which sets
``PYTHONPATH=scripts``):

    make lint-descriptions ARGS="0059 --rules plagiarism,single-source-spine"

Requires ``ANTHROPIC_API_KEY`` — exits with a clear error if unset.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common.ai.client import AiBudgetError, AiUnavailableError, require_ai_client
from common.catalog.entity_index import DEFAULT_TYPES, EntityIndex
from common.related_projects import FLIPCOMMONS_DB, REPO_ROOT, load_env

from ai_lint.cli_common import emit, oversize_error, scope_error, select_rules
from ai_lint.corpus import Corpus
from ai_lint.description_check.runner import vet_description
from ai_lint.patch_load import iter_description_units, load_patches
from ai_lint.report import (
    DESCRIPTION_RULES,
    RULE_MISSING_WIKILINK,
    RULE_PLAGIARISM,
    RULE_SINGLE_SOURCE_SPINE,
    RULE_UNKNOWN_MODEL,
    Severity,
)

_INDEX_RULES = frozenset({RULE_UNKNOWN_MODEL, RULE_MISSING_WIKILINK})
_CORPUS_RULES = frozenset({RULE_PLAGIARISM, RULE_SINGLE_SOURCE_SPINE})


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="lint-descriptions",
        description="AI editorial lint for patch descriptions (requires ANTHROPIC_API_KEY).",
    )
    parser.add_argument(
        "patch_ids",
        nargs="*",
        help="patch numbers/stems to check (required; a run may not exceed the ceiling)",
    )
    parser.add_argument(
        "--patches-dir", default=str(REPO_ROOT / "patches"), help="patches directory"
    )
    parser.add_argument(
        "--rules", default="", help=f"only these: {','.join(DESCRIPTION_RULES)}"
    )
    parser.add_argument("--disable", default="", help="run all rules except these")
    parser.add_argument(
        "--types",
        default="",
        help="entity types for the wikilink index (default: substantive)",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--min-severity",
        choices=["info", "warning"],
        default="info",
        dest="min_severity",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_env()
    args = _parse_args(argv)
    enabled = select_rules(DESCRIPTION_RULES, args.rules, args.disable)

    error = scope_error(args.patch_ids, cost="this makes AI calls per description")
    if error is not None:
        print(f"error: {error}", file=sys.stderr)
        return 2

    # Count the in-scope work up front (cheap, no API key): each enabled rule makes
    # at most one call per description unit, so units x rules is the run's call
    # ceiling — refuse before spending if it exceeds the per-invocation ceiling.
    patches = list(load_patches(Path(args.patches_dir), tuple(args.patch_ids)))
    units = [
        unit
        for filename, data in patches
        for unit in iter_description_units(filename, data)
    ]
    max_calls = len(units) * len(enabled)
    error = oversize_error(max_calls)
    if error is not None:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(
        f"lint-descriptions: {len(units)} description(s) across {len(patches)} "
        f"patch(es), {len(enabled)} rule(s) — at most {max_calls} model call(s)",
        file=sys.stderr,
    )

    try:
        ai = require_ai_client()
    except AiUnavailableError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    index: EntityIndex | None = None
    if enabled & _INDEX_RULES:
        if FLIPCOMMONS_DB.is_file():
            types = tuple(t.strip() for t in args.types.split(",") if t.strip())
            index = EntityIndex.build(FLIPCOMMONS_DB, types or DEFAULT_TYPES)
        else:
            print(
                f"warning: flipcommons dev DB not found at {FLIPCOMMONS_DB} — "
                f"skipping wikilink/unknown-model rules (set FLIPCOMMONS_DIR)",
                file=sys.stderr,
            )

    corpus = Corpus.open()
    if enabled & _CORPUS_RULES and not corpus.available:
        print(
            "warning: pinexplore corpus unavailable — plagiarism uses inline "
            "quotes only, single-source-spine is skipped (set PINEXPLORE_DIR)",
            file=sys.stderr,
        )

    findings = []
    try:
        for unit in units:
            findings.extend(
                vet_description(
                    unit, enabled=enabled, ai=ai, index=index, corpus=corpus
                )
            )
    except AiBudgetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    finally:
        print(
            f"lint-descriptions: {ai.request_count} AI calls, "
            f"{ai.usage.total_tokens} tokens",
            file=sys.stderr,
        )
    return emit(findings, as_json=args.json, min_severity=Severity(args.min_severity))


if __name__ == "__main__":
    raise SystemExit(main())
