"""The parts-kit input contract: a JSONL candidate set.

The seam between candidate *mining* (an interactive session designing SQL/FTS
over the corpus — not this tool's job) and the sweep pipeline. Each line is one
unit of work — one model:

    {"ipdb_id": 4101, "hint": ["rock", "rock-encore"]}

- ``ipdb_id`` — the stable join key to both the corpus and the catalog. One
  candidate per model (the sweep judges the model's whole relationship set in
  one call), so ``ipdb_id`` is the dedupe key.
- ``field`` (optional) — the judged field. Only ``model_relationship`` exists
  today; the key is kept in the contract so a future archetype can slot in.
- ``hint`` (optional) — prior guess(es) at the target slug (a worklist column,
  an earlier session's answer); a string or a list of strings. **Never shown to
  the model** — only diffed deterministically against the sweep's own
  resolution, so an earlier AI's opinion is audited rather than inherited.
- ``evidence`` (optional) — source refs to judge from, in any scheme
  ``quotes.sources``'s ``free_text_for`` resolves (``ipdb:NNNN``, an ``http(s)``
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
    """One unit of work: judge one model's relationships against its evidence."""

    ipdb_id: int
    hint: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()

    @property
    def key(self) -> int:
        return self.ipdb_id

    def refs(self) -> tuple[str, ...]:
        """The evidence refs to judge from — defaulting to the model's IPDB note."""
        return self.evidence or (f"ipdb:{self.ipdb_id}",)


def _parse_hint(raw: object, line_no: int) -> tuple[str, ...]:
    """A hint is an optional string or list of non-empty strings."""
    if raw is None:
        return ()
    if isinstance(raw, str):
        return (raw.strip(),) if raw.strip() else ()
    if isinstance(raw, list) and all(isinstance(h, str) for h in raw):
        return tuple(h.strip() for h in raw if h.strip())
    raise CandidateError(
        f"line {line_no}: hint must be a string or list of strings when present"
    )


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
    if field_key is not None and field_key not in RELATIONAL_FIELDS:
        known = ", ".join(sorted(RELATIONAL_FIELDS))
        raise CandidateError(
            f"line {line_no}: unknown field {field_key!r} (known: {known})"
        )

    evidence = raw.get("evidence", [])
    if not isinstance(evidence, list) or not all(
        isinstance(ref, str) and ref.strip() for ref in evidence
    ):
        raise CandidateError(
            f"line {line_no}: evidence must be a list of non-empty ref strings"
        )

    return CandidateRow(
        ipdb_id=ipdb_id,
        hint=_parse_hint(raw.get("hint"), line_no),
        evidence=tuple(evidence),
    )


def load_candidates(path: Path) -> list[CandidateRow]:
    """Parse and validate a candidates JSONL file; raise :class:`CandidateError`."""
    rows: list[CandidateRow] = []
    seen: set[int] = set()
    for line_no, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        row = _parse_line(line, line_no)
        if row.key in seen:
            raise CandidateError(
                f"line {line_no}: duplicate candidate (ipdb_id={row.ipdb_id})"
            )
        seen.add(row.key)
        rows.append(row)
    if not rows:
        raise CandidateError(f"{path}: no candidate rows")
    return rows
