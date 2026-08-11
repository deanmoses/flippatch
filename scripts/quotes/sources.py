"""Resolve a ``cite:`` to the cached source text it points at.

Sources come from the sister **pinexplore** repo: the web-scrape cache
(``ingest_sources/web/cache.sqlite``) for ``http(s)`` refs — with ``opdb:`` and
``youtube:`` scheme refs resolved to their canonical cached page (the opdb.org
machine page; the watch URL whose text is the video's caption-track transcript)
— and the ``ipdb_machines`` table in ``explore.duckdb`` for ``ipdb:`` refs.

Every quote checker resolves through :meth:`Sources.resolve_cite`. Two checkers
disagreeing about which document a cite names is the failure this module exists
to prevent, so the rules live here rather than in either caller's loop.
"""

from __future__ import annotations

import html
import sys
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from common.paths import EXPLORE_DUCKDB, PINEXPLORE_DIR, WEB_CACHE_DB

if TYPE_CHECKING:
    from collections.abc import Container, Mapping
    from pathlib import Path


# One IPDB machine row as the page prints it: ``(column, page label)`` pairs, a
# ``None`` label for the rows the page renders bare.
#
# ``AverageFunRating`` is left out: it is a moving aggregate, so a point-in-time
# scrape of it evidences nothing the catalog records.
#
# Order and labels are inferred from the key order of pinexplore's
# ``ingest_sources/ipdb_xantari.json`` dump; IPDB resists scraping, so no cached
# page verifies them. A wrong one costs a false FAIL, never a false pass.
_IPDB_ROW_FIELDS: tuple[tuple[str, str | None], ...] = (
    ("Title", None),
    ("Players", "Players"),
    ("AdditionalDetails", None),
    ("Manufacturer", "Manufacturer"),
    ("CommonAbbreviations", "Common Abbreviations"),
    ("Type", "Type"),
    ("MPU", "MPU"),
    ("ModelNumber", "Model Number"),
    ("ProductionNumber", "Production"),
    ("Theme", "Theme"),
    ("NotableFeatures", "Notable Features"),
    ("Toys", "Toys"),
    ("DesignBy", "Design by"),
    ("ArtBy", "Art by"),
    ("DotsAnimationBy", "Dots/Animation by"),
    ("MechanicsBy", "Mechanics by"),
    ("MusicBy", "Music by"),
    ("SoundBy", "Sound by"),
    ("SoftwareBy", "Software by"),
    ("Notes", "Notes"),
    ("MarketingSlogans", "Marketing Slogans"),
    ("PhotosIn", "Photos in"),
    ("Source", "Source"),
)

# The row narrowed to editor-authored prose about the machine — what
# ``ipdb_notes_text`` feeds an AI. ``Source`` ("flyer", "Bally documentation")
# and ``PhotosIn`` record IPDB's own paperwork, so feeding them invites a model
# to mistake IPDB's sourcing for a fact about the machine.
_IPDB_PROSE_COLUMNS = frozenset(
    {"NotableFeatures", "Toys", "Notes", "MarketingSlogans"}
)


class SourceStatus(StrEnum):
    """How a cite resolved against the cache.

    ``PDF`` is its own outcome rather than a resolved document because PDF text
    extraction reads a sheet in reading order: a table arrives as a column of
    unattached cells, and words drawn as artwork never reach the text layer at
    all. A quote read correctly off the rendered sheet routinely is not a
    substring of what was extracted, and the OCR tier does not rescue it —
    measured across this corpus an exact match rejects ~25% of correct spans and
    an ordered-word match ~14%, so no threshold makes a check honest and a fuzzy
    one only trades false rejections for false confidence.
    """

    RESOLVED = "resolved"
    PDF = "pdf"
    MISSING = "missing"


@dataclass(frozen=True, slots=True)
class CiteSource:
    """The outcome of resolving one cite: its status and, if any, its text."""

    status: SourceStatus
    text: str | None = None


def _die(message: str) -> None:
    print(f"FATAL: {message}", file=sys.stderr)
    sys.exit(2)


def require_pinexplore() -> None:
    """Exit loudly, with the fix, unless pinexplore's stores are all present."""
    if not PINEXPLORE_DIR.is_dir():
        _die(
            f"pinexplore repo not found at {PINEXPLORE_DIR} — clone it as a "
            f"sibling of this repo, or point PINEXPLORE_DIR at your checkout"
        )
    if not WEB_CACHE_DB.is_file():
        _die(
            f"web cache not found at {WEB_CACHE_DB} — run `make pull` in "
            f"pinexplore to download it from R2"
        )
    if not EXPLORE_DUCKDB.is_file():
        _die(
            f"explore.duckdb not found at {EXPLORE_DUCKDB} — run `make explore` "
            f"in pinexplore to build it"
        )


def _ipdb_lines(
    row: Mapping[str, object], columns: Container[str] | None = None
) -> str:
    """Render *row*'s fields in page order, narrowed to *columns* if given.

    A blank value is omitted rather than rendered as a bare ``Label:`` — text
    the page never shows, which a quote of the label alone could verify against.
    """
    lines = []
    for column, label in _IPDB_ROW_FIELDS:
        if columns is not None and column not in columns:
            continue
        value = row.get(column)
        if value is None:
            continue
        text = html.unescape(str(value))
        if not text.strip():
            continue
        lines.append(f"{label}: {text}" if label else text)
    return "\n".join(lines)


def ipdb_row_text(row: Mapping[str, object]) -> str:
    """The quotable text of one IPDB machine row, keyed by DuckDB column name.

    Reconstructs what the IPDB page renders so a quote stays ctrl-F honest
    there: the title as a bare heading, then each populated field as the page's
    own ``Label: value`` row. :data:`_IPDB_ROW_FIELDS` holds the order and the
    rule deciding membership. AI extraction wants :func:`ipdb_notes_text`, the
    same rendering narrowed to machine prose.
    """
    return _ipdb_lines(row)


def ipdb_notes_text(row: Mapping[str, object]) -> str:
    """The editor-authored prose of one IPDB machine row — the AI-readable slice.

    IPDB's structured fields are deterministic data read straight from the
    columns, never re-extracted by a model; :data:`_IPDB_PROSE_COLUMNS` says
    what else this drops and why.

    Sharing :func:`ipdb_row_text`'s renderer is load bearing. The extractor
    checks a model's quote against this text and the verbatim gate re-checks the
    shipped patch against the full row, so a delimiter in one and not the other
    is a quote that passes extraction and fails at ship time — hence the page's
    own ``Toys:`` rather than a synthetic markdown heading. Carrying labels at
    all is what lets a model tell a Note from ad copy in Marketing Slogans.
    """
    return _ipdb_lines(row, _IPDB_PROSE_COLUMNS)


class Sources:
    """Source-text lookup over pinexplore's web cache and IPDB table.

    Two views of the same sources, for two callers:
    :meth:`text_for` returns the full text (IPDB's structured rows included) for
    the verbatim quote gate; :meth:`free_text_for` narrows an IPDB row to its
    machine prose, for AI extraction.
    """

    def __init__(self, duck_db: Path = EXPLORE_DUCKDB) -> None:
        # The web cache takes no path: pinexplore's ``web_cache`` resolves its own
        # DB relative to itself, so PINEXPLORE_DIR is what selects it.
        sys.path.insert(0, str(PINEXPLORE_DIR / "scripts" / "web_scrape"))
        import web_cache  # type: ignore[import-not-found]  # pinexplore module, stdlib-only

        self._web_cache = web_cache
        self._duck_db = duck_db
        self._rows: dict[str, dict[str, object]] | None = None

    def resolve_cite(self, ref: str, archive: str | None = None) -> CiteSource:
        """Resolve a whole cite — ref, then its archive snapshot — to a document.

        A dead original is cached under its Wayback snapshot URL while the cite's
        ``ref`` stays the publisher's, which is why there are two addresses to
        try. Each is settled in turn and the first verdict wins, so a readable
        ``ref`` is the document even when the snapshot behind it is a PDF. An
        uncached address is :attr:`SourceStatus.MISSING`, never PDF: a document
        nobody can produce must not pass as one merely unjudgeable.
        """
        for address in [ref, *([archive] if archive else [])]:
            if self.is_pdf(address):
                return CiteSource(SourceStatus.PDF)
            text = self.text_for(address)
            if text:
                return CiteSource(SourceStatus.RESOLVED, text)
        return CiteSource(SourceStatus.MISSING)

    def free_text_for(self, ref: str) -> str | None:
        """Source text for AI extraction — editor-authored prose only.

        The input adapter for the page extractor. Web / opdb / youtube refs
        already resolve to unstructured readable text, so it passes them
        through :meth:`text_for`; an ``ipdb:`` ref narrows to
        :func:`ipdb_notes_text`.
        """
        if ref.startswith("ipdb:"):
            return self._ipdb_notes_text(ref.partition(":")[2])
        return self.text_for(ref)

    def text_for(self, ref: str) -> str | None:
        """The full quotable source text for one address.

        For ``ipdb:`` this is the whole rendered row (:func:`ipdb_row_text`), so
        a quote may legitimately cite a structured field. AI extraction wants
        :meth:`free_text_for` instead.
        """
        if ref.startswith(("http://", "https://")):
            return self._page_text(ref)
        scheme, _, identifier = ref.partition(":")
        if scheme == "ipdb":
            return self._ipdb_text(identifier)
        if scheme == "opdb":
            # opdb:<id> is the opdb.org URL id (flipcommons' canonical URL
            # template); its evidence text is the cached machine page.
            return self._page_text(f"https://opdb.org/machines/{identifier}")
        if scheme == "youtube":
            # youtube:<id> maps to the canonical watch URL; its cached text is
            # the caption-track transcript pinexplore's video transport stores.
            return self._page_text(f"https://www.youtube.com/watch?v={identifier}")
        return None

    def is_pdf(self, ref: str) -> bool:
        """Whether *ref* names a cached PDF.

        The signal is the cache row's ``content_type``, a fact about the
        **document**: the patch never records whether its own quote is
        verifiable, because the patch is the record and a second place to say so
        is a second source of truth.

        Deliberately narrow. Only an ``http(s)`` ref can name a PDF — scheme refs
        resolve to IPDB rows, OPDB pages and caption transcripts, which stay
        fully checkable. The URL's spelling is not consulted, so an HTML page
        served at a ``.pdf`` path stays checked.
        """
        if not ref.startswith(("http://", "https://")):
            return False
        page = self._web_cache.get(ref) or {}
        return str(page.get("content_type") or "").startswith("application/pdf")

    def _page_text(self, url: str) -> str | None:
        page = self._web_cache.get(url)
        text = (page or {}).get("text") or ""
        return text if text.strip() else None

    def _ipdb_rows(self) -> dict[str, dict[str, object]]:
        """Every IPDB row as a column-keyed mapping, read and cached once.

        Selects exactly the columns the renderer knows, so adding a quotable
        field is one edit to :data:`_IPDB_ROW_FIELDS`.
        """
        if self._rows is None:
            import duckdb

            columns = ["IpdbId", *(column for column, _ in _IPDB_ROW_FIELDS)]
            con = duckdb.connect(str(self._duck_db), read_only=True)
            rows = con.execute(
                f"SELECT {', '.join(columns)} FROM ipdb_machines"  # noqa: S608 — column names are this module's own literals
            ).fetchall()
            con.close()
            self._rows = {
                str(row[0]): dict(zip(columns, row, strict=True)) for row in rows
            }
        return self._rows

    def _ipdb_text(self, identifier: str) -> str | None:
        row = self._ipdb_rows().get(identifier)
        return ipdb_row_text(row) if row else None

    def _ipdb_notes_text(self, identifier: str) -> str | None:
        row = self._ipdb_rows().get(identifier)
        text = ipdb_notes_text(row) if row else None
        return text if text and text.strip() else None
