"""Tests for the four description rules with an injected fake AI client.

The static prefilters (entity index, overlap, cite-root concentration) run for
real against temp fixtures; the model call is faked so we assert the rule wiring
— which candidates/pairs reach the AI, and how its verdicts become findings —
without any network.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from ai_lint.corpus import Corpus
from ai_lint.description_check import rules
from ai_lint.description_check.runner import vet_description
from ai_lint.patch_load import CiteRef, DescriptionUnit
from ai_lint.report import Severity
from common.ai.client import AiBudgetError
from common.catalog.entity_index import EntityIndex


class FakeAiClient:
    """Returns a canned structured dict and records the calls it received."""

    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def structured(self, *, system, user, schema, model, max_tokens=512):
        self.calls.append(
            {"system": system, "user": user, "schema": schema, "model": model}
        )
        return self.response


class FakeResolver:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    def text_for(self, ref: str) -> str | None:
        return self.mapping.get(ref)


@pytest.fixture
def index(tmp_path: Path) -> EntityIndex:
    db = tmp_path / "db.sqlite3"
    con = sqlite3.connect(db)
    con.executescript(
        "CREATE TABLE catalog_manufacturer (id INTEGER PRIMARY KEY, slug TEXT, name TEXT);"
        "CREATE TABLE catalog_machinemodel (id INTEGER PRIMARY KEY, slug TEXT, name TEXT);"
    )
    con.execute("INSERT INTO catalog_manufacturer VALUES (1, 'sunwise', 'Sun Wise')")
    con.commit()
    con.close()
    return EntityIndex.build(db, types=("manufacturer", "model"))


def _unit(text: str, cites: dict[str, CiteRef] | None = None) -> DescriptionUnit:
    return DescriptionUnit(
        patch="0059-x.yaml",
        entity_ref="model.american-battle-dome",
        entity_type="model",
        slug="american-battle-dome",
        text=text,
        cites=cites or {},
    )


def test_missing_wikilink_flags_confirmed_candidate(index: EntityIndex):
    unit = _unit("The machine was made by Sun Wise in 1995.")
    ai = FakeAiClient({"confirmations": [{"index": 0, "is_reference": True}]})
    findings = rules.missing_wikilink(unit, index, ai)
    assert len(findings) == 1
    assert findings[0].severity is Severity.WARNING
    assert findings[0].suggestion == "link as [[manufacturer:sunwise]]"


def test_missing_wikilink_already_linked_makes_no_call(index: EntityIndex):
    unit = _unit("The machine was made by [[manufacturer:sunwise]] in 1995.")
    ai = FakeAiClient({"confirmations": []})
    findings = rules.missing_wikilink(unit, index, ai)
    assert findings == []
    assert ai.calls == []  # nothing to confirm → no model call


def test_unknown_model_reports_discoveries(index: EntityIndex):
    unit = _unit("A rare machine called Joker Ball also existed.")
    ai = FakeAiClient({"mentions": [{"name": "Joker Ball", "kind": "machine"}]})
    findings = rules.unknown_model(unit, index, ai)
    assert len(findings) == 1
    assert findings[0].severity is Severity.INFO
    assert "Joker Ball" in findings[0].message


def test_plagiarism_prefilter_gates_the_call():
    quote = (
        "The balls are dropped at regular intervals by the mainspring, and the "
        "player with the lowest score wins."
    )
    # Near-verbatim sentence → prefilter suspicious → AI called → warning.
    unit = _unit(
        "The balls are dropped at regular intervals by the mainspring, and the "
        "player with the lowest score wins.[[cite:1]]",
        cites={"1": CiteRef("1", "https://x.example/a", quote)},
    )
    ai = FakeAiClient(
        {"verdicts": [{"index": 0, "plagiarized": True, "reason": "lifted"}]}
    )
    findings = rules.plagiarism(unit, Corpus(None), ai)
    assert len(findings) == 1
    assert findings[0].severity is Severity.WARNING
    assert len(ai.calls) == 1


def test_plagiarism_paraphrase_not_suspicious_skips_call():
    quote = "The balls are dropped at regular intervals by the mainspring."
    unit = _unit(
        "Every so often a wind-up spring flings the balls back into play.[[cite:1]]",
        cites={"1": CiteRef("1", "https://x.example/a", quote)},
    )
    ai = FakeAiClient({"verdicts": []})
    findings = rules.plagiarism(unit, Corpus(None), ai)
    assert findings == []
    assert ai.calls == []


def test_single_source_spine_flags_single_root_derivative():
    source = "A long article that tells the whole story of the machine in detail."
    unit = _unit(
        "The whole story of the machine, told in detail.[[cite:1]]",
        cites={
            "1": CiteRef("1", "https://en.wikipedia.org/wiki/Foo", "the whole story")
        },
    )
    corpus = Corpus(FakeResolver({"https://en.wikipedia.org/wiki/Foo": source}))
    ai = FakeAiClient({"derivative": True, "reason": "tracks the article's structure"})
    findings = rules.single_source_spine(unit, corpus, ai)
    assert len(findings) == 1
    assert findings[0].severity is Severity.WARNING


def test_single_source_spine_multi_root_skipped():
    unit = _unit(
        "Two independent sources.[[cite:1]][[cite:2]]",
        cites={
            "1": CiteRef("1", "https://a.example/x", "q1"),
            "2": CiteRef("2", "https://b.example/y", "q2"),
        },
    )
    corpus = Corpus(
        FakeResolver({"https://a.example/x": "s", "https://b.example/y": "s"})
    )
    ai = FakeAiClient({"derivative": True, "reason": "should not be asked"})
    assert rules.single_source_spine(unit, corpus, ai) == []


class _BudgetRaiser:
    """An AI client whose every call trips the runaway guard."""

    def structured(
        self, *, system, user, schema, model, max_tokens=512
    ) -> dict[str, object]:
        raise AiBudgetError("request-count cap reached")


def test_runner_does_not_swallow_budget_error(index: EntityIndex):
    # The per-rule `except AiError` must let a run-fatal AiBudgetError through,
    # or a runaway would be logged-and-continued on every remaining unit.
    unit = _unit("Made by Sun Wise.")
    with pytest.raises(AiBudgetError):
        vet_description(
            unit,
            enabled=frozenset({"unknown-model"}),
            ai=_BudgetRaiser(),
            index=index,
            corpus=Corpus(None),
        )
