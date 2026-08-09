"""Unit tests for cite → source-text resolution (quotes.sources).

The pinexplore-backed lookup needs a sibling checkout and its caches, so these
cover the pure renderers (ipdb_row_text / ipdb_notes_text) and ``Sources`` ref
routing against a stubbed cache.
"""

from quotes.sources import Sources, SourceStatus, ipdb_notes_text, ipdb_row_text
from quotes.verbatim import check_quote


def test_ipdb_row_text_serializes_labeled_fields_in_page_order():
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
    assert ipdb_row_text(
        {"Title": "Asteroid Killer", "Type": "Solid State Electronic (SS)"}
    ) == ("Asteroid Killer\nType: Solid State Electronic (SS)")


def test_ipdb_row_text_renders_hardware_and_credit_fields():
    # The IPDB page renders Model Number, MPU and the person-credit rows as
    # "Label: value" lines; the quotable slice must carry them so a credit
    # claim citing ipdb:NNNN can quote them ctrl-F honestly.
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
    assert ipdb_row_text(
        {
            "Title": "Ballyhoo",
            "Notes": "   ",
            "Toys": "",
            "NotableFeatures": "Two flippers.",
        }
    ) == ("Ballyhoo\nNotable Features: Two flippers.")


def test_ipdb_row_text_ignores_join_keys_and_array_columns():
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
) -> tuple[Sources, _FakeWebCache]:
    sources = object.__new__(Sources)
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


# ── resolve_cite: the whole cite, not one address ────────────────────────────
# Every quote checker resolves through here, so the ref → archive fallback and
# the PDF outcome are decided once and cannot drift between them.

_DEAD = "http://maker.test/games/le.aspx"
_SNAPSHOT = (
    "http://web.archive.org/web/20111203043615id_/http://maker.test/games/le.aspx"
)


def test_resolve_cite_prefers_the_publishers_ref():
    sources, _ = _sources_with({_DEAD: "live page", _SNAPSHOT: "stale snapshot"})
    resolved = sources.resolve_cite(_DEAD, _SNAPSHOT)
    assert resolved.status is SourceStatus.RESOLVED
    assert resolved.text == "live page"


def test_resolve_cite_falls_back_to_the_archive_snapshot():
    # The original is dead, so the document is cached under the snapshot URL
    # while the cite's ref stays the publisher's.
    sources, _ = _sources_with({_SNAPSHOT: "archived page text"})
    resolved = sources.resolve_cite(_DEAD, _SNAPSHOT)
    assert resolved.status is SourceStatus.RESOLVED
    assert resolved.text == "archived page text"


def test_resolve_cite_without_an_archive_is_missing():
    sources, _ = _sources_with({})
    assert sources.resolve_cite(_DEAD).status is SourceStatus.MISSING


def test_resolve_cite_treats_an_empty_archive_as_none():
    # A cite with no `archive:` reaches here as "" (the patch carriers hold str,
    # not str | None), which must mean "no snapshot", not "look up the empty URL".
    sources, _ = _sources_with({_DEAD: "live page"})
    resolved = sources.resolve_cite(_DEAD, "")
    assert resolved.status is SourceStatus.RESOLVED
    assert resolved.text == "live page"


def test_resolve_cite_with_neither_address_cached_is_missing():
    sources, _ = _sources_with({})
    assert sources.resolve_cite(_DEAD, _SNAPSHOT).status is SourceStatus.MISSING


def test_resolve_cite_of_a_pdf_is_its_own_outcome():
    sources, _ = _sources_with(
        {"https://a.test/manual.pdf": "flattened text"},
        pdf_urls={"https://a.test/manual.pdf"},
    )
    resolved = sources.resolve_cite("https://a.test/manual.pdf")
    assert resolved.status is SourceStatus.PDF
    assert resolved.text is None


def test_a_readable_ref_wins_over_a_pdf_archive():
    # The addresses are ranked, not pooled: the publisher's page is the document
    # a reader follows, so a snapshot that went to PDF must not cost the gate a
    # source it can actually check.
    sources, _ = _sources_with(
        {_DEAD: "live page text", _SNAPSHOT: ""}, pdf_urls={_SNAPSHOT}
    )
    resolved = sources.resolve_cite(_DEAD, _SNAPSHOT)
    assert resolved.status is SourceStatus.RESOLVED
    assert resolved.text == "live page text"


def test_resolve_cite_of_a_pdf_reached_through_its_archive_is_still_a_pdf():
    # A dead PDF is cached under the snapshot URL; the document class is the
    # same whichever address reaches it.
    archived = (
        "http://web.archive.org/web/20250325113004id_/http://maker.test/flyer.pdf"
    )
    sources, _ = _sources_with({archived: ""}, pdf_urls={archived})
    resolved = sources.resolve_cite("http://maker.test/flyer.pdf", archived)
    assert resolved.status is SourceStatus.PDF


# ── is_pdf: the unjudgeable document class (why: SourceStatus.PDF) ───────────
# The discriminator is a fact the CACHE owns about the document (its
# content_type), never anything recorded in a patch.


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
