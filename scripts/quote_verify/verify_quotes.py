#!/usr/bin/env python3
"""Verify every ``cite:`` quote in the patches against its cached source.

A ``quote:`` is trustworthy only if a reviewer could follow the citation and
ctrl-F find it, so every span must be an exact verbatim substring of the
source text, in source order. Sources come from the sister **pinexplore**
repo: the web-scrape cache (``ingest_sources/web/cache.sqlite``) for
``http(s)`` refs — with ``opdb:`` and ``youtube:`` scheme refs resolved to
their canonical cached page (the opdb.org machine page; the watch URL whose
text is the video's caption-track transcript) — and the ``ipdb_machines``
table in ``explore.duckdb`` for ``ipdb:`` scheme refs.

Matching allows only the normalizations DataPatchAuthoring.md sanctions —
smart quotes straightened and whitespace collapsed (text extraction
hard-wraps prose that renders as spaces) — applied to the SOURCE side; the
quote itself must already be in normalized form (straight quotes, ``[...]``
ellipses).

**PDFs are not gated.** A PDF quote is reported ``SKIP-PDF`` and left to the
author. Extraction reads a sheet in reading order, so a table arrives as a
column of unattached cells and words drawn as artwork never reach the text
layer at all — a correct quote read off the rendered sheet routinely is not a
substring of what was extracted. Checking the OCR tier instead does not
rescue it: measured against text layers across this corpus, an exact match
rejects ~25% of correct spans and an ordered-word match ~14%, so no threshold
makes the check honest, and a fuzzy one would only trade false rejections for
false confidence. Words a session read off the rendered sheet are good
evidence and belong in ``quote:``; this gate simply is not what establishes
them. Nothing in the patch marks which quotes are gated — the discriminator is
the cache row's ``content_type``, a fact about the document, because the patch
is the record and a second place to say so is a second source of truth.

What this does **not** change is what counts as a quote. The test is whether
the evidence is *text*, not whether extraction caught it: outlined flyer type
and a manual with no text layer are words on the sheet and are quotable once
read, while a checkmark in a feature-matrix column is a mark and never becomes
text by being looked at — it stays a quote-less cite (``ref`` + ``locator`` +
``note``). Quoting a feature's row label to establish an edition column
remains the forgery both rules exist to stop.

Run via ``make verify-quotes``. Exits non-zero on any non-verbatim quote or
any quote whose source is missing from the cache (an unverifiable quote is
not a verified one — ``make pull`` in pinexplore refreshes the cache). A
missing document is a failure, never a skip: a PDF the cache does not hold is
one a session could not have read.
Pinexplore is expected as a sibling checkout (``../pinexplore``); override
with the ``PINEXPLORE_DIR`` environment variable.
"""

from __future__ import annotations

import html
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Container, Iterator, Mapping

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PATCHES_DIR = REPO_ROOT / "patches"
PINEXPLORE_DIR = Path(
    os.environ.get("PINEXPLORE_DIR", str(REPO_ROOT.parent / "pinexplore"))
)

_SMART = {"“": '"', "”": '"', "‘": "'", "’": "'"}


def normalize(text: str) -> str:
    """Straighten smart quotes and collapse whitespace runs to single spaces."""
    for smart, straight in _SMART.items():
        text = text.replace(smart, straight)
    return re.sub(r"\s+", " ", text)


# One IPDB machine row as the page prints it: ``(column, page label)`` pairs. A
# ``None`` label renders the value bare, as the page does for the title and the
# "IPD No. 20 / March, 1992 / 4 Players" subtitle beneath it.
#
# Membership rule: **the stored value must be the page's literal string.** A
# field the page reformats would manufacture a false pass, so it stays out —
# ``ProductionNumber`` is ``20270`` here against the page's "20,270 units",
# ``DateOfManufacture`` an ISO timestamp against "March, 1992". Nothing is lost;
# ``AdditionalDetails`` carries the page's own date and player rendering. By that
# rule the ``Players`` row is itself redundant and wrong, but shipped quotes may
# rest on it, so dropping it is a deliberate call.
#
# Order and label spellings are inferred from the key order of pinexplore's
# ``ingest_sources/ipdb_xantari.json`` dump — IPDB resists scraping, so no cached
# page verifies them. Getting one wrong costs a false FAIL, never a false pass;
# the membership rule is what carries the gate's honesty.
_IPDB_ROW_FIELDS: tuple[tuple[str, str | None], ...] = (
    ("Title", None),
    ("Players", "Players"),
    ("AdditionalDetails", None),
    ("Manufacturer", "Manufacturer"),
    ("CommonAbbreviations", "Common Abbreviations"),
    ("Type", "Type"),
    ("MPU", "MPU"),
    ("ModelNumber", "Model Number"),
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
    checks a model's quote against this text and ``verify-quotes`` re-checks the
    shipped patch against the full row, so a delimiter in one and not the other
    is a quote that passes extraction and fails at ship time — hence the page's
    own ``Toys:`` rather than a synthetic markdown heading. Carrying labels at
    all is what lets a model tell a Note from ad copy in Marketing Slogans.
    """
    return _ipdb_lines(row, _IPDB_PROSE_COLUMNS)


def check_quote(quote: str, source: str) -> str | None:
    """Why *quote* fails to verify against *source*, or None if it verifies.

    Each ``[...]``-separated span must appear verbatim in the normalized
    source, and spans must appear in source order.
    """
    src = normalize(source)
    pos = 0
    for span in [s.strip() for s in quote.split("[...]") if s.strip()]:
        found = src.find(normalize(span), pos)
        if found == -1:
            if src.find(normalize(span)) != -1:
                return f"span out of source order: {span[:60]!r}"
            return f"span not verbatim in source: {span[:60]!r}"
        pos = found + len(normalize(span))
    return None


def _die(message: str) -> None:
    print(f"verify-quotes: FATAL: {message}", file=sys.stderr)
    sys.exit(2)


def _require_pinexplore() -> tuple[Path, Path]:
    """The cache sqlite and explore duckdb paths, or a loud exit."""
    if not PINEXPLORE_DIR.is_dir():
        _die(
            f"pinexplore repo not found at {PINEXPLORE_DIR} — clone it as a "
            f"sibling of this repo, or point PINEXPLORE_DIR at your checkout"
        )
    cache = PINEXPLORE_DIR / "ingest_sources" / "web" / "cache.sqlite"
    if not cache.is_file():
        _die(
            f"web cache not found at {cache} — run `make pull` in pinexplore "
            f"to download it from R2"
        )
    duck = PINEXPLORE_DIR / "explore.duckdb"
    if not duck.is_file():
        _die(
            f"explore.duckdb not found at {duck} — run `make explore` in "
            f"pinexplore to build it"
        )
    return cache, duck


class _Sources:
    """Source-text lookup over pinexplore's web cache and IPDB table.

    Two views of the same sources, for two callers:
    :meth:`text_for` returns the full text (IPDB's structured rows included) for
    the verbatim quote gate; :meth:`free_text_for` narrows an IPDB row to its
    machine prose, for AI extraction.
    """

    def __init__(self, cache_db: Path, duck_db: Path) -> None:
        sys.path.insert(0, str(PINEXPLORE_DIR / "scripts" / "web_scrape"))
        import web_cache  # type: ignore[import-not-found]  # pinexplore module, stdlib-only

        self._web_cache = web_cache
        self._duck_db = duck_db
        self._rows: dict[str, dict[str, object]] | None = None

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
        """The full quotable source text for a ref — the verbatim-gate view.

        Used by ``make verify-quotes`` to confirm a ``cite:`` quote is verbatim
        in its source. For ``ipdb:`` this is the whole rendered row
        (:func:`ipdb_row_text`), so a quote may legitimately cite a structured
        field. AI extraction wants :meth:`free_text_for` instead.
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
        """Whether *ref* names a cached PDF — the document class this gate skips.

        A PDF quote is not machine-checkable, so it is an author self-check
        rather than a gated one (see the module docstring). The signal is the
        cache row's ``content_type``, a fact about the **document**: the patch
        never records whether its own quote is verifiable, because the patch is
        the record and a second place to say so is a second source of truth.

        Deliberately narrow. Only an ``http(s)`` ref can name a PDF — scheme
        refs resolve to IPDB rows, OPDB pages and caption transcripts, which
        stay fully gated. A ref the cache does not hold is **not** a PDF: that
        is a NO-SOURCE failure, and a missing document must never pass as an
        ungated one. The URL's spelling is not consulted, so an HTML page served
        at a ``.pdf`` path stays gated.
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


def _quote_units(body: dict[str, object]) -> Iterator[tuple[str, str | None, str]]:
    """Every (ref, archive, quote) triple in an entry: header plus changesets.

    Walks the entry-level ``cite:`` mapping and each inline ``cites:`` entry
    carrying a quote, so inline footnote quotes are verified against their
    source exactly like entry-level ones. ``archive`` is the cite's Wayback
    snapshot URL when present, else None — for a dead original, the document
    is cached under the snapshot URL while ``ref`` stays the publisher's, so
    the caller resolves via ref first and falls back to the archive.
    """
    changesets = body.get("changesets")
    units: list[object] = [body]
    if isinstance(changesets, list):
        units.extend(changesets)
    for unit in units:
        if not isinstance(unit, dict):
            continue
        cite = unit.get("cite")
        specs = cite if isinstance(cite, list) else [cite]
        for spec in specs:
            if isinstance(spec, dict) and spec.get("quote"):
                archive = spec.get("archive")
                yield (
                    str(spec["ref"]),
                    str(archive) if archive else None,
                    str(spec["quote"]),
                )
        cites = unit.get("cites")
        if isinstance(cites, dict):
            for value in cites.values():
                if isinstance(value, dict) and value.get("quote"):
                    archive = value.get("archive")
                    yield (
                        str(value["ref"]),
                        str(archive) if archive else None,
                        str(value["quote"]),
                    )


def main() -> int:
    import yaml

    sources = _Sources(*_require_pinexplore())
    ok = failed = skipped = 0
    for patch in sorted(PATCHES_DIR.glob("[0-9]*.yaml")):
        doc = yaml.safe_load(patch.read_text())
        for claim in doc.get("claims", []):
            ((entity, body),) = claim.items()
            for ref, archive, quote in _quote_units(body):
                # A dead original is cached under its Wayback snapshot URL
                # while the cite's ref stays the publisher's — resolve via the
                # ref first, then the archive.
                addresses = [ref] + ([archive] if archive else [])
                # A PDF quote is the author's own check, not this gate's. Name
                # each one so the run never reads as covering what it did not.
                if any(sources.is_pdf(a) for a in addresses):
                    skipped += 1
                    print(f"SKIP-PDF  {patch.name} {entity} — {ref[:70]}")
                    continue
                source = next(
                    (t for a in addresses if (t := sources.text_for(a))), None
                )
                if source is None:
                    failed += 1
                    print(
                        f"NO-SOURCE {patch.name} {entity} — {ref[:70]} "
                        f"(not in the pinexplore cache; `make pull` there?)"
                    )
                    continue
                problem = check_quote(quote, source)
                if problem is None:
                    ok += 1
                else:
                    failed += 1
                    print(f"FAIL      {patch.name} {entity} — {problem}")
    tail = f", {skipped} skipped (PDF — author-checked)" if skipped else ""
    print(f"\nverify-quotes: {ok} verified, {failed} failed{tail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
