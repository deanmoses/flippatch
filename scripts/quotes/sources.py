"""Resolve a ``cite:`` to the cached source text it points at.

Sources come from the sister **pinexplore** repo: the web-scrape cache
(``ingest_sources/web/cache.sqlite``) for ``http(s)`` refs — with ``opdb:`` and
``youtube:`` scheme refs resolved to their canonical cached page (the opdb.org
machine page; the watch URL whose text is the video's caption-track transcript)
— and the ``ipdb_machines`` table in ``explore.duckdb`` for ``ipdb:`` refs,
topped up from the cached machine page for the handful of labels that table has
no column for (:data:`_IPDB_PAGE_ONLY_LABELS`). A slug-addressed ref
(``williams:some-manual-slug``) resolves through the document library's
``citation_ref`` to whichever copy of the document is cached.

Every quote checker resolves through :meth:`Sources.resolve_cite`. Two checkers
disagreeing about which document a cite names is the failure this module exists
to prevent, so the rules live here rather than in either caller's loop.
"""

from __future__ import annotations

import html
import sys
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from common.paths import EXPLORE_DUCKDB, PINEXPLORE_DIR, WEB_CACHE_DB

if TYPE_CHECKING:
    from collections.abc import Container, Iterator, Mapping
    from pathlib import Path


# One IPDB machine row as the page prints it: ``(column, page label)`` pairs, a
# ``None`` label for the rows the page renders bare.
#
# ``AverageFunRating`` is left out: it is a moving aggregate, so a point-in-time
# scrape of it evidences nothing the catalog records.
#
# Order and labels are inferred from the key order of pinexplore's
# ``ingest_sources/ipdb_xantari.json`` dump. A wrong one costs a false FAIL,
# never a false pass. The archive.org captures now in the web cache render the
# same labels, which is what :data:`_IPDB_PAGE_ONLY_LABELS` reads.
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

# Labels an IPDB machine page prints that the Xantari dump has no column for,
# in the order the page renders them. The cached archive.org captures fill these
# in — and only these.
#
# The dump is the newer source and always wins: a page label is appended only
# when the dump rendered no line under it, so a value the dump states is never
# reached for. That rule is what keeps a 2018 capture from overwriting a 2025
# fact, and it is why ``Production`` is safe to list here. The dump's
# ``ProductionNumber`` is an integer column, so IPDB's non-numeric statuses
# ("Never Produced") arrive as a null indistinguishable from unknown; where the
# dump holds a number, that number is what renders.
#
# Dates are deliberately absent. IPDB has relabelled header dates between
# ``Date Of Manufacture`` and ``Project Date`` since the older captures were
# taken, and the dump carries both its own ``DateOfManufacture`` and the header
# line verbatim in ``AdditionalDetails`` — so a date quote has a current carrier
# already and must never resolve against a stale page. Same for the fun rating,
# which is a moving aggregate the dump also holds.
_IPDB_PAGE_ONLY_LABELS: tuple[str, ...] = (
    "Production",
    "Specialty",
    "Concept by",
    "Easter Eggs",
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


def _ipdb_fields(
    row: Mapping[str, object], columns: Container[str] | None = None
) -> Iterator[tuple[str | None, str]]:
    """*row*'s populated fields as ``(page label, value)`` in page order.

    A blank value is skipped rather than yielded as a bare ``Label:`` — text
    the page never shows, which a quote of the label alone could verify against.
    """
    for column, label in _IPDB_ROW_FIELDS:
        if columns is not None and column not in columns:
            continue
        value = row.get(column)
        if value is None:
            continue
        text = html.unescape(str(value))
        if not text.strip():
            continue
        yield label, text


def _ipdb_lines(
    row: Mapping[str, object], columns: Container[str] | None = None
) -> str:
    """Render *row*'s fields in page order, narrowed to *columns* if given."""
    return "\n".join(
        f"{label}: {text}" if label else text
        for label, text in _ipdb_fields(row, columns)
    )


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
        # Cached machine pages parsed on demand, keyed by IPDB id: most ids have
        # no capture, and parsing one is only worth doing for an id actually
        # cited. An id that resolved to nothing memoizes as ``{}``.
        self._page_fields: dict[str, dict[str, str]] = {}

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
        texts = [
            text
            for page in self._document_captures(ref)
            if (text := str(page.get("text") or "")).strip()
        ]
        # A merged multi-sheet document (a flyer's front and back as separate
        # image captures) is one work in several files: its quotable text is
        # every captured copy's text joined in the library's deterministic
        # order, so a quote may sit on any sheet and a multi-span quote keeps
        # source order across sheets.
        return "\n\n".join(texts) if texts else None

    def is_pdf(self, ref: str) -> bool:
        """Whether *ref* names a cached PDF.

        The signal is the cache row's ``content_type``, a fact about the
        **document**: the patch never records whether its own quote is
        verifiable, because the patch is the record and a second place to say so
        is a second source of truth.

        Two ref shapes can name a PDF: an ``http(s)`` URL, and a slug-addressed
        document ref among whose captured copies is one (a Williams manual is
        routinely a scan) — one PDF makes the whole ref unjudgeable, however
        readable its sibling sheets. The known schemes stay non-PDF — IPDB
        rows, OPDB pages and caption transcripts are fully checkable — and the
        URL's spelling is not consulted, so an HTML page served at a ``.pdf``
        path stays checked.
        """
        if ref.startswith(("http://", "https://")):
            pages = [self._web_cache.get(ref) or {}]
        else:
            pages = self._document_captures(ref)
        return any(
            str(page.get("content_type") or "").startswith("application/pdf")
            for page in pages
        )

    def _document_captures(self, ref: str) -> list[dict[str, object]]:
        """The cached captures behind a slug-addressed ref, in library order.

        A ``<root-slug>:<child-slug>`` cite (a publisher's document, a
        periodical issue) resolves through the document library's
        ``citation_ref`` — pinexplore's ``captures_for_citation_ref`` returns
        whichever of the document's URLs are actually cached, alias-resolved
        through redirects, one row per captured sheet of a merged multi-sheet
        work. The known schemes are excluded so a stray library row can never
        shadow their own resolution.
        """
        scheme, sep, _ = ref.partition(":")
        if not sep or scheme in ("http", "https", "ipdb", "opdb", "youtube", "isbn"):
            return []
        return [dict(page) for page in self._web_cache.captures_for_citation_ref(ref)]

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
        """The dump's row, topped up from the cached page where it is silent.

        The dump has no row for an id it never carried, and a page alone is not
        a machine record — so a missing row is missing, capture or no capture.
        """
        row = self._ipdb_rows().get(identifier)
        if row is None:
            return None
        rendered = {label for label, _ in _ipdb_fields(row) if label}
        page = self._ipdb_page_fields(identifier)
        return "\n".join(
            [
                ipdb_row_text(row),
                *(
                    f"{label}: {text}"
                    for label in _IPDB_PAGE_ONLY_LABELS
                    if label not in rendered and (text := page.get(label))
                ),
            ]
        )

    def _ipdb_page_fields(self, identifier: str) -> dict[str, str]:
        """:data:`_IPDB_PAGE_ONLY_LABELS` as the cached machine page prints them.

        Parses pinexplore's stored capture with pinexplore's own machine-page
        parser: the grammar for IPDB's markup belongs beside the fetcher, and a
        second reading of it here would be a second thing to rot. An uncached,
        blobless or unparseable page contributes nothing — the dump's row still
        resolves, one label short.
        """
        if identifier in self._page_fields:
            return self._page_fields[identifier]
        parse, error = self._ipdb_page_parser()
        page = self._web_cache.get(f"https://www.ipdb.org/machine.cgi?id={identifier}")
        blob = self._web_cache.blob_for(page) if page else None
        fields: dict[str, str] = {}
        if blob is not None and blob.exists():
            try:
                model = parse(blob.read_bytes())
            except error:
                model = None
            if model is not None:
                fields = {
                    label: field.text
                    for label in _IPDB_PAGE_ONLY_LABELS
                    if (field := model.fields.get(label)) and field.text.strip()
                }
        self._page_fields[identifier] = fields
        return fields

    @staticmethod
    def _ipdb_page_parser() -> tuple[Any, type[Exception]]:
        """pinexplore's machine-page parser and the error it raises.

        Imported at call time, like ``web_cache`` in :meth:`__init__`: it pulls
        in lxml, and every caller that never cites an IPDB id pays nothing.
        """
        from parse_ipdb import (  # type: ignore[import-not-found]  # pinexplore module
            IpdbParseError,
            parse_model_page,
        )

        return parse_model_page, IpdbParseError

    def _ipdb_notes_text(self, identifier: str) -> str | None:
        row = self._ipdb_rows().get(identifier)
        text = ipdb_notes_text(row) if row else None
        return text if text and text.strip() else None
