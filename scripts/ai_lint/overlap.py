"""Deterministic text-overlap prefilter for the plagiarism rule.

Cheap, pure-Python word-shingle Jaccard + longest common consecutive run between
a description sentence and its cited source text. It does **not** decide
plagiarism — it selects the suspicious ``(sentence, source)`` pairs worth an AI
paraphrase verdict, keeping model cost down. Mirrors the overlap-scoring shape of
Wikipedia's Earwig Copyvio Detector.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_WORD = re.compile(r"[a-z0-9]+")

# A pair is suspicious when shingles overlap heavily OR a long verbatim run
# survives. Tuned toward recall — the AI verdict is the precision gate.
JACCARD_THRESHOLD = 0.5
RUN_THRESHOLD = 8


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.casefold())


def _shingles(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def shingle_jaccard(a: str, b: str, n: int = 3) -> float:
    """Jaccard overlap of the two texts' word n-gram sets (0.0–1.0)."""
    sa, sb = _shingles(_tokens(a), n), _shingles(_tokens(b), n)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def longest_common_run(a: str, b: str) -> int:
    """Length (in words) of the longest verbatim consecutive token run shared."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0
    prev = [0] * (len(tb) + 1)
    best = 0
    for i in range(1, len(ta) + 1):
        curr = [0] * (len(tb) + 1)
        for j in range(1, len(tb) + 1):
            if ta[i - 1] == tb[j - 1]:
                curr[j] = prev[j - 1] + 1
                best = max(best, curr[j])
        prev = curr
    return best


@dataclass(frozen=True, slots=True)
class Overlap:
    """The overlap scores for one sentence/source pair and whether it's suspicious."""

    jaccard: float
    run: int

    @property
    def suspicious(self) -> bool:
        return self.jaccard >= JACCARD_THRESHOLD or self.run >= RUN_THRESHOLD


def score(sentence: str, source: str) -> Overlap:
    """Overlap of a sentence against a source excerpt."""
    return Overlap(
        jaccard=shingle_jaccard(sentence, source),
        run=longest_common_run(sentence, source),
    )
