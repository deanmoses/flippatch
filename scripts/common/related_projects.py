"""Paths into this repo's sibling checkouts (pinexplore, flipcommons).

The tooling relies on all three repos living as sibling checkouts under one
developer-localhost root — ``flippatch/`` beside ``flipcommons/`` and
``pinexplore/`` — so paths default to siblings and are each overridable by env
var (``PINEXPLORE_DIR`` / ``FLIPCOMMONS_DIR``). ``PINEXPLORE_DIR`` mirrors the
convention ``quote_verify/verify_quotes.py`` already uses.

Nothing here reaches the network. pinexplore's evidence stores are its local
web-scrape cache SQLite (``ingest_sources/web/cache.sqlite``) plus its
``explore.duckdb``; flipcommons' catalog registry is its local dev SQLite
(``backend/db.sqlite3``, a near-clone of prod).

This lives in ``common`` rather than the AI foundation: resolving sibling
projects is domain-neutral, and non-AI scripts need it too.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# scripts/common/related_projects.py -> common -> scripts -> repo root. The
# anchor for sibling resolution below; also the one home for "where is this
# repo" that any script package can import.
REPO_ROOT = Path(__file__).resolve().parents[2]


def load_env() -> None:
    """Load this repo's ``.env`` into ``os.environ`` for CLI entry points.

    Call it as the first line of a script's ``main()`` — never at import time —
    so tool commands (``make extract-page`` / ``make lint-descriptions`` /
    ``make verify-citations``) pick up ``ANTHROPIC_API_KEY`` (and the sibling-dir
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


PINEXPLORE_DIR = _sibling("pinexplore", "PINEXPLORE_DIR")
FLIPCOMMONS_DIR = _sibling("flipcommons", "FLIPCOMMONS_DIR")

# pinexplore's web-scrape cache (pages/PDFs/transcripts) and analytics DB.
WEB_CACHE_DB = PINEXPLORE_DIR / "ingest_sources" / "web" / "cache.sqlite"
EXPLORE_DUCKDB = PINEXPLORE_DIR / "explore.duckdb"

# flipcommons' local dev database — the catalog registry we resolve entity
# mentions and wikilink candidates against.
FLIPCOMMONS_DB = FLIPCOMMONS_DIR / "backend" / "db.sqlite3"
