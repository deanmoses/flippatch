"""Resolve a cite to its cached source text (pinexplore, no network).

The AI rules' adapter over ``quotes.sources.Sources``, so they resolve a cite by
exactly the rules the verbatim gate applies. When pinexplore isn't checked out
(or its caches aren't built), the corpus is *unavailable* and the plagiarism /
spine rules fall back to the verbatim ``quote:`` carried in the patch itself.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from common.paths import EXPLORE_DUCKDB, WEB_CACHE_DB
from quotes.sources import CiteSource, SourceStatus

if TYPE_CHECKING:
    from quotes.sources import Sources


class SourceResolver(Protocol):
    """The slice of ``Sources`` the rules use — the seam a test fake stands in at."""

    def text_for(self, ref: str) -> str | None: ...

    def resolve_cite(self, ref: str, archive: str | None = None) -> CiteSource: ...


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
            from quotes.sources import Sources

            resolver: Sources = Sources()
            return cls(resolver)
        return cls(None)

    @property
    def available(self) -> bool:
        """Whether pinexplore source text can be resolved at all."""
        return self._resolver is not None

    def text_for(self, ref: str) -> str | None:
        """The cached source text for one address, or ``None`` if unresolvable."""
        if self._resolver is None:
            return None
        return self._resolver.text_for(ref)

    def resolve_cite(self, ref: str, archive: str | None = None) -> CiteSource:
        """See :meth:`quotes.sources.Sources.resolve_cite`."""
        if self._resolver is None:
            return CiteSource(SourceStatus.MISSING)
        return self._resolver.resolve_cite(ref, archive)
