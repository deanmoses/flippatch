"""Unit tests for the pure verification logic in quote_verify.verify_quotes.

The pinexplore-backed source lookup needs a sibling checkout and its caches,
so these tests cover the pure functions (normalize, check_quote,
_quote_units) — the part that decides whether a quote is verbatim and which
quotes get verified — plus ``_Sources`` ref routing against a stubbed cache.
"""

from quote_verify.verify_quotes import (
    _quote_units,
    _Sources,
    check_quote,
    normalize,
)

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


def test_ipdb_row_text_serializes_labeled_fields_then_prose():
    from quote_verify.verify_quotes import ipdb_row_text

    text = ipdb_row_text(
        title="Fishing Tengu (&#12388;&#12426;&#22825;&#29399;)",
        manufacturer="Sankyo Precision Equipment Company, Ltd., of Tokyo, Japan",
        type_="Electro-mechanical (EM)",
        players=1,
        theme="Sports - Fishing - Mythology",
        notable_features="Red knob on the cabinet.",
        notes="A tengu is a mythical creature.",
    )
    assert text == (
        "Fishing Tengu (つり天狗)\n"
        "Manufacturer: Sankyo Precision Equipment Company, Ltd., of Tokyo, Japan\n"
        "Type: Electro-mechanical (EM)\n"
        "Players: 1\n"
        "Theme: Sports - Fishing - Mythology\n"
        "Red knob on the cabinet.\n"
        "A tengu is a mythical creature."
    )


def test_ipdb_row_text_skips_empty_fields():
    from quote_verify.verify_quotes import ipdb_row_text

    assert ipdb_row_text(
        title="Asteroid Killer",
        manufacturer=None,
        type_="Solid State Electronic (SS)",
        players=None,
        theme=None,
        notable_features=None,
        notes=None,
    ) == ("Asteroid Killer\nType: Solid State Electronic (SS)")


class _FakeWebCache:
    """Stands in for pinexplore's web_cache module in text_for tests."""

    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.requested: list[str] = []

    def get(self, url: str) -> dict[str, str] | None:
        self.requested.append(url)
        text = self.pages.get(url)
        return {"text": text} if text is not None else None


def _sources_with(pages: dict[str, str]) -> tuple[_Sources, _FakeWebCache]:
    sources = object.__new__(_Sources)
    fake = _FakeWebCache(pages)
    sources._web_cache = fake
    return sources, fake


def test_opdb_ref_resolves_via_cached_machine_page():
    # opdb:<id> is the opdb.org URL id; its evidence text is the cached
    # https://opdb.org/machines/<id> page, like flipcommons' canonical URL.
    sources, fake = _sources_with(
        {"https://opdb.org/machines/2155": "Cactus Canyon Continued"}
    )
    assert sources.text_for("opdb:2155") == "Cactus Canyon Continued"
    assert fake.requested == ["https://opdb.org/machines/2155"]


def test_opdb_ref_missing_from_cache_is_none():
    sources, _ = _sources_with({})
    assert sources.text_for("opdb:9999") is None


def test_youtube_ref_resolves_via_cached_watch_page_transcript():
    # youtube:<id> maps to the canonical watch URL, whose cached text is the
    # caption-track transcript pinexplore's web_video transport stores.
    sources, fake = _sources_with(
        {"https://www.youtube.com/watch?v=O-2BXTXLXIY": "and the winner is Elf"}
    )
    assert sources.text_for("youtube:O-2BXTXLXIY") == "and the winner is Elf"
    assert fake.requested == ["https://www.youtube.com/watch?v=O-2BXTXLXIY"]


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
        ("ipdb:1", "entry quote"),
        ("https://a.test/p", "inline quote"),
        ("ipdb:3", "changeset quote"),
    ]
