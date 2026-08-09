"""File paths to important locations in this project and sister projects."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def _repo_root() -> Path:
    """This repo's root, found by walking up to the directory holding pyproject.toml.

    Marker-based rather than a ``parents[N]`` count so moving this file — or any
    directory above the things resolved from it — can't silently point the whole
    tooling tree one level wrong. A count is invisible when it breaks: every path
    below still resolves, just to somewhere that doesn't exist.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise RuntimeError(f"no pyproject.toml above {here} — cannot locate the repo root")


# Root dir of this project
REPO_ROOT = _repo_root()

# Data patch dir — what `make push` ships to R2.
PATCHES_DIR = REPO_ROOT / "patches"

# Data patch campaign authoring artifacts
CAMPAIGNS_DIR = REPO_ROOT / "campaigns"


def load_env() -> None:
    """Load this repo's ``.env`` into ``os.environ`` for CLI entry points.

    Call it as the first line of a script's ``main()`` — never at import time —
    so tool commands (``make extract-page`` / ``make lint-descriptions`` /
    ``make verify-quote-support``) pick up ``ANTHROPIC_API_KEY`` (and the sibling-dir
    overrides) from ``.env`` without the caller having to ``source`` it first.

    Kept out of import so importing this module never mutates the process
    environment; a real exported var wins because ``load_dotenv`` defaults to
    ``override=False``. Idempotent — safe to call from more than one entry point.
    """
    load_dotenv(REPO_ROOT / ".env")


def _sibling(dir_name: str, env_var: str) -> Path:
    """A sibling checkout of this repo, or an env-var override."""
    override = os.environ.get(env_var, "").strip()
    return Path(override) if override else REPO_ROOT.parent / dir_name


# Root dir of the Flipcommons project
FLIPCOMMONS_DIR = _sibling("flipcommons", "FLIPCOMMONS_DIR")

# Root dir of the Pinexplore project
PINEXPLORE_DIR = _sibling("pinexplore", "PINEXPLORE_DIR")

# Flipcommons' local dev database
FLIPCOMMONS_DB = FLIPCOMMONS_DIR / "backend" / "db.sqlite3"

# Pinexplore's web-scrape cache (pages/PDFs/transcripts)
WEB_CACHE_DB = PINEXPLORE_DIR / "ingest_sources" / "web" / "cache.sqlite"

# Pinexplore's analytics DB
EXPLORE_DUCKDB = PINEXPLORE_DIR / "explore.duckdb"
