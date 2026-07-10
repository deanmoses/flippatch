"""Finding / Report data carriers shared by both entrypoints.

A ``Finding`` is one issue an AI rule raised against one patch entry. Rules are
identified by the hyphenated ids below (toggled with ``--rules`` / ``--disable``
on the CLIs). A ``WARNING`` fails the run (non-zero exit); an ``INFO`` is a
discovery or weak signal that reports but does not fail.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    """How much a finding matters. ``WARNING`` fails the run; ``INFO`` does not."""

    INFO = "info"
    WARNING = "warning"


# Rule ids — the ``--rules`` / ``--disable`` selectors and the tag printed on
# each finding. Kept as plain constants (not an enum) so a rule id is just a
# string wherever it travels — through the AI schemas, the CLI flags, and JSON.
RULE_MISSING_WIKILINK = "missing-wikilink"
RULE_UNKNOWN_MODEL = "unknown-model"
RULE_PLAGIARISM = "plagiarism"
RULE_SINGLE_SOURCE_SPINE = "single-source-spine"
RULE_QUOTE_SUPPORTS_CLAIM = "quote-supports-claim"

DESCRIPTION_RULES: tuple[str, ...] = (
    RULE_MISSING_WIKILINK,
    RULE_UNKNOWN_MODEL,
    RULE_PLAGIARISM,
    RULE_SINGLE_SOURCE_SPINE,
)


@dataclass(frozen=True, slots=True)
class Finding:
    """One issue raised by one rule against one patch entry.

    ``suggestion`` carries a rule-specific actionable hint (the ``[[type:slug]]``
    to insert, the unknown name to acquire, the offending quote handle); ``reason``
    carries the model's short justification. Both optional so one flat type serves
    every rule.
    """

    rule: str
    severity: Severity
    patch: str  # patch filename, e.g. "0059-franchise-descriptions.yaml"
    entity_ref: str  # e.g. "franchise.battle-dome"
    message: str
    suggestion: str = ""
    reason: str = ""

    def as_dict(self) -> dict[str, str]:
        """A JSON-serializable view (``--json`` output)."""
        return {k: str(v) for k, v in dataclasses.asdict(self).items()}


@dataclass(frozen=True, slots=True)
class Report:
    """All findings for one description or one citation-verify run over a patch set."""

    findings: tuple[Finding, ...] = ()

    @property
    def warnings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity is Severity.WARNING)

    @property
    def failed(self) -> bool:
        """Whether the run should exit non-zero (any WARNING present)."""
        return bool(self.warnings)
