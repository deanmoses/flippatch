"""The "candidates, not facts" data model shared by the extraction and sweep tools.

``EvidenceQuote`` and ``Candidate`` are the shapes AiCommon.md §3 reserves for
these tools: a cheap model emits a *candidate value* backed by a *quote whose
verbatim existence has been checked* — never a verified fact. Kept minimal —
value + evidence — with any slice-specific extras (a count, a related-entity ref)
carried by the consumer alongside these, not folded in.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvidenceQuote:
    """A quote, the source it was drawn from, and whether it verified verbatim.

    ``quote_verified`` is the result of ``quotes.verbatim.check_quote`` — it proves
    the quote *exists* verbatim in the source, never that it *supports* the
    claim it backs. That gap is closed downstream (AiCommon.md §3), never here.
    """

    quote: str
    source_ref: str
    quote_verified: bool


@dataclass(frozen=True, slots=True)
class Candidate:
    """A possible value backed by one piece of checked evidence — not a fact."""

    value: str
    evidence: EvidenceQuote
