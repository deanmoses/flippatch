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
    from collections.abc import Iterator

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


def ipdb_row_text(
    *,
    title: str | None,
    manufacturer: str | None,
    type_: str | None,
    players: object | None,
    theme: str | None,
    notable_features: str | None,
    notes: str | None,
) -> str:
    """The quotable text of one IPDB machine row.

    Mirrors what the IPDB page renders so a quote stays ctrl-F honest there:
    the title as a bare heading, the structured fields as ``Label: value``
    rows, then the Notable Features and Notes prose. Empty fields are omitted.
    """
    lines = []
    if title:
        lines.append(html.unescape(title))
    for label, value in (
        ("Manufacturer", manufacturer),
        ("Type", type_),
        ("Players", players),
        ("Theme", theme),
    ):
        if value:
            lines.append(f"{label}: {html.unescape(str(value))}")
    lines.extend(html.unescape(prose) for prose in (notable_features, notes) if prose)
    return "\n".join(lines)


def ipdb_notes_text(*, notable_features: str | None, notes: str | None) -> str:
    """The free-text prose of one IPDB machine row — Notable Features and Notes.

    This is the AI-consumable slice of an IPDB row. IPDB's structured fields
    (Manufacturer, Type, Players, Theme, year) are deterministic data, read
    directly from the columns — never re-extracted by a model, which would
    forfeit their determinism and precision. So AI extraction sees only the
    editor-authored prose here, not the structured rows ``ipdb_row_text``
    renders for the verify-quotes verbatim gate.
    """
    return "\n".join(
        html.unescape(prose) for prose in (notable_features, notes) if prose
    )


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
    the verbatim quote gate; :meth:`free_text_for` returns unstructured prose
    only, for AI extraction.
    """

    def __init__(self, cache_db: Path, duck_db: Path) -> None:
        sys.path.insert(0, str(PINEXPLORE_DIR / "scripts" / "web_scrape"))
        import web_cache  # type: ignore[import-not-found]  # pinexplore module, stdlib-only

        self._web_cache = web_cache
        self._duck_db = duck_db
        self._ipdb: dict[str, str] | None = None
        self._ipdb_notes: dict[str, str] | None = None

    def free_text_for(self, ref: str) -> str | None:
        """Source text for AI extraction — unstructured free text only.

        The input adapter for the page extractor. Web / opdb / youtube refs
        already resolve to unstructured readable text, so it passes them
        through :meth:`text_for`; an ``ipdb:`` ref resolves to its free-text
        Notes / Notable-Features prose alone, so IPDB's structured fields stay
        out of the model's context (they are deterministic data, read directly).
        """
        if ref.startswith("ipdb:"):
            return self._ipdb_notes_text(ref.partition(":")[2])
        return self.text_for(ref)

    def text_for(self, ref: str) -> str | None:
        """The full quotable source text for a ref — the verbatim-gate view.

        Used by ``make verify-quotes`` to confirm a ``cite:`` quote is verbatim
        in its source. For ``ipdb:`` this is the whole rendered row (title, the
        structured Manufacturer/Type/Players/Theme rows, then Notable Features
        and Notes), so a quote may legitimately cite a structured field. AI
        extraction wants :meth:`free_text_for` instead, which drops those
        structured rows.
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

    def _ipdb_text(self, identifier: str) -> str | None:
        if self._ipdb is None:
            import duckdb

            con = duckdb.connect(str(self._duck_db), read_only=True)
            rows = con.execute(
                "SELECT IpdbId, Title, Manufacturer, Type, Players, Theme,"
                " NotableFeatures, Notes FROM ipdb_machines"
            ).fetchall()
            con.close()
            self._ipdb = {
                str(ipdb_id): ipdb_row_text(
                    title=title,
                    manufacturer=manufacturer,
                    type_=type_,
                    players=players,
                    theme=theme,
                    notable_features=features,
                    notes=notes,
                )
                for ipdb_id, title, manufacturer, type_, players, theme, features, notes in rows
            }
        return self._ipdb.get(identifier)

    def _ipdb_notes_text(self, identifier: str) -> str | None:
        if self._ipdb_notes is None:
            import duckdb

            con = duckdb.connect(str(self._duck_db), read_only=True)
            rows = con.execute(
                "SELECT IpdbId, NotableFeatures, Notes FROM ipdb_machines"
            ).fetchall()
            con.close()
            self._ipdb_notes = {
                str(ipdb_id): ipdb_notes_text(notable_features=features, notes=notes)
                for ipdb_id, features, notes in rows
            }
        text = self._ipdb_notes.get(identifier)
        return text if text and text.strip() else None


def _quote_units(body: dict[str, object]) -> Iterator[tuple[str, str]]:
    """Every (ref, quote) pair in an entry: the header plus changesets items.

    Walks the entry-level ``cite:`` mapping and each inline ``cites:`` entry
    carrying a quote, so inline footnote quotes are verified against their
    source exactly like entry-level ones.
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
                yield str(spec["ref"]), str(spec["quote"])
        cites = unit.get("cites")
        if isinstance(cites, dict):
            for value in cites.values():
                if isinstance(value, dict) and value.get("quote"):
                    yield str(value["ref"]), str(value["quote"])


def main() -> int:
    import yaml

    sources = _Sources(*_require_pinexplore())
    ok = failed = skipped = 0
    for patch in sorted(PATCHES_DIR.glob("[0-9]*.yaml")):
        doc = yaml.safe_load(patch.read_text())
        for claim in doc.get("claims", []):
            ((entity, body),) = claim.items()
            for ref, quote in _quote_units(body):
                # A PDF quote is the author's own check, not this gate's. Name
                # each one so the run never reads as covering what it did not.
                if sources.is_pdf(ref):
                    skipped += 1
                    print(f"SKIP-PDF  {patch.name} {entity} — {ref[:70]}")
                    continue
                source = sources.text_for(ref)
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
