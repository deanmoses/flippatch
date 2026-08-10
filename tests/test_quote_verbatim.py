"""Unit tests for the verbatim quote gate (quotes.verbatim).

Covers the pure functions — normalize, check_quote, and the ``_quote_units``
walk that finds every (ref, archive, quote) a patch entry carries — plus the
scoping of the run itself. Cite → source resolution is ``quotes.sources``' job
and is tested there.
"""

import textwrap

from quotes.sources import CiteSource, SourceStatus
from quotes.verbatim import _quote_units, check_quote, main, normalize

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


def test_a_quote_with_no_spans_fails():
    # Splitting on [...] leaves nothing to look for, so every span verifies
    # vacuously — a quote of ellipses alone would otherwise pass the gate while
    # resting on no source text at all.
    for empty in ("[...]", "   ", "[...] [...]"):
        problem = check_quote(empty, SOURCE)
        assert problem is not None, empty
        assert "no text to verify" in problem


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


# ── Scoping the run ──────────────────────────────────────────────────────────
# What a scope must never do is let a partial run read like a clean full pass.


def _patch_corpus(tmp_path, monkeypatch):
    """Two patches, each with one quote, behind a stubbed source lookup."""
    for number, quote in (("0222", "first quote"), ("0223", "second quote")):
        (tmp_path / f"{number}-patch.yaml").write_text(
            textwrap.dedent(f"""\
                claims:
                  - model.a-{number}:
                      cite: {{ref: "ipdb:1", quote: "{quote}"}}
                """)
        )

    class _FakeSources:
        def resolve_cite(self, ref, archive=None):
            return CiteSource(SourceStatus.RESOLVED, "first quote and second quote")

    monkeypatch.setattr("quotes.verbatim.PATCHES_DIR", tmp_path)
    monkeypatch.setattr("quotes.verbatim.require_pinexplore", lambda: None)
    monkeypatch.setattr("quotes.verbatim.Sources", _FakeSources)


def test_a_bare_run_covers_every_patch(tmp_path, monkeypatch, capsys):
    _patch_corpus(tmp_path, monkeypatch)
    assert main([]) == 0
    summary = capsys.readouterr().out.strip().splitlines()[-1]
    assert summary == "verify-quote-verbatim: 2 verified, 0 failed"


def test_a_scoped_run_checks_only_that_patch_and_says_so(tmp_path, monkeypatch, capsys):
    # Stamped into the summary, so a partial run cannot pass for the ship check.
    _patch_corpus(tmp_path, monkeypatch)
    assert main(["0223"]) == 0
    summary = capsys.readouterr().out.strip().splitlines()[-1]
    assert summary == "verify-quote-verbatim (scope: 0223): 1 verified, 0 failed"


def test_a_scope_matching_no_patch_is_refused(tmp_path, monkeypatch, capsys):
    # "0 verified, 0 failed", exit 0, from a typo is the one output never allowed.
    _patch_corpus(tmp_path, monkeypatch)
    assert main(["0999"]) == 2
    captured = capsys.readouterr()
    assert "verified" not in captured.out
    assert "no patch matches 0999" in captured.err


def test_one_bad_id_among_good_ones_is_refused(tmp_path, monkeypatch, capsys):
    # Refused whole, not narrowed: the summary prints the scope as given, so
    # verifying 0223 under "0223 0999" would claim a patch never opened.
    _patch_corpus(tmp_path, monkeypatch)
    assert main(["0223", "0999"]) == 2
    captured = capsys.readouterr()
    assert "verified" not in captured.out
    assert "no patch matches 0999" in captured.err
    assert "0223" not in captured.err  # names the typo, not the valid id
