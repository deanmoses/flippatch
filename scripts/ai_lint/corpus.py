"""Resolve a cite ``ref`` to its cached source text (pinexplore, no network).

Reuses ``quote_verify.verify_quotes._Sources`` — which already routes
``ipdb:<id>`` to ``explore.duckdb``'s ``ipdb_machines`` table and
``opdb:``/``youtube:``/``http(s)`` refs to pinexplore's web-cache SQLite. When
pinexplore isn't checked out (or its caches aren't built), the corpus is
*unavailable* and the plagiarism / spine rules fall back to the verbatim
``quote:`` carried in the patch itself.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from common.paths import EXPLORE_DUCKDB, WEB_CACHE_DB

if TYPE_CHECKING:
    from quote_verify.verify_quotes import _Sources


class SourceResolver(Protocol):
    """The one method the corpus needs — ``ref`` → source text, or ``None``."""

    def text_for(self, ref: str) -> str | None: ...


class Corpus:
    """Cite-ref → cached source text, or ``None`` when pinexplore is absent."""

    def __init__(self, resolver: SourceResolver | None) -> None:
        self._resolver = resolver

    @classmethod
    def open(cls) -> Corpus:
        """Build a corpus over pinexplore's caches if both are present.

        Requires the web-cache SQLite *and* ``explore.duckdb``; if either is
        missing the corpus is unavailable (quote-only fallback).
        """
        if WEB_CACHE_DB.is_file() and EXPLORE_DUCKDB.is_file():
            from quote_verify.verify_quotes import _Sources

            resolver: _Sources = _Sources(WEB_CACHE_DB, EXPLORE_DUCKDB)
            return cls(resolver)
        return cls(None)

    @property
    def available(self) -> bool:
        """Whether pinexplore source text can be resolved at all."""
        return self._resolver is not None

    def text_for(self, ref: str) -> str | None:
        """The cached source text for ``ref``, or ``None`` if unresolvable."""
        if self._resolver is None:
            return None
        return self._resolver.text_for(ref)
