#!/usr/bin/env python3
"""Reconcile Worklist.md against the live Flipcommons dev DB.

The Worklist's slug columns are a frozen pre-re-slugging snapshot and its
hand-maintained DONE markers drift, so this is the campaign's live source of
truth for what is already applied. It keys on the one stable identifier every
row carries — the IPDB number (`catalog_machinemodel.ipdb_id`) — and reports,
per bucket and per maker, which models already carry a `ModelRelationship`
edge, which remain, and which already-set models point at a different target
than the Worklist guessed (vet those).

Since ModelRelationships shipped, lineage lives in the `catalog_modelrelationship`
join table (`relationship_type` + `license_status` + target_machine XOR
target_label), not the retired `bootleg_of` / `licensed_build_of` /
`converted_from` columns. The Worklist's three buckets are now historical
labels: `licensed` ≈ copy+licensed, `bootleg` ≈ copy+unlicensed, `conversion` ≈
conversion / conversion_kit. "Set" here means the model holds ≥1 edge.

Run after rebuilding the dev DB (see README "The dev DB"), under `uv run`:

    uv run python3 patches/authoring/0128-relationships/check_status.py          # console report
    uv run python3 patches/authoring/0128-relationships/check_status.py --write  # also (re)generate STATUS.md

Read-only against the DB.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

# Reuse the repo's sibling-path resolver (dev DB path, env-overridable via
# FLIPCOMMONS_DIR) instead of hard-coding it. This file lives outside scripts/,
# so put scripts/ on the path first; run under `uv run` so the resolver's deps
# are present.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from common.related_projects import FLIPCOMMONS_DB  # noqa: E402

HERE = Path(__file__).resolve().parent
WORKLIST = HERE / "Worklist.md"
STATUS_OUT = HERE / "STATUS.md"
DB = FLIPCOMMONS_DB

# Tolerate the leading ✅ that reconcile_worklist.py stamps onto applied rows.
ROW_RE = re.compile(
    r"\|\s*(?:✅\s*)?(licensed|bootleg|conversion)\s*\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*([^|]*?)\s*\|"
)


def parse_worklist() -> list[tuple[str, str, int, str]]:
    """Return (rel, worklist_slug, ipdb, worklist_target) for every data row."""
    rows = []
    for line in WORKLIST.read_text().splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        rel, slug, ipdb, tgt_cell = m.group(1), m.group(2), int(m.group(3)), m.group(4)
        tm = re.search(r"`([^`]+)`", tgt_cell)
        wl_tgt = tm.group(1) if tm else ("TODO" if "TODO" in tgt_cell else "")
        rows.append((rel, slug, ipdb, wl_tgt))
    return rows


def norm(slug: str) -> str:
    """Loose compare: ignore a trailing disambiguation number (-2, -3, ...)."""
    return re.sub(r"-\d+$", "", slug or "")


class DB_:
    def __init__(self, path: Path):
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()

    def model(self, ipdb: int) -> tuple[int, str] | None:
        self.cur.execute(
            "SELECT id, slug FROM catalog_machinemodel WHERE ipdb_id=?", (ipdb,)
        )
        return self.cur.fetchone()

    def edges(self, mid: int) -> list[tuple[str, str, str | None, str]]:
        """(relationship_type, license_status, target_slug|None, target_label)."""
        self.cur.execute(
            "SELECT r.relationship_type, r.license_status, t.slug, r.target_label "
            "FROM catalog_modelrelationship r "
            "LEFT JOIN catalog_machinemodel t ON r.target_machine_id = t.id "
            "WHERE r.machine_model_id = ?",
            (mid,),
        )
        return [(rt, ls, ts, lbl or "") for rt, ls, ts, lbl in self.cur.fetchall()]

    def maker(self, mid: int) -> str:
        self.cur.execute(
            "SELECT mf.slug FROM catalog_machinemodel m "
            "JOIN catalog_corporateentity ce ON m.corporate_entity_id=ce.id "
            "JOIN catalog_manufacturer mf ON ce.manufacturer_id=mf.id WHERE m.id=?",
            (mid,),
        )
        r = self.cur.fetchone()
        return r[0] if r else "?"


def _edge_desc(edge: tuple[str, str, str | None, str]) -> str:
    rt, ls, ts, lbl = edge
    target = f"`{ts}`" if ts else f"“{lbl}”"
    return f"{rt}/{ls} → {target}"


def build_report():
    if not DB.exists():
        sys.exit(f"dev DB not found at {DB} — rebuild it first (see README).")
    db = DB_(DB)
    rows = parse_worklist()

    done = defaultdict(list)  # (rel, maker) -> [(ipdb, slug, edges)]
    remaining = defaultdict(list)  # (rel, maker) -> [(ipdb, slug, wl_tgt, is_todo)]
    no_model = []  # (rel, ipdb, wl_slug)
    discrepancies = []  # (rel, ipdb, slug, wl_tgt, edges_desc)

    for rel, wl_slug, ipdb, wl_tgt in rows:
        m = db.model(ipdb)
        if m is None:
            no_model.append((rel, ipdb, wl_slug))
            continue
        mid, cur_slug = m
        mk = db.maker(mid)
        edges = db.edges(mid)
        if not edges:
            remaining[(rel, mk)].append((ipdb, cur_slug, wl_tgt, wl_tgt == "TODO"))
            continue
        done[(rel, mk)].append((ipdb, cur_slug, edges))
        edge_slugs = {norm(ts) for _, _, ts, _ in edges if ts}
        if wl_tgt not in ("", "TODO") and norm(wl_tgt) not in edge_slugs:
            edges_desc = "; ".join(_edge_desc(e) for e in edges)
            discrepancies.append((rel, ipdb, cur_slug, wl_tgt, edges_desc))

    return rows, done, remaining, no_model, discrepancies


def render(rows, done, remaining, no_model, discrepancies) -> str:
    out = []
    w = out.append
    w("# Campaign status — Worklist vs live dev DB\n")
    w(
        "_Generated by `check_status.py`. Keyed on `ipdb_id` (stable); the Worklist "
        "slug columns are a frozen snapshot. Lineage is read from the "
        "`catalog_modelrelationship` join table. Regenerate after each dev-DB rebuild._\n"
    )

    w("## Totals\n")
    w("| bucket | worklist rows | relationship set | remaining |")
    w("| --- | ---: | ---: | ---: |")
    for rel in ("licensed", "bootleg", "conversion"):
        n = sum(1 for r in rows if r[0] == rel)
        d = sum(len(v) for k, v in done.items() if k[0] == rel)
        rem = sum(len(v) for k, v in remaining.items() if k[0] == rel)
        w(f"| {rel} | {n} | {d} | {rem} |")
    w(
        f"| **total** | **{len(rows)}** | **{sum(len(v) for v in done.values())}** "
        f"| **{sum(len(v) for v in remaining.values())}** |\n"
    )

    if discrepancies:
        w("## ⚠ Already-set models whose edges omit the Worklist guess — vet these\n")
        w("| rel | ipdb | model | Worklist guess | DB edges |")
        w("| --- | --- | --- | --- | --- |")
        for rel, ipdb, slug, wl_tgt, edges_desc in discrepancies:
            w(f"| {rel} | {ipdb} | `{slug}` | `{wl_tgt}` | {edges_desc} |")
        w("")

    if no_model:
        w("## ⚠ Worklist rows with no matching model (ipdb not in DB)\n")
        for rel, ipdb, slug in no_model:
            w(f"- {rel} ipdb:{ipdb} (worklist slug `{slug}`)")
        w("")

    w("## Remaining work by maker\n")
    for rel in ("licensed", "bootleg", "conversion"):
        keys = sorted(
            (k for k in remaining if k[0] == rel),
            key=lambda k: -len(remaining[k]),
        )
        if not keys:
            continue
        w(f"### {rel}\n")
        w("| maker | remaining | TODO targets |")
        w("| --- | ---: | ---: |")
        for k in keys:
            items = remaining[k]
            todo = sum(1 for *_, is_todo in items if is_todo)
            w(f"| `{k[1]}` | {len(items)} | {todo or ''} |")
        w("")

    w("## Fully-applied makers (all worklist rows set)\n")
    for rel in ("licensed", "bootleg", "conversion"):
        for k in sorted(k for k in done if k[0] == rel):
            if k not in remaining:
                w(f"- {rel}: `{k[1]}` ({len(done[k])})")
    w("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="(re)generate STATUS.md")
    args = ap.parse_args()

    report = render(*build_report())
    print(report)
    if args.write:
        STATUS_OUT.write_text(report)
        print(
            f"\n[wrote {STATUS_OUT.relative_to(HERE.parent.parent.parent)}]",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
