"""Orchestrate the description rules over one description unit.

The reusable core: given a loaded description and the shared context, run the
enabled rules and collect findings. A rule that needs a data source absent at
runtime (the catalog index, the pinexplore corpus) is skipped with a note rather
than crashing; a model error on one rule is reported and the rest still run.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from common.ai.client import AiError

from ai_lint.description_check import rules
from ai_lint.report import (
    RULE_MISSING_WIKILINK,
    RULE_PLAGIARISM,
    RULE_SINGLE_SOURCE_SPINE,
    RULE_UNKNOWN_MODEL,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from common.ai.client import AiClient
    from common.catalog.entity_index import EntityIndex

    from ai_lint.corpus import Corpus
    from ai_lint.patch_load import DescriptionUnit
    from ai_lint.report import Finding

_NEEDS_INDEX = frozenset({RULE_UNKNOWN_MODEL, RULE_MISSING_WIKILINK})
_NEEDS_CORPUS = frozenset({RULE_PLAGIARISM, RULE_SINGLE_SOURCE_SPINE})


def vet_description(
    unit: DescriptionUnit,
    *,
    enabled: frozenset[str],
    ai: AiClient,
    index: EntityIndex | None,
    corpus: Corpus,
) -> list[Finding]:
    """Run the enabled rules on one description; return their findings."""
    findings: list[Finding] = []

    def run(rule: str, produce: Callable[[], list[Finding]]) -> None:
        try:
            findings.extend(produce())
        except AiError as exc:
            print(
                f"  ! {unit.entity_ref}: {rule} skipped — AI error: {exc}",
                file=sys.stderr,
            )

    if RULE_UNKNOWN_MODEL in enabled and index is not None:
        run(RULE_UNKNOWN_MODEL, lambda: rules.unknown_model(unit, index, ai))
    if RULE_MISSING_WIKILINK in enabled and index is not None:
        run(RULE_MISSING_WIKILINK, lambda: rules.missing_wikilink(unit, index, ai))
    if RULE_PLAGIARISM in enabled:
        run(RULE_PLAGIARISM, lambda: rules.plagiarism(unit, corpus, ai))
    if RULE_SINGLE_SOURCE_SPINE in enabled:
        run(
            RULE_SINGLE_SOURCE_SPINE,
            lambda: rules.single_source_spine(unit, corpus, ai),
        )
    return findings
