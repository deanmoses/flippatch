"""The four AI description rules.

Each rule takes the shared context (the loaded :class:`DescriptionUnit`, the
catalog :class:`EntityIndex`, the pinexplore :class:`Corpus`, and an
:class:`AiClient`) and returns ``Finding``\\ s. The static passes here
(entity-index matching, overlap prefilter, cite-root concentration) exist only to
feed or gate the model call — the finding is the AI verdict.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from common.ai.client import CHEAP_MODEL
from patch_validation.lint_patches import _cite_root

from ai_lint import parsing, prompts
from ai_lint.overlap import score
from ai_lint.report import (
    RULE_MISSING_WIKILINK,
    RULE_PLAGIARISM,
    RULE_SINGLE_SOURCE_SPINE,
    RULE_UNKNOWN_MODEL,
    Finding,
    Severity,
)
from ai_lint.segmentation import blank_markers, segment

if TYPE_CHECKING:
    from common.ai.client import AiClient
    from common.catalog.entity_index import EntityIndex, Mention

    from ai_lint.corpus import Corpus
    from ai_lint.patch_load import DescriptionUnit

_WIKILINK = re.compile(r"\[\[([a-z-]+):([^\]:]+)\]\]")


def _existing_link_labels(text: str) -> list[str]:
    """Humanized slugs of entities already wikilinked (so we don't re-flag them)."""
    return [
        slug.replace("-", " ")
        for kind, slug in _WIKILINK.findall(text)
        if kind != "cite"
    ]


def _source_for(unit: DescriptionUnit, handle: str, corpus: Corpus) -> str:
    """The comparable source text for a cite handle: cached page, else the quote."""
    cite = unit.cites.get(handle)
    if cite is None:
        return ""
    return corpus.text_for(cite.ref) or cite.quote


# --------------------------------------------------------------------------- #
# unknown-model
# --------------------------------------------------------------------------- #
def unknown_model(
    unit: DescriptionUnit, index: EntityIndex, ai: AiClient
) -> list[Finding]:
    """Real machines/manufacturers named in prose that aren't in the catalog."""
    scan = blank_markers(unit.text)
    known = {m.surface for m in index.find_mentions(scan)}
    known.update(_existing_link_labels(unit.text))
    prose = " ".join(blank_markers(unit.text).split())
    user = (
        f"Description:\n{prose}\n\n"
        f"Known catalog entities (do not report these): "
        f"{sorted(known) or '(none)'}"
    )
    result = ai.structured(
        system=prompts.SYSTEM_UNKNOWN_MODEL,
        user=user,
        schema=prompts.UNKNOWN_MODEL_SCHEMA,
        model=CHEAP_MODEL,
    )
    findings: list[Finding] = []
    for row in parsing.rows(result, "mentions"):
        name = parsing.as_str(row, "name")
        kind = parsing.as_str(row, "kind")
        if name:
            findings.append(
                Finding(
                    rule=RULE_UNKNOWN_MODEL,
                    severity=Severity.INFO,
                    patch=unit.patch,
                    entity_ref=unit.entity_ref,
                    message=f"names {kind or 'entity'} not in catalog: {name!r}",
                    suggestion=f"consider acquiring/creating this {kind or 'entity'}",
                )
            )
    return findings


# --------------------------------------------------------------------------- #
# missing-wikilink
# --------------------------------------------------------------------------- #
def missing_wikilink(
    unit: DescriptionUnit, index: EntityIndex, ai: AiClient
) -> list[Finding]:
    """Catalog entities named in prose but not wikilinked (AI-confirmed)."""
    scan = blank_markers(unit.text)
    mentions = index.find_mentions(
        scan, exclude_type=unit.entity_type, exclude_slug=unit.slug
    )
    if not mentions:
        return []
    lines = []
    for i, mention in enumerate(mentions):
        ref = mention.refs[0]
        context = _context(unit.text, mention)
        lines.append(
            f"[{i}] phrase {mention.surface!r} → {ref.entity_type} {ref.slug!r} "
            f"(context: …{context}…)"
        )
    user = "Candidates:\n" + "\n".join(lines)
    result = ai.structured(
        system=prompts.SYSTEM_MISSING_LINK,
        user=user,
        schema=prompts.MISSING_LINK_SCHEMA,
        model=CHEAP_MODEL,
    )
    confirmed = {
        idx
        for row in parsing.rows(result, "confirmations")
        if (idx := parsing.as_int(row, "index")) is not None
        and parsing.as_bool(row, "is_reference")
    }
    findings: list[Finding] = []
    for i, mention in enumerate(mentions):
        if i in confirmed:
            ref = mention.refs[0]
            findings.append(
                Finding(
                    rule=RULE_MISSING_WIKILINK,
                    severity=Severity.WARNING,
                    patch=unit.patch,
                    entity_ref=unit.entity_ref,
                    message=f"{mention.surface!r} is the catalog {ref.entity_type} "
                    f"{ref.slug!r} but isn't wikilinked",
                    suggestion=f"link as {ref.wikilink}",
                )
            )
    return findings


def _context(text: str, mention: Mention, width: int = 40) -> str:
    start = max(0, mention.start - width)
    end = min(len(text), mention.end + width)
    return " ".join(text[start:end].split())


# --------------------------------------------------------------------------- #
# plagiarism
# --------------------------------------------------------------------------- #
def plagiarism(unit: DescriptionUnit, corpus: Corpus, ai: AiClient) -> list[Finding]:
    """Description sentences that copy their cited source's phrasing too closely."""
    suspects: list[tuple[str, str]] = []  # (sentence, source)
    for sentence in segment(unit.text):
        for handle in sentence.cite_handles:
            source = _source_for(unit, handle, corpus)
            if source and score(sentence.text, source).suspicious:
                suspects.append((sentence.text, source))
                break  # one flag per sentence is enough
    if not suspects:
        return []
    lines = [
        f"[{i}] SENTENCE: {sentence}\n    SOURCE: {source[:1200]}"
        for i, (sentence, source) in enumerate(suspects)
    ]
    result = ai.structured(
        system=prompts.SYSTEM_PLAGIARISM,
        user="\n\n".join(lines),
        schema=prompts.PLAGIARISM_SCHEMA,
        model=CHEAP_MODEL,
        max_tokens=1024,
    )
    findings: list[Finding] = []
    for row in parsing.rows(result, "verdicts"):
        idx = parsing.as_int(row, "index")
        in_range = idx is not None and 0 <= idx < len(suspects)
        if not in_range or not parsing.as_bool(row, "plagiarized"):
            continue
        assert idx is not None
        sentence_text, _source = suspects[idx]
        findings.append(
            Finding(
                rule=RULE_PLAGIARISM,
                severity=Severity.WARNING,
                patch=unit.patch,
                entity_ref=unit.entity_ref,
                message=f"sentence copies its source too closely: {sentence_text[:100]!r}",
                reason=parsing.as_str(row, "reason"),
            )
        )
    return findings


# --------------------------------------------------------------------------- #
# single-source-spine
# --------------------------------------------------------------------------- #
def single_source_spine(
    unit: DescriptionUnit, corpus: Corpus, ai: AiClient
) -> list[Finding]:
    """Whole-description structural derivation from one dominant source."""
    roots = {
        root
        for cite in unit.cites.values()
        if (root := _cite_root(cite.ref)) is not None
    }
    if len(roots) != 1:
        return []  # multi-source (or unresolvable) — not the single-source case
    # Concatenate this one root's cached source text; without it we can't judge
    # structure (a short quote isn't enough), so skip.
    sources = [
        text for cite in unit.cites.values() if (text := corpus.text_for(cite.ref))
    ]
    if not sources:
        return []
    prose = " ".join(blank_markers(unit.text).split())
    user = (
        f"Description:\n{prose}\n\n"
        f"The single dominant source:\n{' '.join(sources)[:6000]}"
    )
    result = ai.structured(
        system=prompts.SYSTEM_SINGLE_SOURCE_SPINE,
        user=user,
        schema=prompts.SINGLE_SOURCE_SPINE_SCHEMA,
        model=CHEAP_MODEL,
    )
    if not parsing.as_bool(result, "derivative"):
        return []
    return [
        Finding(
            rule=RULE_SINGLE_SOURCE_SPINE,
            severity=Severity.WARNING,
            patch=unit.patch,
            entity_ref=unit.entity_ref,
            message="narrative spine appears lifted from a single source "
            f"({next(iter(roots))})",
            reason=parsing.as_str(result, "reason"),
        )
    ]
