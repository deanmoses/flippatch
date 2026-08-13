# 0215 — the 2026 model discovery sweep

> **Historical.** This folder is the record of how patch `0215-new-2026-models.yaml` found and created the 2026 models — this file plus the artifacts that produced it (`candidates.csv`, `frontier.sql`). The patch is applied and immutable, and its `gen.py` was deleted on 2026-08-13 along with the campaign's other generators (see [../RULEBOOK.md](../RULEBOOK.md#patch-generator)) — nothing here is re-run. For current work see [../README.md](../README.md); for technique see [../RULEBOOK.md](../RULEBOOK.md). Read on for the **dead ends** — they are what stops a later session re-researching a settled question.

The catalog held **6 models dated 2026**; this campaign found the 21 that were missing and emitted the foundation rows for them.

## The signal

Unlike every prior campaign here, the signal was **not in the catalog** — there is no query over `models` that finds a machine the catalog has never heard of. The candidate set is external, so it arrives as a checked-in CSV (`candidates.csv`), and the SQL (`frontier.sql`) does the one thing that belongs in SQL: reconciliation back to the live catalog.

| source                | cached URL                                                                         | what it gave                                         |
| --------------------- | ---------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Pinside, newest-first | `https://pinside.com/pinball/machine?sort_by=machine_manufactured&sort_order=DESC` | names, makers, years, production status              |
| Kineticist game index | `https://www.kineticist.com/games/pinball`                                         | independent corroboration + years                    |
| Kineticist upcoming   | `https://www.kineticist.com/news/upcoming-pinball-machines`                        | confirmation dates; separates confirmed from rumored |
| hexa-pinball.com      | `https://www.hexa-pinball.com/`                                                    | settled the Musketeers licensing question            |

Kits, one-offs, homebrews and prototypes are catalog machines like any other, so every row was in scope.

## What the patch carries, and what it deliberately does not

0215 emitted name / slug / theme / year / month / title / franchise **uncited**, matching the live catalog's own citation coverage on those fields (0.2–2%). It deferred `tag`, `game_format` and `production_status` — the last despite being known, because it was not quotable at the time: Pinside's HTML contains `In production`, but trafilatura drops it from the extracted text, and `make verify-quote-verbatim` checks the extracted text.

Also absent: **lineage** (every remake/variant/conversion-kit edge needs a source — the `variant_of` first proposed here was derived from a name match, exactly the guess a citation exists to prevent) and **record descriptions** (the lint requires inline cites and _two_ sources each). Filling all of this is the enrichment campaign's job.

## The Houdini error, and the gate that prevents it

The first draft **renamed `houdini-master-mystery` into the 100th Anniversary edition**, reasoning from a name match: same maker, "Houdini", `unreleased`, no year. That was wrong, and it reached the dev DB before being caught.

`houdini-master-mystery` is IPDB 6469 — the never-built John Popadiuk / Matt Andrews design. Its own `ipdb_notes` say so outright:

> "This game was not produced and was replaced by American Pinball Inc.'s 2017 'Houdini Master of Mystery' with a playfield from a different designer, and different backbox and artwork."

That evidence was in the catalog the whole time, one column away from the query that proposed the rename. The row was found by reading American Pinball's maker line and then **not** read any further.

The gate is `unreleased_lookalike_unacknowledged`: every same-maker `unreleased` model sharing a word of four or more characters with a candidate must be acknowledged **by slug** in `candidates.csv` before the patch can emit. Similarity becomes a review trigger to be dispositioned, never a merge signal.

Three other bugs the analysis caught in itself, worth knowing if you touch `frontier.sql`:

- **`name_key` is not an identity function.** It is `name_norm(name_strip_paren(...))` and deliberately collapses an edition onto its family, which made all four 2023 Galactic Tank Force rows an exact match for the Victory Edition. Identity uses `name_norm`; family uses `name_key`.
- **Theme redundancy is transitive.** `theme_vocab` carries a parent/child DAG, so the check walks the full ancestor closure. **Inherited themes outrank the rule** — a theme copied verbatim from an existing related model is never pruned for being implied, because pruning would silently diverge the new row from the rows it came from.
- **A Title can be real and still unreachable by name.** Title creation is driven by `title_exists`, not `title_action`: the 100th Anniversary belongs to the existing `houdini` Title, which its own name does not match, and `create: true` against a live title fails the apply as a duplicate.

## Dead ends — do not re-research these

- **OPDB contributes nothing.** Its export is at parity: of 2,354 machines, the 43 absent from the catalog are all group-level rollups (`Rush (Premium/LE)`) where the catalog correctly splits Premium and LE. Its 2026 coverage is 4 machines — fewer than the catalog already had.
- **`opdb.org/changelog` is not a new-machine feed.** All 44 lifetime entries are `move` (38) and `delete` (6) — an ID-reconciliation feed. Useful for keeping the catalog's 2,311 stored `opdb_id`s from going stale; useless for discovery.
- **A separate DuckDB file was considered and rejected.** It would not contain the catalog, so every reconciliation would be answered by something that cannot see the source of truth. The CSV is read _inside_ the foundation session instead.
- **An AI-generated "new for 2026" list was checked and not used.** It misdated _Star Wars: Fall of the Empire_ and _The Walking Dead Remastered_ to 2026 (both 2025, both already correct) and missed five of the sixteen corroborated rows, including all three Sonic editions.
- **The 3 Musketeers is not from a franchise.** hexa-pinball.com: _"Ce flipper s'inspire du célèbre roman Les Trois Mousquetaires d'Alexandre Dumas."_ The 1844 novel — public domain. No franchise and no `licensed` theme, matching the three existing Musketeer Titles.

## Running it

The emit step is gone with `gen.py`; the analysis still runs, and is how you re-read the reasoning behind the candidate list:

```bash
make analyze FILE=../flippatch/campaigns/0215-frontier-2026/model-discovery/frontier.sql PREFIX=frontier
```

While the sweep was live, the analysis was re-run after every edit to `candidates.csv`: its checks are what stopped a stale or mistyped candidate list from being emitted, and `read_view` ran them before yielding a row, so the generator could not emit from an analysis whose detectors had gone dark. That coupling is what the checks were for — they remain readable in `frontier.sql` as the record of what the candidate list was held to.
