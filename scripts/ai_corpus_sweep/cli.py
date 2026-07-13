"""CLI entrypoint for the corpus sweep — the thin stateful shell.

Run via ``make sweep`` (which sets ``PYTHONPATH=scripts``):

    make sweep ARGS="path/to/candidates.jsonl --no-ai"      # free reconcile preview
    make sweep ARGS="path/to/candidates.jsonl --limit 10"   # cheap trial run
    make sweep ARGS="path/to/candidates.jsonl --resume --max-requests 400"
    make sweep ARGS="path/to/candidates.jsonl --status"     # progress, anytime, free
    make sweep ARGS="path/to/candidates.jsonl --regate"     # re-gate stored answers, free

Localhost-only: needs the flipcommons dev DB (reconcile + target resolution)
and, for judging, pinexplore's evidence stores plus ``ANTHROPIC_API_KEY``.

The shell does the impure work — resolve sibling paths, build the client and
index, persist artifacts incrementally, narrate progress — and refuses a run
whose candidate count exceeds the request cap rather than dying mid-spend.
``results.json`` is written after every judged row (atomic replace), so a
killed or budget-stopped run resumes with ``--resume`` instead of re-paying.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from common.ai.client import (
    MAX_REQUESTS,
    AiBudgetError,
    AiUnavailableError,
    require_ai_client,
)
from common.related_projects import (
    EXPLORE_DUCKDB,
    FLIPCOMMONS_DB,
    WEB_CACHE_DB,
    load_env,
)

from ai_corpus_sweep.candidates import CandidateError, load_candidates
from ai_corpus_sweep.catalog import SweepCatalog
from ai_corpus_sweep.render import (
    progress_line,
    render_reconcile,
    render_review,
    render_status,
)
from ai_corpus_sweep.sweep import (
    SweepRow,
    reconcile_candidates,
    regate_rows,
    row_from_json,
    sweep_candidates,
    verify_fill_rows,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ai_corpus_sweep.candidates import CandidateRow
    from ai_corpus_sweep.sweep import EvidenceFn

RESULTS_NAME = "results.json"
REVIEW_NAME = "REVIEW.md"
RECONCILE_NAME = "RECONCILE.md"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sweep",
        description=(
            "Judge a candidate set's corpus-vs-catalog deltas: reconcile against "
            "the dev DB, fan each candidate's full note through a stateless "
            "trusted-tier call, gate deterministically, and emit results.json + "
            "REVIEW.md (requires ANTHROPIC_API_KEY unless --no-ai)."
        ),
    )
    parser.add_argument(
        "candidates",
        type=Path,
        help="candidates JSONL file (one {ipdb_id, field, hint?, evidence?} per line)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="artifact directory (default: the candidates file's directory)",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="reconcile only: bucket candidates against the catalog, spend nothing",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help=(
            "print progress from the out dir's results.json and exit — safe to "
            "run at any time, including while a sweep is running"
        ),
    )
    parser.add_argument(
        "--regate",
        action="store_true",
        help=(
            "re-run the deterministic gates over results.json's stored answers "
            "(no AI calls, no spend) — after a gate fix or a dev-DB rebuild"
        ),
    )
    parser.add_argument(
        "--verify-fills",
        action="store_true",
        dest="verify_fills",
        help=(
            "run ONLY the quote-supports-claim check (one trusted call each) "
            "over fills not yet checked — for runs judged before the fill gate"
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="judge at most N pending candidates (a cheap trial run)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="skip candidates already judged in the out dir's results.json",
    )
    parser.add_argument(
        "--max-requests",
        type=int,
        default=MAX_REQUESTS,
        dest="max_requests",
        help=(
            f"per-invocation AI-call ceiling (default {MAX_REQUESTS}); the run "
            "refuses up front if the pending candidate count exceeds it"
        ),
    )
    return parser.parse_args(argv)


def _load_previous(results_path: Path) -> list[SweepRow]:
    if not results_path.is_file():
        return []
    raw = json.loads(results_path.read_text())
    rows_raw = raw.get("rows", []) if isinstance(raw, dict) else []
    return [row_from_json(row) for row in rows_raw if isinstance(row, dict)]


def _write_results(results_path: Path, rows: Sequence[SweepRow]) -> None:
    """Atomic-replace write so a kill mid-write never corrupts the artifact."""
    payload = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "rows": [row.to_json() for row in rows],
    }
    tmp = results_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(results_path)


def _evidence_fn() -> EvidenceFn | None:
    """quote_verify's source adapter over pinexplore's stores, or None if absent."""
    if not WEB_CACHE_DB.is_file() or not EXPLORE_DUCKDB.is_file():
        return None
    from quote_verify.verify_quotes import _Sources

    sources = _Sources(WEB_CACHE_DB, EXPLORE_DUCKDB)
    return sources.free_text_for


def main(argv: list[str] | None = None) -> int:
    load_env()
    args = _parse_args(argv)

    try:
        candidates = load_candidates(args.candidates)
    except (CandidateError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out_dir: Path = args.out or args.candidates.parent
    results_path = out_dir / RESULTS_NAME

    if args.status:
        # Pure artifact read — no DB, no siblings, safe during a running sweep.
        judged = _load_previous(results_path)
        if not judged and not results_path.is_file():
            print(f"no results yet at {results_path}", file=sys.stderr)
            return 2
        print(render_status(judged, total_candidates=len(candidates)))
        return 0

    if not FLIPCOMMONS_DB.is_file():
        print(
            f"error: flipcommons dev DB not found at {FLIPCOMMONS_DB} — the sweep "
            "reconciles against it (set FLIPCOMMONS_DIR)",
            file=sys.stderr,
        )
        return 2
    catalog = SweepCatalog(FLIPCOMMONS_DB)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.no_ai:
        report = render_reconcile(reconcile_candidates(candidates, catalog=catalog))
        (out_dir / RECONCILE_NAME).write_text(report + "\n")
        print(report)
        print(f"\n[wrote {out_dir / RECONCILE_NAME}]", file=sys.stderr)
        return 0

    if args.regate:
        previous = _load_previous(results_path)
        if not previous:
            print(f"error: nothing to regate at {results_path}", file=sys.stderr)
            return 2
        from common.catalog.entity_index import EntityIndex

        index = EntityIndex.build(FLIPCOMMONS_DB, types=("model", "title"))
        regated = regate_rows(previous, catalog=catalog, index=index)
        _write_results(results_path, regated)
        (out_dir / REVIEW_NAME).write_text(render_review(regated) + "\n")
        changed = sum(
            1
            for old, new in zip(previous, regated, strict=True)
            if old.disposition != new.disposition
        )
        print(
            f"regate: {len(regated)} rows re-gated (no AI calls), "
            f"{changed} changed disposition",
            file=sys.stderr,
        )
        print(render_status(regated, total_candidates=len(candidates)))
        print(f"[wrote {results_path} and {out_dir / REVIEW_NAME}]", file=sys.stderr)
        return 0

    if args.verify_fills:
        previous = _load_previous(results_path)
        unchecked = sum(
            1
            for row in previous
            if row.disposition == "fill" and row.quote_supported is None
        )
        if not unchecked:
            print("no unchecked fills — nothing to verify", file=sys.stderr)
            return 0
        if unchecked > args.max_requests:
            print(
                f"error: {unchecked} unchecked fills exceed the AI-call ceiling "
                f"({args.max_requests}); raise --max-requests {unchecked}",
                file=sys.stderr,
            )
            return 2
        try:
            ai = require_ai_client(max_requests=args.max_requests)
        except AiUnavailableError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(
            f"verifying {unchecked} fill quotes (quote-supports-claim, one call "
            f"each); results.json is rewritten after every row.",
            file=sys.stderr,
        )
        checked: list[SweepRow] = []
        demoted = 0
        try:
            for row in verify_fill_rows(previous, catalog=catalog, ai=ai):
                checked.append(row)
                if row.disposition == "quote-unsupported":
                    demoted += 1
                _write_results(results_path, checked + previous[len(checked) :])
        finally:
            _write_results(results_path, checked + previous[len(checked) :])
            (out_dir / REVIEW_NAME).write_text(
                render_review(checked + previous[len(checked) :]) + "\n"
            )
            print(
                f"verify-fills: {ai.request_count} AI calls, "
                f"{ai.usage.total_tokens} tokens — {demoted} fill(s) demoted to "
                "quote-unsupported",
                file=sys.stderr,
            )
        print(render_status(checked, total_candidates=len(candidates)))
        return 0

    previous = _load_previous(results_path) if args.resume else []
    done_keys = {row.key for row in previous}
    pending: list[CandidateRow] = [c for c in candidates if c.key not in done_keys]
    if args.limit is not None:
        pending = pending[: args.limit]

    if not pending:
        print("nothing pending — all candidates already judged", file=sys.stderr)
        (out_dir / REVIEW_NAME).write_text(render_review(previous) + "\n")
        return 0

    if len(pending) > args.max_requests:
        print(
            f"error: {len(pending)} pending candidates exceed the AI-call ceiling "
            f"({args.max_requests}). Re-run with --limit for a slice, or raise "
            f"--max-requests {len(pending)} deliberately.",
            file=sys.stderr,
        )
        return 2

    evidence_for = _evidence_fn()
    if evidence_for is None:
        print(
            f"error: pinexplore evidence stores not found ({WEB_CACHE_DB}, "
            f"{EXPLORE_DUCKDB}) — `make pull` / `make explore` there, or set "
            "PINEXPLORE_DIR",
            file=sys.stderr,
        )
        return 2

    try:
        ai = require_ai_client(max_requests=args.max_requests)
    except AiUnavailableError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    from common.catalog.entity_index import EntityIndex

    index = EntityIndex.build(FLIPCOMMONS_DB, types=("model", "title"))

    # The safety contract, stated where the operator can see it — not buried in
    # a docstring. Ctrl-C is always safe.
    print(
        f"sweeping {len(pending)} candidates. {RESULTS_NAME} and {REVIEW_NAME} "
        f"are rewritten after EVERY row — Ctrl-C loses at most the row in "
        f"flight; check progress anytime with --status; continue with --resume.",
        file=sys.stderr,
    )

    rows: list[SweepRow] = list(previous)
    interrupted = False
    started = time.monotonic()
    try:
        stream = sweep_candidates(
            pending, catalog=catalog, index=index, evidence_for=evidence_for, ai=ai
        )
        for done, row in enumerate(stream, start=1):
            rows.append(row)
            _write_results(results_path, rows)
            (out_dir / REVIEW_NAME).write_text(render_review(rows) + "\n")
            review_count = sum(1 for r in rows if r.needs_review)
            eta_min = (len(pending) - done) * (time.monotonic() - started) / done / 60
            print(
                f"{progress_line(done, len(pending), row)} "
                f"| review {review_count} | ~{eta_min:.0f}m left",
                file=sys.stderr,
            )
    except AiBudgetError as exc:
        interrupted = True
        print(f"\nbudget stop: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        interrupted = True
        print("\ninterrupted — partial results saved", file=sys.stderr)

    _write_results(results_path, rows)
    (out_dir / REVIEW_NAME).write_text(render_review(rows) + "\n")

    review = sum(1 for row in rows if row.needs_review)
    print(
        f"\nsweep: {len(rows)} rows ({review} need review) — "
        f"{ai.request_count} AI calls, {ai.usage.total_tokens} tokens",
        file=sys.stderr,
    )
    print(f"[wrote {results_path} and {out_dir / REVIEW_NAME}]", file=sys.stderr)
    if interrupted:
        print(
            f"re-run with --resume to judge the remaining candidates:\n"
            f'  make sweep ARGS="{args.candidates} --resume"',
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
