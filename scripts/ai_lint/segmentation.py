"""Split a description into sentences and attach the cites that punctuate each.

Two shared primitives:

- :func:`blank_markers` replaces every ``[[…]]`` marker with equal-length spaces,
  so already-linked entities disappear from the missing-wikilink scan while every
  surviving character keeps its original offset.
- :func:`segment` splits into sentences and associates each ``[[cite:handle]]``
  marker with the sentence it *follows* (a trailing footnote punctuates the
  sentence before it), so the plagiarism and support rules can pair a sentence
  with its evidence.

Pure string I/O — no DB, no network — so it unit-tests directly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Any wikilink or cite marker: [[manufacturer:sunwise]], [[cite:1]], [[cite:abcd]].
_MARKER = re.compile(r"\[\[[^\]]*\]\]")
_CITE = re.compile(r"\[\[cite:([^\]]+)\]\]")
# Sentence-ending punctuation. Slugs are [a-z0-9-] and cites are digits/letters,
# so a '.'/'!'/'?' never occurs inside a marker — safe to scan on blanked text.
_SENTENCE_END = re.compile(r"[.!?]+")


@dataclass(frozen=True, slots=True)
class Sentence:
    """One sentence of a description, cleaned of markers, plus its cite handles.

    ``start``/``end`` are offsets into the original text (the sentence proper,
    excluding any trailing footnote); ``cite_handles`` are the ``[[cite:handle]]``
    handles that punctuate it.
    """

    text: str
    start: int
    end: int
    cite_handles: tuple[str, ...]


def blank_markers(text: str) -> str:
    """Replace every ``[[…]]`` marker with equal-length spaces (offsets preserved)."""
    return _MARKER.sub(lambda m: " " * (m.end() - m.start()), text)


def _clean(raw: str) -> str:
    """A readable sentence: wikilinks become their humanized slug, cites drop out."""

    def repl(match: re.Match[str]) -> str:
        inner = match.group(0)[2:-2]
        kind, _, rest = inner.partition(":")
        if kind == "cite":
            return ""
        return rest.replace("-", " ")

    return " ".join(_MARKER.sub(repl, raw).split())


def segment(text: str) -> list[Sentence]:
    """Split ``text`` into sentences with their punctuating cite handles."""
    blanked = blank_markers(text)
    cites = [(m.start(), m.group(1)) for m in _CITE.finditer(text)]
    length = len(blanked)
    sentences: list[Sentence] = []
    start = 0
    for match in _SENTENCE_END.finditer(blanked):
        text_end = match.end()
        # Trailing whitespace + blanked markers belong to the sentence just
        # ended, so a footnote after the period associates with it.
        nxt = text_end
        while nxt < length and blanked[nxt].isspace():
            nxt += 1
        clean = _clean(text[start:text_end])
        if clean:
            handles = tuple(h for pos, h in cites if start <= pos < nxt)
            sentences.append(Sentence(clean, start, text_end, handles))
        start = nxt
    if start < length:
        tail = _clean(text[start:])
        if tail:
            handles = tuple(h for pos, h in cites if pos >= start)
            sentences.append(Sentence(tail, start, len(text), handles))
    return sentences
