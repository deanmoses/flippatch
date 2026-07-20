# 0181 — Bingo production years

This directory coordinates a data patch that fills `MachineModel.year` for bingo machines the catalog carries with **no year at all**, from [bingo.cdyn.com](https://bingo.cdyn.com/machines/index.html)'s alpha-by-manufacturer machine listing.

## Why a year is worth a campaign

A missing year disables the single strongest signal for telling two same-named games apart. That is not theoretical: the [0177-exports](../0177-exports/README.md) campaign's `export_namesake_review` tiered Splin S.A.'s modern six-card *Acapulco* as a **foreign build (copy)** of Bally's 1961 *Acapulco* — a claim nothing supports — purely because both models were year-less and the tiering could not measure the gap between them. The year-less bingo corpus is where nearly all of that noise lives.

## The source, and its one column

cdyn's listing is one pipe-table per manufacturer: `Game Name | Game Number | Game Type | Year`. It is the only source found that dates the late European bingo makers (Sirmo, Splin, Wimi, Show Games, G.A.A.), and its **Year column is fully populated** — 212 rows, zero unknowns.

Its **Game Number column is not**: it is the literal string `unknown` for every maker except Bally (and one Williams row). So this campaign takes years from cdyn and nothing else. The model numbers the catalog holds for Bally come from IPDB, and no source numbers the Europeans at all — which is exactly why the match below needs two different keys.

The page is read from **pinexplore's web scrape cache**, never the network, so the rows extracted here and the quotes the patch cites come from the same durable blob `make verify-quotes` checks against. [extract_cdyn.py](extract_cdyn.py) parses it into [cdyn_machines.tsv](cdyn_machines.tsv), a checked-in audit artifact a reviewer can diff when the page changes.

## Matching: two keys, and why the number wins

[years.sql](years.sql) matches a year-less model to a cdyn row on the strongest key its maker offers.

**By game number (Bally).** The manufacturer's own number, already in the catalog from IPDB. This key survives contact with the data where the name does not: matching Bally on *name* put the catalog's #535 *Broadway* onto cdyn's 1955 #576 *Broadway* (cdyn lists both a 1951 #535 and a 1955 #576), and collapsed two distinct *Tahiti* records onto one row. Both are guard anchors now.

The number needs care of its own. Bally's trailing letter is **not** a variant marker — #634 is *Fun Way* and #634-A is *Lotta Fun*, #652 is *Fun Spot* and #652-A is *Barrel-O'-Fun* — so normalizing it away merges different games. But the catalog sometimes records the stem where cdyn has the letter (catalog has *Barrel O' Fun '61* as #670, cdyn numbers it 670-A), so an exact-only key misses those. The resolution is exact-first, stem-as-fallback, with the name-agreement gate making the fallback safe.

**By name (every European maker).** No number exists in any source for these. Acceptable only because each maker has a small catalog that cdyn lists in full, so the uniqueness requirement is a real constraint rather than a formality.

## The gate

A year is emitted only when the match is unambiguous **in both directions** and the value is a clean four-digit year. Everything else lands in `year_rejected` with a reason, because a wrong year is worse than a missing one — it silently re-tiers every same-name comparison downstream.

| reject reason | what it catches |
| --- | --- |
| `model matches several source rows` | one model, several candidate source rows — which year is unknowable |
| `source row matches several models` | one cdyn row, several catalog models (*Golden Gate (3-game)* / *(4-game)*; *Miss Disco (2 card)* / *(7 card)*) — probably the same year for both, but that is a human's call |
| `number matched, name differs` | mostly benign spelling variants (*The Twist* / "Twist", *Broadway* / "Broadway_51"), but also #1017, which is *Golden Gate 75* here and *Mystic Gate* there — a real question |
| `year not a number` / `year out of range` | a malformed source value |

```bash
P=patches/authoring/0181-bingo-years/years.sql
make analyze PLAN=$P PREFIX=year                        # summary, gated on checks
make analyze PLAN=$P Q="FROM year_patch_rows;"          # what gen.py emits
make analyze PLAN=$P Q="FROM year_rejected;"            # what the gate held back
make analyze PLAN=$P Q="FROM year_number_collisions;"   # same maker+number, two models
```

## The patch

[gen.py](gen.py) is a pure emitter over `year_patch_rows`. Each entry asserts one field and cites the machine's own table row verbatim:

```yaml
- model.acapulco:
    cite:
      ref: 'https://bingo.cdyn.com/machines/index.html'
      quote: '| Acapulco | 669 | magic numbers | 1961 |'
    year: 1961
```

The cite is a URL, not a `scheme:id`, so bingo.cdyn.com must be seeded as a citation source root — it already is ("Bingo Pinballs"), which is why the patch emits no `sources:` block.

```bash
uv run python3 patches/authoring/0181-bingo-years/extract_cdyn.py   # refresh the TSV
uv run python3 patches/authoring/0181-bingo-years/gen.py
make validate && make verify-quotes
```

Scope is deliberately **year-less models only**. A cdyn/catalog year disagreement on an already-dated model is a real question, but adjudicating an existing catalog claim is a different and much more careful patch.

## What this does not fix

cdyn does not list a Splin *Acapulco*, so that model stays year-less and the pair that motivated the campaign is **not** resolved by a direct year comparison. What the patch does supply is the **maker's era** — six Splin models dated 1999–2003 — placing the maker 38 years after Bally's 1961 game.

So dating a maker's *other* models is worth as much here as dating the model itself, and the follow-up belongs in [0177-exports](../0177-exports/README.md): a maker-era fallback in `export_namesake_review` for pairs where one side has no year of its own.

## Also surfaced: `year_number_collisions`

Two live models sharing one maker + game number. Not this campaign's business to fix, but the number is about to become a load-bearing key, so the collisions are worth a look — some are legitimate reward-variant pairs (*Skill Derby (Replay Model)* / *(Non-replay Model)*), others are duplicates (*Bow and Arrow* twice on Bally #1033), one game under two names (*Gator* / *Alligator* on #838), or a placeholder value used across six unrelated games (Game Plan #110).

## The dev DB

Verify every fact against the flipcommons localhost SQLite dev DB — this doc goes stale; the dev DB is ground truth, and [years.sql](years.sql) reads it live. Then `make validate` here. Committing and `make push` are the user's call, never automatic.
