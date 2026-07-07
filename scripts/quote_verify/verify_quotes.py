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

Run via ``make verify-quotes``. Exits non-zero on any non-verbatim quote or
any quote whose source is missing from the cache (an unverifiable quote is
not a verified one — ``make pull`` in pinexplore refreshes the cache).
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
    """Source-text lookup over pinexplore's web cache and IPDB table."""

    def __init__(self, cache_db: Path, duck_db: Path) -> None:
        sys.path.insert(0, str(PINEXPLORE_DIR / "scripts" / "web_scrape"))
        import web_cache  # type: ignore[import-not-found]  # pinexplore module, stdlib-only

        self._web_cache = web_cache
        self._duck_db = duck_db
        self._ipdb: dict[str, str] | None = None

    def text_for(self, ref: str) -> str | None:
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
    ok = failed = 0
    for patch in sorted(PATCHES_DIR.glob("[0-9]*.yaml")):
        doc = yaml.safe_load(patch.read_text())
        for claim in doc.get("claims", []):
            ((entity, body),) = claim.items()
            for ref, quote in _quote_units(body):
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
    print(f"\nverify-quotes: {ok} verified, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
