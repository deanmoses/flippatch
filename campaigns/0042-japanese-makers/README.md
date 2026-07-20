# 0042 — early-Japanese maker years

Asserts production years on seven early-Japanese models flipcommons carried with a
null or placeholder (`1900`) year. Years come from the **eremeka catalog**
(thetastates.com) and its companion blog (earlyarcadesjapan.blogspot.com), seeded as
citation roots in 0041.

## Signal & attribution

The eremeka catalog dates each game (often from period machine directories and
advertisements). We derive the structured `year` field from that research, so the
attribution is **flipcommons-catalog** with a `cite` to the eremeka page — the blog
post where one exists (richer dating evidence), else the tag listing. All seven
models carry an IPDB id, so the `expect` guard is `ipdb_id` (present even where year
is null). Approximate eremeka dates (marked `~`) are asserted with the uncertainty
recorded in the note (the model has no "approximate" flag).

## Rows

| model | ipdb | year | was | note |
|---|--:|--:|---|---|
| apollo-moon | 6812 | 1972 | null | |
| the-world-series | 6069 | 1972 | 1900 | superseded opdb/fc-catalog 1900 |
| new-big-race | 6070 | 1972 | null | 1973 directory printed late 1972 |
| asteroid-killer | 3810 | 1979 | 1980 | |
| indy-game | 6774 | 1967 | null | ~ approximate |
| lets-go-moon | 6773 | 1968 | null | ~ approximate |
| ultra-attack | 6068 | 1972 | null | ~ approximate |

Run `gen.py` from the flipcommons backend (reads live guard values).
