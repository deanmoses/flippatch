#!/usr/bin/env python3
"""Stamp Worklist.md rows already applied in the live dev DB.

Idempotent companion to check_status.py: it rewrites Worklist.md in place,
prefixing the `rel` cell of every row whose lineage relationship is already
set in the DB (keyed on ipdb_id) with a ✅ marker, and leaving still-to-author
rows unmarked. Re-run after any dev-DB rebuild to refresh the markers; existing
✅ marks are stripped first, so running twice is a no-op.

It does NOT touch the target column — where a set row's DB target disagrees
with the Worklist's guess, that conflict is surfaced by check_status.py and
resolved by hand, not silently overwritten.

    python3 patches/authoring/0128-relationships/reconcile_worklist.py

After running, re-align tables:  npx prettier@3.8.1 --write Worklist.md
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKLIST = HERE / "Worklist.md"
DB = Path("/Users/moses/dev/flipcommons/backend/db.sqlite3")

REL_COL = {
    "licensed": "licensed_build_of_id",
    "bootleg": "bootleg_of_id",
    "conversion": "converted_from_id",
}
# A row line, capturing the rel cell (with any existing ✅) and the ipdb.
ROW_RE = re.compile(r"^(\|\s*)(?:✅\s*)?(licensed|bootleg|conversion)(\s*\|\s*`[^`]+`\s*\|\s*)(\d+)(\s*\|)")


def main() -> None:
    if not DB.exists():
        sys.exit(f"dev DB not found at {DB} — rebuild it first (see README).")
    con = sqlite3.connect(DB)
    cur = con.cursor()

    def is_set(ipdb: int, rel: str) -> bool:
        cur.execute(
            f"SELECT {REL_COL[rel]} FROM catalog_machinemodel WHERE ipdb_id=?", (ipdb,)
        )
        r = cur.fetchone()
        return bool(r and r[0] is not None)

    stamped = 0
    out = []
    for line in WORKLIST.read_text().splitlines(keepends=True):
        m = ROW_RE.match(line)
        if not m:
            out.append(line)
            continue
        pre, rel, mid_cols, ipdb, post = m.groups()
        rest = line[m.end():]
        marker = "✅ " if is_set(int(ipdb), rel) else ""
        if marker:
            stamped += 1
        out.append(f"{pre}{marker}{rel}{mid_cols}{ipdb}{post}{rest}")

    WORKLIST.write_text("".join(out))
    print(f"stamped {stamped} already-applied rows in {WORKLIST.name}")


if __name__ == "__main__":
    main()
