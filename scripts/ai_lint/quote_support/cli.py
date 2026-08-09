"""CLI entrypoint for the quote-support checker.

Run via the opt-in ``make verify-quote-support`` target (which sets
``PYTHONPATH=scripts``):

    make verify-quote-support ARGS="0059"        # scoped to one patch
    make verify-quote-support ARGS="0059 0114"   # a few patches

**A run must name patch ids.** This tool makes one paid AI call per cite on the
trusted (expensive) model, so a bare invocation is refused rather than silently
billing the whole corpus. There is no run-everything option: the corpus exceeds the
per-invocation ceiling (:data:`~common.ai.client.MAX_REQUESTS`), so a run must be
scoped small enough to fit — a scope whose cite count would exceed the ceiling is
refused too, telling the caller to narrow it.

Requires ``ANTHROPIC_API_KEY`` — exits with a clear error if unset.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common.ai.client import (
    AiBudgetError,
    AiError,
    AiUnavailableError,
    require_ai_client,
)
from common.paths import REPO_ROOT, load_env

from ai_lint.cli_common import emit, oversize_error, scope_error
from ai_lint.corpus import Corpus
from ai_lint.patch_load import load_patches
from ai_lint.quote_support.verify import collect_pairs, verify_pair
from ai_lint.report import Severity


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="verify-quote-support",
        description=(
            "AI check that each cite's quote supports its claim (requires "
            "ANTHROPIC_API_KEY). Builds on `make verify-quote-verbatim`."
        ),
    )
    parser.add_argument(
        "patch_ids",
        nargs="*",
        help="patch numbers/stems to verify (required; a run may not exceed the ceiling)",
    )
    parser.add_argument(
        "--patches-dir", default=str(REPO_ROOT / "patches"), help="patches directory"
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

    error = scope_error(
        args.patch_ids,
        cost="this makes one paid AI call per cite on the trusted model",
    )
    if error is not None:
        print(f"error: {error}", file=sys.stderr)
        return 2

    # Count the in-scope cite pairs up front (loading patches is cheap and needs no
    # API key). verify_pair makes at most ONE trusted-model call per pair, so the
    # pair count is the run's call count — refuse before spending if it exceeds the
    # per-invocation ceiling, telling the caller to scope to fewer patches.
    patches = list(load_patches(Path(args.patches_dir), tuple(args.patch_ids)))
    pairs = [
        pair for filename, data in patches for pair in collect_pairs(filename, data)
    ]
    error = oversize_error(len(pairs))
    if error is not None:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(
        f"verify-quote-support: {len(pairs)} cite(s) across {len(patches)} patch(es) in "
        f"scope — at most {len(pairs)} trusted-model call(s)",
        file=sys.stderr,
    )

    try:
        ai = require_ai_client()
    except AiUnavailableError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    corpus = Corpus.open()
    if not corpus.available:
        print(
            "error: pinexplore corpus unavailable — citation support cannot be "
            "verified without the cited source text to judge each quote in "
            "context (set PINEXPLORE_DIR, or run `make pull` in pinexplore)",
            file=sys.stderr,
        )
        return 2

    findings = []
    try:
        for pair in pairs:
            try:
                finding = verify_pair(pair, corpus, ai)
                if finding is not None:
                    findings.append(finding)
            except AiError as exc:
                print(
                    f"  ! {pair.entity_ref}: skipped — AI error: {exc}",
                    file=sys.stderr,
                )
                continue
    except AiBudgetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    finally:
        print(
            f"verify-quote-support: {ai.request_count} AI calls, "
            f"{ai.usage.total_tokens} tokens",
            file=sys.stderr,
        )
    return emit(findings, as_json=args.json, min_severity=Severity(args.min_severity))


if __name__ == "__main__":
    raise SystemExit(main())
