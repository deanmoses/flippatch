"""Unit tests for the verbatim quote gate (quotes.verbatim).

Covers the pure functions — normalize, check_quote, and the ``_quote_units``
walk that finds every (ref, archive, quote) a patch entry carries. Cite → source
resolution is ``quotes.sources``' job and is tested there.
"""

from quotes.verbatim import _quote_units, check_quote, normalize

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


def test_quote_units_walks_entry_inline_and_changesets_quotes():
    body = {
        "cite": {"ref": "ipdb:1", "quote": "entry quote"},
        "description": "x[[cite:1]] y[[cite:2]]",
        "cites": {
            "1": {"ref": "https://a.test/p", "quote": "inline quote"},
            "2": "ipdb:2",  # bare ref, no quote — skipped
        },
        "changesets": [
            {"cite": {"ref": "ipdb:3", "quote": "changeset quote"}},
        ],
    }
    assert list(_quote_units(body)) == [
        ("ipdb:1", None, "entry quote"),
        ("https://a.test/p", None, "inline quote"),
        ("ipdb:3", None, "changeset quote"),
    ]


def test_quote_units_carries_the_archive_url():
    # A cite for a dead original names the Wayback snapshot in `archive:`; the
    # gate resolves the source text via ref first, then the archive. The unit
    # must surface the archive so the caller can fall back to it.
    body = {
        "cite": {
            "ref": "http://maker.test/flyer.pdf",
            "archive": "http://web.archive.org/web/20250325113004id_/http://maker.test/flyer.pdf",
            "quote": "transcribed span",
        },
    }
    assert list(_quote_units(body)) == [
        (
            "http://maker.test/flyer.pdf",
            "http://web.archive.org/web/20250325113004id_/http://maker.test/flyer.pdf",
            "transcribed span",
        ),
    ]


def test_quote_units_walks_cite_lists():
    # cite: takes a list of specs (multi-source evidence); every quote-bearing
    # element must be verified, wherever it sits in the list.
    body = {
        "cite": [
            "ipdb:1",  # bare ref, no quote — skipped
            {"ref": "https://a.test/p", "quote": "first source"},
            {"ref": "ipdb:2", "quote": "second source"},
        ],
        "changesets": [
            {"cite": [{"ref": "ipdb:3", "quote": "changeset list quote"}]},
        ],
    }
    assert list(_quote_units(body)) == [
        ("https://a.test/p", None, "first source"),
        ("ipdb:2", None, "second source"),
        ("ipdb:3", None, "changeset list quote"),
    ]
