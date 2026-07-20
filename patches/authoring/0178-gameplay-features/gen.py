#!/usr/bin/env python3
"""Generate BOTH of the campaign's patches from ``features.sql``:

- ``patches/0178-gameplay-feature-vocab.yaml`` — creates the features (name,
  parents, aliases) from the ``gpf_new_vocab`` view, plus the aliases that hang on
  features which already existed.
- ``patches/0179-gameplay-features-ipdb.yaml`` — assigns them to the models whose
  IPDB notable features name them, from ``gpf_assignments``.

Both are REGENERATED WHOLE on every run. Production has only ingested through
``0038-model-game-formats``, so every patch above that is still rewritable: the
right move when the audit widens is to re-emit these two and replay the dev DB
from the pre-0039 baseline, not to bolt a second pair on beside them.

ONE SOURCE. The feature list lives only in ``features.sql``'s ``_gpf_new``; with
62 features across a parent/child tree, a hand-written YAML copy would drift from
the analysis that justifies it, and the assignment view would silently reference
features the vocab patch never created. ``gpf_checks`` gates the pairing from the
other side (every declared feature must exist, every assignment must land).

Detection, vetting and quote extraction all live in ``features.sql`` (this dir);
this script is just the emitter. It reads that file's ``gpf_assignments`` view
from the live flipcommons catalog via the duckdb CLI (run with cwd = the
flipcommons checkout, so the view's ``.read scripts/analysis/catalog.sql`` and its
``ATTACH`` resolve), then writes one patch entry per model+feature:

- a ``cite: ipdb:<id>`` carrying the verbatim phrase from the model's IPDB
  notable features. The quote is cut from the RAW source text, not the parsed
  segment, so it is verbatim by construction and passes ``make verify-quotes``;
  ``gpf_checks`` gates that invariant at analysis time too.
No ``note:``. A note here could only say one of two things: what the feature IS,
which is the feature's own description (a separate patch writes those, once each,
for the detail pages — repeating them across 312 model claims would be 312 copies
of a definition that belongs in one place), or that IPDB lists it, which the
``cite:`` already says. So the cite carries the whole claim.

Features are asserted BARE, without a count, even where IPDB supplies one
("Ball elevator (1)", "Vertical ball elevators (2)"): the campaign's rule is to
claim only what is unambiguous, and the count adds a second claim per row for no
detection benefit.

Run from the flippatch repo root::

    uv run python3 patches/authoring/0178-gameplay-features/gen.py
"""

from __future__ import annotations

import sys

from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTHORING = HERE.parent  # patches/authoring/
REPO_ROOT = AUTHORING.parent.parent  # -> repo root
sys.path.insert(0, str(AUTHORING))  # patchkit

import patchkit as pk  # noqa: E402

VOCAB_PATH = REPO_ROOT / "patches" / "0178-gameplay-feature-vocab.yaml"
ASSIGN_PATH = REPO_ROOT / "patches" / "0179-gameplay-features-ipdb.yaml"
FEATURES_SQL = HERE / "features.sql"



def write_vocab() -> int:
    """The vocab patch — create the features, then hang aliases on pre-existing ones."""
    features = pk.read_view(FEATURES_SQL, "gpf_new_vocab", prefix="gpf")
    # PARENTS FIRST. A patch may reference an entity it creates earlier in the
    # same file, but only ABOVE the reference (DataPatches.md -> same-patch
    # create) — so the tree must be emitted in topological order, not the
    # alphabetical order the view returns. Ties break alphabetically to keep the
    # output stable between runs.
    by_slug = {f["slug"]: f for f in features}
    ordered: list[dict] = []
    placed: set[str] = set()

    def place(f: dict, seen: frozenset[str] = frozenset()) -> None:
        if f["slug"] in placed:
            return
        if f["slug"] in seen:
            raise SystemExit(f"parent cycle through {f['slug']}")
        for parent in sorted(f["parents"]):
            if parent in by_slug:  # created here; catalog parents need no ordering
                place(by_slug[parent], seen | {f["slug"]})
        placed.add(f["slug"])
        ordered.append(f)

    for f in sorted(features, key=lambda f: f["slug"]):
        place(f)
    features = ordered

    entries = []
    for f in features:
        rel = {}
        if f["parents"]:
            rel["gameplay_feature_parent"] = f["parents"]
        if f["aliases"]:
            rel["gameplay_feature_alias"] = f["aliases"]
        entries.append(
            pk.entry(
                f"gameplay-feature.{f['slug']}",
                create=True,
                fields={"name": f["name"]},
                relationships=rel or None,
            )
        )
    # Aliases on features that already existed — what is left once every
    # positional variant has been split off into a feature of its own: true
    # synonyms, carrying no distinguishing fact.
    existing: dict[str, list[str]] = {}
    for a in pk.read_view(FEATURES_SQL, "gpf_existing_alias", prefix="gpf"):
        existing.setdefault(a["slug"], []).append(a["alias"])
    for slug in sorted(existing):
        entries.append(
            pk.entry(
                f"gameplay-feature.{slug}",
                relationships={"gameplay_feature_alias": sorted(existing[slug])},
            )
        )
    pk.write_patch(
        VOCAB_PATH,
        attribution="flipcommons-catalog",
        description="Gameplay-feature vocabulary from IPDB notable features.",
        entries=entries,
    )
    nodes = sum(1 for f in features if not f["assignable"])
    print(f"wrote {VOCAB_PATH.relative_to(REPO_ROOT)} — {len(features)} features "
          f"({nodes} taxonomy nodes), {len(existing)} existing features gaining aliases")
    return len(features)


def write_assignments() -> None:
    """The assignment patch — one entry per model, citing IPDB verbatim."""
    rows = pk.read_view(FEATURES_SQL, "gpf_assignments", prefix="gpf")

    # One entry per model, carrying every feature that model earned — a model can
    # match more than one family (Pirates of the Caribbean has both a ball cannon
    # and a mini-playfield), and two entries for the same ref would be two claims
    # where one will do.
    by_model: dict[str, list[dict]] = {}
    for r in rows:
        by_model.setdefault(r["slug"], []).append(r)

    entries: list[str] = []
    missing_ipdb: list[str] = []
    for slug in sorted(by_model):
        # SOURCE ORDER, not feature order: verify-quotes requires the " [...] "-
        # joined spans to appear in the source in the order written, so a model
        # matching several families must follow its own IPDB text.
        group = sorted(by_model[slug], key=lambda r: (r["quote_pos"], r["feature"]))
        ipdb_id = group[0]["ipdb_id"]
        if not ipdb_id:
            missing_ipdb.append(slug)
            continue
        # DEDUPE the spans. One phrase can assign two features — "left and right
        # dual inlanes" asserts both the left and the right child — and both rows
        # then carry the SAME verbatim span. Repeating it would make the second
        # copy read as out of source order, which verify-quotes rejects.
        seen: set[str] = set()
        spans = [
            r["quote"] for r in group
            if not (r["quote"] in seen or seen.add(r["quote"]))
        ]
        quote = " [...] ".join(spans)
        # A counted member ({slug: n}) only where the count IS the fact — the
        # bingo card count. Everything else is bare, even where IPDB gives a
        # number, so the claim says no more than the source unambiguously does.
        members: list[object] = []
        for r in sorted(group, key=lambda r: r["feature"]):
            members.append(
                {r["feature"]: r["feature_count"]} if r["feature_count"] else r["feature"]
            )
        entries.append(
            pk.entry(
                f"model.{slug}",
                cite={"ref": f"ipdb:{ipdb_id}", "quote": quote},
                relationships={"gameplay_feature": members},
            )
        )

    if missing_ipdb:
        raise SystemExit(
            f"{len(missing_ipdb)} models have no ipdb_id to cite: {missing_ipdb}"
        )

    pk.write_patch(
        ASSIGN_PATH,
        attribution="ipdb",
        description="Gameplay features from IPDB notable features.",
        entries=entries,
    )
    per_feature = {f: sum(1 for r in rows if r["feature"] == f) for f in {r["feature"] for r in rows}}
    print(f"wrote {ASSIGN_PATH.relative_to(REPO_ROOT)} — {len(entries)} entries, "
          f"{len(rows)} feature assignments across {len(per_feature)} features")
    for f, n in sorted(per_feature.items(), key=lambda kv: (-kv[1], kv[0]))[:12]:
        print(f"  {n:4d}  {f}")


def main() -> None:
    write_vocab()
    write_assignments()


if __name__ == "__main__":
    main()
