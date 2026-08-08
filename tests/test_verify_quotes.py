"""Unit tests for the pure verification logic in quote_verify.verify_quotes.

The pinexplore-backed source lookup needs a sibling checkout and its caches,
so these tests cover the pure functions (normalize, check_quote, _quote_units,
and the ipdb_row_text / ipdb_notes_text renderers) — the part that decides what
counts as a source and whether a quote is verbatim in it — plus ``_Sources``
ref routing against a stubbed cache.
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


def test_ipdb_row_text_serializes_labeled_fields_in_page_order():
    from quote_verify.verify_quotes import ipdb_row_text

    text = ipdb_row_text(
        {
            "Title": "Fishing Tengu (&#12388;&#12426;&#22825;&#29399;)",
            "Players": 1,
            "AdditionalDetails": "IPD No. 3862 / June, 1974 / 1 Player",
            "Manufacturer": "Sankyo Precision Equipment Company, Ltd., of Tokyo, Japan",
            "Type": "Electro-mechanical (EM)",
            "Theme": "Sports - Fishing - Mythology",
            "NotableFeatures": "Red knob on the cabinet.",
            "Notes": "A tengu is a mythical creature.",
        }
    )
    assert text == (
        "Fishing Tengu (つり天狗)\n"
        "Players: 1\n"
        "IPD No. 3862 / June, 1974 / 1 Player\n"
        "Manufacturer: Sankyo Precision Equipment Company, Ltd., of Tokyo, Japan\n"
        "Type: Electro-mechanical (EM)\n"
        "Theme: Sports - Fishing - Mythology\n"
        "Notable Features: Red knob on the cabinet.\n"
        "Notes: A tengu is a mythical creature."
    )


def test_ipdb_row_text_skips_empty_fields():
    from quote_verify.verify_quotes import ipdb_row_text

    assert ipdb_row_text(
        {"Title": "Asteroid Killer", "Type": "Solid State Electronic (SS)"}
    ) == ("Asteroid Killer\nType: Solid State Electronic (SS)")


def test_ipdb_row_text_renders_hardware_and_credit_fields():
    # The IPDB page renders Model Number, MPU and the person-credit rows as
    # "Label: value" lines; the quotable slice must carry them so a credit
    # claim citing ipdb:NNNN can quote them ctrl-F honestly.
    from quote_verify.verify_quotes import ipdb_row_text

    text = ipdb_row_text(
        {
            "Title": "Houdini: Master of Mystery",
            "Manufacturer": "American Pinball, Incorporated",
            "Type": "Solid State Electronic (SS)",
            "Players": 4,
            "Theme": "Magic - Illusions",
            "ModelNumber": "GAM0001",
            "MPU": "Multimorphic P3-ROC",
            "DesignBy": "Joe Balcer",
            "ArtBy": "Jeff Busch, Matt Riesterer",
            "DotsAnimationBy": "Ish Raneses",
            "MechanicsBy": "Joe Balcer",
            "MusicBy": "Matt Kern",
            "SoundBy": "Matt Kern",
            "SoftwareBy": "Josh Kugler",
            "Notes": "MSRP when new: $6,995",
        }
    )
    assert text == (
        "Houdini: Master of Mystery\n"
        "Players: 4\n"
        "Manufacturer: American Pinball, Incorporated\n"
        "Type: Solid State Electronic (SS)\n"
        "MPU: Multimorphic P3-ROC\n"
        "Model Number: GAM0001\n"
        "Theme: Magic - Illusions\n"
        "Design by: Joe Balcer\n"
        "Art by: Jeff Busch, Matt Riesterer\n"
        "Dots/Animation by: Ish Raneses\n"
        "Mechanics by: Joe Balcer\n"
        "Music by: Matt Kern\n"
        "Sound by: Matt Kern\n"
        "Software by: Josh Kugler\n"
        "Notes: MSRP when new: $6,995"
    )


def test_ipdb_row_text_renders_toys_and_marketing_slogans():
    # Both are editor-authored prose the IPDB page prints as labeled rows, so a
    # `toys` claim citing ipdb:NNNN can quote the Toys line ctrl-F honestly.
    from quote_verify.verify_quotes import ipdb_row_text

    text = ipdb_row_text(
        {
            "Title": "The Addams Family",
            "Toys": "'Thing' hand - ball capture device.\r\n'Electric chair'",
            "MarketingSlogans": '"A pinball experience for the whole family!"',
        }
    )
    assert text == (
        "The Addams Family\n"
        "Toys: 'Thing' hand - ball capture device.\r\n'Electric chair'\n"
        'Marketing Slogans: "A pinball experience for the whole family!"'
    )


def test_ipdb_row_text_renders_ipdbs_own_sourcing_rows():
    # Source and Photos In are about IPDB's paperwork, not the machine — on the
    # page, so quotable; excluded from the AI slice by ipdb_notes_text.
    from quote_verify.verify_quotes import ipdb_row_text

    text = ipdb_row_text(
        {
            "Title": "Ballyhoo",
            "CommonAbbreviations": "TAF",
            "PhotosIn": "Pinball Memories, page 18",
            "Source": "Bally documentation",
        }
    )
    assert text == (
        "Ballyhoo\n"
        "Common Abbreviations: TAF\n"
        "Photos in: Pinball Memories, page 18\n"
        "Source: Bally documentation"
    )


def test_ipdb_row_text_omits_values_the_page_renders_differently():
    # A quote of "20270" would verify here and be un-findable on IPDB. The
    # page's own date and player rendering rides along in AdditionalDetails.
    from quote_verify.verify_quotes import ipdb_row_text

    text = ipdb_row_text(
        {
            "Title": "The Addams Family",
            "DateOfManufacture": "1992-03-01T00:00:00",
            "ProductionNumber": 20270,
            "AverageFunRating": 8.3,
            "AdditionalDetails": "IPD No. 20 / March, 1992 / 4 Players",
        }
    )
    assert text == ("The Addams Family\nIPD No. 20 / March, 1992 / 4 Players")


def test_ipdb_row_text_omits_blank_values_rather_than_a_bare_label():
    # Real rows carry blank prose, and a bare "Notes:" is text the page never
    # shows — a quote of the label alone would verify against nothing.
    from quote_verify.verify_quotes import ipdb_row_text

    assert ipdb_row_text(
        {
            "Title": "Ballyhoo",
            "Notes": "   ",
            "Toys": "",
            "NotableFeatures": "Two flippers.",
        }
    ) == ("Ballyhoo\nNotable Features: Two flippers.")


def test_ipdb_row_text_ignores_join_keys_and_array_columns():
    from quote_verify.verify_quotes import ipdb_row_text

    assert (
        ipdb_row_text(
            {
                "Title": "Ballyhoo",
                "IpdbId": 1,
                "ManufacturerId": 42,
                "ManufacturerShortName": "Bally",
                "TypeShortName": "EM",
                "ImageFiles": [{"Url": "x", "Name": "y"}],
            }
        )
        == "Ballyhoo"
    )


def test_ipdb_notes_text_is_free_text_prose_only():
    from quote_verify.verify_quotes import ipdb_notes_text

    # Structured fields are deterministic data resolved directly, never re-read
    # by a model; Source and Photos In are not about the machine at all.
    text = ipdb_notes_text(
        {
            "Title": "Fishing Tengu",
            "Manufacturer": "Sankyo",
            "Players": 1,
            "NotableFeatures": "Red knob on the cabinet.",
            "Toys": "Dancing tengu",
            "Notes": "A tengu is a mythical creature.",
            "MarketingSlogans": '"Reel in the fun!"',
            "Source": "flyer",
            "PhotosIn": "Pinball Memories, page 18",
            "CommonAbbreviations": "FT",
        }
    )
    assert text == (
        "Notable Features: Red knob on the cabinet.\n"
        "Toys: Dancing tengu\n"
        "Notes: A tengu is a mythical creature.\n"
        'Marketing Slogans: "Reel in the fun!"'
    )


def test_ipdb_notes_text_labels_match_ipdb_row_text_verbatim():
    # A model's quote is checked against the notes text at extraction and
    # against the row text at ship time, so a delimiter in one and not the
    # other is a quote that passes the first gate and fails the second.
    from quote_verify.verify_quotes import check_quote, ipdb_notes_text, ipdb_row_text

    row = {
        "Title": "The Addams Family",
        "Manufacturer": "Bally",
        "NotableFeatures": "Two-level playfield.",
        "Toys": "'Thing' hand - ball capture device.",
        "Notes": "The best-selling pinball machine of all time.",
        "MarketingSlogans": '"A pinball experience for the whole family!"',
    }
    for line in ipdb_notes_text(row).split("\n"):
        assert check_quote(line, ipdb_row_text(row)) is None


def test_ipdb_notes_text_empty_prose_is_empty_string():
    from quote_verify.verify_quotes import ipdb_notes_text

    assert ipdb_notes_text({"Title": "Ballyhoo", "Manufacturer": "Bally"}) == ""


class _FakeWebCache:
    """Stands in for pinexplore's web_cache module in text_for tests.

    ``pdf_urls`` marks which stubbed pages the cache holds as PDFs, mirroring
    the real row's ``content_type`` — the fact ``is_pdf`` reads.
    """

    def __init__(self, pages: dict[str, str], pdf_urls: set[str] | None = None) -> None:
        self.pages = pages
        self.pdf_urls = pdf_urls or set()
        self.requested: list[str] = []

    def get(self, url: str) -> dict[str, str] | None:
        self.requested.append(url)
        text = self.pages.get(url)
        if text is None:
            return None
        content_type = "application/pdf" if url in self.pdf_urls else "text/html"
        return {"text": text, "content_type": content_type}


def _sources_with(
    pages: dict[str, str], pdf_urls: set[str] | None = None
) -> tuple[_Sources, _FakeWebCache]:
    sources = object.__new__(_Sources)
    fake = _FakeWebCache(pages, pdf_urls)
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


def test_free_text_for_ipdb_returns_machine_prose_only():
    # The AI extractor's input adapter: an ipdb: ref resolves to the row's
    # machine prose alone.
    sources, _ = _sources_with({})
    sources._rows = {
        "5632": {
            "Title": "Dogs Race",
            "Manufacturer": "Chicago Coin",
            "Notes": "Converted from an earlier Gottlieb model.",
            "Source": "flyer",
        }
    }
    assert sources.free_text_for("ipdb:5632") == (
        "Notes: Converted from an earlier Gottlieb model."
    )


def test_free_text_for_web_ref_matches_text_for():
    # Web / opdb / youtube refs already resolve to unstructured readable text, so
    # the free-text adapter passes them straight through.
    sources, _ = _sources_with({"https://a.test/p": "readable page text"})
    assert sources.free_text_for("https://a.test/p") == "readable page text"


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


# ── is_pdf: the ungated document class ───────────────────────────────────────
# A PDF quote is not machine-checkable. Text extraction reads a sheet in
# reading order, so a table becomes a column of unattached cells, and words
# drawn as artwork never reach the text layer at all — a correct quote a
# session read off the rendered sheet routinely is not a substring of what
# was extracted. Measured on this corpus, an exact check against the OCR tier
# rejects a quarter of correct spans, so there is no threshold that makes the
# check honest. PDF quotes are therefore an author self-check, and the gate
# says so rather than failing them. The discriminator is a fact the CACHE owns
# about the document (its content_type), never anything recorded in a patch.


def test_cached_pdf_ref_is_pdf():
    sources, _ = _sources_with(
        {"https://a.test/manual.pdf": "flattened text"},
        pdf_urls={"https://a.test/manual.pdf"},
    )
    assert sources.is_pdf("https://a.test/manual.pdf") is True


def test_cached_html_ref_is_not_pdf():
    sources, _ = _sources_with({"https://a.test/p": "page text"})
    assert sources.is_pdf("https://a.test/p") is False


def test_uncached_ref_is_not_pdf():
    # An uncached document is a NO-SOURCE failure, not a skip: a session that
    # cannot produce the source cannot have read it. Never let a missing
    # document masquerade as an ungated one.
    sources, _ = _sources_with({})
    assert sources.is_pdf("https://a.test/missing.pdf") is False


def test_scheme_refs_are_not_pdf():
    # ipdb/opdb/youtube resolve to structured rows and transcripts, which stay
    # fully gated. Only an http(s) ref can name a PDF.
    sources, _ = _sources_with({"https://opdb.org/machines/2155": "Cactus Canyon"})
    assert sources.is_pdf("ipdb:5632") is False
    assert sources.is_pdf("opdb:2155") is False
    assert sources.is_pdf("youtube:O-2BXTXLXIY") is False


def test_pdf_extension_alone_does_not_skip_the_gate():
    # The URL's spelling is not the signal — an HTML page served at a .pdf
    # path stays gated. Only the cache's content_type exempts a document.
    sources, _ = _sources_with({"https://a.test/notreally.pdf": "html masquerading"})
    assert sources.is_pdf("https://a.test/notreally.pdf") is False
