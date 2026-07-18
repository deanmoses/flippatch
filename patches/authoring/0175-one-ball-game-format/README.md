# 0175 — One-ball game format

Adds the **`one-ball`** non-pinball `game_format` and assigns the catalog's one-ball machines to it. The third format campaign to come out of the [0173 non-pinball probe](../0173-nonpinball-formats/README.md), after [bingo](../0172-bingo-game-format/README.md) (0172) and [rolldown](../0173-rolldown-game-format/README.md) (0173-rolldown). Copies their shape: the vocab lives in the shared [`0110-game-formats.yaml`](../../0110-game-formats.yaml) create patch, the assignments in [`0175-one-ball-game-format.yaml`](../../0175-one-ball-game-format.yaml).

## What one-ball is

A 1930s–early-1950s coin-op gambling genre played on a pinball-style flipperless playfield: the player shoots a **single ball per play** at scoring holes for a **cash or ticket payout**, classically horse-race themed with shifting odds. It is the direct ancestor of the in-line bingo (0172) — Bally pivoted from one-ball to bingo in the early '50s after the federal Johnson Act (1951–52) killed the payout trade. IPDB catalogs these **as pinball**, which is the blind spot the 0173 probe exists to fix.

We ship it **flat** — a sibling `game_format`, not a child of `pinball` — matching the bingo/rolldown precedent. GameFormat has no parent-hierarchy column (it is the only sibling taxonomy without one), and one-ball is a gambling _cousin_ of flipper pinball rather than a subtype of it; the pinball kinship is carried in the format name/description and each model's note, not in the taxonomy shape. (A GameFormat hierarchy remains a possible future flipcommons project.)

## Candidate set

From the live 0173 analysis: the 30 `format_review` keyword candidates for `proposed_format='one-ball'`, plus 7 `format_review_payout` recall-ancestors the keyword detector missed (Ace, Bally Bonus, Center Smash, Derby Champ, Midget Racer, both Whiz Ball Jack Pot). The two payout data-quirks (Gottlieb Nudge-It, Stern Pokémon Premium) were never pulled. Every row was vetted against its verbatim IPDB `notes` + `notable_features`.

Reproduce the raw queues:

```bash
P=patches/authoring/0173-nonpinball-formats/formats.sql
make analyze PLAN=$P Q="SELECT id,label,maker,year,reward_types FROM format_review WHERE proposed_format='one-ball';"
make analyze PLAN=$P Q="SELECT id,label,maker,year,reward_types FROM format_review_payout;"
```

## Vetting outcome — 26 assigned, 11 held/excluded

**Assigned (26).** Each carries an IPDB quote that states one ball per play + payout, or cross-references it to a named one-ball game. The replay/non-payout siblings (Blue Grass, Gold Cup) are the amusement-side form of the same one-ball horse-race genre and are cited via the cross-reference to their one-ball payout twin; Whirlaway is cited via the trade note that it converts Bally one-ball games; Monopolee via the note that its default is one-ball with a two-ball model only "where one-ball payout is not permissible."

Ace, Bally Bonus, Center Smash, Grand Prize, Big Shot (1-Ball), King Fish, Monopolee, Velvet, Stable Mate, Deauville, New Deal, Mazuma, Pamco Ballot, Horse Shoes, Mardi Gras, Long Shot, Blue Grass, New Daily-Races, Whirlaway, Across the Board, both Jumbo listings, Sunshine Park, Gold Cup, Multiple, Plus or Minus.

**Excluded / held (11), with the source reason:**

| Model                                 | ipdb       | Reason                                                                                                                                                                                                                                               |
| ------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New Yorker (Bally 1935)               | 4148       | "10 balls per game" — a multi-ball payout table, not one-ball.                                                                                                                                                                                       |
| Midget Racer (Bally)                  | 1592       | "5 balls for 5 cents" — a 5-ball racing payout game.                                                                                                                                                                                                 |
| Big Shot (5-Ball) (Cal. Exhibit 1936) | 6906       | "5 balls for 5 cents"; its one-ball text only cross-references its 1-Ball sibling.                                                                                                                                                                   |
| Owl (Mills 1941)                      | 1732       | "5 balls for 5 cents", built to evade 1-ball bans; free-play, payout model unconfirmed.                                                                                                                                                              |
| Pearls Of East (Taiwan YuanMei)       | 6072       | Modern solid-state "5 balls for 25 cents" — not one-ball.                                                                                                                                                                                            |
| High Stepper (Puget Sound 1949)       | 6729       | Source: "we don't know if it is One-ball like those two source games."                                                                                                                                                                               |
| Automatic (unknown)                   | 6910       | Source: "We cannot find any information … to verify if it was a one-ball payout."                                                                                                                                                                    |
| Whiz Ball Jack Pot ×2 (1932)          | 3550, 5619 | 1932 cash-payout jackpot pin tables, ball count unstated — the pre-1935 gambling block the probe flags as its own project.                                                                                                                           |
| Derby Champ (Keeney 1938)             | 3059       | Probable one-ball (horse-race name, cash-payout console, Keeney one-ball era), but no IPDB or web source states the ball count. Web search (2026-07) found the Keeney one-ball payout genre but nothing on this title. Revisit if a source surfaces. |
| Hold Your Horses (unknown)            | 6743       | Probable one-ball: an amalgam Converted Game built on Bally's 1946 one-ball Victory Special/Derby, with a "Skill Lane option for 5-ball jurisdictions" (a one-ball tell). Held as inferential + one-off amalgam; revisit.                            |

## Notes

- All 26 cites are `ipdb:<id>` scheme cites; quotes verify against pinexplore's `ipdb_machines` corpus (`make verify-quotes`), drawn from either the Notes or Notable Features prose.
- Attribution is `flipcommons-catalog` (classifying a source's free text into a structured field is the default first-party case — the source never carried a `game_format`).
