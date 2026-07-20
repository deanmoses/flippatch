"""Worksheet generator: classify IPDB 'not a pinball' models into game formats.

Reads explore.duckdb, takes every model IPDB self-labels "not a pinball"
(ipdb_non_pinball_signals.explicit_not_pinball) that is present in flipcommons
(models.ipdb_id), and for each extracts the verbatim IPDB sentence that names
what the game actually is. Format is assigned from that verbatim prose; rows
with no positive device-type phrase fall to the 'miscellaneous' catch-all
(cited to IPDB's verbatim 'not a pinball' wording).

Output: worksheet.csv (auditable worksheet) + a summary.
No YAML is emitted here; that is a second step after review.
"""

import csv
import re
from collections import Counter

import duckdb

con = duckdb.connect("explore.duckdb", read_only=True)

rows = con.execute(
    """
    SELECT m.IpdbId AS ipdb_id, fc.slug AS fc_slug, m.Title,
           coalesce(m.Notes,'') AS notes,
           coalesce(m.AdditionalDetails,'') AS details,
           coalesce(m.NotableFeatures,'') AS features
    FROM ipdb_non_pinball_signals m
    JOIN models fc ON fc.ipdb_id = m.IpdbId
    WHERE m.explicit_not_pinball
    ORDER BY m.Title
    """
).fetchall()


def sentences(text: str) -> list[str]:
    """Split note text into sentences, normalizing CR/LF and whitespace."""
    text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    # split on sentence boundaries but keep it simple
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


# Format rules, in priority order. Each: (format_slug, compiled keyword regex).
# The first matching device-type phrase wins. Phrases are deliberately specific
# device descriptors, not theme words.
RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "slot-machine",
        re.compile(
            r"slot machine|one-armed bandit|operates like a slot", re.IGNORECASE
        ),
    ),
    (
        "shuffle",
        re.compile(
            r"shuffle alley|shuffle ?board|\bbowler\b|bowling alley|puck bowler|\bbowling\b",
            re.IGNORECASE,
        ),
    ),
    (
        "pitch-and-bat",
        re.compile(
            r"pitch[- ]and[- ]bat|pitch.{0,4}bat|baseball game|\bbaseball\b",
            re.IGNORECASE,
        ),
    ),
    (
        "gun-game",
        re.compile(
            r"shooting gallery|\brifle\b|gun game|\bgun\b|target shooting",
            re.IGNORECASE,
        ),
    ),
    ("video-game", re.compile(r"video game|video arcade", re.IGNORECASE)),
    ("bagatelle", re.compile(r"bagatelle", re.IGNORECASE)),
]

NOT_PINBALL_RE = re.compile(r"[^.!?]*not a pinball[^.!?]*[.!?]", re.IGNORECASE)

# False positives in the explicit_not_pinball signal. Two mechanisms:
#  - Cross-reference: the "not a pinball" phrase is about a *different* game named in
#    the text. Af-Tor/Chicago Cubs call THEMSELVES "the first/second pinball machine
#    with alphanumeric displays" (the phrase is about Williams' Hyperball); New Crazy
#    15's phrase is about a sibling game "Pop Up".
#  - Negation: the note DECLINES to call it non-pinball. Chuck-O-Luck (511) - "it
#    does have pins, pinballs, and a ball shooter, therefore we did not classify it
#    as Not A Pinball" - is a pinball/pachinko-like that IPDB explicitly kept.
# Leave these unlabeled (honest null) rather than mislabel a real pinball.
# See README.md for the full audit narrative.
EXCLUDE: set[int] = {25, 502, 6786, 511}

# Hand-verified corrections where the keyword auto-match fired on a cross-reference
# to another game, or where the real device type differs from the theme word in the
# name. ipdb_id -> (format_slug, sentence_substring); the quote is re-extracted as
# the sentence containing the substring, so it stays faithful to the live IPDB text.
OVERRIDES: dict[int, tuple[str, str]] = {
    6433: (
        "miscellaneous",
        "a disc is used instead of a ball",
    ),  # Skill Derby (horse-race disc game), not gun
    2180: (
        "miscellaneous",
        "a disc is used instead of a ball",
    ),  # Skill Derby replay model
    6508: ("miscellaneous", "wall game"),  # Bally Alley: wall game, not shuffle
    6509: ("miscellaneous", "wall game"),  # Bally Lane: wall game, not shuffle
    6524: (
        "shuffle",
        "puck game",
    ),  # Bally Baseball: puck game (correct fmt, fix quote)
    6129: ("miscellaneous", "arcade game"),  # Magic Baseball: arcade game, not bat
    3025: ("slot-machine", "console slot machine"),  # Club House: fix quote
    5392: (
        "miscellaneous",
        "not sure how this game shoots",
    ),  # Pin Boy Bowling: mechanism unknown
    6132: (
        "shuffle",
        "puck is slid across the playfield",
    ),  # 5th Inning: puck game, not bat
    3239: (
        "miscellaneous",
        "re-designated this listing as Not A Pinball",
    ),  # phantom listing
    # Auto-quote described the rebound shuffleboard *sibling*; the "neither a shuffle
    # board" sentence is about a pictured specimen IPDB suspects is operator-modified.
    # Quote the clean categorical opening line about the listed machine instead.
    5976: (
        "miscellaneous",
        "not a pinball but is included here for clarification",
    ),  # Bulls-Eye Drop Ball (Upright): hybrid oddity
    # "video game" was describing the cabinet SHAPE only; it is an EM game with
    # physical balls in a 33-hole pop-up array.
    3181: (
        "miscellaneous",
        "not a pinball machine but is included",
    ),  # Joker's Wild: not actually video
}


def sentence_with(blob: str, needle: str) -> str:
    for s in sentences(blob):
        if needle.lower() in s.lower():
            return s
    return ""


def classify(
    ipdb_id: int, notes: str, details: str, features: str
) -> tuple[str, str, str]:
    """Return (format_slug, verbatim_quote, matched_rule)."""
    blob = " ".join([notes, details, features])
    if ipdb_id in OVERRIDES:
        fmt, needle = OVERRIDES[ipdb_id]
        quote = sentence_with(blob, needle)
        return fmt, quote, "override"
    sents = sentences(blob)
    for fmt, rx in RULES:
        for s in sents:
            if rx.search(s):
                return fmt, s, fmt
    # catch-all: pick the best 'not a pinball' sentence. Prefer one that refers
    # to THIS game (self-ref cue) and does not merely name another quoted title.
    cands = [
        s
        for s in sentences(blob)
        if re.search(r"not a pinball|not pinball", s, re.IGNORECASE)
    ]
    if cands:

        def score(s: str) -> tuple[int, int, int]:
            self_ref = bool(
                re.search(
                    r"\b(this game|this is|this machine|we |classif|reclassif|marking this)\b",
                    s,
                    re.IGNORECASE,
                )
            )
            other_game = bool(re.search(r"'[^']{2,}'", s))  # a quoted other title
            return (int(self_ref), -int(other_game), -len(s))

        quote = max(cands, key=score)
    else:
        quote = ""
    return "miscellaneous", quote, "catch-all"


def to_ascii(s: str) -> str:
    """Plain-ASCII the quote per DataPatches guidance (no smart quotes / mojibake)."""
    repl = {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "…": "..."}
    for k, v in repl.items():
        s = s.replace(k, v)
    return s.encode("ascii", "ignore").decode("ascii")


# Cross-reference additions: games whose OWN note never self-labels, but which
# another entry's note identifies as not-a-pinball. The fact (and thus the cite)
# lives in the *referencing* entry, so cite_ipdb differs from the model's own id.
# Found via xref_sweep.py. Hyperball is the only in-catalog case.
CROSS_REF = [
    {
        "ipdb_id": 3169,  # hyperball's own id (used for the expect guard / entity ref)
        "fc_slug": "hyperball",
        "title": "Hyperball",
        "format": "miscellaneous",
        "rule": "cross-ref",
        "cite_ipdb": 25,  # Af-Tor's entry, which contains the statement
        "quote": "An earlier game, Williams' 1981 'Hyperball', had an alpha-numeric display but is Not A Pinball.",
    },
]

out = []
excluded = []
for ipdb_id, fc_slug, title, notes, details, features in rows:
    if ipdb_id in EXCLUDE:
        excluded.append((ipdb_id, title))
        continue
    fmt, quote, rule = classify(ipdb_id, notes, details, features)
    out.append(
        {
            "ipdb_id": ipdb_id,
            "fc_slug": fc_slug,
            "title": title,
            "format": fmt,
            "rule": rule,
            "cite_ipdb": ipdb_id,  # own-note labels cite their own entry
            "quote": to_ascii(quote)[:300],
        }
    )

out.extend(CROSS_REF)

with open("worksheet.csv", "w", newline="") as f:
    w = csv.DictWriter(
        f,
        fieldnames=[
            "ipdb_id",
            "fc_slug",
            "title",
            "format",
            "rule",
            "cite_ipdb",
            "quote",
        ],
    )
    w.writeheader()
    w.writerows(out)

# Summary
dist = Counter(r["format"] for r in out)
print(f"Labeled: {len(out)}  (excluded false positives: {len(excluded)})")
for ipdb_id, title in excluded:
    print(f"  EXCLUDED {ipdb_id} {title}")
for fmt, n in dist.most_common():
    print(f"  {fmt:20s} {n}")
print()
print("=== catch-all rows (no positive device phrase) ===")
for r in out:
    if r["format"] == "miscellaneous":
        print(f"  {r['ipdb_id']:>5} {r['title'][:40]:40s} | {r['quote'][:80]}")
