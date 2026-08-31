"""Offline tests for the corpus sweep — fixture SQLite, fake AI, no siblings.

The fixture catalog stages the campaign's real failure shapes against the
`catalog_modelrelationship` join table: a mis-seeded conversion edge (whose
note supports a different target — a fill plus a set-but-unsupported), a copy
edge whose stored license_status the note contradicts (a conflict), an EM/SS
same-name pair only a stated year can disambiguate, and a same-name copy whose
target resolution must exclude the judged model itself.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import replace

import pytest
from ai_corpus_sweep import gate
from ai_corpus_sweep import sweep as sweep_mod
from ai_corpus_sweep.candidates import CandidateError, CandidateRow, load_candidates
from ai_corpus_sweep.catalog import CatalogEdge, SweepCatalog
from ai_corpus_sweep.fields import SPEC
from ai_corpus_sweep.judge import (
    RELATIONAL_SCHEMA,
    JudgeClaim,
    build_user_prompt,
    judge_candidate,
    parse_claims,
)
from ai_corpus_sweep.render import progress_line, render_reconcile, render_review
from ai_corpus_sweep.sweep import SweepRow, regate_rows, row_from_json, sweep_candidates
from common.catalog.entity_index import EntityIndex
from jsonschema import Draft7Validator

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
    title_id INTEGER, corporate_entity_id INTEGER, technology_generation_id INTEGER);
CREATE TABLE catalog_modelrelationship (
    id INTEGER PRIMARY KEY, machine_model_id INTEGER, target_machine_id INTEGER,
    target_label TEXT DEFAULT '', relationship_type TEXT, license_status TEXT);
"""

# (id, slug, name, year, ipdb, title, corp, tech)
_MODELS = [
    (1, "hurdy-gurdy", "Hurdy Gurdy", 1966, 1291, 1, 1, 1),
    (2, "central-park", "Central Park", 1966, 483, 2, 1, 1),
    # The mis-seeded conversion: catalog edge → Central Park, note → Hurdy Gurdy.
    (3, "spider", "Spider", 1968, 5555, 3, 3, 1),
    (4, "mata-hari", "Mata Hari", 1977, 9001, 4, 2, 1),
    (5, "mata-hari-ss", "Mata Hari", 1978, 9002, 4, 2, 2),
    (6, "nero", "Nero", 1982, 7777, 5, 3, None),
    (7, "aquarius", "Aquarius", 1970, 300, 6, 1, 1),
    # Same-name copy of 7 — target resolution must not pick itself.
    (8, "aquarius-dama", "Aquarius", 1971, 6015, 6, 3, 1),
    # The parenthetical blind spot (DEFECT 1): the true target's name AND title
    # carry a "(Bally)" suffix the note does not; a different maker's same-named
    # game is the only bare "Supersonic" the name index can reach. The *maker*
    # suffix that first exposed this is a retired convention, but the shape is
    # permanent — the catalog is full of "Dragon (EM)" / "AC/DC (Pro)".
    (9, "supersonic", "Supersonic (Bally)", 1979, 100, 7, 2, 2),
    (10, "supersonic-z", "Supersonic", 1980, 101, 8, 4, 2),
    # DEFECT 6: a DIFFERENT brand whose slug merely has the stated maker as a
    # prefix ("Bally" ⊂ "bally-wulff"). Substring leniency let it satisfy a
    # note that says "Bally", leaving the true target (9) in a false tie.
    (31, "supersonic-bw", "Supersonic (Bally Wulff)", 1979, 4106, 7, 10, 2),
    # The false-green shape (DEFECT 2): the only catalog "Major League" is
    # PAMCO's 1934 game; notes citing Williams' 1963 one must not fill with it.
    (11, "major-league", "Major League", 1934, 102, 9, 5, 1),
    (12, "al-twins", "A.L. Twins", 1963, 103, 10, 6, 1),
    # The filter-order shape: a year match must not beat a maker contradiction.
    (13, "champion-cc", "Champion", 1949, 104, 11, 7, 1),
    (14, "champion-bally", "Champion", None, 105, 11, 2, 1),
    (15, "tanforan", "Tanforan", 1949, 106, 12, 3, 1),
    # Brand-vs-corporate-entity leniency: "Premier" must stay compatible with a
    # Gottlieb-brand model built by Premier Technology. arena-vifico carries a
    # copy/licensed edge → arena, so a note saying UNLICENSED is a conflict.
    (16, "arena", "Arena (Gottlieb)", 1987, 107, 13, 8, 2),
    (17, "arena-vifico", "Arena (VIFICO)", 1988, 108, 13, 9, 2),
    (18, "fly-high-t", "Fly High", 1979, 109, 14, 3, 1),
    # An and-joined two-donor note: its fill must flag, not green on one donor.
    (20, "dual-kit", "Dual Kit", 1984, 111, 15, 3, 1),
    # A common-word model name ("Colors") that ordinary prose mentions unquoted.
    (21, "colors", "Colors", 1954, 112, 16, 1, 1),
    # The King-of-Diamonds shape: a shared title drags in same-maker/same-year
    # siblings, but only ONE candidate is actually NAMED as the note states.
    # rey-copy carries a copy/unknown edge → king-of-diamonds (an agree case).
    (22, "king-of-diamonds", "King of Diamonds", 1967, 113, 17, 1, 1),
    (23, "diamond-jack", "Diamond Jack", 1967, 113 + 887, 17, 1, 1),
    (24, "rey-copy", "Rey Copy", 1971, 115, 18, 3, 1),
    # A second Dama conversion of the SAME donor as nero (model 6) — two fills
    # sharing one target is a same-name-merge collision the render must flag.
    (25, "nero-two", "Nero II", 1985, 116, 19, 3, 1),
    # DEFECT 9: the only "Dracula" is Stern ELECTRONICS' 1979 game; the modern
    # "Stern" brand (Stern Pinball) exists but made nothing until 1999, so a
    # 1979 note saying "Stern" cannot possibly mean it.
    (34, "dracula", "Dracula", 1979, 4001, 23, 11, 2),
    (35, "batman-modern", "Batman", 2008, 4002, 24, 12, 2),
    # The same-maker-target shape (Big Ben (Italy)): a variant whose note names
    # the SAME maker's own game — never a valid copy target.
    (19, "nero-aab", "Nero Add-A-Ball", 1983, 110, 5, 3, 1),
    # Multiple relationships from one note (the punky-willy shape).
    (26, "twin-copy", "Twin Copy", 1985, 4101, 3, 3, 1),
    # The ambiguous-resolution-with-an-existing-edge shape: its note names a
    # bare "Mata Hari" (no year), which never narrows past the EM/SS pair.
    # Technology deliberately unknown: this row exists to test AMBIGUOUS
    # handling, so it must not be silently resolved by the technology
    # tie-break (a kit carries no technology generation of its own anyway).
    (27, "amb-kit", "Amb Kit", 1984, 4102, 15, 3, None),
    # Carries a text-target edge, for the label-wording diff.
    (28, "label-kit", "Label Kit", 1981, 4103, 15, 3, 1),
    # DEFECT 7: its note copies another game's ARTWORK, not its design.
    (32, "art-copy", "Art Copy", 1979, 4107, 20 + 1, 3, 1),
    # The same, but someone already seeded the artwork edge as a copy: the note
    # must never be read as confirming it.
    (33, "art-seeded", "Art Seeded", 1979, 4108, 20 + 2, 3, 1),
    # A same-name pair where ONE candidate's technology is unknown: the
    # technology tie-break must not guess against missing data (DEFECT 2's
    # lesson — a candidate can't be excluded by a fact it doesn't carry).
    (29, "vulcan-x", "Vulcan", 1977, 4104, 20, 1, 1),
    (30, "vulcan-y", "Vulcan", 1977, 4105, 20, 1, None),
]

# (machine_model_id, target_machine_id, target_label, relationship_type, license)
_EDGES = [
    (3, 2, "", "conversion", "unknown"),  # spider → central-park (mis-seeded)
    (17, 16, "", "copy", "licensed"),  # arena-vifico → arena, license set
    (24, 22, "", "copy", "unknown"),  # rey-copy → king-of-diamonds (agree)
    (27, 5, "", "conversion_kit", "unknown"),  # amb-kit → mata-hari-ss
    # A text-target edge: its wording is payload the note must still agree with.
    (28, None, "several Gottlieb EM models", "conversion_kit", "unknown"),
    (33, 7, "", "copy", "unknown"),  # art-seeded → aquarius: an artwork edge
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
            # A brand whose slug begins with another brand's whole slug.
            (9, "bally-wulff", "Bally Wulff"),
            # DEFECT 9: a historical brand and its modern successor, whose
            # *name* is the bare token the old company's notes use ("Stern").
            (10, "stern-electronics", "Stern Electronics"),
            (11, "stern-pinball", "Stern"),
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
            (10, "bally-wulff-gmbh", "Bally Wulff GmbH", 9),
            (11, "stern-electronics-inc", "Stern Electronics, Inc.", 10),
            (12, "stern-pinball-inc", "Stern Pinball, Inc.", 11),
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
            (20, "vulcan", "Vulcan"),
            (21, "art-copy", "Art Copy"),
            (22, "art-seeded", "Art Seeded"),
            (23, "dracula", "Dracula"),
            (24, "batman-modern", "Batman"),
        ],
    )
    con.executemany(
        "INSERT INTO catalog_machinemodel VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        _MODELS,
    )
    con.executemany(
        "INSERT INTO catalog_modelrelationship "
        "(machine_model_id, target_machine_id, target_label, relationship_type, "
        "license_status) VALUES (?, ?, ?, ?, ?)",
        _EDGES,
    )
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
    "ipdb:108": "Made under license from Premier's 1987 'Arena'.",
    "ipdb:109": "Conversion kit for Bally's 1979 'Supersonic'.",
    "ipdb:4107": (
        "Backglass artwork is in part a copy of Gottlieb's 1970 'Aquarius'; "
        "artwork was also used again on another game."
    ),
    "ipdb:4108": "Backglass artwork is in part a copy of Gottlieb's 1970 'Aquarius'.",
    "ipdb:110": (
        "This is the add-a-ball version of Dama's 1982 'Nero' made for export. "
        "The backglass indicates this version is manufactured under licence."
    ),
    "ipdb:111": (
        "Conversion kit for Bally's 1978 'Mata Hari' and Bally's 1979 'Supersonic'."
    ),
    "ipdb:115": "A modified copy of Gottlieb's 1967 'King of Diamonds'.",
    "ipdb:116": "Conversion kit for Bally's 1978 'Mata Hari'.",
    "ipdb:4101": (
        "A copy of Gottlieb's 1970 'Aquarius' and Gottlieb's 1967 'King of Diamonds'."
    ),
    "ipdb:4102": "Conversion kit for Bally's 'Mata Hari'.",
    "ipdb:4103": "Conversion kit for several Gottlieb EM models.",
}


def evidence_for(ref):
    return _NOTES.get(ref)


class FakeAi:
    """An AiClient whose judge answers are keyed on the evidence ref in the prompt.

    ``supports`` scripts the quote-supports-claim verdict for the fill gate's
    second call (recognized by the CLAIM: line in its user prompt).
    """

    def __init__(self, answers, supports=True):
        self.answers = answers
        self.supports = supports
        self.calls = []

    def structured(self, *, system, user, schema, model, max_tokens=512):
        self.calls.append(
            {"system": system, "user": user, "model": model, "max_tokens": max_tokens}
        )
        if "CLAIM:" in user:
            return {
                "supported": self.supports,
                "reason": "" if self.supports else "quote does not establish it",
            }
        for marker, answer in self.answers.items():
            if f"[source: {marker}]" in user:
                return answer
        raise AssertionError(f"no scripted answer matches prompt: {user[:120]}")


def rel(
    rel_type,
    *,
    license="unknown",
    title="",
    maker="",
    year=None,
    label="",
    quote="",
    hedged=False,
    reason="note states it",
):
    return {
        "relationship_type": rel_type,
        "license_status": license,
        "target_title": title,
        "target_maker": maker,
        "target_year": year,
        "target_label": label,
        "quote": quote,
        "hedged": hedged,
        "reason": reason,
    }


def rels(*members):
    return {"relationships": list(members)}


def _mk_claim(
    title, *, maker="", year=None, label="", rel_type="conversion", license="unknown"
):
    return JudgeClaim(
        relationship_type=rel_type,
        license_status=license,
        target_title=title,
        target_maker=maker,
        target_year=year,
        target_label=label,
        quote="q",
        hedged=False,
        reason="",
    )


def _run(candidates, catalog, index, ai):
    return [
        row
        for batch in sweep_candidates(
            candidates, catalog=catalog, index=index, evidence_for=evidence_for, ai=ai
        )
        for row in batch
    ]


# ── candidates.py ────────────────────────────────────────────────────────────


def test_load_candidates_parses_and_defaults(tmp_path):
    path = tmp_path / "c.jsonl"
    path.write_text(
        '{"ipdb_id": 5555, "hint": "central-park"}\n'
        "\n"
        '{"ipdb_id": 6015, "hint": ["a", "b"], "evidence": ["https://x.test/p"]}\n'
    )
    rows = load_candidates(path)
    assert rows[0] == CandidateRow(5555, hint=("central-park",))
    assert rows[0].refs() == ("ipdb:5555",)
    assert rows[1].hint == ("a", "b")
    assert rows[1].refs() == ("https://x.test/p",)


@pytest.mark.parametrize(
    "line",
    [
        "not json",
        '{"ipdb_id": "5555"}',
        '{"ipdb_id": 5555, "field": "widebody"}',
        '{"ipdb_id": 5555, "hint": 3}',
        '{"ipdb_id": 5555, "evidence": "ipdb:5555"}',
    ],
)
def test_load_candidates_rejects_bad_rows(tmp_path, line):
    path = tmp_path / "c.jsonl"
    path.write_text(line + "\n")
    with pytest.raises(CandidateError):
        load_candidates(path)


def test_load_candidates_rejects_duplicates(tmp_path):
    path = tmp_path / "c.jsonl"
    row = '{"ipdb_id": 5555}\n'
    path.write_text(row + row)
    with pytest.raises(CandidateError, match="duplicate"):
        load_candidates(path)


# ── judge.py ─────────────────────────────────────────────────────────────────


def test_parse_claims_normalizes_and_drops_invalid():
    claims = parse_claims(
        {
            "relationships": [
                {
                    "relationship_type": "conversion_kit",
                    "license_status": "unknown",
                    "target_title": "Hurdy Gurdy",
                    "target_maker": "none",
                    "target_year": "1966",
                    "quote": "Conversion kit",
                    "reason": "n/a",
                },
                {
                    "relationship_type": "bogus",
                    "license_status": "unknown",
                    "quote": "x",
                },
            ]
        }
    )
    assert len(claims) == 1
    claim = claims[0]
    assert claim.relationship_type == "conversion_kit"
    assert claim.target_maker == ""  # "none" sentinel normalized away
    assert claim.target_year == 1966
    assert claim.reason == ""
    assert parse_claims({}) == []


def test_parse_claims_defaults_bad_license_to_unknown():
    [claim] = parse_claims(
        {
            "relationships": [
                {"relationship_type": "copy", "license_status": "?", "quote": "q"}
            ]
        }
    )
    assert claim.license_status == "unknown"


def test_prompt_carries_note_and_identity_but_never_catalog_or_hint(catalog):
    facts = catalog.by_ipdb(5555)
    prompt = build_user_prompt(facts, SPEC, (("ipdb:5555", _NOTES["ipdb:5555"]),))
    assert "Spider" in prompt
    assert "Hurdy Gurdy (Italy)" in prompt  # the note rides along in full
    assert "central-park" not in prompt  # the catalog's current value stays out


def test_judge_requests_room_for_a_long_answer(catalog):
    # ipdb:1723's multi-relationship note truncated the structured answer at a
    # 1024-token cap, landing a permanent ai-error. The judge emits EVERY
    # relationship a note supports, so its budget must fit the worst real note.
    facts = catalog.by_ipdb(5555)
    ai = FakeAi({"ipdb:5555": rels()})
    judge_candidate(ai, facts, SPEC, (("ipdb:5555", _NOTES["ipdb:5555"]),))
    assert ai.calls[0]["max_tokens"] >= 4096


# ── gate.resolve_target ──────────────────────────────────────────────────────


def _resolve(index, catalog, title, *, maker="", year=None, exclude=0, subject=None):
    return gate.resolve_target(
        _mk_claim(title, maker=maker, year=year),
        index=index,
        catalog=catalog,
        exclude_model_id=exclude,
        subject=subject,
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


def test_resolve_rejects_a_different_brand_sharing_the_stated_makers_token(
    index, catalog
):
    """DEFECT 6: 'Bally' must not be satisfied by Bally Wulff — a separate
    Manufacturer record that merely has `bally` as a slug prefix."""
    resolution = _resolve(index, catalog, "Supersonic", maker="Bally", year=1979)
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "supersonic"


def test_stated_brand_naming_no_manufacturer_stays_lenient(index, catalog):
    """DEFECT 6's fix must not cost the leniency it was built for: 'Premier'
    names no Manufacturer record, so it still reaches a Gottlieb-brand model
    through its `premier-technology` corporate entity."""
    resolution = _resolve(index, catalog, "Arena", maker="Premier", year=1987)
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "arena"


def test_stated_brand_yields_when_that_brand_is_impossible_in_the_stated_year(
    index, catalog
):
    """DEFECT 9: the LAI shape. "Stern's 1979 'Dracula'" means Stern
    Electronics; the *modern* Stern (Stern Pinball) carries the bare name
    "Stern" and so wins DEFECT 6's exact-brand test — against a company that
    made nothing until 1999. An exact brand match may only veto a candidate
    when that brand could plausibly be the referent at the stated year."""
    resolution = _resolve(index, catalog, "Dracula", maker="Stern", year=1979)
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "dracula"


def test_stated_brand_still_vetoes_when_that_brand_is_alive_in_the_stated_year(
    index, catalog
):
    """DEFECT 9's fix must not undo DEFECT 6: Bally was very much alive in
    1979, so "Bally" naming a real brand still vetoes Bally Wulff's namesake
    rather than falling back to substring leniency."""
    resolution = _resolve(index, catalog, "Supersonic", maker="Bally", year=1979)
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "supersonic"


def test_stated_brand_with_no_stated_year_keeps_the_strict_veto(index, catalog):
    """No stated year → nothing to gate the binding with → stay strict. The
    year is the only evidence that separates a live brand from an anachronism;
    without it, DEFECT 6's exactness is the safer default."""
    resolution = _resolve(index, catalog, "Supersonic", maker="Bally")
    assert resolution.chosen is None or resolution.chosen.slug == "supersonic"


def test_subject_technology_breaks_an_em_ss_tie(index, catalog):
    """The fipermatic shape: a bare title that narrows to same-year EM/SS
    twins is settled by the SUBJECT's own technology — an EM machine is not
    built from an SS design."""
    em = catalog.by_slug("spider")  # Electromechanical
    resolution = _resolve(index, catalog, "Mata Hari", maker="Bally", subject=em)
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "mata-hari"
    assert "technology" in resolution.how

    ss = catalog.by_slug("supersonic-z")  # Solid State
    resolution = _resolve(index, catalog, "Mata Hari", maker="Bally", subject=ss)
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "mata-hari-ss"


def test_unknown_subject_technology_never_narrows(index, catalog):
    """A subject carrying no technology cannot break the tie."""
    unknown = catalog.by_slug("nero")  # technology is NULL
    resolution = _resolve(index, catalog, "Mata Hari", maker="Bally", subject=unknown)
    assert resolution.status == "ambiguous"


def test_technology_tiebreak_skipped_when_a_candidate_lacks_technology(index, catalog):
    """A tie-break, never a filter: with one candidate's technology unknown we
    would be guessing against missing data, so the tie stands."""
    em = catalog.by_slug("spider")  # Electromechanical
    resolution = _resolve(index, catalog, "Vulcan", maker="Gottlieb", subject=em)
    assert resolution.status == "ambiguous"
    assert {c.slug for c in resolution.considered} == {"vulcan-x", "vulcan-y"}


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


def test_resolve_reaches_parenthetically_suffixed_names(index, catalog):
    """DEFECT 1: a bare note title must reach a catalog name carrying a
    trailing "(...)" disambiguator the source never uses."""
    resolution = _resolve(index, catalog, "Supersonic", maker="Bally", year=1979)
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "supersonic"


def test_resolve_strips_note_side_parenthetical(index, catalog):
    resolution = _resolve(index, catalog, "Hurdy Gurdy (Italy)")
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "hurdy-gurdy"


def test_resolve_unknown_year_candidate_is_never_excluded(index, catalog):
    """DEFECT 2 (Champion shape): a year match must not beat a maker
    contradiction, and a year-unknown candidate survives the year filter."""
    resolution = _resolve(index, catalog, "Champion", maker="Bally", year=1949)
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "champion-bally"


def test_exact_name_match_breaks_title_group_ambiguity(index, catalog):
    resolution = _resolve(
        index, catalog, "King of Diamonds", maker="Gottlieb", year=1967
    )
    assert resolution.status == "unique"
    assert resolution.chosen.slug == "king-of-diamonds"
    assert "exact name" in resolution.how


def test_exact_name_tiebreak_leaves_true_same_name_pairs_ambiguous(index, catalog):
    assert _resolve(index, catalog, "Mata Hari").status == "ambiguous"


def test_resolution_trail_names_the_pre_narrow_candidates(index, catalog):
    resolution = _resolve(index, catalog, "Mata Hari", year=1978)
    assert "mata-hari" in resolution.how
    assert "mata-hari-ss" in resolution.how


# ── per-claim disposition against the edge set ───────────────────────────────


def test_misseeded_edge_splits_into_fill_and_set_but_unsupported(catalog, index):
    """spider's catalog edge is conversion→central-park; the note supports a
    conversion_kit→hurdy-gurdy. The note's target is a new fill; the stored
    edge no claim accounts for becomes set-but-unsupported."""
    ai = FakeAi(
        {
            "ipdb:5555": rels(
                rel(
                    "conversion_kit",
                    title="Hurdy Gurdy",
                    maker="Gottlieb",
                    year=1966,
                    quote="Conversion kit for Gottlieb's 1966 'Hurdy Gurdy (Italy)'.",
                )
            )
        }
    )
    rows = _run([CandidateRow(5555)], catalog, index, ai)
    fill = next(r for r in rows if r.disposition == gate.FILL)
    assert fill.resolved_slug == "hurdy-gurdy"
    unsup = next(r for r in rows if r.disposition == gate.SET_BUT_UNSUPPORTED)
    assert unsup.resolved_slug == "central-park"
    assert unsup.needs_review


def test_conflict_on_license_axis(catalog, index):
    """arena-vifico holds copy/LICENSED → arena; a note calling it UNLICENSED is
    a conflict on the license axis — the wrong-seeded-value case."""
    ai = FakeAi(
        {
            "ipdb:108": rels(
                rel(
                    "copy",
                    license="unlicensed",
                    title="Arena",
                    maker="Premier",
                    year=1987,
                    quote="Made under license from Premier's 1987 'Arena'.",
                )
            )
        }
    )
    [row] = _run([CandidateRow(108)], catalog, index, ai)
    assert row.disposition == gate.CONFLICT
    assert row.resolved_slug == "arena"
    assert any("license_status" in r for r in row.reasons)


def test_agrees_when_edge_matches_type_and_license(catalog, index):
    """rey-copy holds copy/unknown → king-of-diamonds; a matching note agrees
    (brand-vs-corporate-entity leniency also lets 'Premier' reach a Gottlieb
    machine — see the license conflict case)."""
    ai = FakeAi(
        {
            "ipdb:115": rels(
                rel(
                    "copy",
                    title="King of Diamonds",
                    maker="Gottlieb",
                    year=1967,
                    quote="A modified copy of Gottlieb's 1967 'King of Diamonds'.",
                )
            )
        }
    )
    [row] = _run([CandidateRow(115)], catalog, index, ai)
    assert row.disposition == gate.AGREES
    assert not row.needs_review


def _amb_kit_claim(license="unknown"):
    """amb-kit's note names a bare 'Mata Hari' — never narrows past the EM/SS
    pair, so resolution stays ambiguous while a catalog edge to one of them
    exists (conversion_kit/unknown → mata-hari-ss)."""
    return rels(
        rel(
            "conversion_kit",
            license=license,
            title="Mata Hari",
            maker="Bally",  # both Mata Haris are Bally — never disambiguates
            quote="Conversion kit for Bally's 'Mata Hari'.",
        )
    )


def test_ambiguous_resolution_containing_a_matching_edge_is_agreement(catalog, index):
    """An ambiguous resolution that CONTAINS a matching catalog edge is
    consistency, not doubt — every survivor fits the note's stated facts."""
    ai = FakeAi({"ipdb:4102": _amb_kit_claim()})
    [row] = _run([CandidateRow(4102)], catalog, index, ai)
    assert row.disposition == gate.AGREES
    assert not row.needs_review
    assert any("ambiguous" in reason for reason in row.reasons)


def test_ambiguous_agreement_requires_matching_license(catalog, index):
    """...but the edge must match on BOTH axes. A note supporting
    conversion_kit/LICENSED must not confirm the stored /unknown edge — and
    must not suppress that edge from surfacing as unsupported either."""
    ai = FakeAi({"ipdb:4102": _amb_kit_claim(license="licensed")})
    rows = _run([CandidateRow(4102)], catalog, index, ai)
    assert [r.disposition for r in rows] == [
        gate.AMBIGUOUS,
        gate.SET_BUT_UNSUPPORTED,
    ]
    assert all(r.needs_review for r in rows)


def test_brand_vs_corporate_entity_is_compatible(catalog, index):
    """'Premier' (corporate entity) must stay compatible with a Gottlieb-brand
    model: a copy/licensed note matches the stored copy/licensed edge → agrees."""
    ai = FakeAi(
        {
            "ipdb:108": rels(
                rel(
                    "copy",
                    license="licensed",
                    title="Arena",
                    maker="Premier",
                    year=1987,
                    quote="Made under license from Premier's 1987 'Arena'.",
                )
            )
        }
    )
    [row] = _run([CandidateRow(108)], catalog, index, ai)
    assert row.disposition == gate.AGREES
    assert row.resolved_slug == "arena"


def test_facts_mismatch_instead_of_false_green(catalog, index):
    """DEFECT 2 (Major League shape): stated maker/year contradicting the only
    catalog match must escalate, never fill."""
    ai = FakeAi(
        {
            "ipdb:103": rels(
                rel(
                    "conversion",
                    title="Major League",
                    maker="Williams",
                    year=1963,
                    quote="Conversion of Williams' 1963 'Major League'.",
                )
            )
        }
    )
    [row] = _run([CandidateRow(103)], catalog, index, ai)
    assert row.disposition == gate.FACTS_MISMATCH
    assert row.needs_review
    assert row.resolved_slug is None


def test_year_noise_of_one_is_tolerated(catalog, index):
    ai = FakeAi(
        {
            "ipdb:109": rels(
                rel(
                    "conversion_kit",
                    title="Supersonic",
                    maker="Bally",
                    year=1980,  # catalog says 1979
                    quote="Conversion kit for Bally's 1979 'Supersonic'.",
                )
            )
        }
    )
    [row] = _run([CandidateRow(109)], catalog, index, ai)
    assert row.disposition == gate.FILL
    assert row.resolved_slug == "supersonic"


def test_artwork_scoped_quote_never_greens_as_a_machine_copy(catalog, index):
    """DEFECT 7: "Backglass artwork is in part a copy of X" says the ART was
    copied, not that this MACHINE reproduces X's design. It resolves uniquely
    and quotes verbatim, so only this gate stands between it and a green."""
    ai = FakeAi(
        {
            "ipdb:4107": rels(
                rel(
                    "copy",
                    title="Aquarius",
                    maker="Gottlieb",
                    year=1970,
                    quote="Backglass artwork is in part a copy of Gottlieb's 1970 'Aquarius'",
                )
            )
        }
    )
    [row] = _run([CandidateRow(4107)], catalog, index, ai)
    assert row.disposition == gate.ASSET_SCOPED
    assert row.needs_review
    assert any("backglass was copied" in reason for reason in row.reasons)


def test_asset_scoped_quote_outranks_a_hint_disagreement(catalog, index):
    """The `jaws` specimen: a stale hint naming a DIFFERENT wrong target must
    not demote this to a mere two-sessions-disagree row. Gating it at the fill
    step let exactly that happen — the claim is not lineage at all, whatever
    the hint says."""
    ai = FakeAi(
        {
            "ipdb:4107": rels(
                rel(
                    "copy",
                    title="Aquarius",
                    maker="Gottlieb",
                    year=1970,
                    quote="Backglass artwork is in part a copy of Gottlieb's 1970 'Aquarius'",
                )
            )
        }
    )
    [row] = _run([CandidateRow(4107, hint=("central-park",))], catalog, index, ai)
    assert row.disposition == gate.ASSET_SCOPED


def test_asset_scoped_quote_never_confirms_a_seeded_edge(catalog, index):
    """And it must not AGREE with an artwork edge someone already seeded —
    silently blessing a wrong catalog value is the costlier direction."""
    ai = FakeAi(
        {
            "ipdb:4108": rels(
                rel(
                    "copy",
                    title="Aquarius",
                    maker="Gottlieb",
                    year=1970,
                    quote="Backglass artwork is in part a copy of Gottlieb's 1970 'Aquarius'",
                )
            )
        }
    )
    rows = _run([CandidateRow(4108)], catalog, index, ai)
    assert gate.ASSET_SCOPED in [r.disposition for r in rows]
    assert gate.AGREES not in [r.disposition for r in rows]


@pytest.mark.parametrize(
    ("quote", "expected"),
    [
        # The asset is the SUBJECT of the copy verb — the claim is about art.
        ("Backglass artwork is in part a copy of Gottlieb's 1970 'Scuba'", "backglass"),
        ("The playfield design appears to be a copy of Bally's 'Playboy'", "playfield"),
        ("Cabinet art is a copy of Gottlieb's 'Volley'", "cabinet"),
        # The asset trails the verb — an aside on a real machine copy. These are
        # verbatim shipped quotes (0158-rowamet, 0160-europlay); both must stay green.
        (
            "This is a copy of the EM game Gottlieb's 1977 'Vulcan' except the "
            "backglass depicts a woman instead of Vulcan, the Roman god of fire.",
            "",
        ),
        (
            "This Europlay game is a converted electromechanical Gottlieb game "
            "with a digital display and sound card added.",
            "",
        ),
        ("A copy of Gottlieb's 1977 'Jungle Queen'.", ""),
        ("Conversion kit for Bally's 1979 'Supersonic'.", ""),
    ],
)
def test_asset_scoped_quote_detection(quote, expected):
    assert gate.asset_scoped_quote(quote) == expected


def test_same_maker_copy_target_escalates(catalog, index):
    """The Big Ben (Italy) shape: a note naming the SAME maker's own game as a
    copy target is a chain link, never the licensor's original — escalate."""
    ai = FakeAi(
        {
            "ipdb:110": rels(
                rel(
                    "copy",
                    license="licensed",
                    title="Nero",
                    maker="Dama",
                    year=1982,
                    quote="the add-a-ball version of Dama's 1982 'Nero'",
                )
            )
        }
    )
    [row] = _run([CandidateRow(110)], catalog, index, ai)
    assert row.disposition == gate.SAME_MAKER
    assert row.needs_review
    assert row.resolved_slug is None


def test_same_maker_target_is_fine_for_conversions(catalog, index):
    """In-house conversions exist — the other-maker rule applies only to copies."""
    ai = FakeAi(
        {
            "ipdb:110": rels(
                rel(
                    "conversion",
                    title="Nero",
                    maker="Dama",
                    year=1982,
                    quote="the add-a-ball version of Dama's 1982 'Nero'",
                )
            )
        }
    )
    [row] = _run([CandidateRow(110)], catalog, index, ai)
    assert row.disposition == gate.FILL
    assert row.resolved_slug == "nero"


def test_hint_mismatch_routes_to_review(catalog, index):
    ai = FakeAi(
        {
            "ipdb:7777": rels(
                rel(
                    "conversion_kit",
                    title="Mata Hari",
                    year=1978,
                    quote="Conversion kit for Bally's 1978 'Mata Hari'.",
                )
            )
        }
    )
    [row] = _run([CandidateRow(7777, hint=("mata-hari",))], catalog, index, ai)
    assert row.disposition == gate.HINT_MISMATCH
    assert row.needs_review


def test_same_name_copy_fill_excludes_self(catalog, index):
    ai = FakeAi(
        {
            "ipdb:6015": rels(
                rel(
                    "copy",
                    title="Aquarius",
                    quote="A copy of Gottlieb's 1970 'Aquarius'.",
                )
            )
        }
    )
    [row] = _run([CandidateRow(6015, hint=("aquarius",))], catalog, index, ai)
    assert row.disposition == gate.FILL
    assert row.resolved_slug == "aquarius"


def test_unverbatim_quote_fails_the_gate(catalog, index):
    ai = FakeAi(
        {
            "ipdb:6015": rels(
                rel("copy", title="Aquarius", quote="a paraphrase, not the note")
            )
        }
    )
    [row] = _run([CandidateRow(6015)], catalog, index, ai)
    assert row.disposition == gate.QUOTE_FAIL


# ── the fill support gate + multi-target ─────────────────────────────────────


def test_fill_quote_must_support_the_claim(catalog, index):
    """A verbatim quote that doesn't ESTABLISH the relationship must not ship as
    a cite quote. Reuses ai_lint's quote-supports-claim rule."""
    ai = FakeAi(
        {
            "ipdb:109": rels(
                rel(
                    "conversion_kit",
                    title="Supersonic",
                    maker="Bally",
                    quote="Conversion kit",
                )
            )
        },
        supports=False,
    )
    [row] = _run([CandidateRow(109)], catalog, index, ai)
    assert row.disposition == gate.QUOTE_UNSUPPORTED
    assert row.needs_review
    assert row.quote_supported is False
    assert row.resolved_slug == "supersonic"  # the resolution itself is fine
    support_calls = [c for c in ai.calls if "CLAIM:" in c["user"]]
    assert len(support_calls) == 1
    assert "Supersonic" in support_calls[0]["user"]


def test_support_claim_asserts_a_non_unknown_license(catalog, index):
    """license_status is edge data the source must establish, so a licensed /
    unlicensed fill puts authorization in the claim the support gate checks.
    `unknown` asserts nothing about authorization, so it adds no clause."""
    ai = FakeAi(
        {
            "ipdb:6015": rels(
                rel(
                    "copy",
                    license="unlicensed",
                    title="Aquarius",
                    quote="A copy of Gottlieb's 1970 'Aquarius'.",
                )
            )
        }
    )
    _run([CandidateRow(6015)], catalog, index, ai)
    [support] = [c for c in ai.calls if "CLAIM:" in c["user"]]
    assert "WITHOUT the design owner's authorization" in support["user"]

    plain = FakeAi(
        {
            "ipdb:6015": rels(
                rel(
                    "copy",
                    title="Aquarius",
                    quote="A copy of Gottlieb's 1970 'Aquarius'.",
                )
            )
        }
    )
    _run([CandidateRow(6015)], catalog, index, plain)
    [support] = [c for c in plain.calls if "CLAIM:" in c["user"]]
    assert "authorization" not in support["user"]


def test_fill_with_supported_quote_stays_green(catalog, index):
    ai = FakeAi(
        {
            "ipdb:109": rels(
                rel(
                    "conversion_kit",
                    title="Supersonic",
                    maker="Bally",
                    quote="Conversion kit for Bally's 1979 'Supersonic'.",
                )
            )
        },
        supports=True,
    )
    [row] = _run([CandidateRow(109)], catalog, index, ai)
    assert row.disposition == gate.FILL
    assert row.quote_supported is True


def test_support_check_only_runs_for_fills(catalog, index):
    """agrees/no-claim/review rows ship no cite — no support call is spent."""
    ai = FakeAi({"ipdb:1291": rels()}, supports=False)
    [row] = _run([CandidateRow(1291)], catalog, index, ai)
    assert row.disposition == gate.NO_CLAIM
    assert row.quote_supported is None
    assert all("CLAIM:" not in c["user"] for c in ai.calls)


def test_fill_quote_naming_a_second_donor_flags_multi_target(catalog, index):
    ai = FakeAi(
        {
            "ipdb:111": rels(
                rel(
                    "conversion_kit",
                    title="Supersonic",
                    maker="Bally",
                    year=1979,
                    quote=(
                        "Conversion kit for Bally's 1978 'Mata Hari' and Bally's "
                        "1979 'Supersonic'."
                    ),
                )
            )
        }
    )
    [row] = _run([CandidateRow(111)], catalog, index, ai)
    assert row.disposition == gate.MULTI_TARGET
    assert row.needs_review
    assert any("Mata Hari" in r or "mata-hari" in r for r in row.reasons)
    assert all("CLAIM:" not in c["user"] for c in ai.calls)


def test_unquoted_common_word_model_names_do_not_trip_multi_target(catalog, index):
    subject = catalog.by_ipdb(6015)
    target = catalog.by_slug("aquarius")
    plain = "A copy of Gottlieb's 1970 'Aquarius', with different cabinet colors."
    assert (
        gate.other_models_in_quote(plain, index=index, subject=subject, target=target)
        == []
    )
    quoted = "A copy of Gottlieb's 1970 'Aquarius' and Gottlieb's 1954 'Colors'."
    assert gate.other_models_in_quote(
        quoted, index=index, subject=subject, target=target
    ) == ["colors"]


# ── multi-relationship and label targets ─────────────────────────────────────


def test_multiple_relationships_from_one_note(catalog, index):
    """The punky-willy shape: a copy of two designs → two fills from one call."""
    ai = FakeAi(
        {
            "ipdb:4101": rels(
                rel(
                    "copy",
                    title="Aquarius",
                    maker="Gottlieb",
                    year=1970,
                    quote="A copy of Gottlieb's 1970 'Aquarius'",
                ),
                rel(
                    "copy",
                    title="King of Diamonds",
                    maker="Gottlieb",
                    year=1967,
                    quote="Gottlieb's 1967 'King of Diamonds'",
                ),
            )
        }
    )
    rows = _run([CandidateRow(4101)], catalog, index, ai)
    assert len(rows) == 2
    assert {r.resolved_slug for r in rows} == {"aquarius", "king-of-diamonds"}
    assert all(r.disposition == gate.FILL for r in rows)


def test_guidance_names_only_fields_the_schema_accepts():
    """The guidance is the model's only spec of the answer shape, and the schema
    is `additionalProperties: False` — so a field name the guidance invents is
    not a typo, it is a hard row failure. (Regression: the guidance asked for
    `target_machine`, the patch-syntax name, while the schema takes
    `target_title` — every row whose model obeyed the guidance died `ai-error`.)
    """
    props = RELATIONAL_SCHEMA["properties"]["relationships"]["items"]["properties"]
    named = set(
        re.findall(r"\b(?:target|license|relationship)_[a-z_]+\b", SPEC.guidance)
    )
    assert named <= set(props), (
        f"guidance names non-schema fields: {named - set(props)}"
    )


def test_relational_schema_tolerates_null_string_fields():
    """A model that means "no value" reaches for null as readily as "" — and the
    parser already treats both as absent. Rejecting null at the schema wastes a
    whole row on a difference the parser erases."""
    payload = {
        "relationships": [
            {
                "relationship_type": "copy",
                "license_status": "unknown",
                "target_title": "Arena",
                "target_maker": None,
                "target_label": None,
                "quote": "A copy of Premier's 1987 'Arena'.",
            }
        ]
    }
    Draft7Validator(RELATIONAL_SCHEMA).validate(payload)
    [claim] = parse_claims(payload)
    assert claim.target_maker == ""
    assert claim.target_label == ""


def test_parse_claims_accepts_retheme():
    """`retheme` is a real relationship_type since the retheme edge shipped —
    a note describing one must survive parsing, not drop as an invalid type."""
    [claim] = parse_claims(
        {
            "relationships": [
                {
                    "relationship_type": "retheme",
                    "license_status": "licensed",
                    "target_title": "Supersonic",
                    "quote": "q",
                }
            ]
        }
    )
    assert claim.relationship_type == "retheme"
    assert claim.license_status == "licensed"


def test_retheme_fill_claims_the_retheme_verb(catalog, index):
    """A machine-target retheme fills like any edge, and the support check must
    put the re-theme relation — not a copy or conversion — to the model."""
    ai = FakeAi(
        {
            "ipdb:109": rels(
                rel(
                    "retheme",
                    title="Supersonic",
                    maker="Bally",
                    year=1979,
                    quote="Conversion kit for Bally's 1979 'Supersonic'.",
                )
            )
        }
    )
    [row] = _run([CandidateRow(109)], catalog, index, ai)
    assert row.disposition == gate.FILL
    assert row.relationship_type == "retheme"
    assert row.resolved_slug == "supersonic"
    [support] = [c for c in ai.calls if "CLAIM:" in c["user"]]
    assert "re-theme" in support["user"]


def test_same_maker_retheme_target_is_fine(catalog, index):
    """The Shrek shape: a maker re-skinning its OWN machine is a normal licensed
    re-theme. The other-maker rule is a copy rule and must not reach retheme."""
    ai = FakeAi(
        {
            "ipdb:110": rels(
                rel(
                    "retheme",
                    license="licensed",
                    title="Nero",
                    maker="Dama",
                    year=1982,
                    quote="the add-a-ball version of Dama's 1982 'Nero'",
                )
            )
        }
    )
    [row] = _run([CandidateRow(110)], catalog, index, ai)
    assert row.disposition != gate.SAME_MAKER
    assert row.resolved_slug == "nero"


def test_retheme_label_target_escalates(catalog, index):
    """A re-theme's donor is always a known, seeded machine: DataPatches rejects
    a `target_label` on a retheme and the DB has a CHECK to match. Greening one
    as a fill would author a patch that cannot ingest — escalate instead."""
    ai = FakeAi(
        {
            "ipdb:1291": rels(
                rel(
                    "retheme",
                    label="several late-1970s Gottliebs",
                    quote="Gottlieb produced",
                )
            )
        }
    )
    [row] = _run([CandidateRow(1291)], catalog, index, ai)
    assert row.disposition == gate.LABEL_TARGET_INVALID
    assert row.needs_review


def _label_claim():
    return rels(
        rel(
            "conversion_kit",
            label="several late-1970s Gottliebs",
            quote="Gottlieb produced",
        )
    )


def test_label_target_fill_is_support_checked(catalog, index):
    """A plural/unseeded target rides target_label and never resolves to a slug,
    so quote-supports-claim is the ONLY gate that can stand between model-written
    label prose and a patch — it must run, with the label in the claim."""
    ai = FakeAi({"ipdb:1291": _label_claim()}, supports=True)
    [row] = _run([CandidateRow(1291)], catalog, index, ai)
    assert row.disposition == gate.FILL
    assert row.target_label == "several late-1970s Gottliebs"
    assert row.resolved_slug is None
    assert row.quote_supported is True
    [support] = [c for c in ai.calls if "CLAIM:" in c["user"]]
    assert "several late-1970s Gottliebs" in support["user"]


def test_label_target_fill_with_unsupported_quote_escalates(catalog, index):
    """The label fill's quote is verbatim but establishes nothing — the same
    standard a machine fill is held to."""
    ai = FakeAi({"ipdb:1291": _label_claim()}, supports=False)
    [row] = _run([CandidateRow(1291)], catalog, index, ai)
    assert row.disposition == gate.QUOTE_UNSUPPORTED
    assert row.quote_supported is False
    assert row.needs_review


def _label_kit_claim(label):
    return rels(rel("conversion_kit", label=label, quote="Conversion kit for"))


def test_label_edge_agrees_despite_formatting_only_differences(catalog, index):
    """label-kit holds a label edge worded "several Gottlieb EM models". Case
    and punctuation are not a disagreement — normalization absorbs them, so a
    re-judge of the same note still greens."""
    ai = FakeAi({"ipdb:4103": _label_kit_claim("Several Gottlieb EM models.")})
    [row] = _run([CandidateRow(4103)], catalog, index, ai)
    assert row.disposition == gate.AGREES
    assert not row.needs_review


def test_label_edge_wording_contradiction_is_a_conflict(catalog, index):
    """...but a real word-level difference is a disagreement about the target
    itself: "unknown Williams donor" must not confirm "several Gottlieb EM
    models" just because both are conversion_kit/unknown."""
    ai = FakeAi({"ipdb:4103": _label_kit_claim("unknown Williams donor")})
    [row] = _run([CandidateRow(4103)], catalog, index, ai)
    assert row.disposition == gate.CONFLICT
    assert row.needs_review
    assert any("target_label wording" in reason for reason in row.reasons)


# ── whole-model shapes: no-claim / no-model / no-evidence ────────────────────


def test_empty_claims_and_catalog_edges_paths(catalog, index):
    ai = FakeAi(
        {
            # Catalog holds a conversion edge for spider (5555); the note here
            # supports nothing → set-but-unsupported.
            "ipdb:5555": rels(),
            # Catalog empty for hurdy-gurdy (1291) → a green net false positive.
            "ipdb:1291": rels(),
            # A hedged claim → uncertain.
            "ipdb:9002": rels(rel("conversion_kit", title="X", hedged=True, quote="q")),
        }
    )
    rows = _run(
        [CandidateRow(5555), CandidateRow(1291), CandidateRow(9002)],
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


def test_no_model_and_no_evidence(catalog, index):
    ai = FakeAi({})
    rows = _run([CandidateRow(424242), CandidateRow(9001)], catalog, index, ai)
    assert [r.disposition for r in rows] == [gate.NO_MODEL, gate.NO_EVIDENCE]
    assert ai.calls == []  # neither model reaches the judge


def test_sweep_never_leaks_hint_or_catalog_state_to_the_model(catalog, index):
    ai = FakeAi(
        {
            "ipdb:5555": rels(
                rel(
                    "conversion_kit",
                    title="Hurdy Gurdy",
                    quote="Conversion kit for Gottlieb's 1966 'Hurdy Gurdy (Italy)'.",
                )
            )
        }
    )
    _run([CandidateRow(5555, hint=("central-park",))], catalog, index, ai)
    judge_call = next(c for c in ai.calls if "CLAIM:" not in c["user"])
    assert "central-park" not in judge_call["user"]
    assert "central-park" not in judge_call["system"]
    assert judge_call["model"] == "claude-sonnet-5"  # TRUSTED_MODEL, never cheap tier


# ── regate (offline) ─────────────────────────────────────────────────────────


def _fill_row(**overrides):
    base = {
        "ipdb_id": 109,
        "disposition": gate.FILL,
        "verdict": "yes",
        "relationship_type": "conversion_kit",
        "license_status": "unknown",
        "quote": "Conversion kit for Bally's 1979 'Supersonic'.",
        "target_title": "Supersonic",
        "target_maker": "Bally",
        "target_year": 1979,
        "evidence": (("ipdb:109", _NOTES["ipdb:109"]),),
    }
    base.update(overrides)
    return SweepRow(**base)


def test_regate_preserves_quote_supported(catalog, index):
    [row] = regate_rows([_fill_row(quote_supported=True)], catalog=catalog, index=index)
    assert row.disposition == gate.FILL
    assert row.quote_supported is True

    [row] = regate_rows(
        [_fill_row(quote_supported=False)], catalog=catalog, index=index
    )
    assert row.disposition == gate.QUOTE_UNSUPPORTED


def test_regate_rebuckets_stored_answers_without_ai(catalog, index):
    stale = _fill_row(disposition=gate.UNRESOLVED, model_slug="fly-high-t")
    untouched = SweepRow(ipdb_id=424242, disposition=gate.NO_MODEL)
    regated = regate_rows([stale, untouched], catalog=catalog, index=index)
    assert regated[0].disposition == gate.FILL
    assert regated[0].resolved_slug == "supersonic"
    assert regated[0].quote_verified
    assert regated[1] == untouched  # verdict-less rows pass through unchanged


def test_regate_re_synthesizes_set_but_unsupported(catalog, index):
    """A zero-claim model that still holds a catalog edge persists ONLY
    synthesized set-but-unsupported rows — no claim row and no no-claim marker.
    Regate must re-derive those too, or they go stale against a rebuilt DB."""
    ai = FakeAi({"ipdb:5555": rels()})
    rows = _run([CandidateRow(5555)], catalog, index, ai)
    # The live shape: nothing a claim-only re-gate condition would catch.
    assert [r.disposition for r in rows] == [gate.SET_BUT_UNSUPPORTED]
    assert not any(r.is_claim for r in rows)

    # A stale stored row must come back corrected — proof it was re-derived
    # rather than passed through untouched.
    stale = replace(rows[0], disposition=gate.CONFLICT, resolved_slug="wrong")
    [regated] = regate_rows([stale], catalog=catalog, index=index)
    assert regated.disposition == gate.SET_BUT_UNSUPPORTED
    assert regated.resolved_slug == "central-park"


# ── persistence round-trip and rendering ─────────────────────────────────────


def test_row_json_round_trip(catalog, index):
    ai = FakeAi(
        {
            "ipdb:7777": rels(
                rel(
                    "conversion_kit",
                    title="Mata Hari",
                    maker="Bally",
                    year=1978,
                    quote="Conversion kit for Bally's 1978 'Mata Hari'.",
                )
            )
        }
    )
    [row] = _run([CandidateRow(7777)], catalog, index, ai)
    hydrated = row_from_json(json.loads(json.dumps(row.to_json())))
    assert hydrated == row


def test_ready_to_author_fills_grouped_by_maker(catalog, index):
    ai = FakeAi(
        {
            "ipdb:7777": rels(
                rel(
                    "conversion_kit",
                    title="Mata Hari",
                    year=1978,
                    quote="Conversion kit for Bally's 1978 'Mata Hari'.",
                )
            ),
            "ipdb:109": rels(
                rel(
                    "conversion_kit",
                    title="Supersonic",
                    maker="Bally",
                    quote="Conversion kit for Bally's 1979 'Supersonic'.",
                )
            ),
        }
    )
    rows = _run([CandidateRow(7777), CandidateRow(109)], catalog, index, ai)
    review = render_review(rows)
    assert "### dama (2)" in review  # both subjects are Dama models


def test_shared_target_fills_get_a_merge_warning(catalog, index):
    ai = FakeAi(
        {
            "ipdb:7777": rels(
                rel(
                    "conversion_kit",
                    title="Mata Hari",
                    year=1978,
                    quote="Conversion kit for Bally's 1978 'Mata Hari'.",
                )
            ),
            "ipdb:116": rels(
                rel(
                    "conversion_kit",
                    title="Mata Hari",
                    year=1978,
                    quote="Conversion kit for Bally's 1978 'Mata Hari'.",
                )
            ),
        }
    )
    rows = _run([CandidateRow(7777), CandidateRow(116)], catalog, index, ai)
    review = render_review(rows)
    assert "shared target" in review
    assert "`nero`" in review
    assert "`nero-two`" in review


def test_review_has_a_per_maker_roster(catalog, index):
    ai = FakeAi(
        {
            "ipdb:7777": rels(
                rel(
                    "conversion_kit",
                    title="Mata Hari",
                    year=1978,
                    quote="Conversion kit for Bally's 1978 'Mata Hari'.",
                )
            ),
            "ipdb:9002": rels(rel("conversion_kit", title="X", hedged=True, quote="q")),
        }
    )
    rows = _run([CandidateRow(7777), CandidateRow(9002)], catalog, index, ai)
    review = render_review(rows)
    assert "## Per-maker roster" in review
    assert "| `dama` | 1 |" in review  # 1 fill for dama
    assert "uncertain 1" in review  # the hedged claim, named by disposition


def test_model_reason_is_labeled_distinctly(catalog, index):
    ai = FakeAi(
        {
            "ipdb:5555": rels(
                rel(
                    "conversion_kit",
                    title="Hurdy Gurdy",
                    quote="Conversion kit for Gottlieb's 1966 'Hurdy Gurdy (Italy)'.",
                )
            )
        }
    )
    rows = _run([CandidateRow(5555)], catalog, index, ai)
    fill = next(r for r in rows if r.disposition == gate.FILL)
    assert any(reason.startswith("model: ") for reason in fill.reasons)


def test_render_review_sections(catalog, index):
    ai = FakeAi(
        {
            "ipdb:5555": rels(
                rel(
                    "conversion_kit",
                    title="Hurdy Gurdy",
                    quote="Conversion kit for Gottlieb's 1966 'Hurdy Gurdy (Italy)'.",
                )
            ),
            "ipdb:7777": rels(
                rel(
                    "conversion_kit",
                    title="Mata Hari",
                    year=1978,
                    quote="Conversion kit for Bally's 1978 'Mata Hari'.",
                )
            ),
        }
    )
    rows = _run([CandidateRow(5555), CandidateRow(7777)], catalog, index, ai)
    review = render_review(rows)
    assert "## Needs review (1)" in review  # spider's set-but-unsupported edge
    assert "set-but-unsupported" in review
    assert "Hurdy Gurdy (Italy)" in review  # the full note rides in the detail block
    assert "## Ready to author" in review
    assert "`mata-hari-ss`" in review


def test_progress_line_names_the_outcome(catalog, index):
    ai = FakeAi(
        {
            "ipdb:7777": rels(
                rel(
                    "conversion_kit",
                    title="Mata Hari",
                    year=1978,
                    quote="Conversion kit for Bally's 1978 'Mata Hari'.",
                )
            )
        }
    )
    rows = _run([CandidateRow(7777)], catalog, index, ai)
    line = progress_line(3, 10, rows)
    assert line == "[3/10] ipdb:7777 `nero`: fill → mata-hari-ss"


def test_render_reconcile_buckets_and_mismatches(catalog):
    from ai_corpus_sweep.sweep import reconcile_candidates

    report = render_reconcile(
        reconcile_candidates(
            [
                CandidateRow(5555, hint=("hurdy-gurdy",)),
                CandidateRow(7777),
                CandidateRow(424242),
            ],
            catalog=catalog,
        )
    )
    assert "| set | 1 |" in report
    assert "| empty | 1 |" in report
    assert "| no-model | 1 |" in report
    assert "central-park" in report  # spider's edge ≠ the prior guess
    assert "hurdy-gurdy" in report


def test_label_compare_ignores_a_leading_article():
    """DEFECT 12: a label is prose the sweep re-derives; "an electromechanical
    Gottlieb game" and "electromechanical Gottlieb game" are one wording. The
    europlay `jaws` row conflicted against a patch this campaign itself wrote.
    """
    claim = _mk_claim("", label="electromechanical Gottlieb game")
    edge = CatalogEdge(
        rel_type="conversion",
        license="unknown",
        target_slug=None,
        target_label="an electromechanical Gottlieb game",
    )
    assert gate._same_label(claim, edge)


def test_label_compare_still_sees_a_real_wording_difference():
    """The article strip must not blunt the check: "unknown Williams donor"
    must still not confirm a stored "several Gottlieb EM models"."""
    claim = _mk_claim("", label="unknown Williams donor")
    edge = CatalogEdge(
        rel_type="conversion",
        license="unknown",
        target_slug=None,
        target_label="several Gottlieb EM models",
    )
    assert not gate._same_label(claim, edge)


# ── DEFECT 11: authorization from a second source ────────────────────────────


def test_parse_claim_reads_a_license_quote():
    """A bootleg's IPDB note establishes the COPY and never the AUTHORIZATION;
    `unlicensed` asserts that second thing, and it lives in a maker-level trade
    history — a DIFFERENT source. One `quote` cannot establish both, which is
    why the shipped patches carry two cites. The claim must express that."""
    claim = parse_claims(
        {
            "relationships": [
                {
                    "relationship_type": "copy",
                    "license_status": "unlicensed",
                    "target_title": "Xenon",
                    "target_maker": "Bally",
                    "target_year": 1980,
                    "quote": "This is a copy of Bally's 1980 'Xenon'.",
                    "license_quote": "usar a Reserva de Mercado como escudo para copiar impunemente",
                    "hedged": False,
                    "reason": "r",
                }
            ]
        }
    )[0]
    assert claim.quote == "This is a copy of Bally's 1980 'Xenon'."
    assert claim.license_quote == (
        "usar a Reserva de Mercado como escudo para copiar impunemente"
    )


def test_parse_claim_without_a_license_quote_leaves_it_empty():
    """The common case: license `unknown`, nothing to establish, no second
    quote. The field must stay optional or every ordinary row breaks."""
    claim = parse_claims(
        {
            "relationships": [
                {
                    "relationship_type": "copy",
                    "license_status": "unknown",
                    "target_title": "Xenon",
                    "quote": "a copy of Bally's 1980 'Xenon'",
                    "hedged": False,
                    "reason": "r",
                }
            ]
        }
    )[0]
    assert claim.license_quote == ""


def test_license_quote_is_verified_against_the_other_evidence_source():
    """The authorization quote is verbatim in the MAKER-level source, not in
    the model's own note — so it must be verified across all evidence, exactly
    as the primary quote is."""
    evidence = (
        ("ipdb:4592", "This is a copy of Bally's 1980 'Xenon'."),
        (
            "https://augustocampos.net/taito-brasil",
            "a LTD, sediada em Campinas, usava a Reserva de Mercado como escudo "
            "para copiar impunemente a tecnologia do exterior.",
        ),
    )
    ok, ref = sweep_mod._verify_quote("usar a Reserva de Mercado como escudo", evidence)
    assert not ok  # not verbatim — "usava", not "usar"
    ok, ref = sweep_mod._verify_quote(
        "usava a Reserva de Mercado como escudo para copiar impunemente", evidence
    )
    assert ok
    assert ref == "https://augustocampos.net/taito-brasil"
