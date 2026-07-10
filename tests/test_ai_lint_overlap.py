"""Tests for ai_lint.overlap — the deterministic plagiarism prefilter."""

from __future__ import annotations

from ai_lint.overlap import longest_common_run, score, shingle_jaccard

_SOURCE = (
    "The game consists of a pinball game from two to four players. The balls "
    "are dropped at regular intervals by the mainspring, and the player with "
    "the lowest score wins the round."
)


def test_near_verbatim_sentence_is_suspicious():
    sentence = (
        "The balls are dropped at regular intervals by the mainspring, and the "
        "player with the lowest score wins."
    )
    result = score(sentence, _SOURCE)
    assert result.suspicious
    assert longest_common_run(sentence, _SOURCE) >= 8


def test_independent_paraphrase_is_not_suspicious():
    sentence = (
        "Up to four people take turns firing spring-loaded shots, and whoever "
        "keeps the fewest balls in their own net takes the game."
    )
    assert not score(sentence, _SOURCE).suspicious


def test_jaccard_bounds():
    assert shingle_jaccard("", "anything") == 0.0
    assert shingle_jaccard("same words here now", "same words here now") == 1.0
