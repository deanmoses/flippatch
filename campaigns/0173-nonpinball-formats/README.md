# 0173 — Non-pinball game format candidate hunt

An audit-trail probe (no patch of its own) that finds catalog models which should carry a **non-pinball `game_format`** but don't yet. Each format the review confirms becomes its own downstream campaign — vocab + assignments — the way [0172](../0172-bingo-game-format/README.md) (bingo) and [0173-rolldown](../0173-rolldown-game-format/README.md) did.

## Why this exists

The original format sweep ([0010](../0010-game-formats/README.md)) matched only IPDB notes that **self-label** "not a pinball" — high precision, but blind to the genres IPDB **catalogs as pinball**. Bingo was the first of those rescued (its own 307-model campaign, 0172). Rolldown, one-ball payout, and the poker/keno consoles were still stranded: real non-pinball genres with no format to assign. This probe hunts that blind spot.

The seed was the six grid-reuse machines 0172 hand-flagged "not a bingo, but not a pinball either" — Evans _Poker-eno_ and _Tango_, Williams _Jolly Joker_ and _Space Glider_, _Rallye_, _L'Hirondelle_. _Jolly Joker_ is now typed `rolldown`; the other five still sit untyped.

## Running it: [formats.sql](formats.sql)

A DuckDB analysis over the live flipcommons catalog, built on its shared [analysis foundation](../../../../flipcommons/scripts/analysis/README.md) — read that for how `make analyze` resolves paths, prints the `analysis_context` watermark, and gates on the `_checks` view. Needs the `duckdb` CLI and the flipcommons dev DB.

```bash
F=campaigns/0173-nonpinball-formats/formats.sql
make analyze FILE=$F PREFIX=format                                            # summary, gated on checks
make analyze FILE=$F Q="FROM format_review WHERE proposed_format='one-ball';" # per-format queue
make analyze FILE=$F Q="FROM format_candidates ORDER BY proposed_format;"     # full candidate list
make analyze FILE=$F Q="FROM format_review_payout;"                           # keyword-invisible payout machines
make analyze FILE=$F Q="FROM format_review_pinmech;"                          # what pin_mech held out
make analyze FILE=$F Q="FROM format_excluded_review;"                         # confirmed false positives
```

## How candidates are detected

One keyword detector per format over the model's free text (`ipdb_notes` + `ipdb_notable_features` + `description`), plus three structural detectors (decoded M2Ms from the foundation) that do most of the precision work. All are heuristics — every row still wants source review before it becomes a claim.

- **`pin_mech`** — a structured pinball mechanism (`flippers` / `pop-bumpers` / `slingshots`) marks a pinball on its face, usually a bowling- or baseball-**themed** flipper game. These are held **out** of candidates (surfaced in `format_review_pinmech`, never silently dropped). **Caveat:** pre-1947 pin games are flipperless too (the flipper arrived with Gottlieb's 1947 _Humpty Dumpty_), so _absence_ of `pin_mech` is not proof of non-pinball for early games.
- **`is_grid`** — the structured 25-`trap-holes` grid (the 5×5 bingo card). Post-0172 the untyped holders are the grid-reuse non-bingos, whose IPDB text is bare (`"Trap holes (25). Equipped with Electropak."`) — keyword-invisible, grid-only. The only way _Poker-eno_ and _Tango_ surface.
- **`has_payout_reward`** — a `Cash Payout` / `Ticket Payout` reward type (foundation `rewards` view): the keyword-invisible **gambling** signal. It surfaces 9 untyped payout consoles (one-ball / slot ancestors like _Ace_, _Derby Champ_, _Midget Racer_) whose bare notes no keyword detector catches — a pure recall gain (they don't overlap the keyword candidates). Not auto-classified, since payout spans several formats and the odd modern pinball carries a stray payout reward (the empty-noted 2026 Stern _Pokémon_ is the data quirk that proves it); instead they land in `format_review_payout` for hand-assignment, and every keyword candidate's row now shows its `reward_types` for at-a-glance vetting.

Three other foundation views were evaluated as extra signals and are all **inert on this population**, so none is used (recorded so a later pass needn't re-check): relationship **edges** (`model_edges`) — only 1/140 candidates carries any; **title-mates** (`title_size`, the variant-cabinet idea via a shared Title) — every candidate is alone in its Title; and **tags** — the vocabulary (`widebody` / `prototype` / `remake` / `home-use`) is all pinball-production attributes, nothing genre-relevant. The mechanism detectors do now read through the foundation's decoded `model_gameplay_features` view rather than the raw M2M tables (behavior-identical, but convention-following and live-feature-filtered).

Proposed formats split two ways: **new vocab** this probe scouts (`rolldown`, `one-ball`, `poker-console`, and the `pin-table(review)` / `pop-up-novelty` grid tags), and **existing vocab to recall-extend** where the 0010 sweep under-collected (`slot-machine`, `gun-game`, `shuffle`, `bagatelle`, `pitch-and-bat`).

## The vetting

Human review is encoded as id-keyed lookups in the analysis's reference section, so re-running re-derives the vetted list and `format_checks` flags any lookup gone stale:

- **`_format_excluded`** — confirmed false positives, with the reason (e.g. _Pool Alley_, which IPDB says "looks like a puck/ball bowler but it is neither").
- **`_grid_reuse`** — the five still-untyped grid-reuse non-bingos from 0172, each tagged with the format its exclusion reasoning implies. The only channel that finds the keyword-invisible consoles.

`format_checks` guards: no `pin_mech` row leaks into candidates, no `_format_excluded` entry is stale, no `_grid_reuse` id has lost its grid.

## Status — post-one-ball

`make analyze … PREFIX=format` is green. **140 candidates**, 83 themed-pinball held out by `pin_mech`, 1 confirmed false positive, plus **9 keyword-invisible payout machines** the reward signal recovers (`format_review_payout`). Counts are a live snapshot, re-derived each run. By proposed format:

| Proposed format          | Candidates | New / existing vocab | Notes                                                                                   |
| ------------------------ | ---------- | -------------------- | --------------------------------------------------------------------------------------- |
| gun-game                 | 31         | existing             | recall-extend `gun-game`                                                                 |
| one-ball                 | 30         | **new** (shipped)    | shipped as [0175](../0175-one-ball-game-format/README.md): 26 typed, 11 vetted out/held |
| pitch-and-bat (baseball) | 25         | existing             | recall-extend `pitch-and-bat`                                                            |
| slot-machine             | 20         | existing             | 1930s reel/payout gambling                                                               |
| bagatelle                | 17         | existing             | pre-flipper plunger tables; era-ambiguous                                               |
| rolldown                 | 6          | **new** (shipped)    | 0173 typed 9; the 6 left are the vetted-out variant-cabinet pinballs + FPs               |
| poker-console            | 4          | **new** (parked)     | vetted — collapses to 1 sourceable model (_Poker-eno_); see below                       |
| shuffle (bowler)         | 4          | existing             | recall-extend `shuffle`                                                                  |
| pin-table(review)        | 2          | —                    | _Rallye_, _L'Hirondelle_ — may just be early flipperless pinball, an editorial call     |
| pop-up-novelty           | 1          | —                    | _Space Glider_                                                                           |

Counts are detector recall, not vetted claims — each queue still needs a source pass.

## poker-console — vetted and parked (do not re-attempt without new evidence)

The "poker-console (4)" queue was source-vetted and **does not hold up as a 4-model campaign**. Of the four candidates, only one is cleanly attributable, so no patch was authored. Findings, so the next session need not redo the pass:

- **Poker-eno** (Evans 1936, `ipdb:4271`) — the only solid member. The name is literally the "Poke-eno" poker-keno game; IPDB gives the ball/grid mechanism ("5 ball play. Trap holes (25). A ball falling in playfield holes lights corresponding light on backglass."). A poker/keno-scored payout pin-table (42″×21″), not a console in the strict sense.
- **Tango** (Evans 1935, `ipdb:2498`) — **unsourceable as poker.** IPDB notes are bare ("Trap holes (25). Equipped with Electropak."); no source ties it to poker vs keno vs another odds game. The only basis is the 0172 `_grid_reuse` read ("Evans grid console, not a bingo"), which is our own analysis, not a citable source. The H.C. Evans archive (`rwatts.cdyn.com/Machines/hcevans.html`) does not cover it. Held.
- **Hot Cha!** (ESCO 1932, `ipdb:1241`) — **excluded.** A six-game counter novelty (Hot Cha / Play Ball / Football / Shoot the Moon / Domino Pool / Indian Dice); no poker. A spurious keyword match.
- **Players Choice** (Betco 1966, `ipdb:6997`) — **excluded.** A gumball-vending counter game whose poker angle is IPDB's own *presumption* ("we presume 5 balls are played to score … a poker hand") about one of several interchangeable *educational* boards (50 States, presidents, birds). Primarily a kids' novelty vendor.

So the campaign's premise — clear the _Poker-eno_ + _Tango_ grid-reuse pair — only half-holds (Tango can't be sourced), leaving a would-be 1-member vocab. Deliberately **not** minted. Revisit only if a source surfaces that states Tango's (or another candidate's) poker/keno scoring, or if the `poker-console` name is reconsidered (Poker-eno is a pin-table, not a console — candidate names weighed were `poker`, `poker-keno`, `poker-pinball`).

## Recommended next steps

- **`one-ball`** — ✅ **done.** Shipped as the [0175 one-ball campaign](../0175-one-ball-game-format/README.md): vocab added to `0110-game-formats.yaml`, 26 models assigned in `0175-one-ball-game-format.yaml`, 11 vetted out/held (including _Derby Champ_ and _Midget Racer_ from `format_review_payout`). See that dir's README for the full assigned/held breakdown.
- **`poker-console`** — parked; see the section above. Not worth stepping into without new evidence.
- **The recall-extension formats** (gun / baseball / slot / bagatelle / bowler) — a lighter pass to top up existing vocab, but pollution-prone; vet hard before authoring. The rolldown pilot is the cautionary tale: its detector both over- and under-collected, so the vetted set was 9, not the raw 13.
- **The 1932–46 gambling block** — a third of the untyped pool, no pinball mechanism, where "flipperless pin game" vs "payout device" is genuinely hard because _all_ early pinball was flipperless. Its own project, not a format detector.
