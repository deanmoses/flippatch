# 0172 — Bingo game format

Sets `game_format = bingo-pinball` on the catalog's bingo machines. This directory is the audit trail: how the candidate set was detected and vetted.

## The candidate hunt: [bingo.sql](bingo.sql)

A read-only DuckDB analysis over the live flipcommons catalog. It reuses flipcommons' shared DuckDB layer **verbatim**: the decode foundation (`scripts/analysis/catalog.sql`, pulled in by a `.read`) and its runner (`scripts/analysis/analysis`) — we keep no copy of either. `make analyze` sets cwd to the flipcommons checkout (so the `.read` and the foundation's `ATTACH` resolve) and delegates to that runner, which prints the `analysis_context` watermark + `bingo_summary` and **gates on `bingo_checks`** (nonzero exit on any row):

```bash
F=campaigns/0172-bingo-game-format/bingo.sql
make analyze FILE=$F PREFIX=bingo                              # watermark + summary, gated on checks
make analyze FILE=$F Q="FROM bingo_candidates ORDER BY maker, name;"   # ad-hoc query (bypasses runner)
make analyze FILE=$F Q="FROM bingo_review;"                    # human-review queue, notes inline
make analyze FILE=$F Q="FROM bingo_excluded_review;"          # the false positives, auditable
```

Requirements: the `duckdb` CLI on `PATH` and the flipcommons dev DB (`../flipcommons/backend/db.sqlite3`, overridable with `FLIPCOMMONS_DIR`). Nothing is written or persisted; every count is a live snapshot — the SQL is the source of truth for the candidate list, re-derived on each run rather than frozen into an exported file. (`gen.py` reads the `bingo_patch_rows` view as JSON via the raw `duckdb` CLI, since the runner is for interactive summary/checks, not machine-readable dumps.)

## How candidates are detected

Bingo membership lives in IPDB free text and catalog structure, but no single signal is enough, so `bingo_candidates` is the **union of five detectors** minus a hand-vetted exclusion list:

- **`by_word`** — the notes / notable_features / description say "bingo". Precise on the makers' own history, but **low recall**: about half the real bingos never use the word, and it drags in non-bingos whose text merely mentions bingo (poker novelties, one-ball precursors, the "Bingo Novelty Mfg Co." company name, gambling-law history).
- **`by_struct`** — the notable_features PROSE carries the hole grid (18/20/21/24/25/28) **plus** a card count or a Bally/United feature name (Magic Squares/Screen/Line, Mystic Lines, in-line). The conjunct keeps the noisier counts (which include 1940s one-ball payout & ticket games) from matching.
- **`by_hole25`** — the **structured** `trap-holes` gameplay-feature = 25, the 5×5 card grid. Near-definitive (173 models carry it, none with a non-bingo format) and needs no conjunct; it catches modern machines whose prose lost the hole text. Only 25 is safe bare — other counts ride `by_struct`.
- **`by_maker`** — a model by a **verified bingo-only manufacturer** (`_bingo_maker`: SIRMO, Splin, WIMI, G.A.A., SG, TSCC). Catches the modern electronic six-card machines with no hole prose and no "bingo" word — invisible to the other three. NB: "0 non-bingo formats" alone does **not** prove bingo-only (a pinball maker like Recel/Playmatic shows the same, because `game_format` is sparsely populated); each maker here was verified by inspecting its whole catalog.
- **`by_lineage`** — a model with a `model_edges` relationship (conversion / variant / copy / retheme) whose target is a **core bingo** (one of the four signals above). Catches converted bingos that describe themselves only through their donor — e.g. Bally _Bamboo_, a repainted _Orient_ — with no bingo word, hole prose, or bingo-only maker. Keyed on the core set, not the applied `game_format`, so it reproduces without the patch applied. Genre-preserving for these edge types, but review each (a conversion _can_ change type; the precision check found none doing so).

All are heuristics; every row still wants source review before it becomes a claim. `bingo_checks` includes **anchor checks** — one known example per detector (Coney Island/word, Acapulco/struct+hole25, Penalty One Ball/maker, Bamboo/lineage) that fails the run if a detector goes dark, e.g. from a renamed foundation column (which happened twice this campaign: `model→models`, `notes→ipdb_notes`).

## The vetting (reproducible, in `bingo.sql`)

The human review is encoded as lookups in the analysis's reference section, keyed by model id, so re-running re-derives the _vetted_ list — `bingo_checks` flags any lookup that has gone stale:

- **`_bingo_excluded`** — confirmed false positives a detector caught (with the reason): poker/keno consoles and pop-up novelties reusing a 25-hole grid, "pin table" games, the pre-1951 lite-a-line precursors, company-name mentions, and cross-reference FPs (e.g. the flipper-pin `serenade-3`).
- **`_bingo_bucket`** — ambiguous cases kept as candidates but tagged for editorial context: `one-ball`, `word-bingo` (Bally Crosswords / Spelling-Bee), `hybrid` (Williams combination bingo+pinball). Everything else is `core`.
- **`_bingo_maker`** — the verified bingo-only manufacturers for `by_maker`.

## Generating the patch: [gen.py](gen.py)

`gen.py` reads `bingo.sql`'s `bingo_patch_rows` view (via the duckdb CLI, cwd = the flipcommons checkout) and emits the single `patches/0172-bingo-game-format.yaml`, attributed to `flipcommons-catalog`. Three evidence patterns, all self-contained:

- **struct rows** — a `note:` reasoning from the model's own `trap-holes`/`gobble-holes` count, **no cite** (evidence is the catalog's own data, so a cite would mislead — DataPatchAuthoring.md).
- **maker rows** — a `note:` reasoning from the bingo-only manufacturer (the modern six-card machines), **no cite**.
- **word rows** — `cite: ipdb:<id>` with a hand-authored verbatim "bingo" quote (the `WORD_QUOTES` table in `gen.py`; `make verify-quotes` gates each). Flagged rows add a short bucket note.

```bash
uv run python3 campaigns/0172-bingo-game-format/gen.py
make validate          # structural + editorial lint
make verify-quotes     # every cite quote verbatim vs the IPDB corpus
```

## Status

- **Full recall sweep done.** `patches/0172-bingo-game-format.yaml`, **311 entries** (188 struct / 49 word / 70 maker / 4 lineage). Passes `make validate` and `make verify-quotes`; applied cleanly via the snapshot replay.
- **Recall verified against the export analysis.** After applying, the untagged-SIRMO/Splin miss query returns **0**, and the Tier-2 "bingo prose but untagged" net returns only the 41 confirmed false positives that live in `_bingo_excluded` — no real bingo with bingo prose is left untagged.
- **Precision note.** trap-holes alone is not the rule: 26/27/29/30/31-hole and low gobble-hole games are correctly excluded. Only structured 25 is bare-safe; the review culled 6 grid-reusing non-bingos (Evans Poker-eno/Tango, Magister Rallye, Williams Jolly Joker/Space Glider, L'Hirondelle).
- **Two weak-evidence word rows to eyeball** — `cherry-picker` (only bingo text is the title of Lawton's book _Bingo Pinball Machines_) and `continental-super-7` (its bingo mention is about a same-named GAA game). Both genuine bingos; quotes just indirect.
- **Hand off** — commit + `make push` are the user's call.
