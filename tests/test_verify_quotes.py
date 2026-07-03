"""Unit tests for the pure verification logic in quote_verify.verify_quotes.

The pinexplore-backed source lookup needs a sibling checkout and its caches,
so these tests cover only the pure functions (normalize, check_quote) — the
part that decides whether a quote is verbatim.
"""

from quote_verify.verify_quotes import check_quote, normalize

SOURCE = (
    "The new company, which debuted at this year’s Pinball Expo in Chicago,\n"
    "says it’s on a mission “to bring the joy of real mechanical pinball\n"
    "machines to home arcades.”\n"
    "Company:\n"
    "1969 Socker Ace - サッカーエース (Soccer Ace) by 日本展望娯楽社\n"
)


def test_normalize_straightens_smart_quotes_and_collapses_whitespace():
    assert normalize("a “b”\n  c’s") == 'a "b" c\'s'


def test_verbatim_span_verifies():
    assert check_quote("debuted at this year's Pinball Expo", SOURCE) is None


def test_span_across_extraction_linebreak_verifies():
    # Hard-wrapped prose renders as spaces; whitespace-collapse bridges it.
    assert check_quote('on a mission "to bring the joy', SOURCE) is None


def test_multi_span_in_source_order_verifies():
    assert check_quote("The new company [...] Socker Ace", SOURCE) is None


def test_paraphrase_fails():
    problem = check_quote("1969 Socker Ace by Nihon Tenbo", SOURCE)
    assert problem is not None
    assert "not verbatim" in problem


def test_spans_out_of_source_order_fail():
    problem = check_quote("Socker Ace [...] The new company", SOURCE)
    assert problem is not None
    assert "out of source order" in problem


def test_non_ascii_verbatim_verifies():
    assert check_quote("サッカーエース (Soccer Ace) by 日本展望娯楽社", SOURCE) is None
