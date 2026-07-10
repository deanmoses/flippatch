"""CLI entrypoint for the page extractor — the thin stateful shell.

Run via the opt-in ``make extract-page`` target (which sets ``PYTHONPATH=scripts``):

    make extract-page ARGS="ipdb:5632"
    make extract-page ARGS="https://example.com/dogs-race --target 'Dogs Race'"

Localhost-only: it resolves the source ref to page text out of pinexplore's web
cache / explore.duckdb, so it needs that sibling checkout. Requires
``ANTHROPIC_API_KEY`` — exits with a clear error if unset.

The shell does the impure work (resolve the ref, build the client, print);
:func:`ai_page_extract.extract.extract` is the pure, offline-testable core.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from common.ai.client import (
    MAX_REQUESTS,
    AiBudgetError,
    AiUnavailableError,
    require_ai_client,
)
from common.related_projects import (
    EXPLORE_DUCKDB,
    FLIPCOMMONS_DB,
    WEB_CACHE_DB,
    load_env,
)

from ai_page_extract.catalog import CatalogDb, ModelRef
from ai_page_extract.extract import PageMetadata, extract
from ai_page_extract.fields import MODEL_INFO_FIELDS, build_slices
from ai_page_extract.framework import TargetContext
from ai_page_extract.render import format_summary

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from common.catalog.entity_index import EntityRef


@dataclass(frozen=True, slots=True)
class ResolvedPage:
    """A cached source resolved to its text and (for web pages) its metadata."""

    text: str
    metadata: PageMetadata | None


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="extract-page",
        description=(
            "Fan a cached source page out across cheap-model slices and print a "
            "packet of candidate claims with quote-checked evidence (requires "
            "ANTHROPIC_API_KEY)."
        ),
    )
    parser.add_argument(
        "source_ref",
        help=(
            "source ref: an http(s) URL, or opdb:<id> / youtube:<id> / ipdb:<id> "
            "(an ipdb: ref extracts from its free-text Notes / Notable-Features "
            "prose; IPDB's structured fields are resolved directly, not by the AI)"
        ),
    )
    parser.add_argument(
        "--target",
        default=None,
        help=(
            'the model this run is about, as you know it (e.g. "Joker"). Strongly '
            "recommended on maker-index / whole-lineup pages: it frames every slice "
            "so a sibling machine's facts aren't attributed to the target."
        ),
    )
    parser.add_argument(
        "--maker",
        default=None,
        help="the target's manufacturer / corporate entity (sharpens disambiguation)",
    )
    parser.add_argument(
        "--note",
        default=None,
        help='free-form per-run instruction (e.g. "ignore the sidebar\'s related list")',
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help=(
            "print the full packet JSON. The default is a compact view: "
            "candidates-state fields in full, the empty states collapsed to a "
            "coverage tail (with errored slices called out)."
        ),
    )
    parser.add_argument(
        "--max-requests",
        type=int,
        default=MAX_REQUESTS,
        dest="max_requests",
        help=f"per-invocation AI-call ceiling (default {MAX_REQUESTS}; one page is ~23)",
    )
    return parser.parse_args(argv)


def _page_metadata(row: Mapping[str, object]) -> PageMetadata:
    """Narrow a web-cache row into the typed metadata the packet carries."""

    def as_str(key: str) -> str | None:
        value = row.get(key)
        return value if isinstance(value, str) else None

    def as_int(key: str) -> int | None:
        value = row.get(key)
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    return PageMetadata(
        last_updated=as_str("last_updated"),
        content_type=as_str("content_type"),
        rendered=as_int("rendered"),
        title=as_str("title"),
    )


def _resolve_page(source_ref: str) -> ResolvedPage | None:
    """The cached page (text + metadata) for the ref, or None. Localhost-only.

    Metadata (a text-quality signal for the master session, and the future
    freshness key) is available for ``http(s)`` refs from the web-cache row; for
    ``opdb`` / ``youtube`` / ``ipdb`` refs it is None for now.
    """
    if not WEB_CACHE_DB.is_file():
        print(
            f"error: pinexplore web cache not found at {WEB_CACHE_DB} — run "
            f"`make pull` in pinexplore, or set PINEXPLORE_DIR",
            file=sys.stderr,
        )
        return None
    # The input adapter (AiPageDataExtractor.md): resolves an http(s)/opdb/youtube/
    # ipdb ref to its unstructured source text. free_text_for keeps IPDB's
    # structured fields out of the fan-out — an ipdb: ref yields its Notes prose
    # alone. Constructing it also puts pinexplore's web_cache module on the path.
    from quote_verify.verify_quotes import _Sources

    sources = _Sources(WEB_CACHE_DB, EXPLORE_DUCKDB)
    text = sources.free_text_for(source_ref)
    if text is None:
        return None

    metadata: PageMetadata | None = None
    if source_ref.startswith(("http://", "https://")):
        import web_cache  # type: ignore[import-not-found]  # pinexplore module on the path

        row = web_cache.get(source_ref)
        if row:
            metadata = _page_metadata(row)
    return ResolvedPage(text=text, metadata=metadata)


# Source-ref schemes that carry a structured external id we can key a model on.
_ID_REF_SCHEMES = ("ipdb:", "opdb:")


def _ref_target_banner(
    source_ref: str,
    target_name: str,
    ref_model: ModelRef | None,
    name_matches: Sequence[EntityRef],
) -> str | None:
    """Warn (never error) when an external-id source ref and ``--target`` disagree.

    The deterministic ref/target cross-check (AiPageDataExtractor.md build order §8):
    an ``ipdb:``/``opdb:`` ref can denote a *different* machine than the target name
    resolves to, because IPDB splits EM/SS (and other variants) into separate
    records. Every candidate is otherwise silently pinned to whichever record the
    author has in mind — wrong data aimed at the wrong entity. This surfaces the
    divergence; the pure comparison (``ref_model`` from the id lookup vs.
    ``name_matches`` from ``EntityIndex.resolve``) is offline-testable, the DB I/O
    stays in the shell. A mismatch is a *warning*: the catalog may simply not hold
    the ref's model yet, so it is at once a mis-attribution alert and a
    catalog-gap / disambiguation signal — never a hard failure.
    """
    match_slugs = sorted({ref.slug for ref in name_matches})
    if ref_model is None:
        return (
            f"warning: {source_ref} is not in the catalog by its IPDB/OPDB id — it "
            f"may name a model the catalog does not hold yet (a possible gap). "
            f"Candidates are attributed to --target {target_name!r} regardless."
        )
    ref_label = f"model:{ref_model.slug} ({ref_model.name})"
    if not match_slugs:
        return (
            f"warning: {source_ref} → {ref_label}, but --target {target_name!r} "
            f"resolves to no catalog model — the target name may be off, or that "
            f"model may be missing. The ref is the more reliable anchor."
        )
    shown = ", ".join(f"model:{slug}" for slug in match_slugs)
    if ref_model.slug not in match_slugs:
        return (
            f"warning: source ref and --target disagree — {source_ref} → {ref_label}, "
            f"but --target {target_name!r} → {shown}. The page describes "
            f"model:{ref_model.slug}; confirm which record you are authoring "
            f"(IPDB often splits EM/SS or variants into separate records)."
        )
    if len(match_slugs) > 1:
        return (
            f"note: --target {target_name!r} is ambiguous ({shown}); {source_ref} "
            f"pins it to {ref_label}."
        )
    return None  # a single name match, equal to the ref — no divergence to report


def _check_ref_target(source_ref: str, target_name: str, catalog: CatalogDb) -> None:
    """Resolve the id-ref and the target name and print any divergence (localhost).

    The impure half of the cross-check: the id → model lookup and the name → model
    resolution both hit the flipcommons DB; the comparison is the pure
    :func:`_ref_target_banner`.
    """
    from common.catalog.entity_index import EntityIndex

    ref_model = catalog.model_for_external_ref(source_ref)
    index = EntityIndex.build(FLIPCOMMONS_DB)
    name_matches = index.resolve(target_name, types=("model",))
    banner = _ref_target_banner(source_ref, target_name, ref_model, name_matches)
    if banner is not None:
        print(banner, file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    load_env()
    args = _parse_args(argv)

    try:
        ai = require_ai_client(max_requests=args.max_requests)
    except AiUnavailableError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    resolved = _resolve_page(args.source_ref)
    if resolved is None:
        print(
            f"error: no cached source text for {args.source_ref!r} "
            f"(not in the pinexplore cache; `make pull` there?)",
            file=sys.stderr,
        )
        return 2

    catalog: CatalogDb | None = None
    if FLIPCOMMONS_DB.is_file():
        catalog = CatalogDb(FLIPCOMMONS_DB)
    else:
        print(
            f"warning: flipcommons dev DB not found at {FLIPCOMMONS_DB} — grounding "
            f"single-value fields on hardcoded fallback vocab (set FLIPCOMMONS_DIR)",
            file=sys.stderr,
        )

    target = (
        TargetContext(name=args.target, maker=args.maker, note=args.note)
        if args.target
        else None
    )
    if target is None and (args.maker or args.note):
        print(
            "warning: --maker / --note are ignored without --target (the model the "
            "run is about)",
            file=sys.stderr,
        )

    # Ref/target cross-check: an ipdb:/opdb: ref may denote a different model than
    # --target resolves to by name (IPDB splits EM/SS into separate records). Warn
    # before the run so candidates aren't silently pinned to the wrong record.
    if (
        catalog is not None
        and target is not None
        and args.source_ref.startswith(_ID_REF_SCHEMES)
    ):
        _check_ref_target(args.source_ref, target.name, catalog)

    try:
        packet = extract(
            page_text=resolved.text,
            source_ref=args.source_ref,
            slices=build_slices(catalog),
            ai=ai,
            expected_fields=MODEL_INFO_FIELDS,
            page_metadata=resolved.metadata,
            target=target,
        )
    except AiBudgetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    finally:
        print(
            f"extract-page: {ai.request_count} AI calls, "
            f"{ai.usage.total_tokens} tokens",
            file=sys.stderr,
        )

    if args.verbose:
        print(json.dumps(packet.to_json(), indent=2, ensure_ascii=False))
    else:
        print(format_summary(packet))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
