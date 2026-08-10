# Acquiring the 2026 models and enriching their families

Patch `0215-new-2026-models.yaml` created names and themes for some new-for-2026 models, but nothing else: no credits, gameplay features, `production_status`, `game_format`, cabinet, display or system. We now want to fully flesh them out, as described in `~/dev/flipcommons/docs/DataPatchAuthoring.md`#`Fill every field you can — grounded in DomainModel.md`.

## Model families

Each family is independent work, done by a separate AI session in its own folder under `model-families/`.

- **✅ 0216, 0219 · [houdini](model-families/houdini)** (American Pinball) — 100th Anniversary **+ 2 older**: Master of Mystery, Master of Mystery (Deluxe)
- **✅ 0220 · [transformers](model-families/transformers)** (Stern) — MTMTE Pro / Premium / LE **+ 5 older**: Transformers Pro & LE (2011), Autobot Crimson LE, Decepticon Violet LE, The Pin (2012)
- **✅ 0221 · [sonic-hedgehog](model-families/sonic-hedgehog)** (Jersey Jack) — Collector's / Special / Arcade Edition
- **open · [galactic-tank-force](model-families/galactic-tank-force)** (American Pinball) — Victory Edition **+ 4 older** (2023): Classic, Deluxe, Limited Edition, Signature
- **open · [cirqus-voltaire](model-families/cirqus-voltaire)** (American Pinball) — Remake **+ 1 older**: Cirqus Voltaire (Bally, 1997)
- **open · [bon-jovi](model-families/bon-jovi)** (Barrels of Fun) — Bon Jovi
- **open · [fish-tales](model-families/fish-tales)** (Cardona) — Ultimate Fishing Challenge (Kit) **+ 1 older**: Fish Tales (Williams, 1992). Needs the Cardona citation root in its own patch — see [RULEBOOK.md](RULEBOOK.md#citation-roots).
- **open · [arabian-nights](model-families/arabian-nights)** (Pedretti) — Tales of the Arabian Nights 30th Anniversary + Legacy Edition **+ 1 older**: TOTAN (Williams, 1996)
- **open · [musketeers](model-families/musketeers)** (HEXA) — The 3 Musketeers base + Elegance Edition
- **open · [p3-modules](model-families/p3-modules)** (Multimorphic) — Dungeon Crawler Carl, Ender's Game
- **open · [yukon-yeti](model-families/yukon-yeti)** (Turner) — Yukon Yeti
- **open · [ramps-pinball](model-families/ramps-pinball)** (Ramp's) — Monster League Hockey **+ 2 siblings**: Road Trip, Little Shop of Horrors
- **open · [resident-evil](model-families/resident-evil)** (World Pinball) — Resident Evil. Mostly **corporate-entity** work: the maker's site is password-gated, and everything about the machine itself traces to one unconfirmed post. Read `ResidentEvil.md` before spending time on it.
- **open · [obsidian-high](model-families/obsidian-high)** (UP Pinball) — The Fiery End of Obsidian High
- **open · [pokemon](model-families/pokemon)** (Stern) — Pokémon Pro / Premium / Limited Edition. **Not created by 0215** — all three editions were already in the catalog, and are just as bare as the rest. Runs SPIKE 3: the `stern-spike-3` System already exists (created in 0220) — reference it, never re-create. Its cached manuals are `Pokemon_Pro_web.pdf` + `Pokemon_LE_Pre_web.pdf`, the second covering LE **and** Premium in one document.

## Campaign rules

**Patch numbering**: a session claims the next free `patches/` number when it starts. The file pattern is `patches/NNNN-<family-slug>.yaml`.

**Complete the family's older siblings.** Each per-family campaign fleshes out missing data for the whole family, not just its 2026 member(s) — a family's primary documents mostly describe the older machines too, so it is context-efficient to do at once.

**Don't overwrite data on existing models.** Only assert missing facts. If you think an existing fact is wrong, get user approval before correcting it.

**We ship all patches at the end.** The done families are snapshot-validated and committed, but not shipped to prod. They are thus still mutable, so that if improving our technique on a later family shows an earlier one needs changing, we can.

## The loop

[RULEBOOK.md](RULEBOOK.md) governs this loop — sources, PDF citing, citation roots, feature vocabulary, the gates.

1. **Baseline survey — every field the patch might touch.** Table the catalog's current state per model: fields, credits, features, themes, lineage, `production_quantity`, `tag`, month. Houdini's first pass skipped `production_quantity`/`tag` and re-asserted what 0215 already set. Only assert what is missing, and duplicate-scan against `model_claims` from other actors, not `patch_claims` — the apply silently swallows an exact duplicate along with its citation.
2. **Research and fetch the primary documents.** Find as many as exist and cache all of them, even ones you aren't sure are citable — [RULEBOOK.md](RULEBOOK.md#finding-and-fetching-documents) has the discovery moves and the per-maker floor.
3. **Evidence inventory into the family's own `<Family>.md`** — what's cached, what each document actually carries, traps — before extracting claims. Afterwards the same file records what was **sought and not found** and what was **deliberately not asserted**, each with its reason, so every omission reads as a decision rather than a miss. Transformers' "Sought and not found" and Sonic's "Not asserted" sections are the pattern.
4. **Emit from a `gen.py`**, facts inline, via patchkit. [transformers/gen.py](model-families/transformers/gen.py) is the best template so far, consider copying it. Record user decisions in the family notes.
5. **Iterate against the quote gates freely** — an uncommitted patch is cheap to regenerate. `make verify-quote-verbatim`, fix spans, re-emit; then `make verify-quote-support ARGS="<NNNN>"` and triage. Read [RULEBOOK.md](RULEBOOK.md#operating-the-quote-gates) before triaging: a clean pass is not the goal and re-running to chase one costs ~300k tokens a time.
6. **Snapshot loop freely** ([Rebuilding the database](RULEBOOK.md#rebuilding-the-database)) and verify resolution through `make analyze` — `patch_entry_cites` shows each claim with its quote and note.
7. **At family completion, promote.** Move anything generalizable into RULEBOOK.md under the heading it belongs to, and fix stale guidance there. Don't append run histories to either file; your `<Family>.md` keeps the family record — evidence inventory, decisions, sought-and-not-found, the future-unique-features worklist, gate-run history.

**Give feedback**: throughout the loop, if you see anything that is not ergonomic or could otherwise be improved about the tooling, say so. These campaigns are the initial consumers of the improved search, OCR and PDF handling in [Pinexplore's web cache](~/dev/pinexplore/docs/WebCache.md) as well as citation verification improvements.

Consider opening a done family when you are in one of these situations:

- **[Transformers.md](model-families/transformers/Transformers.md)** — your evidence is a per-edition feature matrix; the maker's old product pages are 404 and you need Wayback; your older siblings have IPDB rows.
- **[SonicHedgehog.md](model-families/sonic-hedgehog/SonicHedgehog.md)** — you are triaging `verify-quote-support` warnings and want to see which ones were kept and why; you are hunting a maker's file host or a Shopify-backed store; you need the shape of a "Not asserted (and why)" section.
- **[Houdini.md](model-families/houdini/Houdini.md)** — you are creating feature vocabulary or classifying toys (0219 was written, judged too granular, and reworked twice — the rulings are recorded); two primary sources disagree and you need the precedent for which one won.

## Open follow-ups

### Theme redundancy on existing rows

Surfaced by 0215's `_theme_ancestor` check and not yet touched: Stern _Transformers_ 2011 (5 rows, `science-fiction` under `robots`), _Galactic Tank Force_ 2023 (4 rows), _Fish Tales_ 1992, Metallica (several, `music` under `heavy-metal` — Guns N' Roses gets it right), and _Tales of the Arabian Nights_ 1996 missing `literature`.

These are **seed rows, not 0215's** — 0215 created only the 2026 models, so there is nothing in it to edit. Pruning a redundant theme means retracting an existing claim, which needs user approval per the don't-overwrite rule; adding TOTAN's missing `literature` is an ordinary assert. All but Metallica sit inside a family on the board (transformers, galactic-tank-force, fish-tales, arabian-nights), so that family's session can raise them; Metallica belongs to no family here and needs a home.
