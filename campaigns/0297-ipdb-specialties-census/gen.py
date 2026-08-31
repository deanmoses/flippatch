#!/usr/bin/env python3
"""Generate ``patches/0297-ipdb-specialties-census.yaml`` — IPDB's `Specialty:` row over
the full corpus, landed on the catalog's own classification vocabulary.

The full-corpus re-run of 0290. Detection, the specialty mapping, the single-valued
safety gate and the conflict adjudications all live in ``specialties.sql`` (this dir);
this script is a pure emitter over its ``spec_patch_rows`` view, read from the live
flipcommons catalog via the duckdb CLI.

Every model entry asserts one field and cites the machine listing with the span of its
own `Specialty:` row that states it::

    - model.gay-cruise:
        cite:
          ref: "ipdb:990"
          quote: "Specialty: [...] Add-A-Ball"
        reward_type: [add-a-ball]

Four things about the emitted shape are worth knowing.

**The quote resolves through the census, not the dump or a capture.** The Xantari dump
has no Specialty column, so the words are absent from all 6,671 records. flippatch's
``ipdb:`` resolver renders the ``Specialty:`` line from pinexplore's advanced-search
census — the same rows this analysis reads — so a quote here is checked against its own
source. 0290 resolved the same quote through an archive.org capture, which reached 156
listings where the census reaches 3,291.

**One entry per (model, specialty), so several entries may share a record.** IPDB runs
its specialties together on one line and each asserts a different field on different
evidence, so they are separate changesets — the shape DataPatchAuthoring.md sanctions as
"separate entries on the same record".

**Some entries carry a second field.** A widebody is a wider-than-standard pinball
cabinet, so `game_format: pinball` follows from the designation and rides the same
changeset as the tag. ``specialties.sql`` decides which rows earn it and withholds it
wherever the format is otherwise spoken for; this script only reads the flag.

**Nothing is created.** Unlike 0290, this patch mints no vocabulary: the two terms that
run needed are live, and `wwii-contract` — the only new term this corpus wants — is
created and asserted in 0296, then deferred here so this patch cannot restate it.

Run from the flippatch repo root::

    uv run python3 campaigns/0297-ipdb-specialties-census/gen.py
    make validate
    make verify-quote-verbatim ARGS="0297"
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Repo root by marker, never by counting parents, so a campaign dir stays movable.
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").is_file())
sys.path.insert(0, str(ROOT / "scripts"))  # patchkit + common

import patchkit as pk  # noqa: E402

PATCH_PATH = pk.PATCHES_DIR / "0297-ipdb-specialties-census.yaml"
SPEC_SQL = HERE / "specialties.sql"

# Admin-only and lint-capped at 80 chars; the rationale lives in README.md and this
# module's docstring, the per-row evidence in each cite quote.
DESCRIPTION = "Machine classifications from IPDB's Specialty field."

# Fields holding ONE value are emitted as a scalar; the rest as a relationship member
# list. Naming the split here lets the emitter refuse a field the analysis invents,
# rather than guessing a shape for it.
SCALAR_FIELDS = {"game_format", "cabinet"}
MEMBER_FIELDS = {"tag", "reward_type", "gameplay_feature"}

def main() -> int:
    rows = pk.read_view(SPEC_SQL, "spec_patch_rows", prefix="spec")
    if not rows:
        raise SystemExit("spec_patch_rows returned no rows — nothing to emit")

    entries = []
    for r in sorted(rows, key=lambda r: (str(r["slug"]), str(r["specialty"]))):
        slug, field, value = str(r["slug"]), str(r["field"]), str(r["value"])
        quote = pk.clean_quote(str(r["quote"]).strip())
        if not quote:
            raise SystemExit(f"{slug}: quote became empty after cleaning")

        fields: dict[str, object] = {}
        members: dict[str, list[str]] = {}
        if field in SCALAR_FIELDS:
            fields[field] = value
        elif field in MEMBER_FIELDS:
            members[field] = [value]
        else:
            raise SystemExit(f"{slug}: unexpected field {field!r}")

        if r["implies_pinball"]:
            implied = str(r["implied_game_format"])
            if field != "tag" or value != "widebody":
                raise SystemExit(f"{slug}: {field}={value} must not imply a format")
            fields["game_format"] = implied

        entries.append(
            pk.entry(
                f"model.{slug}",
                cite={"ref": str(r["cite_ref"]), "quote": quote},
                fields=fields or None,
                relationships=members or None,
            )
        )

    pk.write_patch(
        PATCH_PATH,
        attribution="ipdb",
        description=DESCRIPTION,
        entries=entries,
    )
    models = len({str(r["slug"]) for r in rows})
    pinball = sum(1 for r in rows if r["implies_pinball"])
    by_field = Counter(str(r["field"]) for r in rows)
    spread = ", ".join(f"{n} {f}" for f, n in sorted(by_field.items()))
    print(
        f"wrote {PATCH_PATH.relative_to(pk.REPO_ROOT)} — {len(rows)} assertions over "
        f"{models} models ({spread}; {pinball} also naming the format)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
