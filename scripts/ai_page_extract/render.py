"""Compact packet rendering — the default human/master-session view.

The full ``Packet.to_json`` is unwieldy for a one-line source: every in-scope
field is listed even when empty, wrapping zero candidates in
``state``/``aggregate``/``samples``/``slice`` scaffolding. That bulk is pure
context noise for the arbiter, whose decision material is only the
``candidates``-state fields.

:func:`format_summary` prints those in full and collapses the empty states to a
coverage tail — but the tail **splits ``not-checked`` from ``checked-absent``**
and surfaces any error / partial-sample ``note``, because a field left
``not-checked`` by a slice that *errored* is a genuine coverage gap, not a real
absence, and collapsing it into "absent" would launder that gap (the
anti-satisficing receipt has to survive the collapse — AiPageDataExtractor.md,
"Compact packet view"). ``--verbose`` on the CLI restores the full JSON.

Pure and offline-testable like the rest of the core: ``Packet`` in, ``str`` out.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ai_page_extract.extract import (
    _NOT_COVERED,
    STATE_CANDIDATES,
    STATE_CHECKED_ABSENT,
    STATE_NOT_CHECKED,
)

if TYPE_CHECKING:
    from ai_page_extract.extract import FieldResult, Packet


def format_summary(packet: Packet) -> str:
    """Render ``packet`` as the compact default view (see module docstring)."""
    lines: list[str] = [f"source_ref: {packet.source_ref}"]
    if packet.page_metadata is not None:
        meta = " ".join(
            f"{key}={value!r}"
            for key, value in packet.page_metadata.items()
            if value is not None
        )
        lines.append(f"page_metadata: {meta}" if meta else "page_metadata: (none)")

    absent: list[str] = []
    not_covered: list[str] = []
    # (field, note) pairs — coverage gaps that must stay visible per field.
    errored: list[tuple[str, str]] = []

    lines.append("")
    lines.append("candidates:")
    found_any = False
    for field, result in packet.fields.items():
        if result.state == STATE_CANDIDATES:
            found_any = True
            lines.extend(_render_field(field, result))
        elif result.state == STATE_CHECKED_ABSENT:
            # A checked-absent field with a partial-sample note is a gap, not a
            # clean absence — route it to the visible-gap list, not the tail.
            if result.note is not None:
                errored.append((field, result.note))
            else:
                absent.append(field)
        elif result.state == STATE_NOT_CHECKED:
            if result.note is None or result.note == _NOT_COVERED:
                not_covered.append(field)
            else:
                errored.append((field, result.note))
    if not found_any:
        lines.append("  (none)")

    lines.append("")
    lines.append(f"checked-absent ({len(absent)}): {', '.join(absent) or '—'}")
    lines.append(f"not-checked ({len(not_covered)}): {', '.join(not_covered) or '—'}")
    if errored:
        lines.append("gaps (slice errored / samples failed):")
        lines.extend(f"  ⚠ {field} — {note}" for field, note in errored)

    return "\n".join(lines)


def _render_field(field: str, result: FieldResult) -> list[str]:
    """One candidates-state field: a header with its sample tally, then each candidate in full."""
    tally = f"{result.aggregate}, {result.samples_completed}/{result.samples} samples"
    header = f"  {field}  [{tally}]"
    if result.note is not None:
        header += f"  ⚠ {result.note}"
    lines = [header]
    lines.extend(
        f"    {json.dumps(c.to_json(), ensure_ascii=False)}" for c in result.candidates
    )
    return lines
