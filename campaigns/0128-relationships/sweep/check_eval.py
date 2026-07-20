#!/usr/bin/env python3
"""Score a sweep run against the frozen expectations in ``eval-expected.json``.

Why this exists: `--regate` proves a *code* change for free, but a **guidance**
change cannot be regated — changing the prompt changes the model's answers, so
it needs a re-judge and something to measure the result against. Nothing played
that role when `retheme` was added, and the reasoned safety argument for it
("zero overlap with the 39 retheme models") was well-formed and wrong: the type
leaked onto the licensed builds it should never have claimed. A new type's risk
lives in the rows it should NOT claim, and only a frozen baseline sees that.

    uv run python3 check_eval.py            # score results.json
    uv run python3 check_eval.py --verbose  # list every regression

Exit 1 on any regression, so it can gate a guidance change.

The expectations are a human triage of the 2026-07-17 full run, and that triage
was demonstrably coarse in at least one place (the DEFECT 12 label rows). Treat
a failure here as "explain the difference", not "the model is wrong" — and fix
the expectation when the expectation is what's wrong.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def row_key(row: dict) -> str:
    target = row.get("resolved_slug") or (row.get("target_label") or "")[:40]
    return f"{row['ipdb_id']}:{target}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(HERE / "results.json"))
    ap.add_argument("--expected", default=str(HERE / "eval-expected.json"))
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    expected = json.loads(Path(args.expected).read_text())["rows"]
    rows = {row_key(r): r for r in json.loads(Path(args.results).read_text())["rows"]}

    ok, regressed, missing = 0, [], []
    for key, want in expected.items():
        got = rows.get(key)
        if got is None:
            missing.append((key, want))
            continue
        bad = []
        if got["disposition"] != want["expect_disposition"]:
            bad.append(f"disposition {want['expect_disposition']!r} → {got['disposition']!r}")
        want_rel = want.get("expect_relationship_type")
        if want_rel and got.get("relationship_type") != want_rel:
            bad.append(f"type {want_rel!r} → {got.get('relationship_type')!r}")
        if bad:
            regressed.append((key, want, bad))
        else:
            ok += 1

    total = len(expected)
    print(f"eval: {ok}/{total} as expected, {len(regressed)} regressed, {len(missing)} missing")
    if regressed and args.verbose:
        print("\nREGRESSED:")
        for key, want, bad in regressed:
            print(f"  {key} ({want['model']}, {want['maker']})")
            for b in bad:
                print(f"      {b}")
            print(f"      why: {want['why']}")
    if missing and args.verbose:
        print("\nMISSING (row not produced by this run — resolution or claim changed):")
        for key, want in missing:
            print(f"  {key} ({want['model']}) — expected {want['expect_disposition']}")
    if regressed or missing:
        if not args.verbose:
            print("re-run with --verbose to list them")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
