"""Select patch files by id — the one definition of what a scope argument means.

The verbatim gate and both AI checkers share this, so a scope selects the same
files and a bad id draws the same refusal whichever tool reads it. Living below
them all is also what keeps the deterministic tier from importing the AI tier to
ask what "0223" means.

The structural and editorial gates deliberately glob ``*.yaml`` instead: a
misnamed file is what they exist to catch, and ``[0-9]*.yaml`` would hide it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


def _requested(patch_id: str) -> str:
    return patch_id.removesuffix(".yaml")


def _spellings(path: Path) -> set[str]:
    return {path.stem, path.stem.split("-", 1)[0]}


def patch_paths(patches_dir: Path, patch_ids: Sequence[str] = ()) -> list[Path]:
    """Every ``NNNN-slug.yaml`` patch in *patches_dir*, narrowed to *patch_ids*.

    An id is a bare number (``0223``) or a full stem (``0223-cirqus-voltaire``),
    either way with an optional ``.yaml``. Empty *patch_ids* means every patch.
    """
    wanted = {_requested(pid) for pid in patch_ids}
    return [
        path
        for path in sorted(patches_dir.glob("[0-9]*.yaml"))
        if not wanted or wanted & _spellings(path)
    ]


def unmatched_ids(patches_dir: Path, patch_ids: Sequence[str]) -> list[str]:
    """The requested ids naming no patch file, in the order they were given."""
    known = {
        spelling for path in patch_paths(patches_dir) for spelling in _spellings(path)
    }
    return [pid for pid in patch_ids if _requested(pid) not in known]


def unmatched_scope_error(patches_dir: Path, patch_ids: Sequence[str]) -> str | None:
    """Refusal message when a scope names a patch that does not exist, or None.

    The whole run is refused rather than narrowed to the ids that matched: each
    tool announces the scope it was given and reports — or bills — against it, so
    a dropped typo would let a partial run pass as the scope that was asked for.
    Costs nothing to call, so it can land ahead of any spending.
    """
    unmatched = unmatched_ids(patches_dir, patch_ids)
    if not unmatched:
        return None
    return (
        f"no patch matches {' '.join(unmatched)} in {patches_dir} — nothing ran; "
        f"fix the id(s) and try again."
    )
