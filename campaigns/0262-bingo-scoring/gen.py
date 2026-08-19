#!/usr/bin/env python3
"""Emit the bingo scoring-attachment patch from ``scoring.sql``'s ``scoring_patch_rows``.

A pure emitter: the detection, the model/page match, the gate and the diff against what
the catalog already holds all live in the analysis file, which ``pk.read_view`` runs the
checks of before yielding a row.

Each entry attaches one machine's scoring methods and cites that machine's own cdyn page,
quoting its complete ``Features`` row — cdyn's whole feature reading of the machine, not
a span trimmed to the words we wanted.

The second cite, on a ``next-game-award`` row evidenced only by an instance term (a
machine listing "OK game" but never the words "next game award"), points at cdyn's
feature glossary, which is the page that places the instance under the parent. Without
it the entry would assert a family membership its own quote does not contain.

No ``note:``. A note could only repeat what the feature IS — that is the feature record's
own description, written in 0260 — or say that cdyn lists it, which the cite already says.

Run from the flippatch repo root::

    uv run python3 campaigns/0262-bingo-scoring/gen.py
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Repo root by marker, never by counting parents, so a campaign dir stays movable.
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common

import patchkit as pk  # noqa: E402

SCORING_SQL = HERE / "scoring.sql"
PATCH_PATH = pk.PATCHES_DIR / "0262-bingo-scoring-attachments.yaml"

FEATURES_URL = "https://bingo.cdyn.com/machines/features.html"
# The glossary's own enumeration of the next-game-award family, verbatim. Machines that
# list only an instance rest on this sentence for the parent claim.
FAMILY_QUOTE = (
    "Something you do on the current game will enable a feature automatically on the "
    "next game. [...] See: - ballyhole - red letter game - ok game - futurity game - "
    "sunny circles"
)


def main() -> int:
    rows = pk.read_view(SCORING_SQL, "scoring_patch_rows", prefix="scoring")

    by_model: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_model[row["slug"]].append(row)

    entries = []
    for slug in sorted(by_model):
        group = by_model[slug]
        # One machine, one page, one quote: the analysis groups by (model, feature) and
        # every feature of a machine is read off the same Features cell.
        urls = {r["url"] for r in group}
        quotes = {r["quote"] for r in group}
        if len(urls) != 1 or len(quotes) != 1:
            raise SystemExit(f"model.{slug}: rows disagree about the source page or quote")

        cites: list[dict[str, str]] = [
            {"ref": urls.pop(), "quote": pk.clean_quote(quotes.pop())}
        ]
        if any(r["needs_family_cite"] for r in group):
            cites.append({"ref": FEATURES_URL, "quote": pk.clean_quote(FAMILY_QUOTE)})

        entries.append(
            pk.entry(
                f"model.{slug}",
                cite=cites,
                relationships={
                    "gameplay_feature": sorted(r["feature_slug"] for r in group)
                },
            )
        )

    pk.write_patch(
        PATCH_PATH,
        attribution="flipcommons-catalog",
        description="Bingo scoring methods, from bingo.cdyn.com feature blocks.",
        entries=entries,
    )
    per_feature: dict[str, int] = defaultdict(int)
    for row in rows:
        per_feature[row["feature_slug"]] += 1
    breakdown = ", ".join(f"{n} {f}" for f, n in sorted(per_feature.items()))
    print(
        f"wrote {PATCH_PATH.relative_to(pk.REPO_ROOT)} — {len(entries)} entries, "
        f"{len(rows)} attachments ({breakdown})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
