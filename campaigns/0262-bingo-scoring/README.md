# 0262 — Bingo scoring attachments

This directory coordinates a data patch attaching the three bingo **scoring** gameplay features — `in-line-scoring`, `section-scoring` and `next-game-award` — to the machines that carry them, from [bingo.cdyn.com](https://bingo.cdyn.com/machines/index.html)'s per-machine feature blocks.

## Why the records existed with nobody pointing at them

[0244](../../patches/shipped/) created the three records and [0260](../../patches/0260-bingo-scoring-descriptions.yaml) described them. Between them they had **zero model attachments** against 311 bingo-pinball models — vocabulary and prose with no corpus underneath. That is what forced 0260's descriptions to name *Carnival Queen* and *Border Beauty* in bare prose the DB-aware audit then reported as uncarried links, and it is the gap [../0239-descriptions/gaps.jsonl](../0239-descriptions/gaps.jsonl) recorded.

## The source, and why not the one 0181 used

[../0181-bingo-years](../0181-bingo-years/README.md) already parses cdyn's alpha listing, and that page has a `Game Type` column — three-card, magic screen, mystic lines. It correlates with scoring method but does not state it: mystic-line games score sections only, magic-screen games score both, early card games score lines. Reading a scoring method out of a marketing label is inference, and a cite cannot rest on inference.

Each cdyn **machine page** instead ends its `Game Parameters` table with a `Features` cell drawn from the site's own vocabulary ([machines/features.html](https://bingo.cdyn.com/machines/features.html)):

```text
| Features | - advancing odds/scores - blue section scores - colored lines - [...] - in-line scoring - roll-over buttons - section scoring - super-section |
```

That states the method, per machine, in the source's own words. [extract_cdyn_features.py](extract_cdyn_features.py) parses every cached machine page into [cdyn_features.tsv](cdyn_features.tsv), a checked-in audit artifact a reviewer can diff when a page changes; the pages are read from **pinexplore's web scrape cache**, never the network, so the extracted rows and the cited quotes come from the same durable blob `make verify-quote-verbatim` checks against.

Seeding the cache took one batch: the machine URLs are the outbound links of the alpha listing (`web_cache.py links`), and 204 of the 214 were not yet held. 214 pages are cached, **190 carry a Features cell** — cdyn documents the other 24 with images only.

## The next-game-award family, and the second cite

A machine rarely lists the words *next game award*; it lists an instance — `ballyhole`, `red letter game`, `OK game`, `futurity`, `sunny circles`. features.html is what ties the two together: "Something you do on the current game will enable a feature automatically on the next game. [...] See: - ballyhole - red letter game - ok game - futurity game - sunny circles". So an entry evidenced only by an instance ships **two cites** — the machine page for what the machine has, features.html for what that thing is. 59 of the 239 attachments need it; the rest name the parent directly.

**Deliberately excluded: United's `lite-a-name`.** 0260's description glosses it as the same idea, and features.html does describe it as progressive "like Bally's futurity" — but it does not list it under next game award, and the mechanism differs (lite-a-name pays an in-line score on completion rather than setting up the next game). Attaching it would be our inference, not the source's claim. It stays a gaps.jsonl row.

## Matching: three keys and a tie-break

[scoring.sql](scoring.sql) matches a catalog model to a cdyn machine page on the strongest key available, reusing 0181's exact-then-stem number logic verbatim (Bally's trailing letter is not a variant marker — #634 is *Fun Way*, #634-A is *Lotta Fun*).

| key | when | corroboration required |
| --- | --- | --- |
| number (exact, then stem) | the maker numbers its games and both sides state one | the names must agree |
| name, unnumbered model | no number exists in any source (the European makers) | year, if the model's format is unset |
| name, unnumbered **source** | the catalog numbers it but cdyn's page says `unknown` | year, always |

**The year tie-break.** United reused its game names across eras — a 1940s game and a 1950s bingo both called *Havana*, *Hawaii*, *Manhattan*, *Mexico*, *Nevada*, *Rio*, *Singapore*, *South Seas*, *Tropicana*, *Serenade*, *Show Boat*, *Brazil* — and neither carries a game number, so the name key lands on both and the ambiguity gate rejected every one. But cdyn's page states the year and exactly one catalog model matches it. That is a second agreeing fact, not a coin flip, so where the year **decides** a group it does; where two candidates agree (United's *Rodeo*, a 1-card and a 3-card model of the same 1953 game) or none does (Sirmo's two year-less *Golden Gate*s), the group is left whole and fails the ambiguity gate as before.

**Unclassified models are in scope.** Restricting to `game_format_slug = 'bingo-pinball'` was the first cut and it silently lost real bingos: cdyn's Bally #1025 *Bali*, #634 *Fun Way*, #912 *Hole In One*, #913 *Stock Market* are all in the catalog under the right maker and number with **no game format recorded at all**. They dropped out of scope and surfaced as apparently-missing models. A model whose format is unset is one the catalog has not classified, not one it says is something else — so it is in scope, while a model carrying a different format is not. Bally alone has 592 format-unset models, which is why the weak key reaching into them must be corroborated by the year. 16 of the gated models are unclassified; every one of them is also a missing `game_format` the catalog should carry, recorded as bycatch.

## The gate

| reject reason | what it catches |
| --- | --- |
| `model matches several source pages` | one model, several candidate pages |
| `source page matches several models` | one page, several models the year could not decide between |
| `number matched, name differs` | the Barrel-O'-Fun / Fun Spot number swap, *Broadway* #535, *The Twist* |
| `year disagrees` | the two sides are describing different machines |
| `name match onto unclassified model, year unconfirmed` | the widened scope's weak corner, uncorroborated |
| `numbered model matched by name only, year unconfirmed` | the catalog numbered it, the page did not, nothing else agrees |

18 rows land there. All are real questions for a human, and all are recorded in [gaps.jsonl](../0239-descriptions/gaps.jsonl).

## Dead ends

- **IPDB carries no scoring-method field for bingos.** Its notable-features free text describes cards and holes, not whether wins are counted in lines or sections, so there is no second source to corroborate cdyn per machine. cdyn is the backbone here without an independent second root, which the campaign's own approved-cdyn-only precedent covers (README of ../0239-descriptions, 2026-08-15).
- **The alpha listing's Game Type column** was tested as a signal and rejected — see above.
- **11 cdyn machines have no catalog model at all** (`scoring_unmatched_source`), plus Helco's *New Five* under a maker the catalog does not carry. Those are missing records, not missing attachments.

```bash
F=campaigns/0262-bingo-scoring/scoring.sql
make analyze FILE=$F PREFIX=scoring                     # summary, gated on checks
make analyze FILE=$F Q="FROM scoring_patch_rows;"       # what gen.py emits
make analyze FILE=$F Q="FROM scoring_rejected;"         # what the gate held back
make analyze FILE=$F Q="FROM scoring_unmatched_source;" # cdyn pages no model claimed
```

## The patch

[gen.py](gen.py) is a pure emitter over `scoring_patch_rows` — **149 entries, 239 attachments** (134 in-line-scoring, 74 next-game-award, 31 section-scoring). Each entry quotes the machine's complete Features row rather than a span trimmed to the words we wanted:

```yaml
- model.ballerina:
    cite:
      - ref: "https://bingo.cdyn.com/machines/bally/ballerina"
        quote: "| Features | - advancing odds/scores - blue section scores - colored lines - [...] |"
    gameplay_feature: [in-line-scoring, section-scoring]
```

The cites are URLs, so bingo.cdyn.com must be seeded as a citation source root — it already is ("Bingo Pinballs", covering `bingo.cdyn.com` and `danny.cdyn.com`), which is why the patch emits no `sources:` block.

## A note on the foundation

`.read scripts/analysis/catalog.sql` — the line every earlier campaign analysis opens with, including ../0181-bingo-years/years.sql — **now fails**: the foundation moved to `scripts/analysis/sql/`, and the runner attaches it before reading the analysis, so no `.read` of it is wanted at all. `make analyze FILE=campaigns/0181-bingo-years/years.sql PREFIX=year` errors out today for that reason. This file carries no foundation `.read`.
