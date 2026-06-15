# 0011 game-formats — authoring record

Positively labels **pitch-and-bat**, **shuffle** and **bagatelle** games that
[0010](../0010-game-formats/) left null. 0010 only labeled the 136 models IPDB
*self-flags* "not a pinball"; real pitch-and-bat bat-games, shuffle alleys and
antique bagatelles are catalogued by IPDB **without** that disclaimer, so they
stayed null.

One patch, assignment-only — **no vocab patch**: the `pitch-and-bat`, `shuffle`
and `bagatelle` GameFormat rows already exist (created in 0009). Uses the shared
[`../patchkit.py`](../patchkit.py) helper.

**Attribution `flipcommons-catalog`, citing `ipdb`.** IPDB has no game_format
field, so there is no IPDB claim to supersede — deriving a structured format by
parsing IPDB prose is flipcommons' own editorial work. Each entry still carries
`cite: ipdb:<id>`, because the IPDB sentence is the actual evidence.

## Pipeline

1. **`classify.py`** (run from **pinexplore**, reads `explore.duckdb`) — applies
   the positive signal to every catalogued IPDB model, excludes every ipdb_id
   0010 already labeled, and writes **`worksheet.csv`**. The editorial judgment
   is the `INCLUDE` dict (`ipdb_id -> (format, needle)`); the quote is re-extracted
   live as the sentence containing the needle, and must contain the format keyword
   (faithfulness guard). `FLAGGED` and `REJECTED` record the dead-ends.

   ```bash
   cd pinexplore
   uv run --active python ../pindata/patches/authoring/0011-game-formats/classify.py
   ```

2. **`gen.py`** (run from **flipcommons/backend**) — reads `worksheet.csv`, looks
   up live slugs/`ipdb_id`s for the `expect:` guards, emits `0011-game-formats.yaml`
   via `patchkit`:

   ```bash
   cd flipcommons/backend
   uv run python ../../pindata/patches/authoring/0011-game-formats/gen.py
   ```

## Signal + judgment

- **Positive prose only.** A sentence in the game's **own** IPDB notes that names
  the mechanism *and* is about *this* game:
  - **pitch-and-bat** — "Player bats the ball airborne into the bleachers",
    "pitch & bat" / "Pitch and Bat buttons", self-describing "… bat game".
  - **shuffle** — "miniature shuffle alley", "refers to this … as 'Shuffle Board'".
  - **bagatelle** — the game *itself* called a bagatelle ("this bagatelle is …",
    "X bagatelles of circa/copyright YYYY", "vertical playfield bagatelle").
- **33 labeled**: pitch-and-bat 16, bagatelle 15, shuffle 2.
- **Traps handled** (see `REJECTED` in `classify.py`): a baseball *name* is not a
  bat game (Soc-A-Ball "not a bat game", Lite-League "no bat … represented by
  lights"); keyword cross-references read in context (Red Ball's "rebound
  shuffleboard" is about *Bumper Shuffle*); puck/hockey *backbox animations* and
  *mini-bagatelle features* on real pinballs (PIN·BOT, Jungle Lord, Big Guns) are
  not the game's format; a flipper machine playing a bowling *theme* is not a
  shuffle alley (Strikes N' Spares — "strengthened flipper assembly", DMDs — left
  null); phantom listings (Double Play) skipped.
- **3 FLAGGED, left null** — a bat/baseball name but no own-note mechanism prose
  (Bat-A-Ball, Junior League Bat-A-Ball, The Pitcher's Battle). An honest unknown
  beats a wrong format.
