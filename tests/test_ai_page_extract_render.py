"""Tests for the compact packet view (``ai_page_extract.render.format_summary``).

The flip to compact-by-default only pays off if the collapse is *lossless where
it matters*: candidates-state fields print in full, and the three-state coverage
receipt survives — with ``not-checked`` kept distinct from ``checked-absent`` and
an errored slice surfaced as a gap rather than laundered into "absent".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai_page_extract.extract import (
    _NOT_COVERED,
    STATE_CANDIDATES,
    STATE_CHECKED_ABSENT,
    STATE_NOT_CHECKED,
    FieldResult,
    Packet,
    PacketCandidate,
    PageMetadata,
)
from ai_page_extract.render import format_summary
from common.ai.candidates import Candidate, EvidenceQuote

if TYPE_CHECKING:
    from common.types import Json


def _candidate(value: str, *, verified: bool = True, **extra: Json) -> PacketCandidate:
    return PacketCandidate(
        candidate=Candidate(
            value=value,
            evidence=EvidenceQuote(
                quote=f"quote for {value}",
                source_ref="ipdb:1",
                quote_verified=verified,
            ),
        ),
        extra=extra,
    )


def _field(
    state: str,
    *,
    candidates: tuple[PacketCandidate, ...] = (),
    aggregate: str = "single-read",
    samples: int = 1,
    completed: int = 1,
    note: str | None = None,
) -> FieldResult:
    return FieldResult(
        state=state,
        candidates=candidates,
        aggregate=aggregate,
        samples=samples,
        samples_completed=completed,
        slice_label="slice",
        note=note,
    )


def _packet(fields: dict[str, FieldResult], **meta: object) -> Packet:
    return Packet(
        source_ref="ipdb:1",
        fields=fields,
        page_metadata=PageMetadata(**meta) if meta else None,  # type: ignore[typeddict-item]
    )


def test_candidate_field_prints_in_full():
    packet = _packet(
        {"year": _field(STATE_CANDIDATES, candidates=(_candidate("1976", month=3),))}
    )
    out = format_summary(packet)
    # The candidate line is complete JSON — value, quote, verification, and extras.
    assert '"value": "1976"' in out
    assert '"quote": "quote for 1976"' in out
    assert '"quote_verified": true' in out
    assert '"month": 3' in out


def test_absent_collapses_to_a_single_tail_line():
    packet = _packet(
        {
            "cabinet": _field(STATE_CHECKED_ABSENT),
            "franchise": _field(STATE_CHECKED_ABSENT),
        }
    )
    out = format_summary(packet)
    assert "checked-absent (2): cabinet, franchise" in out
    # Collapsed — the empty fields are not each rendered as a block.
    assert "slice" not in out


def test_not_checked_stays_distinct_from_absent():
    packet = _packet(
        {
            "cabinet": _field(STATE_CHECKED_ABSENT),
            "entity_discovery": _field(
                STATE_NOT_CHECKED, completed=0, note=_NOT_COVERED
            ),
        }
    )
    out = format_summary(packet)
    assert "checked-absent (1): cabinet" in out
    assert "not-checked (1): entity_discovery" in out


def test_errored_slice_is_surfaced_as_a_gap_not_absent():
    # A not-checked field whose note is an error (not the plain not-covered note)
    # is a genuine coverage hole — it must be called out, never folded into a tail.
    packet = _packet(
        {
            "system": _field(STATE_NOT_CHECKED, completed=0, note="rate limit: 429"),
        }
    )
    out = format_summary(packet)
    assert (
        "not-checked (0):" in out
    )  # the errored field is NOT counted as plain not-covered
    assert "⚠ system — rate limit: 429" in out


def test_partial_sample_failure_on_absent_field_is_a_gap():
    # checked-absent with a partial-sample note is a gap, not a clean absence.
    packet = _packet(
        {
            "themes": _field(
                STATE_CHECKED_ABSENT,
                aggregate="union",
                samples=3,
                completed=1,
                note="2 of 3 samples failed: boom",
            ),
        }
    )
    out = format_summary(packet)
    assert "themes" not in out.split("checked-absent")[1].split("\n")[0]
    assert "⚠ themes — 2 of 3 samples failed: boom" in out


def test_page_metadata_omits_nulls():
    packet = _packet(
        {"year": _field(STATE_CHECKED_ABSENT)},
        last_updated="2020-01-01",
        content_type=None,
        rendered=None,
        title="Dogs Race",
    )
    out = format_summary(packet)
    assert "last_updated='2020-01-01'" in out
    assert "title='Dogs Race'" in out
    assert "content_type" not in out


def test_no_candidates_says_none():
    packet = _packet({"year": _field(STATE_CHECKED_ABSENT)})
    out = format_summary(packet)
    assert "candidates:\n  (none)" in out
