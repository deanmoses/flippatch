"""Offline tests for the corpus sweep — fixture SQLite, fake AI, no siblings.

The fixture catalog stages the campaign's real failure shapes: a mis-seeded
``converted_from`` (the conflict bucket), an EM/SS same-name pair only a stated
year can disambiguate, and a same-name bootleg whose target resolution must
exclude the judged model itself.
"""

from __future__ import annotations

import json
import sqlite3

import pytest
from ai_corpus_sweep import gate
from ai_corpus_sweep.candidates import CandidateError, CandidateRow, load_candidates
from ai_corpus_sweep.catalog import SweepCatalog
from ai_corpus_sweep.fields import RELATIONAL_FIELDS
from ai_corpus_sweep.judge import JudgeAnswer, build_user_prompt, parse_answer
from ai_corpus_sweep.render import progress_line, render_reconcile, render_review
from ai_corpus_sweep.sweep import row_from_json, sweep_candidates
from common.catalog.entity_index import EntityIndex

# ── Fixture catalog ──────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE catalog_manufacturer (id INTEGER PRIMARY KEY, slug TEXT, name TEXT);
CREATE TABLE catalog_corporateentity (
    id INTEGER PRIMARY KEY, slug TEXT, name TEXT, manufacturer_id INTEGER);
CREATE TABLE catalog_technologygeneration (
    id INTEGER PRIMARY KEY, slug TEXT, name TEXT);
CREATE TABLE catalog_title (id INTEGER PRIMARY KEY, slug TEXT, name TEXT);
CREATE TABLE catalog_machinemodel (
    id INTEGER PRIMARY KEY, slug TEXT, name TEXT, year INTEGER, ipdb_id INTEGER,
    title_id INTEGER, corporate_entity_id INTEGER, technology_generation_id INTEGER,
    converted_from_id INTEGER, bootleg_of_id INTEGER, licensed_build_of_id INTEGER);
CREATE TABLE catalog_tag (id INTEGER PRIMARY KEY, slug TEXT, name TEXT);
CREATE TABLE catalog_machinemodel_tags (machinemodel_id INTEGER, tag_id INTEGER);
"""

# (id, slug, name, year, ipdb, title, corp, tech, conv_from, bootleg_of)
_MODELS = [
    (1, "hurdy-gurdy", "Hurdy Gurdy", 1966, 1291, 1, 1, 1, None, None),
    (2, "central-park", "Central Park", 1966, 483, 2, 1, 1, None, None),
    # The mis-seeded conversion: note says Hurdy Gurdy, catalog says Central Park.
    (3, "spider", "Spider", 1968, 5555, 3, 3, 1, 2, None),
    (4, "mata-hari", "Mata Hari", 1977, 9001, 4, 2, 1, None, None),
    (5, "mata-hari-ss", "Mata Hari", 1978, 9002, 4, 2, 2, None, None),
    (6, "nero", "Nero", 1982, 7777, 5, 3, None, None, None),
    (7, "aquarius", "Aquarius", 1970, 300, 6, 1, 1, None, None),
    # Same-name bootleg of 7 — target resolution must not pick itself.
    (8, "aquarius-dama", "Aquarius", 1971, 6015, 6, 3, 1, None, None),
    # The (Maker)-suffix blind spot (DEFECT 1): the true target's name AND title
    # carry a campaign "(Bally)" suffix; a different maker's same-named game is
    # the only bare "Supersonic" the name index can reach.
    (9, "supersonic", "Supersonic (Bally)", 1979, 100, 7, 2, 2, None, None),
    (10, "supersonic-z", "Supersonic", 1980, 101, 8, 4, 2, None, None),
    # The false-green shape (DEFECT 2): the only catalog "Major League" is
    # PAMCO's 1934 game; notes citing Williams' 1963 one must not fill with it.
    (11, "major-league", "Major League", 1934, 102, 9, 5, 1, None, None),
    (12, "al-twins", "A.L. Twins", 1963, 103, 10, 6, 1, None, None),
    # The filter-order shape: a year match must not beat a maker contradiction.
    (13, "champion-cc", "Champion", 1949, 104, 11, 7, 1, None, None),
    (14, "champion-bally", "Champion", None, 105, 11, 2, 1, None, None),
    (15, "tanforan", "Tanforan", 1949, 106, 12, 3, 1, None, None),
    # Brand-vs-corporate-entity leniency: "Premier" must stay compatible with a
    # Gottlieb-brand model built by Premier Technology.
    (16, "arena", "Arena (Gottlieb)", 1987, 107, 13, 8, 2, None, None),
    (17, "arena-vifico", "Arena (VIFICO)", 1988, 108, 13, 9, 2, None, None),
    (18, "fly-high-t", "Fly High", 1979, 109, 14, 3, 1, None, None),
    # An and-joined two-donor note: its fill must flag, not green on one donor.
    (20, "dual-kit", "Dual Kit", 1984, 111, 15, 3, 1, None, None),
    # A common-word model name ("Colors") that ordinary prose mentions unquoted.
    (21, "colors", "Colors", 1954, 112, 16, 1, 1, None, None),
    # The King-of-Diamonds shape: a shared title drags in same-maker/same-year
    # siblings, but only ONE candidate is actually NAMED as the note states.
    (22, "king-of-diamonds", "King of Diamonds", 1967, 113, 17, 1, 1, None, None),
    (23, "diamond-jack", "Diamond Jack", 1967, 113 + 887, 17, 1, 1, None, None),
    (24, "rey-copy", "Rey Copy", 1971, 115, 18, 3, 1, None, None),
    # A second Dama conversion of the SAME donor as nero (model 6) — two fills
    # sharing one target is a same-name-merge collision the render must flag.
    (25, "nero-two", "Nero II", 1985, 116, 19, 3, 1, None, None),
    # The same-maker-target shape (Big Ben (Italy)): a variant whose note names
    # the SAME maker's own game — never a valid licensed/bootleg target.
    (19, "nero-aab", "Nero Add-A-Ball", 1983, 110, 5, 3, 1, None, None),
]


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "catalog.sqlite"
    con = sqlite3.connect(path)
    con.executescript(_SCHEMA)
    con.executemany(
        "INSERT INTO catalog_manufacturer VALUES (?, ?, ?)",
        [
            (1, "gottlieb", "Gottlieb"),
            (2, "bally", "Bally"),
            (3, "dama", "Dama"),
            (4, "zaccaria", "Zaccaria"),
            (5, "pamco", "PAMCO"),
            (6, "vifico", "VIFICO"),
            (7, "williams", "Williams"),
            (8, "chicago-coin", "Chicago Coin"),
        ],
    )
    con.executemany(
        "INSERT INTO catalog_corporateentity VALUES (?, ?, ?, ?)",
        [
            (1, "d-gottlieb-company", "D. Gottlieb & Company", 1),
            (2, "bally-manufacturing-corporation", "Bally Manufacturing", 2),
            (3, "dama-srl", "Dama S.R.L.", 3),
            (4, "zaccaria-spa", "Zaccaria S.p.A.", 4),
            (5, "pacific-amusement", "Pacific Amusement Manufacturing", 5),
            (6, "williams-electronics", "Williams Electronics", 7),
            (7, "chicago-coin-machine", "Chicago Coin Machine", 8),
            (8, "premier-technology", "Premier Technology", 1),
            (9, "vifico-sa", "VIFICO S.A.", 6),
        ],
    )
    con.executemany(
        "INSERT INTO catalog_technologygeneration VALUES (?, ?, ?)",
        [(1, "em", "Electromechanical"), (2, "ss", "Solid State")],
    )
    con.executemany(
        "INSERT INTO catalog_title VALUES (?, ?, ?)",
        [
            (1, "hurdy-gurdy", "Hurdy Gurdy"),
            (2, "central-park", "Central Park"),
            (3, "spider", "Spider"),
            (4, "mata-hari", "Mata Hari"),
            (5, "nero", "Nero"),
            (6, "aquarius", "Aquarius"),
            (7, "supersonic", "Supersonic (Bally)"),
            (8, "supersonic-z", "Supersonic (Zaccaria)"),
            (9, "major-league", "Major League"),
            (10, "al-twins", "A.L. Twins"),
            (11, "champion", "Champion"),
            (12, "tanforan", "Tanforan"),
            (13, "arena", "Arena (Gottlieb)"),
            (14, "fly-high-t", "Fly High"),
            (15, "dual-kit", "Dual Kit"),
            (16, "colors", "Colors"),
            (17, "king-of-diamonds", "King of Diamonds"),
            (18, "rey-copy", "Rey Copy"),
            (19, "nero-two", "Nero II"),
        ],
    )
    con.executemany(
        "INSERT INTO catalog_machinemodel VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
        _MODELS,
    )
    con.execute("INSERT INTO catalog_tag VALUES (1, 'bootleg', 'Bootleg')")
    con.commit()
    con.close()
    return path


@pytest.fixture
def catalog(db_path):
    cat = SweepCatalog(db_path)
    yield cat
    cat.close()


@pytest.fixture
def index(db_path):
    return EntityIndex.build(db_path, types=("model", "title"))


_NOTES = {
    "ipdb:5555": "Conversion kit for Gottlieb's 1966 'Hurdy Gurdy (Italy)'.",
    "ipdb:7777": "Conversion kit for Bally's 1978 'Mata Hari'.",
    "ipdb:6015": "A copy of Gottlieb's 1970 'Aquarius'.",
    "ipdb:1291": "Gottlieb produced 2,600 units of this game.",
    "ipdb:9002": "This game also exists as a prototype with different art.",
    "ipdb:103": "Conversion of Williams' 1963 'Major League'.",
    "ipdb:106": "Conversion kit for Bally's 1949 'Champion'.",
    "ipdb:108": "Made under license from Premier's 1987 'Arena'.",
    "ipdb:109": "Conversion kit for Bally's 1979 'Supersonic'.",
    "ipdb:110": (
        "This is the add-a-ball version of Dama's 1982 'Nero' made for export. "
        "The backglass indicates this version is manufactured under licence."
    ),
    "ipdb:111": (
        "Conversion kit for Bally's 1978 'Mata Hari' and Bally's 1979 'Supersonic'."
    ),
    "ipdb:115": "A modified copy of Gottlieb's 1967 'King of Diamonds'.",
    "ipdb:116": "Conversion kit for Bally's 1978 'Mata Hari'.",
}


def evidence_for(ref):
    return _NOTES.get(ref)


class FakeAi:
    """An AiClient whose answers are keyed on the evidence ref in the prompt.

    ``supports`` scripts the quote-supports-claim verdict for the fill gate's
    second call (recognized by the CLAIM: line in its user prompt).
    """

    def __init__(self, answers, supports=True):
        self.answers = answers
        self.supports = supports
        self.calls = []

    def structured(self, *, system, user, schema, model, max_tokens=512):
        self.calls.append({"system": system, "user": user, "model": model})
        if "CLAIM:" in user:
            return {
                "supported": self.supports,
                "reason": "" if self.supports else "quote does not establish it",
            }
        for marker, answer in self.answers.items():
            if f"[source: {marker}]" in user:
                return answer
        raise AssertionError(f"no scripted answer matches prompt: {user[:120]}")


def yes(title, maker="", year=None, quote=""):
    return {
        "verdict": "yes",
        "quote": quote,
        "target_title": title,
        "target_maker": maker,
        "target_year": year,
        "reason": "note states it outright",
    }


# ── candidates.py ────────────────────────────────────────────────────────────


def test_load_candidates_parses_and_defaults(tmp_path):
    path = tmp_path / "c.jsonl"
    path.write_text(
        '{"ipdb_id": 5555, "field": "converted_from", "hint": "central-park"}\n'
        "\n"
        '{"ipdb_id": 6015, "field": "bootleg_of", "evidence": ["https://x.test/p"]}\n'
    )
    rows = load_candidates(path)
    assert rows[0] == CandidateRow(5555, "converted_from", hint="central-park")
    assert rows[0].refs() == ("ipdb:5555",)
    assert rows[1].refs() == ("https://x.test/p",)
    assert rows[1].hint is None


@pytest.mark.parametrize(
    "line",
    [
        "not json",
        '{"ipdb_id": "5555", "field": "converted_from"}',
        '{"ipdb_id": 5555, "field": "widebody"}',
        '{"ipdb_id": 5555, "field": "converted_from", "hint": 3}',
        '{"ipdb_id": 5555, "field": "converted_from", "evidence": "ipdb:5555"}',
    ],
)
def test_load_candidates_rejects_bad_rows(tmp_path, line):
    path = tmp_path / "c.jsonl"
    path.write_text(line + "\n")
    with pytest.raises(CandidateError):
        load_candidates(path)


def test_load_candidates_rejects_duplicates(tmp_path):
    path = tmp_path / "c.jsonl"
    row = '{"ipdb_id": 5555, "field": "converted_from"}\n'
    path.write_text(row + row)
    with pytest.raises(CandidateError, match="duplicate"):
        load_candidates(path)


# ── judge.py ─────────────────────────────────────────────────────────────────


def test_parse_answer_normalizes_sentinels_and_year():
    answer = parse_answer(
        {
            "verdict": "yes",
            "quote": "Conversion kit",
            "target_title": "Hurdy Gurdy",
            "target_maker": "none",
            "target_year": "1966",
            "reason": "n/a",
        }
    )
    assert answer.target_maker == ""
    assert answer.target_year == 1966
    assert answer.reason == ""


def test_prompt_carries_note_and_identity_but_never_catalog_or_hint(catalog):
    facts = catalog.by_ipdb(5555)
    spec = RELATIONAL_FIELDS["converted_from"]
    prompt = build_user_prompt(facts, spec, (("ipdb:5555", _NOTES["ipdb:5555"]),))
    assert "Spider" in prompt
    assert "Hurdy Gurdy (Italy)" in prompt  # the note rides along in full
    assert "central-park" not in prompt  # the catalog's current value stays out


# ── gate.resolve_target ──────────────────────────────────────────────────────


def _resolve(index, catalog, title, *, maker="", year=None, exclude=0):
    answer = JudgeAnswer(
        verdict="yes",
        quote="q",
        target_title=title,
        target_maker=maker,
        target_year=year,
        reason="",
    )
    return gate.resolve_target(
        answer, index=index, catalog=catalog, exclude_model_id=exclude
    )


def test_resolve_unique(index, catalog):
    resolution = _resolve(index, catalog, "Hurdy Gurdy")
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "hurdy-gurdy"


def test_resolve_year_disambiguates_em_vs_ss(index, catalog):
    resolution = _resolve(index, catalog, "Mata Hari", year=1978)
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "mata-hari-ss"
    assert "year 1978" in resolution.how


def test_resolve_without_facts_stays_ambiguous(index, catalog):
    resolution = _resolve(index, catalog, "Mata Hari")
    assert resolution.status == "ambiguous"
    assert {c.slug for c in resolution.considered} == {"mata-hari", "mata-hari-ss"}


def test_resolve_excludes_the_judged_model_itself(index, catalog):
    resolution = _resolve(index, catalog, "Aquarius", exclude=8)
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "aquarius"


def test_resolve_mismatched_year_filter_never_wipes_the_set(index, catalog):
    resolution = _resolve(index, catalog, "Mata Hari", year=1912)
    assert resolution.status == "ambiguous"
    assert "filter skipped" in resolution.how


def test_resolve_unknown_name(index, catalog):
    assert _resolve(index, catalog, "Zorch Nebula").status == "none"


# ── the 0128 hardening defects (TOOL-NOTES.md) ───────────────────────────────


def test_resolve_reaches_maker_suffixed_names(index, catalog):
    """DEFECT 1: a bare note title must reach a '(Maker)'-suffixed catalog name."""
    resolution = _resolve(index, catalog, "Supersonic", maker="Bally", year=1979)
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "supersonic"


def test_resolve_strips_note_side_parenthetical(index, catalog):
    """The stated title may carry a parenthetical the catalog name lacks."""
    resolution = _resolve(index, catalog, "Hurdy Gurdy (Italy)")
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "hurdy-gurdy"


def test_resolve_unknown_year_candidate_is_never_excluded(index, catalog):
    """DEFECT 2 (Champion shape): a year match must not beat a maker
    contradiction, and a year-unknown candidate survives the year filter."""
    resolution = _resolve(index, catalog, "Champion", maker="Bally", year=1949)
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "champion-bally"


def test_ambiguous_resolution_containing_catalog_value_is_agreement(db_path, index):
    """An ambiguous resolution that INCLUDES the catalog's current value is
    consistency, not conflict — don't drag a settled row into review."""
    con = sqlite3.connect(db_path)
    # Point spider's converted_from at the SS Mata Hari before opening the catalog.
    con.execute("UPDATE catalog_machinemodel SET converted_from_id = 5 WHERE id = 3")
    con.commit()
    con.close()
    catalog = SweepCatalog(db_path)
    ai = FakeAi(
        {
            # No year stated → "Mata Hari" stays ambiguous (EM vs SS), but the
            # catalog already points at one of the two.
            "ipdb:5555": yes("Mata Hari", quote="Conversion kit for")
        }
    )
    [row] = _run([CandidateRow(5555, "converted_from")], catalog, index, ai)
    catalog.close()
    assert row.disposition == gate.AGREES
    assert not row.needs_review
    assert any("ambiguous" in reason for reason in row.reasons)


def test_sweep_facts_mismatch_instead_of_false_green(catalog, index):
    """DEFECT 2 (Major League shape): stated maker/year contradicting the only
    catalog match must escalate, never fill."""
    ai = FakeAi(
        {
            "ipdb:103": yes(
                "Major League",
                maker="Williams",
                year=1963,
                quote="Conversion of Williams' 1963 'Major League'.",
            )
        }
    )
    [row] = _run([CandidateRow(103, "converted_from")], catalog, index, ai)
    assert row.disposition == gate.FACTS_MISMATCH
    assert row.needs_review
    assert row.resolved_slug is None  # a contradicted match is no resolution


def test_sweep_brand_vs_corporate_entity_is_compatible(catalog, index):
    """'Premier' (corporate entity) must stay compatible with a Gottlieb-brand
    model — no false facts-mismatch escalation."""
    ai = FakeAi(
        {
            "ipdb:108": yes(
                "Arena",
                maker="Premier",
                year=1987,
                quote="Made under license from Premier's 1987 'Arena'.",
            )
        }
    )
    [row] = _run([CandidateRow(108, "licensed_build_of")], catalog, index, ai)
    assert row.disposition == gate.FILL
    assert row.resolved_slug == "arena"


def test_sweep_year_noise_of_one_is_tolerated(catalog, index):
    """±1 year between note and catalog is data noise, not a contradiction."""
    ai = FakeAi(
        {
            "ipdb:109": yes(
                "Supersonic",
                maker="Bally",
                year=1980,  # catalog says 1979
                quote="Conversion kit for Bally's 1979 'Supersonic'.",
            )
        }
    )
    [row] = _run([CandidateRow(109, "converted_from")], catalog, index, ai)
    assert row.disposition == gate.FILL
    assert row.resolved_slug == "supersonic"


def test_same_maker_target_never_greens_or_conflicts(catalog, index):
    """The Big Ben (Italy) shape: a note naming the SAME maker's own game as a
    licensed-build target is a chain link (the maker's own variant), never the
    licensor's original — escalate, don't fill and don't accuse the catalog."""
    ai = FakeAi(
        {
            "ipdb:110": yes(
                "Nero",
                maker="Dama",
                year=1982,
                quote="the add-a-ball version of Dama's 1982 'Nero'",
            )
        }
    )
    [row] = _run([CandidateRow(110, "licensed_build_of")], catalog, index, ai)
    assert row.disposition == gate.SAME_MAKER
    assert row.needs_review
    assert row.resolved_slug is None


def test_same_maker_target_is_fine_for_conversions(catalog, index):
    """In-house conversions exist — the rule applies only to licensed/bootleg."""
    ai = FakeAi(
        {
            "ipdb:110": yes(
                "Nero",
                maker="Dama",
                year=1982,
                quote="the add-a-ball version of Dama's 1982 'Nero'",
            )
        }
    )
    [row] = _run([CandidateRow(110, "converted_from")], catalog, index, ai)
    assert row.disposition == gate.FILL
    assert row.resolved_slug == "nero"


def test_fill_quote_must_support_the_claim(catalog, index):
    """The jungle-queen shape: a verbatim quote that doesn't ESTABLISH the
    relationship must not ship as a cite quote. The judgment reuses ai_lint's
    quote-supports-claim rule (same prompt, same trusted tier)."""
    ai = FakeAi(
        {
            # Verbatim in note ipdb:109, but establishes nothing about the donor.
            "ipdb:109": yes("Supersonic", maker="Bally", quote="Conversion kit")
        },
        supports=False,
    )
    [row] = _run([CandidateRow(109, "converted_from")], catalog, index, ai)
    assert row.disposition == gate.QUOTE_UNSUPPORTED
    assert row.needs_review
    assert row.quote_supported is False
    assert row.resolved_slug == "supersonic"  # the resolution itself is fine
    # The support call carried the synthesized claim and the fenced source.
    support_calls = [c for c in ai.calls if "CLAIM:" in c["user"]]
    assert len(support_calls) == 1
    assert "Supersonic" in support_calls[0]["user"]


def test_fill_with_supported_quote_stays_green(catalog, index):
    ai = FakeAi(
        {
            "ipdb:109": yes(
                "Supersonic",
                maker="Bally",
                quote="Conversion kit for Bally's 1979 'Supersonic'.",
            )
        },
        supports=True,
    )
    [row] = _run([CandidateRow(109, "converted_from")], catalog, index, ai)
    assert row.disposition == gate.FILL
    assert row.quote_supported is True


def test_support_check_only_runs_for_fills(catalog, index):
    """agrees/no-claim/review rows ship no cite — no support call is spent."""
    ai = FakeAi(
        {"ipdb:1291": {"verdict": "no", "reason": "production note only"}},
        supports=False,
    )
    [row] = _run([CandidateRow(1291, "converted_from")], catalog, index, ai)
    assert row.disposition == gate.NO_CLAIM
    assert row.quote_supported is None
    assert all("CLAIM:" not in c["user"] for c in ai.calls)


def test_fill_quote_naming_a_second_donor_flags_multi_target(catalog, index):
    """An and-joined two-donor note (the authoring session's catch): a fill
    whose quote names another catalog model besides the resolved target is a
    multi-target signal — review, never a single-donor green."""
    ai = FakeAi(
        {
            "ipdb:111": yes(
                "Supersonic",
                maker="Bally",
                year=1979,
                quote=(
                    "Conversion kit for Bally's 1978 'Mata Hari' and Bally's "
                    "1979 'Supersonic'."
                ),
            )
        }
    )
    [row] = _run([CandidateRow(111, "converted_from")], catalog, index, ai)
    assert row.disposition == gate.MULTI_TARGET
    assert row.needs_review
    assert any("Mata Hari" in reason or "mata-hari" in reason for reason in row.reasons)
    # No support call is spent on a row already headed to review.
    assert all("CLAIM:" not in c["user"] for c in ai.calls)


def test_unquoted_common_word_model_names_do_not_trip_multi_target(catalog, index):
    """IPDB notes write machine titles in quotes; a bare prose word that happens
    to be a model name ("different cabinet colors") is not a second target."""

    answer_quote = (
        "A copy of Gottlieb's 1970 'Aquarius', with different cabinet colors."
    )
    subject = catalog.by_ipdb(6015)
    target = catalog.by_slug("aquarius")
    others = gate.other_models_in_quote(
        answer_quote, index=index, subject=subject, target=target
    )
    assert others == []
    quoted = "A copy of Gottlieb's 1970 'Aquarius' and Gottlieb's 1954 'Colors'."
    others = gate.other_models_in_quote(
        quoted, index=index, subject=subject, target=target
    )
    assert others == ["colors"]


def test_fill_quote_naming_only_its_target_is_not_multi_target(catalog, index):
    ai = FakeAi(
        {
            "ipdb:109": yes(
                "Supersonic",
                maker="Bally",
                quote="Conversion kit for Bally's 1979 'Supersonic'.",
            )
        }
    )
    [row] = _run([CandidateRow(109, "converted_from")], catalog, index, ai)
    assert row.disposition == gate.FILL


def test_ready_to_author_fills_grouped_by_maker(catalog, index):
    ai = FakeAi(
        {
            "ipdb:7777": yes(
                "Mata Hari",
                year=1978,
                quote="Conversion kit for Bally's 1978 'Mata Hari'.",
            ),
            "ipdb:109": yes(
                "Supersonic",
                maker="Bally",
                quote="Conversion kit for Bally's 1979 'Supersonic'.",
            ),
        }
    )
    rows = _run(
        [CandidateRow(7777, "converted_from"), CandidateRow(109, "converted_from")],
        catalog,
        index,
        ai,
    )
    review = render_review(rows)
    assert "### dama (2)" in review  # both subjects are Dama models


def test_exact_name_match_breaks_title_group_ambiguity(index, catalog):
    """The King-of-Diamonds shape (petaco pass): a shared title drags in
    same-maker/same-year siblings, but exactly one candidate is NAMED as the
    note states — a deterministic tie-break, not a judgment call."""
    resolution = _resolve(
        index, catalog, "King of Diamonds", maker="Gottlieb", year=1967
    )
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "king-of-diamonds"
    assert "exact name" in resolution.how


def test_exact_name_tiebreak_leaves_true_same_name_pairs_ambiguous(index, catalog):
    """Both Mata Haris are exactly named 'Mata Hari' — the tie-break must not
    fake a resolution where the names genuinely collide."""
    resolution = _resolve(index, catalog, "Mata Hari")
    assert resolution.status == "ambiguous"


def test_resolution_trail_names_the_pre_narrow_candidates(index, catalog):
    """The artifact must show what narrowing DROPPED (hardening UX note) —
    the visibility that would have exposed DEFECTs 1-2 by eye."""
    resolution = _resolve(index, catalog, "Mata Hari", year=1978)
    assert "mata-hari" in resolution.how
    assert "mata-hari-ss" in resolution.how


def test_shared_target_fills_get_a_merge_warning(catalog, index):
    """Two same-maker fills resolving to ONE target (rmg's space-orbit pair)
    are an un-authorable slug collision — REVIEW.md must flag the pair."""
    ai = FakeAi(
        {
            "ipdb:7777": yes(
                "Mata Hari",
                year=1978,
                quote="Conversion kit for Bally's 1978 'Mata Hari'.",
            ),
            "ipdb:116": yes(
                "Mata Hari",
                year=1978,
                quote="Conversion kit for Bally's 1978 'Mata Hari'.",
            ),
        }
    )
    rows = _run(
        [CandidateRow(7777, "converted_from"), CandidateRow(116, "converted_from")],
        catalog,
        index,
        ai,
    )
    review = render_review(rows)
    assert "shared target" in review
    assert "`nero`" in review
    assert "`nero-two`" in review


def test_review_has_a_per_maker_roster(catalog, index):
    ai = FakeAi(
        {
            "ipdb:7777": yes(
                "Mata Hari",
                year=1978,
                quote="Conversion kit for Bally's 1978 'Mata Hari'.",
            ),
            "ipdb:9002": {"verdict": "uncertain", "reason": "prototype talk only"},
        }
    )
    rows = _run(
        [CandidateRow(7777, "converted_from"), CandidateRow(9002, "converted_from")],
        catalog,
        index,
        ai,
    )
    review = render_review(rows)
    assert "## Per-maker roster" in review
    assert "| `dama` | 1 |" in review  # 1 fill for dama
    assert "uncertain 1" in review  # bally's escalation named by disposition


def test_model_reason_is_labeled_distinctly(catalog, index):
    ai = FakeAi(
        {
            "ipdb:5555": yes(
                "Hurdy Gurdy",
                quote="Conversion kit for Gottlieb's 1966 'Hurdy Gurdy (Italy)'.",
            )
        }
    )
    [row] = _run([CandidateRow(5555, "converted_from")], catalog, index, ai)
    assert any(reason.startswith("model: ") for reason in row.reasons)


def test_regate_preserves_quote_supported(catalog, index):
    """--regate is offline — a stored support verdict must survive it."""
    from ai_corpus_sweep.sweep import SweepRow, regate_rows

    checked = SweepRow(
        ipdb_id=109,
        field="converted_from",
        disposition=gate.FILL,
        verdict="yes",
        quote="Conversion kit for Bally's 1979 'Supersonic'.",
        target_title="Supersonic",
        target_maker="Bally",
        target_year=1979,
        quote_supported=True,
        evidence=(("ipdb:109", _NOTES["ipdb:109"]),),
    )
    [row] = regate_rows([checked], catalog=catalog, index=index)
    assert row.disposition == gate.FILL
    assert row.quote_supported is True

    unsupported = SweepRow(
        ipdb_id=109,
        field="converted_from",
        disposition=gate.FILL,  # judged before the support gate existed
        verdict="yes",
        quote="Conversion kit for Bally's 1979 'Supersonic'.",
        target_title="Supersonic",
        target_maker="Bally",
        target_year=1979,
        quote_supported=False,
        evidence=(("ipdb:109", _NOTES["ipdb:109"]),),
    )
    [row] = regate_rows([unsupported], catalog=catalog, index=index)
    assert row.disposition == gate.QUOTE_UNSUPPORTED


def test_regate_rebuckets_stored_answers_without_ai(catalog, index):
    """--regate: stored verdicts re-gate against fixed code + live DB, no AI."""
    from ai_corpus_sweep.sweep import SweepRow, regate_rows

    stale = SweepRow(
        ipdb_id=109,
        field="converted_from",
        disposition=gate.UNRESOLVED,  # what the pre-fix gate concluded
        model_slug="fly-high-t",
        verdict="yes",
        quote="Conversion kit for Bally's 1979 'Supersonic'.",
        target_title="Supersonic",
        target_maker="Bally",
        target_year=1979,
        evidence=(("ipdb:109", _NOTES["ipdb:109"]),),
    )
    untouched = SweepRow(
        ipdb_id=424242, field="converted_from", disposition=gate.NO_MODEL
    )
    regated = regate_rows([stale, untouched], catalog=catalog, index=index)
    assert regated[0].disposition == gate.FILL
    assert regated[0].resolved_slug == "supersonic"
    assert regated[0].quote_verified
    assert regated[1] == untouched  # verdict-less rows pass through unchanged


# ── end-to-end sweep over the fixture ────────────────────────────────────────


def _run(candidates, catalog, index, ai):
    return list(
        sweep_candidates(
            candidates, catalog=catalog, index=index, evidence_for=evidence_for, ai=ai
        )
    )


def test_sweep_catches_the_misseeded_conversion_as_conflict(catalog, index):
    ai = FakeAi(
        {
            "ipdb:5555": yes(
                "Hurdy Gurdy",
                maker="Gottlieb",
                year=1966,
                quote="Conversion kit for Gottlieb's 1966 'Hurdy Gurdy (Italy)'.",
            )
        }
    )
    [row] = _run(
        [CandidateRow(5555, "converted_from", hint="central-park")],
        catalog,
        index,
        ai,
    )
    assert row.disposition == gate.CONFLICT
    assert row.catalog_now == "central-park"
    assert row.resolved_slug == "hurdy-gurdy"
    assert row.quote_verified
    assert row.needs_review


def test_sweep_fill_with_year_disambiguation(catalog, index):
    ai = FakeAi(
        {
            "ipdb:7777": yes(
                "Mata Hari",
                maker="Bally",
                year=1978,
                quote="Conversion kit for Bally's 1978 'Mata Hari'.",
            )
        }
    )
    [row] = _run([CandidateRow(7777, "converted_from")], catalog, index, ai)
    assert row.disposition == gate.FILL
    assert row.resolved_slug == "mata-hari-ss"
    assert row.quote_ref == "ipdb:7777"
    assert not row.needs_review


def test_sweep_hint_mismatch_routes_to_review(catalog, index):
    ai = FakeAi(
        {
            "ipdb:7777": yes(
                "Mata Hari",
                year=1978,
                quote="Conversion kit for Bally's 1978 'Mata Hari'.",
            )
        }
    )
    [row] = _run(
        [CandidateRow(7777, "converted_from", hint="mata-hari")], catalog, index, ai
    )
    assert row.disposition == gate.HINT_MISMATCH
    assert row.needs_review


def test_sweep_same_name_bootleg_fill_excludes_self(catalog, index):
    ai = FakeAi(
        {"ipdb:6015": yes("Aquarius", quote="A copy of Gottlieb's 1970 'Aquarius'.")}
    )
    [row] = _run(
        [CandidateRow(6015, "bootleg_of", hint="aquarius")], catalog, index, ai
    )
    assert row.disposition == gate.FILL
    assert row.resolved_slug == "aquarius"


def test_sweep_unverbatim_quote_fails_the_gate(catalog, index):
    ai = FakeAi({"ipdb:6015": yes("Aquarius", quote="a paraphrase, not the note")})
    [row] = _run([CandidateRow(6015, "bootleg_of")], catalog, index, ai)
    assert row.disposition == gate.QUOTE_FAIL


def test_sweep_no_verdict_paths(catalog, index):
    ai = FakeAi(
        {
            # Catalog holds converted_from for spider (5555) but the note (here)
            # supports nothing: the set-but-unsupported review bucket.
            "ipdb:5555": {"verdict": "no", "reason": "no conversion language"},
            # Catalog empty for hurdy-gurdy: a green net false positive.
            "ipdb:1291": {"verdict": "no", "reason": "production note only"},
            "ipdb:9002": {"verdict": "uncertain", "reason": "prototype talk only"},
        }
    )
    rows = _run(
        [
            CandidateRow(5555, "converted_from"),
            CandidateRow(1291, "converted_from"),
            CandidateRow(9002, "converted_from"),
        ],
        catalog,
        index,
        ai,
    )
    assert [r.disposition for r in rows] == [
        gate.SET_BUT_UNSUPPORTED,
        gate.NO_CLAIM,
        gate.UNCERTAIN,
    ]
    assert rows[0].needs_review
    assert not rows[1].needs_review


def test_sweep_no_model_and_no_evidence(catalog, index):
    ai = FakeAi({})
    rows = _run(
        [CandidateRow(424242, "converted_from"), CandidateRow(9001, "converted_from")],
        catalog,
        index,
        ai,
    )
    assert [r.disposition for r in rows] == [gate.NO_MODEL, gate.NO_EVIDENCE]
    assert ai.calls == []  # neither row reaches the model


def test_sweep_never_leaks_hint_or_catalog_state_to_the_model(catalog, index):
    ai = FakeAi(
        {
            "ipdb:5555": yes(
                "Hurdy Gurdy",
                quote="Conversion kit for Gottlieb's 1966 'Hurdy Gurdy (Italy)'.",
            )
        }
    )
    _run(
        [CandidateRow(5555, "converted_from", hint="central-park")], catalog, index, ai
    )
    [call] = ai.calls
    assert "central-park" not in call["user"]
    assert "central-park" not in call["system"]
    assert call["model"] == "claude-sonnet-5"  # TRUSTED_MODEL, never the cheap tier


# ── persistence round-trip and rendering ─────────────────────────────────────


def test_row_json_round_trip(catalog, index):
    ai = FakeAi(
        {
            "ipdb:7777": yes(
                "Mata Hari",
                maker="Bally",
                year=1978,
                quote="Conversion kit for Bally's 1978 'Mata Hari'.",
            )
        }
    )
    [row] = _run([CandidateRow(7777, "converted_from")], catalog, index, ai)
    hydrated = row_from_json(json.loads(json.dumps(row.to_json())))
    assert hydrated == row


def test_render_review_sections(catalog, index):
    ai = FakeAi(
        {
            "ipdb:5555": yes(
                "Hurdy Gurdy",
                quote="Conversion kit for Gottlieb's 1966 'Hurdy Gurdy (Italy)'.",
            ),
            "ipdb:7777": yes(
                "Mata Hari",
                year=1978,
                quote="Conversion kit for Bally's 1978 'Mata Hari'.",
            ),
        }
    )
    rows = _run(
        [
            CandidateRow(5555, "converted_from", hint="central-park"),
            CandidateRow(7777, "converted_from"),
        ],
        catalog,
        index,
        ai,
    )
    review = render_review(rows)
    assert "## Needs review (1)" in review
    assert "conflict" in review
    assert "Hurdy Gurdy (Italy)" in review  # the full note rides in the detail block
    assert "## Ready to author" in review
    assert "`mata-hari-ss`" in review


def test_progress_line_names_the_outcome(catalog, index):
    ai = FakeAi(
        {
            "ipdb:7777": yes(
                "Mata Hari",
                year=1978,
                quote="Conversion kit for Bally's 1978 'Mata Hari'.",
            )
        }
    )
    [row] = _run([CandidateRow(7777, "converted_from")], catalog, index, ai)
    line = progress_line(3, 10, row)
    assert line == "[3/10] ipdb:7777 `nero` converted_from: fill → mata-hari-ss"


def test_render_reconcile_buckets_and_mismatches(catalog):
    from ai_corpus_sweep.sweep import reconcile_candidates

    report = render_reconcile(
        reconcile_candidates(
            [
                CandidateRow(5555, "converted_from", hint="hurdy-gurdy"),
                CandidateRow(7777, "converted_from"),
                CandidateRow(424242, "converted_from"),
            ],
            catalog=catalog,
        )
    )
    assert "| set | 1 |" in report
    assert "| empty | 1 |" in report
    assert "| no-model | 1 |" in report
    assert "`central-park` | `hurdy-gurdy`" in report  # catalog ≠ prior guess
