"""Tests for ai_lint.segmentation — sentence split + cite association."""

from __future__ import annotations

from ai_lint.segmentation import Sentence, blank_markers, segment


def test_blank_markers_preserves_length_and_removes_markers():
    text = "A [[model:bar-baz]] and [[cite:1]] end."
    blanked = blank_markers(text)
    assert len(blanked) == len(text)
    assert "[[" not in blanked
    # Non-marker characters keep their exact offset.
    assert blanked.index("end.") == text.index("end.")


def test_segment_associates_trailing_footnote_with_its_sentence():
    text = (
        "Foo built [[model:bar-baz]] in 1994.[[cite:1]] "
        "Then [[manufacturer:qux]] rethemed it.[[cite:2]]"
    )
    sentences = segment(text)
    assert len(sentences) == 2
    first, second = sentences
    assert first.cite_handles == ("1",)
    assert second.cite_handles == ("2",)
    # Wikilinks render as their humanized slug; cite markers drop out.
    assert "bar baz" in first.text
    assert "[[" not in first.text
    assert "qux" in second.text


def test_segment_multiple_cites_in_one_sentence():
    text = "It shipped in 1994 per two sources.[[cite:1]][[cite:2]]"
    (sentence,) = segment(text)
    assert isinstance(sentence, Sentence)
    assert sentence.cite_handles == ("1", "2")


def test_segment_uncited_sentence_has_no_handles():
    text = "This sentence has no footnote at all."
    (sentence,) = segment(text)
    assert sentence.cite_handles == ()
