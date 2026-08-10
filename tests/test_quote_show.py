"""Unit tests for the cite source preview (quotes.show).

Resolution itself is ``quotes.sources``' job and is tested there; these pin the
CLI contract — which stream carries the text, what each exit code means, and
that ``--check`` gives the gate's own verdict.
"""

from typing import ClassVar

import pytest
from quotes.show import main
from quotes.sources import CiteSource, SourceStatus

IPDB_ROW = "Cirqus Voltaire\nPlayers: 4\nNotable Features: Ringmaster head."


class _FakeSources:
    """Stands in for Sources: one canned resolution, and the call it saw."""

    resolved: ClassVar[CiteSource]
    calls: ClassVar[list[tuple[str, str | None]]] = []

    def resolve_cite(self, ref: str, archive: str | None = None) -> CiteSource:
        type(self).calls.append((ref, archive))
        return self.resolved


@pytest.fixture
def fake_sources(monkeypatch):
    def install(resolved: CiteSource) -> type[_FakeSources]:
        _FakeSources.resolved = resolved
        _FakeSources.calls = []
        monkeypatch.setattr("quotes.show.require_pinexplore", lambda: None)
        monkeypatch.setattr("quotes.show.Sources", _FakeSources)
        return _FakeSources

    return install


def test_resolved_text_goes_to_stdout_and_the_header_to_stderr(fake_sources, capsys):
    # stdout is the source text alone, so a preview pipes into grep or a file.
    fake_sources(CiteSource(SourceStatus.RESOLVED, IPDB_ROW))
    assert main(["ipdb:4059"]) == 0
    captured = capsys.readouterr()
    assert captured.out == IPDB_ROW + "\n"
    assert "resolved" in captured.err
    assert "ipdb:4059" in captured.err


def test_the_archive_flag_reaches_the_resolver(fake_sources):
    # Else the preview shows a document the gate would not match against.
    fake = fake_sources(CiteSource(SourceStatus.RESOLVED, "archived page text"))
    argv = ["http://maker.test/le.aspx", "--archive", "http://web.archive.org/x"]
    assert main(argv) == 0
    assert fake.calls == [("http://maker.test/le.aspx", "http://web.archive.org/x")]


def test_check_verifies_a_draft_quote_without_printing_the_text(fake_sources, capsys):
    fake_sources(CiteSource(SourceStatus.RESOLVED, IPDB_ROW))
    assert main(["ipdb:4059", "--check", "Notable Features: Ringmaster head."]) == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("OK")
    assert IPDB_ROW not in captured.out


def test_check_reports_the_gates_own_failure_wording(fake_sources, capsys):
    # Same predicate as the gate, so an author learns one set of failure modes.
    fake_sources(CiteSource(SourceStatus.RESOLVED, IPDB_ROW))
    assert main(["ipdb:4059", "--check", "Ringmaster hat"]) == 1
    assert "not verbatim in source" in capsys.readouterr().out


def test_check_spans_out_of_order_fail_like_the_gate(fake_sources, capsys):
    fake_sources(CiteSource(SourceStatus.RESOLVED, IPDB_ROW))
    assert main(["ipdb:4059", "--check", "Ringmaster head. [...] Players: 4"]) == 1
    assert "out of source order" in capsys.readouterr().out


def test_a_pdf_cite_reports_skip_pdf_and_shows_nothing(fake_sources, capsys):
    # Printing the mangled extraction would invite quoting from it.
    fake_sources(CiteSource(SourceStatus.PDF))
    assert main(["http://maker.test/flyer.pdf"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "SKIP-PDF" in captured.err


def test_an_uncached_cite_reports_no_source_with_the_fix(fake_sources, capsys):
    fake_sources(CiteSource(SourceStatus.MISSING))
    assert main(["https://a.test/p"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "NO-SOURCE" in captured.err
    assert "pinexplore" in captured.err


def test_an_empty_check_quote_fails_rather_than_reporting_ok(fake_sources, capsys):
    # `--check "$UNSET"` must not read as a verdict; check_quote owns the rule,
    # so the preview reports it the same way the gate would.
    fake_sources(CiteSource(SourceStatus.RESOLVED, IPDB_ROW))
    assert main(["ipdb:4059", "--check", "[...]"]) == 1
    assert "no text to verify" in capsys.readouterr().out


def test_a_failed_check_and_an_unresolvable_cite_differ_in_exit_code(fake_sources):
    # 1 is "does not verify"; 2 is "nothing to check it against".
    fake_sources(CiteSource(SourceStatus.RESOLVED, IPDB_ROW))
    assert main(["ipdb:4059", "--check", "nope"]) == 1
    fake_sources(CiteSource(SourceStatus.MISSING))
    assert main(["ipdb:4059", "--check", "nope"]) == 2
