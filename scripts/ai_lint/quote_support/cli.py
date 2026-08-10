"""CLI entrypoint for the quote-support checker.

Run via the opt-in ``make verify-quote-support`` target (which sets
``PYTHONPATH=scripts``):

    make verify-quote-support ARGS="0059"        # scoped to one patch
    make verify-quote-support ARGS="0059 0114"   # a few patches

**A run must name patch ids.** This tool makes one paid AI call per claim on the
trusted (expensive) model, so a bare invocation is refused rather than silently
billing the whole corpus. There is no run-everything option: the corpus exceeds the
per-invocation ceiling (:data:`~common.ai.client.MAX_REQUESTS`), so a run must be
scoped small enough to fit — a scope whose claim count would exceed the ceiling is
refused too, telling the caller to narrow it. An id naming no patch refuses the
run rather than being dropped from it — a partial run must not bill and report as
the scope that was asked for.

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
from common.patch_files import unmatched_scope_error
from common.paths import REPO_ROOT, load_env

from ai_lint.cli_common import emit, oversize_error, scope_error
from ai_lint.corpus import Corpus
from ai_lint.patch_load import load_patches
from ai_lint.quote_support.verify import collect_claims, unjudged, verify_claim
from ai_lint.report import Severity


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="verify-quote-support",
        description=(
            "AI check that each claim's cited evidence supports it (requires "
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
        cost="this makes one paid AI call per claim on the trusted model",
    )
    if error is not None:
        print(f"error: {error}", file=sys.stderr)
        return 2

    patches_dir = Path(args.patches_dir)
    error = unmatched_scope_error(patches_dir, args.patch_ids)
    if error is not None:
        print(f"error: {error}", file=sys.stderr)
        return 2

    # Count the in-scope claims up front (loading patches is cheap and needs no API
    # key). verify_claim makes at most ONE trusted-model call per claim, so the claim
    # count is the run's call count — refuse before spending if it exceeds the
    # per-invocation ceiling, telling the caller to scope to fewer patches.
    patches = list(load_patches(patches_dir, tuple(args.patch_ids)))
    claims = [
        claim for filename, data in patches for claim in collect_claims(filename, data)
    ]
    error = oversize_error(len(claims))
    if error is not None:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(
        f"verify-quote-support: {len(claims)} claim(s) across {len(patches)} "
        f"patch(es) in scope — at most {len(claims)} trusted-model call(s)",
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
        for claim in claims:
            try:
                finding = verify_claim(claim, corpus, ai)
                if finding is not None:
                    findings.append(finding)
            except AiError as exc:
                findings.append(unjudged(claim, str(exc)))
                print(f"  ! {claim.entity_ref}: not judged — {exc}", file=sys.stderr)
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
