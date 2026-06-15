# 0010 game-formats — authoring record

Marks the catalog entries that IPDB's notes identify as **not pinball** with a
`game_format` (slot-machine, video-game, gun-game, shuffle, bagatelle, or the
`miscellaneous` catch-all). Pinball machines are deliberately left null.

Two patches:

- **`0009-game-format-vocab.yaml`** — creates the four new formats. **Hand-written**,
  not generated: four static rows with no guards/notes/cites, so a generator buys
  nothing (the "handful of static edits -> hand-write" rule).
- **`0010-game-formats.yaml`** — the 135 per-model assignments, **generated** by
  `gen.py` (live `expect:` guards, verbatim notes, cites — where a generator earns
  its keep).

This is the worked reference for the patch-authoring workflow (flipcommons
`docs/DataPatchAuthoring.md`), using the shared `../patchkit.py` helper.

**Attribution `flipcommons-catalog`, citing `ipdb`.** IPDB has no game_format
field, so there is no IPDB claim to supersede — deriving a structured format by
classifying IPDB's free-text notes is flipcommons' own editorial work. Each
assignment still carries `cite: ipdb:<id>`, because the IPDB sentence is the
actual evidence. The vocab patch 0009 is `flip-museum` (the categories are
museum-defined).

## Pipeline

1. **`classify.py`** (run from **pinexplore**, reads `explore.duckdb`) — takes every
   model IPDB self-labels "not a pinball", extracts the verbatim sentence that
   names the device, assigns a format, and writes **`worksheet.csv`**. Holds the
   hand-verified `OVERRIDES` (keyword false positives) and `EXCLUDE` (real
   pinballs the signal mislabeled).
2. **`xref_sweep.py`** (pinexplore) — sweeps all notes for "‹other game› is not a
   pinball"; surfaced Hyperball, whose own note never self-labels. Its row is the
   `CROSS_REF` entry in `classify.py`, cited to the *referencing* record.
3. **`gen.py`** (run from **flipcommons/backend**) — reads `worksheet.csv`, looks
   up live slugs/`ipdb_id`s for the `expect:` guards, emits `0010-game-formats.yaml`
   via `patchkit`:

   ```bash
   cd flipcommons/backend
   uv run python ../../pindata/patches/authoring/0010-game-formats/gen.py
   ```

## Signal + judgment

- Only signal: IPDB Notes that **self-label** "not a pinball" (OPDB has no format
  data). Format assigned **only from verbatim IPDB prose** that names the device —
  no inferred categories.
- 135 labeled; 4 excluded as false positives — Af-Tor, Chicago Cubs (real pinball,
  the phrase is about Williams' Hyperball), New Crazy 15 (ambiguous, phrase is about
  a sibling game), and Chuck-O-Luck (negation — IPDB explicitly declined to call it
  non-pinball). pitch-and-bat ends up unused (real baseball games aren't ones IPDB
  flags non-pinball).
