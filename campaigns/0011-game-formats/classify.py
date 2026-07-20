"""Worksheet generator: positively label pitch-and-bat / shuffle / bagatelle.

Patch 0010 labeled game_format only for the models IPDB *self-flags* "not a
pinball". Real pitch-and-bat bat-games, shuffle alleys and antique bagatelles are
catalogued by IPDB WITHOUT that disclaimer, so 0010 left them null. This patch
(0011) assigns those three formats off a POSITIVE IPDB signal: a sentence in the
game's own notes that names the mechanism AND is about THIS game.

The editorial judgment is frozen as the INCLUDE dict below: ipdb_id -> (format,
needle). The quote is re-extracted live as the sentence containing `needle`, so
it stays faithful to the current IPDB text; the needle must also appear in that
sentence's format keyword (asserted), guarding against a quote that names the
mechanism for a *different* game (the cross-reference trap).

Reads explore.duckdb, joins to flipcommons `models` (so only catalogued games
count), excludes every ipdb_id 0010 already labeled, and writes worksheet.csv.
No YAML here; that is gen.py (a second step, backend-side).
"""

import csv
import re
from collections import Counter
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
con = duckdb.connect("explore.duckdb", read_only=True)

# ipdb_ids 0010 already labeled - never re-label them.
LABELED_0010 = {
    int(r["ipdb_id"])
    for r in csv.DictReader(
        (HERE.parent / "0010-game-formats" / "worksheet.csv").open()
    )
}

# --- the vetted assignments: ipdb_id -> (format_slug, sentence needle) ---------
# Each needle is a substring unique to the evidence sentence in THAT game's own
# notes. The quote is re-extracted as the sentence containing the needle.
INCLUDE: dict[int, tuple[str, str]] = {
    # pitch-and-bat: the recurring mechanism template + self-describing prose.
    2910: ("pitch-and-bat", "bats the ball airborne"),  # Bat-A-Score
    5574: ("pitch-and-bat", "bats the ball airborne"),  # Batting Practice (Scientific)
    6036: ("pitch-and-bat", "bats the ball airborne"),  # Batting Practice (Irving Kaye)
    2442: ("pitch-and-bat", "bats the ball airborne"),  # Deluxe Super Slugger
    5966: ("pitch-and-bat", "bats the ball airborne"),  # Dingbat
    4767: ("pitch-and-bat", "bats the ball airborne"),  # Home Run
    3502: ("pitch-and-bat", "bats the ball airborne"),  # Star Slugger
    4737: ("pitch-and-bat", "bats the ball airborne"),  # Star Super Slugger
    4897: ("pitch-and-bat", "bats the ball airborne"),  # Super Home Run
    5507: ("pitch-and-bat", "bats the ball airborne"),  # Texas Leaguer
    350: ("pitch-and-bat", "last bat game from this manufacturer"),  # Bonus Baseball
    661: ("pitch-and-bat", "backglass on this bat game"),  # De Luxe World Series
    3209: ("pitch-and-bat", "Pitch and Bat buttons"),  # League Leader
    3335: ("pitch-and-bat", "pitch & bat' baseball game"),  # Pennant Fever
    4700: ("pitch-and-bat", "other pitch & bats"),  # Pitch'Em & Bat'Em
    6813: (
        "pitch-and-bat",
        "Hit a ball that come from pitcher by the bat",
    ),  # Base Ball (Komaya)
    # shuffle: the game described as a shuffle alley / shuffle board / bowler.
    3661: ("shuffle", "miniature shuffle alley"),  # Bowlette
    3245: (
        "shuffle",
        "documentation refers to this Model 120",
    ),  # Shuffle-King (Shuffle Board)
    # bagatelle: the game ITSELF described as a bagatelle (not a pinball with a
    # mini-bagatelle feature, which we exclude - see REJECTED below).
    4944: ("bagatelle", "Corinthian Bagatelle Association"),  # "Corinthian" 21T
    5375: ("bagatelle", "This bagatelle has a shooter lane"),  # Corinthian Twinity
    5681: ("bagatelle", "dates this bagatelle"),  # Berlin Or Bust
    5997: ("bagatelle", "This bagatelle is a pin table"),  # Black Beauty Game
    1040: ("bagatelle", "Gold Star bagatelles of circa 1933"),  # Gold Star (circa 1933)
    4898: ("bagatelle", "Gold Star bagatelles of copyright 1934"),  # Gold Star (1934)
    4758: ("bagatelle", "first bagatelle game"),  # Hy-Ball
    5521: ("bagatelle", "rarest model of all"),  # Indian Chief
    5431: ("bagatelle", "Vertical playfield bagatelle"),  # Pickwick (1901)
    5432: ("bagatelle", "Vertical playfield bagatelle"),  # Pickwick (Improved)
    4894: ("bagatelle", "This bagatelle also includes"),  # Poker Ball
    6049: ("bagatelle", "each example of this bagatelle"),  # Skill Ball Junior
    5357: ("bagatelle", "French-Chinese bagatelle"),  # Unknown (French-Chinese)
    4820: ("bagatelle", "Parlor Bagatelle"),  # Unknown ("Three Bell")
    5797: ("bagatelle", "this bagatelle came in two sizes"),  # Whoopee Game (1932)
}

# Keyword that the chosen quote must contain, per format (faithfulness guard).
FORMAT_KEYWORD = {
    "pitch-and-bat": re.compile(r"\bbat|\bpitch", re.IGNORECASE),
    "shuffle": re.compile(r"shuffle|bowl", re.IGNORECASE),
    "bagatelle": re.compile(r"bagatelle", re.IGNORECASE),
}

# Considered and deliberately LEFT NULL. The worksheet records these so the
# signal we relied on is auditable against the ones we ruled out.
#
# FLAGGED - a bat/baseball NAME but no own-note prose describing the mechanism.
# Name != mechanism, so an honest null beats a guess.
FLAGGED: dict[int, str] = {
    6022: "Bat-A-Ball (1946): named a bat game, but own note only says 'floor-standing upright game' - no mechanism prose.",
    4675: "Junior League Bat-A-Ball (1946): counter version of 6022; same, no mechanism prose.",
    5923: "The Pitcher's Battle (1935): a baseball 'Game Board' (24x14x3 in); device type unclear, no pitch-and-bat or bagatelle prose.",
}

# REJECTED - the keyword fired but the sentence is a cross-reference, a feature on
# a real pinball, or an explicit negation. Representative cases (not exhaustive).
REJECTED: list[tuple[int, str, str]] = [
    (
        4336,
        "Strikes N' Spares (1995)",
        "IPDB notes a 'strengthened flipper assembly' and DMD displays - a Gottlieb System 3 flipper machine playing a bowling theme, not a shuffle alley. Left null (pinball default).",
    ),
    (
        5108,
        "Lite-League (1946)",
        "FEATURES: 'No pins, no balls, no plunger, no bat' - lights, not a bat game.",
    ),
    (
        3067,
        "Double Play (1965)",
        "Phantom listing ('cannot find any evidence'); 'bat game' is a cross-ref to 'Big League'.",
    ),
    (6722, "Soc-A-Ball", "Own note: 'This is not a bat game.'"),
    (
        3593,
        "Batman Forever (1995)",
        "Matched 'Batwing Ball Cannon' - a real Williams/Bally pinball.",
    ),
    (
        1254,
        "Humpty Dumpty (1947)",
        "The first flipper pinball; note cross-refs bats on other baseball games.",
    ),
    (
        225,
        "Bermuda (1947)",
        "A pinball; note recounts an anecdote about putting a bat on a pinball.",
    ),
    (
        2501,
        "Target Gallery (1962)",
        "'Batting an errant ball into a horseshoe' is incidental, not the game's mechanism.",
    ),
    (
        5751,
        "Pool Alley",
        "'looks like a traditional puck bowler or ball bowler but it is neither.'",
    ),
    (
        1932,
        "Red Ball (1959)",
        "'rebound shuffleboard game' is a cross-ref to 'Bumper Shuffle', not Red Ball.",
    ),
    (
        722,
        "Double-Shuffle (1949)",
        "'puck moves across shuffleboard' is backglass animation on a themed pinball.",
    ),
    (
        1709,
        "Olympic Hockey (1972)",
        "'puck moves across hockey rink' is backglass animation on a themed pinball.",
    ),
    (
        1260,
        "Ice Fever",
        "'puck slides into the net' is backbox animation on a themed pinball.",
    ),
    (
        1796,
        "PIN-BOT (1986)",
        "'bagatelle mini-playfield' is a feature on a pinball, not a bagatelle game.",
    ),
    (
        1338,
        "Jungle Lord (1981)",
        "'ball in a mini-bagatelle' is a feature on a pinball.",
    ),
    (
        250,
        "Big Guns (1987)",
        "'captive ball is shot into a bagatelle for a bonus' is a feature on a pinball.",
    ),
]


def sentences(text: str) -> list[str]:
    text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]


def sentence_with(blob: str, needle: str) -> str:
    for s in sentences(blob):
        if needle.lower() in s.lower():
            return s
    return ""


def to_ascii(s: str) -> str:
    repl = {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "…": "..."}
    for k, v in repl.items():
        s = s.replace(k, v)
    return s.encode("ascii", "ignore").decode("ascii")


# The IPD header ("<id> / <date> / <n> Player(s)") sits in AdditionalDetails with
# no terminal punctuation, so the splitter glues it to the next sentence. Drop it.
_IPD_HEADER = re.compile(r"^\s*\d+\s*/[^.]*?\bPlayers?\b\s*")


def clean_quote(quote: str, limit: int = 240) -> str:
    """Strip the IPD header prefix and truncate long run-ons at a word boundary."""
    quote = _IPD_HEADER.sub("", quote).strip()
    # Drop scaffolding that introduces a quoted passage ("... translates as
    # follows: "<text>") so we quote the supporting sentence itself, not the
    # framing - avoids a dangling inner quote that reads as complete.
    intro = re.match(r'^.*?:\s*"(.+)$', quote)
    if intro:
        quote = intro.group(1).strip()
    if len(quote) > limit:
        quote = quote[:limit].rsplit(" ", 1)[0].rstrip(",;:") + " [...]"
    return quote


# Pull every catalogued IPDB model's prose (joined to flipcommons models).
rows = {
    ipdb_id: (slug, title, blob)
    for ipdb_id, slug, title, blob in con.execute(
        """
        SELECT m.IpdbId, fc.slug, m.Title,
               coalesce(m.Notes,'') || ' ' || coalesce(m.AdditionalDetails,'') || ' ' || coalesce(m.NotableFeatures,'')
        FROM ipdb_machines m JOIN models fc ON fc.ipdb_id = m.IpdbId
        """
    ).fetchall()
}

out = []
problems = []
for ipdb_id, (fmt, needle) in INCLUDE.items():
    if ipdb_id in LABELED_0010:
        problems.append(f"{ipdb_id}: already labeled by 0010 - must not re-label")
        continue
    if ipdb_id not in rows:
        problems.append(f"{ipdb_id}: not a catalogued flipcommons model")
        continue
    slug, title, blob = rows[ipdb_id]
    quote = sentence_with(blob, needle)
    if not quote:
        problems.append(
            f"{ipdb_id} ({title}): needle '{needle}' not found in IPDB text"
        )
        continue
    if not FORMAT_KEYWORD[fmt].search(quote):
        problems.append(f"{ipdb_id} ({title}): quote lacks {fmt} keyword: {quote!r}")
        continue
    out.append(
        {
            "ipdb_id": ipdb_id,
            "fc_slug": slug,
            "title": title,
            "format": fmt,
            "rule": "positive-prose",
            "cite_ipdb": ipdb_id,  # evidence is in the game's own note
            "quote": clean_quote(to_ascii(quote)),
        }
    )

if problems:
    raise SystemExit("CLASSIFY PROBLEMS:\n  " + "\n  ".join(problems))

out.sort(key=lambda r: (r["format"], r["title"]))
with (HERE / "worksheet.csv").open("w", newline="") as f:
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
print(f"Labeled: {len(out)}")
for fmt, n in dist.most_common():
    print(f"  {fmt:16s} {n}")
print(f"\nFLAGGED (left null): {len(FLAGGED)}")
for ipdb_id, why in FLAGGED.items():
    print(f"  {ipdb_id}: {why}")
print(f"\nREJECTED (representative): {len(REJECTED)}")
for ipdb_id, title, why in REJECTED:
    print(f"  {ipdb_id} {title}: {why}")
