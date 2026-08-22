#!/usr/bin/env python3
"""Whether flipcommons' dev database matches the data patches on disk.

The catalog audit reports on what a local flipcommons DB *ingested*, while the patch
range it is handed comes from the files in ``patches/``. When the two disagree the
audit is quietly wrong about its own scope — blind to a patch never applied, and
reading superseded text for one edited since — and nothing in its own output can say
so, because it has no way to miss what it cannot see.

Two callers need that answer, in different words:

- ``scripts/analysis/audit-patches`` renders it as a banner above the report, worded
  relative to the findings that follow.
- ``make db-patch-state`` renders it alone, as a status line, where there is no report
  to be relative to and silence would be indistinguishable from a broken command.

Same facts, two renderings, one implementation: a second copy of the ledger
reconciliation is a copy that drifts.

**mtime, not a content hash.** The ledger's ``input_fingerprint`` is flipcommons'
canonical-JSON digest of the *parsed* patch, not of the file, so matching it here would
mean duplicating the apply engine's normalisation. mtime errs the safe way round — an
edit always bumps it, so a drifted patch is never missed, while a ``git checkout`` that
rewrites an unchanged file costs one spurious report.
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from common.paths import FLIPCOMMONS_DIR, PATCHES_DIR, load_env

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

# The ledger is the only complete roster of applied patches: a patch that declares
# nothing but citation roots writes no changeset and reaches none of the claim views,
# but it does get a run row. The GROUP BY is belt-and-braces — a partial unique index
# already allows only one successful run per patch — and costs nothing if that ever
# relaxes; the timestamps are ISO, so lexical max() is chronological.
_LEDGER_SQL = """
    SELECT patch_id, max(finished_at)
    FROM provenance_ingestrun
    WHERE status = 'success' AND patch_id IS NOT NULL
    GROUP BY patch_id
"""

# The ordinal a patch filename opens with — how the audit addresses a range.
PATCH_NUMBER_RE = re.compile(r"^(\d+)-")

_RULE = "═" * 76


class State(Enum):
    """How one patch file stands against the ledger."""

    CURRENT = "current"
    EDITED = "edited"
    UNAPPLIED = "unapplied"


@dataclass(frozen=True)
class PatchState:
    """One patch file's standing. ``applied_at`` is local time, None if never applied."""

    stem: str
    state: State
    applied_at: datetime | None


def flipcommons_dir() -> Path:
    """The flipcommons checkout — ``FLIPCOMMONS_DIR``, this repo's ``.env``, or the
    sibling default.

    ``load_env()`` runs before the environment is read, because ``FLIPCOMMONS_DIR`` is
    resolved at that module's import time and an override living only in ``.env`` would
    otherwise be missed. Mirrors ``patchkit._flipcommons_dir``; the audit wrapper asks
    this module for the path rather than resolving its own, so every entry point in the
    repo agrees on where flipcommons is.
    """
    load_env()
    return Path(os.environ.get("FLIPCOMMONS_DIR") or FLIPCOMMONS_DIR)


def _applied(db: Path) -> dict[str, datetime]:
    """Patch id to the UTC instant its latest successful ingest finished."""
    uri = f"file:{db}?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as con:
        rows: list[tuple[str, str | None]] = con.execute(_LEDGER_SQL).fetchall()
    # finished_at is stored UTC and file mtimes are local, so the instant is made
    # explicit here and every comparison below runs on epoch seconds. Only the DISPLAY
    # is localised — comparing wall-clock strings reads every fresh patch as hours stale.
    return {
        patch_id: datetime.fromisoformat(finished).replace(tzinfo=UTC)
        for patch_id, finished in rows
        if finished
    }


def patches_since(number: int, patches_dir: Path = PATCHES_DIR) -> list[Path]:
    """Every mutable patch numbered ``number`` or higher.

    The catalog audit reports on the patch it is given and every later one, so deriving
    the checked set from that number rather than from a list of filenames makes the
    freshness check cover exactly what the report covers. Handed only the files named on
    a command line, it would stay silent about a later patch nobody mentioned — which is
    the one thing it exists to speak up about.
    """
    numbered = (
        (PATCH_NUMBER_RE.match(p.stem), p) for p in sorted(patches_dir.glob("*.yaml"))
    )
    return [p for m, p in numbered if m and int(m.group(1)) >= number]


def read_states(paths: Iterable[Path], db: Path) -> list[PatchState] | None:
    """Each patch file's standing against the ledger, ordered by patch number.

    None when the ledger cannot be read — an older database without the table. That is
    reported as "unknown" rather than as every patch being unapplied, which is the one
    wrong answer worse than staying quiet.
    """
    try:
        applied = _applied(db)
    except sqlite3.Error:
        return None

    states = []
    for path in sorted(paths):
        at = applied.get(path.stem)
        if at is None:
            states.append(PatchState(path.stem, State.UNAPPLIED, None))
        else:
            drifted = path.stat().st_mtime > at.timestamp()
            state = State.EDITED if drifted else State.CURRENT
            states.append(PatchState(path.stem, state, at.astimezone()))
    return states


def _banner_label(state: PatchState) -> str:
    if state.state is State.UNAPPLIED or state.applied_at is None:
        return "NOT APPLIED — absent from the report below"
    return f"EDITED SINCE APPLIED — audited as of {state.applied_at:%H:%M}"


def _status_label(state: PatchState) -> str:
    if state.state is State.UNAPPLIED or state.applied_at is None:
        return "NOT APPLIED"
    return f"EDITED SINCE APPLIED (applied {state.applied_at:%H:%M})"


def render_banner(states: Sequence[PatchState]) -> str | None:
    """The audit's banner: exceptions only, None when everything is current.

    Negative-only on purpose — it rides above another command's output, where saying
    nothing is the right way to say the report can be trusted as it stands.
    """
    stale = [s for s in states if s.state is not State.CURRENT]
    if not stale:
        return None
    width = max(len(s.stem) for s in stale)
    body = [f"       {s.stem:<{width}}   {_banner_label(s)}" for s in stale]
    return "\n".join(
        [_RULE, "  ⚠  STALE — database and patches/ do not match", *body, _RULE]
    )


def render_status(states: Sequence[PatchState]) -> str:
    """The standalone answer: always affirmative, expanded only when there is drift."""
    if not states:
        return "No patches in patches/."
    noun = "patch" if len(states) == 1 else "patches"
    span = f"{states[0].stem[:4]}-{states[-1].stem[:4]}"
    head = f"patches/ vs the dev DB — {len(states)} {noun} ({span})"

    stale = [s for s in states if s.state is not State.CURRENT]
    if not stale:
        return f"{head}, all applied and current."
    width = max(len(s.stem) for s in stale)
    body = [f"  {s.stem:<{width}}   {_status_label(s)}" for s in stale]
    return "\n".join(
        [f"{head}:", f"  {len(states) - len(stale)} applied and current", *body]
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Always exits 0. Drift is an answer, not a failure — and under ``make`` a nonzero
    exit renders as ``*** Error 1``, which reads as the tool breaking rather than as the
    database being behind."""
    parser = argparse.ArgumentParser(
        description="Report whether flipcommons' dev DB matches the patches on disk."
    )
    parser.add_argument(
        "--banner",
        action="store_true",
        help="render for the catalog audit: exceptions only, silent when current",
    )
    parser.add_argument(
        "--flipcommons-dir",
        action="store_true",
        help="print the resolved flipcommons checkout and exit",
    )
    parser.add_argument(
        "--since",
        type=int,
        metavar="N",
        help="check every patch numbered N or higher — the set the catalog audit "
        "reports on — instead of the files named",
    )
    parser.add_argument(
        "--patches-dir",
        type=Path,
        default=PATCHES_DIR,
        metavar="DIR",
        help="the mutable patch directory to reconcile; defaults to this repo's "
        "patches/. The audit wrapper resolves that directory itself, to derive the "
        "range it audits, and passes it here so the two can never name different sets",
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="patch files to check; defaults to every patches/*.yaml",
    )
    args = parser.parse_args(argv)

    if args.flipcommons_dir:
        print(flipcommons_dir())
        return 0

    db = flipcommons_dir() / "backend" / "db.sqlite3"
    if not db.is_file():
        if not args.banner:
            print(f"no flipcommons dev database at {db}")
        return 0

    if args.since is not None:
        paths = patches_since(args.since, args.patches_dir)
    else:
        paths = [
            p
            for p in (args.files or sorted(args.patches_dir.glob("*.yaml")))
            if p.is_file()
        ]
    states = read_states(paths, db)
    if states is None:
        if not args.banner:
            print(f"could not read the ingest ledger in {db}")
        return 0

    if args.banner:
        banner = render_banner(states)
        if banner is not None:
            print(banner, end="\n\n")
    else:
        print(render_status(states))
    return 0


if __name__ == "__main__":
    sys.exit(main())
