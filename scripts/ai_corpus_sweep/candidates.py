"""The parts-kit input contract: a JSONL candidate set.

The seam between candidate *mining* (an interactive session designing SQL/FTS
over the corpus — not this tool's job) and the sweep pipeline. Each line is one
unit of work — one (model, field) pair:

    {"ipdb_id": 5441, "field": "converted_from", "hint": "amazon-hunt"}

- ``ipdb_id`` — the stable join key to both the corpus and the catalog.
- ``field`` — a :mod:`ai_corpus_sweep.fields` registry key.
- ``hint`` (optional) — a prior guess at the target slug (a worklist column, an
  earlier session's answer). **Never shown to the model** — it is only diffed
  deterministically against the sweep's own resolution, so an earlier AI's
  opinion can be audited rather than inherited.
- ``evidence`` (optional) — source refs to judge from, in any scheme
  ``quote_verify``'s ``free_text_for`` resolves (``ipdb:NNNN``, an ``http(s)``
  web-cache URL). Defaults to the row's own IPDB note.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from ai_corpus_sweep.fields import RELATIONAL_FIELDS


class CandidateError(ValueError):
    """A malformed candidates file — bad JSON, unknown field, or a duplicate row."""


@dataclass(frozen=True, slots=True)
class CandidateRow:
    """One unit of work: judge one field of one model against its evidence."""

    ipdb_id: int
    field: str
    hint: str | None = None
    evidence: tuple[str, ...] = ()

    @property
    def key(self) -> tuple[int, str]:
        return (self.ipdb_id, self.field)

    def refs(self) -> tuple[str, ...]:
        """The evidence refs to judge from — defaulting to the row's IPDB note."""
        return self.evidence or (f"ipdb:{self.ipdb_id}",)


def _parse_line(line: str, line_no: int) -> CandidateRow:
    try:
        raw = json.loads(line)
    except json.JSONDecodeError as exc:
        raise CandidateError(f"line {line_no}: not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise CandidateError(f"line {line_no}: expected a JSON object")

    ipdb_id = raw.get("ipdb_id")
    if not isinstance(ipdb_id, int) or isinstance(ipdb_id, bool) or ipdb_id < 1:
        raise CandidateError(f"line {line_no}: ipdb_id must be a positive integer")

    field_key = raw.get("field")
    if field_key not in RELATIONAL_FIELDS:
        known = ", ".join(sorted(RELATIONAL_FIELDS))
        raise CandidateError(
            f"line {line_no}: unknown field {field_key!r} (known: {known})"
        )

    hint = raw.get("hint")
    if hint is not None and not isinstance(hint, str):
        raise CandidateError(f"line {line_no}: hint must be a string when present")

    evidence = raw.get("evidence", [])
    if not isinstance(evidence, list) or not all(
        isinstance(ref, str) and ref.strip() for ref in evidence
    ):
        raise CandidateError(
            f"line {line_no}: evidence must be a list of non-empty ref strings"
        )

    return CandidateRow(
        ipdb_id=ipdb_id,
        field=field_key,
        hint=(hint.strip() or None) if isinstance(hint, str) else None,
        evidence=tuple(evidence),
    )


def load_candidates(path: Path) -> list[CandidateRow]:
    """Parse and validate a candidates JSONL file; raise :class:`CandidateError`."""
    rows: list[CandidateRow] = []
    seen: set[tuple[int, str]] = set()
    for line_no, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        row = _parse_line(line, line_no)
        if row.key in seen:
            raise CandidateError(
                f"line {line_no}: duplicate candidate "
                f"(ipdb_id={row.ipdb_id}, field={row.field})"
            )
        seen.add(row.key)
        rows.append(row)
    if not rows:
        raise CandidateError(f"{path}: no candidate rows")
    return rows
