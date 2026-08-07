# 0215 — recent 2026 model sweep

Swept 2026-08-03. The catalog held **6 models dated 2026**; this campaign found the 21 that were missing and emits the foundation rows for them.

## The signal

Unlike every prior campaign here, the signal is **not in the catalog**. There is no query over `models` that finds a machine the catalog has never heard of. The candidate set is external, so it arrives as a checked-in CSV (`candidates.csv`) and the SQL does the one thing that does belong in SQL: the reconciliation back to the live catalog.

Three sources, all cached in the pinexplore web cache, all already seeded citation roots:

| source                | cached URL                                                                         | what it gave                                         |
| --------------------- | ---------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Pinside, newest-first | `https://pinside.com/pinball/machine?sort_by=machine_manufactured&sort_order=DESC` | names, makers, years, production status              |
| Kineticist game index | `https://www.kineticist.com/games/pinball`                                         | independent corroboration + years                    |
| Kineticist upcoming   | `https://www.kineticist.com/news/upcoming-pinball-machines`                        | confirmation dates; separates confirmed from rumored |
| hexa-pinball.com      | `https://www.hexa-pinball.com/`                                                    | settled the Musketeers licensing question            |

`corroboration` records evidence strength — `both` or `kineticist` — as a column, not a filter. Kits, one-offs, homebrews and prototypes are catalog machines like any other, so every row is in scope.

## What the patch carries, and what it deliberately does not

Citation coverage in the live catalog draws the line, not taste:

| field                                                  | claims       | cited  |                      |
| ------------------------------------------------------ | ------------ | ------ | -------------------- |
| name / slug / theme / year / month / title / franchise | 20,552 … 243 | 0.2–2% | **in 0215, uncited** |
| tag                                                    | 608          | 27%    | deferred             |
| game_format                                            | 647          | 59%    | deferred             |
| production_status                                      | 184          | 91%    | deferred             |

`production_status` is deferred despite being known, for a concrete reason: **it is not quotable today.** Pinside's HTML contains `In production`, but trafilatura drops it from the extracted text, and `make verify-quotes` checks the extracted text. Citability is uneven even for `year` — the Musketeers archive page yields a clean `"...is a pinball machine from March 2026, manufactured by HEXA Pinball"`, while Bon Jovi's page extracts 661 characters of marketing copy and no date at all.

Also absent: **lineage** (every remake/variant/conversion-kit edge needs a source — the `variant_of` first proposed here was derived from a name match, exactly the guess a citation exists to prevent) and **record descriptions** (the lint requires inline cites and _two_ sources each).

## The gate

`frontier_checks` caught four bugs in its own analysis and generator:

1. **`name_key` is not an identity function.** It is `name_norm(name_strip_paren(...))` — it deliberately collapses an edition onto its family. Using it for the "already present?" join made all four 2023 Galactic Tank Force rows an exact match for the Victory Edition. Identity uses `name_norm`; family uses `name_key`.
2. **A standing-red check is not a gate.** An early draft asserted an entire tier as a permanent failure, which would have blocked `read_view` forever and trained the operator to ignore the gate.
3. **Theme redundancy is transitive.** `theme_vocab` carries a parent/child DAG; the check walks its full ancestor closure, so `robots` resolving to `[outer-space, science-fiction]` is caught two levels up. It found `music`/`hard-rock`, `science-fiction`/`robots`, `outer-space`/`science-fiction` and `sports`/`fishing`.
4. **A Title can be real and still unreachable by name.** Title creation is driven by `title_exists`, not by `title_action`: the 100th Anniversary belongs to the existing `houdini` Title, which its own name does not match, and `create: true` against a live title fails the apply as a duplicate.

**Inherited themes outrank the redundancy rule.** A theme copied verbatim from an existing related model is never pruned for being implied, because pruning it would silently diverge the new row from the rows it came from. `inherited_themes` marks them and the check exempts exactly those; the exemption is load-bearing (five pairs would otherwise fire) and does not weaken the rule for anything derived fresh.

## The Houdini error — and the gate that now prevents it

The first draft of this patch **renamed `houdini-master-mystery` into the 100th Anniversary edition**, reasoning from a name match: same maker, "Houdini", `unreleased`, no year. That was wrong, and it shipped to the dev DB before being caught.

`houdini-master-mystery` is IPDB 6469 — the never-built John Popadiuk / Matt Andrews design. Its own `ipdb_notes` say so outright:

> "This game was not produced and was replaced by American Pinball Inc.'s 2017 'Houdini Master of Mystery' with a playfield from a different designer, and different backbox and artwork."

That evidence was in the catalog the whole time, one column away from the query that proposed the rename. The row was found by reading American Pinball's maker line and then **not** read any further.

Fixed by restoring the snapshot and replaying: the 100th Anniversary is now a plain create joining the existing `houdini` Title, and `houdini-master-mystery` is untouched (0 claims from this patch).

The gate is `unreleased_lookalike_unacknowledged`. `_lookalike` finds every same-maker `unreleased` model sharing a word of four or more characters with a candidate, and each pair must be acknowledged **by slug** in `candidates.csv` before the patch can emit. Similarity becomes a review trigger that has to be dispositioned, never a merge signal. It is load-bearing: it fires on exactly the Houdini pair.

**Galactic Tank Force (Victory Edition)** — a new edition of the 2023 GTF family. Emitted as a plain model; the `variant_of` edge waits for a source.

## Dead ends

- **OPDB contributes nothing.** Its export is at parity: of 2,354 machines the 43 absent from the catalog are all group-level rollups (`Rush (Premium/LE)`) where the catalog correctly splits Premium and LE. Its 2026 coverage is 4 machines — fewer than the catalog already had.
- **`opdb.org/changelog` is not a new-machine feed.** All 44 lifetime entries are `move` (38) and `delete` (6) — an ID-reconciliation feed. Useful for keeping the catalog's 2,311 stored `opdb_id`s from going stale; useless for discovery.
- **A separate DuckDB file was considered and rejected.** It would not contain the catalog, so every reconciliation would be answered by something that cannot see the source of truth — the trap `CLAUDE.md` flags for pinexplore's `explore.duckdb`. The CSV is read _inside_ the foundation session instead.
- **An AI-generated "new for 2026" list was checked and not used.** It misdated _Star Wars: Fall of the Empire_ and _The Walking Dead Remastered_ to 2026 (both 2025, both already correct) and missed five of the sixteen corroborated rows, including all three Sonic editions.
- **The 3 Musketeers is not from a franchise.** hexa-pinball.com: _"Ce flipper s'inspire du célèbre roman Les Trois Mousquetaires d'Alexandre Dumas."_ The 1844 novel — public domain. No franchise and no `licensed` theme, matching the three existing Musketeer Titles.

## Follow-up the sweep surfaced but did not touch

The theme-redundancy rule indicts existing rows too, all mechanically detectable via `_theme_ancestor`: Stern _Transformers_ 2011 (5 rows, `science-fiction` under `robots`), _Galactic Tank Force_ 2023 (4 rows), _Fish Tales_ 1992, Metallica (several, `music` under `heavy-metal` — Guns N' Roses gets it right), and _Tales of the Arabian Nights_ 1996 missing `literature`.

## Running it

```bash
make analyze FILE=../flippatch/campaigns/0215-frontier-2026/frontier.sql PREFIX=frontier
uv run python campaigns/0215-frontier-2026/gen.py
make validate
```

Re-run the analysis after every edit to `candidates.csv` — the checks are what stop a stale or mistyped candidate list from being emitted. `read_view` runs them before it yields a row, so the generator cannot emit from an analysis whose detectors have gone dark.
