# 0266 — the merchant-paid award reward type

Creates a seventh `RewardType`, `merchant-paid`, and attaches it to the machines whose awards the location paid rather than the machine. Patch 0267 carries its description.

## Why the type exists

Harvest Moon (Bally, 1936) prompted it. IPDB records only "Non-payout.", which was read as `novelty` — but novelty is defined as "no mechanism by which skilled play returns anything of value to the player", and Bally's own advertisement in The Billboard of March 7 1936, p. 78 sells the machine on "PROGRESSIVE AWARDS" and a "Light-up Back-Board, showing all winners", offering operators "a crack at 'payout profits' in NON-PAYOUT TERRITORY". Something was won; the merchant paid it. None of the six existing types covered that: the machine dispenses nothing (not `cash-payout`, not `ticket-payout`), and value is returned (not `novelty`).

The catalog already drew the distinction implicitly. The two 1935 machines carrying `novelty` (Jennings' Hunter and Sportsman) both have IPDB text reading "Non-payout, **novelty play only**" — the qualifier is explicit. King Fish (Genco, 1935) is non-payout and carries `free-play`, because IPDB names a "Free play hole (1)". And 38 further models whose IPDB text mentions non-payout carry no reward type at all: leaving it unset was the established default for exactly the cases this type now names.

## The mining pass

One regex sweep over `ipdb_notes || ipdb_notable_features` across the whole model corpus (no year filter), on these alternates:

```
merchant | in trade | trade pri | non-cash | the location would | location award |
operator can verify | paid a …prize | prizes? (placed|range|are|is) |
award(s|ed)? (the )?(player|prize) | redeem | storekeeper | counter pay
```

37 candidates, hand-classified to 15 IPDB-evidenced models plus Harvest Moon. Raw output kept in `candidates-raw.txt`; the confirmed list is `confirmed.txt`.

**This is a floor, not a survey.** The sweep reads IPDB free text only. Source phrasing varies far more than the pattern captures ("in trade", "the location", "the operator", "the merchant", "under-the-counter"), and the 38 non-payout models with no reward type were not individually adjudicated — many are probably this type, with no note saying so. A later pass should work that set machine by machine.

### Rejected, and why

- **Person's name.** `atlantis-2`, `teenage-mutant-ninja-turtles`, `a-maze-ing-baseball`, `total-recall` — all match "Rehman Merchant", a programmer.
- **Merchant present, but not paying.** `rockelite`, `big-game` — the merchant watches the tilt lamp from behind the counter. `american-keen-ball-game`, `united-keen-ball` — "Merchant should not allow small children to play this game", an instruction-card line.
- **The machine pays.** `tout` — the lock on the payout drawer is about who empties it.
- **Ticket-vending, so `ticket-payout` covers it.** `whirl-pool` (ticket redeemed on location), `monte-carlo-mirrored-backbox-model`, `euro-star`, `les-fleches` (tokens redeemable for centime values). The machine dispensing a token is the distinguishing act; where it lands is a redemption detail.
- **False match on "location".** `flipper-3` — "depending on the location where it lands" means a place on the playfield.
- **Unattributed award.** `log-cabin`, `log-cabin-2`, `log-cabin-3` (Caille, 1901–03) — "Landing the ball into the top center hole paid a prize" never says who paid. Left unset rather than guessed.
- **Speculation.** `basketball-2` — "or maybe anticipation of under-the-counter payouts by the location owner" is IPDB hedging, not an assertion.
- **Off-topic prize.** `krazy-komiks`, `unknown-four-crowns` (contest prizes for artists), `build-up` ("trade magazines"), `pickwick`, `whiffle-board` (prose about the 1892 trade stimulator), `big-bank-nite` (theatre-lottery theme background), `playland-2` ("no prizes are given" — a novelty candidate, if anything).

## Boundary

The type turns on **who hands the award over**, not what the award is. Cash, trade credit and goods all qualify when the location pays. A machine that dispenses anything itself — coins, tickets, tokens — is that dispensing type instead.

## Regenerating

```bash
PYTHONPATH=scripts uv run python campaigns/0266-merchant-paid-rewards/gen.py
```

0267 (the description) is hand-authored; there is no generator for it.

The Billboard scan is cited as `billboard:1936-03-07` and resolves through the pinexplore document library — document 14979, `citation_ref` set to that ref. Its quotes report `SKIP-PDF`, so they are author-checked, transcribed from the rendered sheet.
