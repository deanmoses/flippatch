"""The stateless core: page text + slices → packet of checked candidates.

A pure function (``extract``) — no disk, no network of its own, no sibling
checkout. It takes already-resolved page text and an ``AiClient`` (the offline
mock seam), runs each slice, unions repeated samples, runs every returned quote
through ``quotes.verbatim.check_quote``, and returns a ``Packet``. Source-ref
resolution, page-metadata lookup, and usage reporting live in the CLI shell
(``cli.py``), keeping this core as offline-testable as the rest of the tooling.

The packet is keyed by **field**, not by slice, matching the "one of three states
per field category" output spec — because a slice does not always map 1:1 to a
field: a dependency-pair slice (technology generation + subgeneration, display
type + subtype) resolves two fields in one call, and each lands in its own field
entry with its own state.

Coverage is explicit: every in-scope field named in ``expected_fields`` is
pre-seeded as ``not-checked`` and only overwritten if a slice actually covers it,
so the packet distinguishes "looked and found nothing" (``checked-absent``) from
"no slice covered this" (``not-checked``) — the anti-satisficing receipt, never a
silent omission.

Per the "candidates, not facts" discipline, an unverifiable quote is **kept and
flagged** (``quote_verified: false``), never silently dropped and never presented
as a fact — the master session sees exactly what did and did not check out.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict, cast

from common.ai.candidates import Candidate, EvidenceQuote
from common.ai.client import CHEAP_MODEL, AiError
from quotes.verbatim import check_quote

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from common.ai.client import AiClient
    from common.types import Json

    from ai_page_extract.framework import ExtractedItem, Slice, TargetContext

# Packet states for a field (AiPageDataExtractor.md, "Output format").
STATE_CANDIDATES = "candidates"
STATE_CHECKED_ABSENT = "checked-absent"
STATE_NOT_CHECKED = "not-checked"

_NOT_COVERED = "no slice covered this field in this run"


class PageMetadata(TypedDict):
    """The web-cache row's quality/freshness signals the master session should see.

    ``last_updated`` is the date the *page* states (never the game's — a hint for
    the year slice, not a candidate); ``rendered`` flags a headless-render fetch
    (thin JS pages read worse). All nullable — a structured (non-web) source has
    none. See AiPageDataExtractor.md "Output format".
    """

    last_updated: str | None
    content_type: str | None
    rendered: int | None
    title: str | None


@dataclass(frozen=True, slots=True)
class PacketCandidate:
    """A shared ``Candidate`` plus this tool's slice-specific extras.

    The shared shape stays minimal (value + evidence); ``extra`` carries what a
    given slice adds — a ``count`` for an enumerative feature, a ``related``
    entity for a lineage signal, a ``role`` for a credit, an unverified-quote
    reason when a quote fails to check. Flattened into the packet JSON by
    :meth:`to_json`.
    """

    candidate: Candidate
    extra: Mapping[str, Json]

    def to_json(self) -> dict[str, Json]:
        out: dict[str, Json] = {
            "value": self.candidate.value,
            "quote": self.candidate.evidence.quote,
            "source_ref": self.candidate.evidence.source_ref,
            "quote_verified": self.candidate.evidence.quote_verified,
        }
        out.update(self.extra)
        return out


@dataclass(frozen=True, slots=True)
class FieldResult:
    """One field's outcome: its state, candidates, provenance, and sample tally.

    ``note`` carries the reason a field is ``not-checked`` (no slice covered it, or
    every sample errored) *or* a partial-failure note when a union slice completed
    some but not all samples — a "no silent caps" receipt, never hidden.
    """

    state: str
    candidates: tuple[PacketCandidate, ...]
    aggregate: str
    samples: int
    samples_completed: int
    slice_label: str
    note: str | None = None

    def to_json(self) -> dict[str, Json]:
        out: dict[str, Json] = {
            "state": self.state,
            "aggregate": self.aggregate,
            "samples": self.samples,
            "samples_completed": self.samples_completed,
            "candidates": [c.to_json() for c in self.candidates],
        }
        if self.slice_label:
            out["slice"] = self.slice_label
        if self.note is not None:
            out["note"] = self.note
        return out


@dataclass(frozen=True, slots=True)
class Packet:
    """The full extraction result for one (page, record) — candidates, not facts."""

    source_ref: str
    fields: Mapping[str, FieldResult]
    page_metadata: PageMetadata | None = None

    def to_json(self) -> dict[str, Json]:
        # PageMetadata is a TypedDict of JSON scalars, but ``dict(td)`` types as
        # ``dict[str, object]`` (a TypedDict's ``__getitem__`` is object-typed);
        # cast to assert the Json-ness the fields already guarantee.
        page_metadata = (
            cast("dict[str, Json]", dict(self.page_metadata))
            if self.page_metadata
            else None
        )
        return {
            "source_ref": self.source_ref,
            "page_metadata": page_metadata,
            "fields": {key: result.to_json() for key, result in self.fields.items()},
        }


def extract(
    *,
    page_text: str,
    source_ref: str,
    slices: Sequence[Slice],
    ai: AiClient,
    expected_fields: Sequence[str] = (),
    page_metadata: PageMetadata | None = None,
    target: TargetContext | None = None,
) -> Packet:
    """Run every slice over ``page_text`` and return the collated, field-keyed packet.

    Pure: the same inputs always yield the same packet. Every field in
    ``expected_fields`` is pre-seeded ``not-checked`` so an uncovered field is
    reported, never silently dropped; slices overwrite the fields they cover.
    ``target`` (when given) frames every slice with the model the run is *about*,
    so a multi-model page stops attributing a sibling's facts to it.
    ``AiBudgetError`` from the client's runaway guard is intentionally **not**
    caught — it must abort the whole run; only per-sample ``AiError`` is contained.
    """
    results: dict[str, FieldResult] = {
        field: FieldResult(
            state=STATE_NOT_CHECKED,
            candidates=(),
            aggregate="none",
            samples=0,
            samples_completed=0,
            slice_label="",
            note=_NOT_COVERED,
        )
        for field in expected_fields
    }
    for slice_ in slices:
        results.update(_run_slice(slice_, page_text, source_ref, ai, target))
    return Packet(source_ref=source_ref, fields=results, page_metadata=page_metadata)


def _run_slice(
    slice_: Slice,
    page_text: str,
    source_ref: str,
    ai: AiClient,
    target: TargetContext | None = None,
) -> dict[str, FieldResult]:
    fields = slice_.fields or (slice_.key,)
    raw: list[ExtractedItem] = []
    completed = 0
    last_error: str | None = None
    for _ in range(slice_.samples):
        try:
            result = ai.structured(
                system=_system_for(slice_),
                user=slice_.user_prompt(page_text, target),
                schema=slice_.schema,
                model=CHEAP_MODEL,
                max_tokens=slice_.max_tokens,
            )
        except AiError as exc:
            # A single sample failing must not discard the samples that did
            # complete — for a union slice that would throw away verified
            # candidates. Only a slice with zero completed samples is not-checked.
            last_error = str(exc)
            continue
        completed += 1
        raw.extend(slice_.parser(result))

    if completed == 0:
        return {
            field: FieldResult(
                state=STATE_NOT_CHECKED,
                candidates=(),
                aggregate=slice_.aggregate,
                samples=slice_.samples,
                samples_completed=0,
                slice_label=slice_.key,
                note=last_error,
            )
            for field in fields
        }

    partial = (
        None
        if completed == slice_.samples
        else f"{slice_.samples - completed} of {slice_.samples} samples failed: {last_error}"
    )
    buckets: dict[str, list[ExtractedItem]] = {field: [] for field in fields}
    primary = fields[0]
    for item in raw:
        buckets.setdefault(item.field or primary, []).append(item)

    out: dict[str, FieldResult] = {}
    for field in fields:
        candidates = tuple(
            _verify(item, page_text, source_ref)
            for item in _merge(buckets.get(field, []))
        )
        out[field] = FieldResult(
            state=STATE_CANDIDATES if candidates else STATE_CHECKED_ABSENT,
            candidates=candidates,
            aggregate=slice_.aggregate,
            samples=slice_.samples,
            samples_completed=completed,
            slice_label=slice_.key,
            note=partial,
        )
    return out


def _system_for(slice_: Slice) -> str:
    # Imported lazily so the module has no import-time dependency on prompt text.
    from ai_page_extract.framework import SYSTEM

    return SYSTEM


def _merge(items: list[ExtractedItem]) -> list[ExtractedItem]:
    """Union duplicate items within a field, keyed by value (+ related entity/role).

    A ``single-read`` slice returns one sample, so this is a no-op there. For a
    ``union`` slice it collapses the same value surfaced by several samples into
    one item. When one sample supplied a count and another did not, keep the
    **whole** counted item — count and quote must come from the same sample, so
    the quote actually supports the count.
    """
    merged: dict[tuple[str, str], ExtractedItem] = {}
    for item in items:
        secondary = item.extra.get("related") or item.extra.get("role") or ""
        key = (item.value.strip().lower(), str(secondary).strip().lower())
        existing = merged.get(key)
        if existing is None or (
            existing.extra.get("count") is None and item.extra.get("count") is not None
        ):
            merged[key] = item
    return list(merged.values())


def _verify(item: ExtractedItem, page_text: str, source_ref: str) -> PacketCandidate:
    """Check the item's quote verbatim against the page; keep-and-flag either way."""
    reason = check_quote(item.quote, page_text) if item.quote else "no quote provided"
    extra = dict(item.extra)
    if reason is not None:
        extra["quote_unverified_reason"] = reason
    return PacketCandidate(
        candidate=Candidate(
            value=item.value,
            evidence=EvidenceQuote(
                quote=item.quote,
                source_ref=source_ref,
                quote_verified=reason is None,
            ),
        ),
        extra=extra,
    )
