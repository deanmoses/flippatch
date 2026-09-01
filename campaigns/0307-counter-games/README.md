# 0307–0310 — IPDB's `Table Top/Counter Game` specialty, and retiring `tabletop`

IPDB's Specialty field carries 27 values; this campaign works the largest one the comparison layer still reported as pointing at absent target vocabulary: **Table Top/Counter Game**, on 321 listings, 320 of which match a live model.

## The finding that shaped it

pinexplore mapped the heading to the display string `Table Top/Counter Game` rather than a slug, on the reading that it spans two of our cabinets — `tabletop` and `countertop` — and needs per-model research to split them. That research is this campaign, and its answer is that **there is nothing to split**.

**Every member is a coin-operated counter game.** 236 of the 320 are pre-1940 and 65 more carry no year. The 19 post-war members are the ones that might have held a home machine, and none does: `whiz-bowler` (1954) is "a ball gum vender", `zipper-3` has "A coin view window on the back of the game allows the [operator]", `players-choice-2` was "displayed as a new product at the 1966 MOA Convention", `skill-cards` "could be placed on a light aluminum stand, or mounted on the wall with brackets", and the four Williams 4-IN-1s are a 100-unit operator run. Not one home or consumer machine is in the set — which is the only thing `tabletop` describes that `countertop` does not.

**There is no wording to split on either, and the wording that exists is a trap.** 245 of the 320 IPDB notes contain neither "counter" nor "table". Of the 21 that say `pin table`, twenty use it to name a *different, legged sibling model* ("The pin table version is Whirlpool's 1932 'Whirlpool'"). In 1930s trade usage a pin table is the **legged** form — the opposite of the modern reading — which IPDB states outright on `official-counter` (`ipdb:1694`): "'Official Pin Table' is often affixed to this counter version even though the term 'pin table' refers to games that have legs". Three further members are British counter games with "PIN TABLE" printed on the glass, which IPDB's own notes call counter games.

**The two `tabletop` models are that trap, already sprung.** Neither `betcha-ball-2` nor `lucky-star-3` carries the specialty — IPDB excluded them deliberately, because both are the legged siblings of counter games it *does* list (`betcha-ball`, `lucky-star`, both already `countertop`). `lucky-star-3`'s note opens "This is a pin table."; `betcha-ball-2` is Zenith's Model GRT, "combination Game on Radio Table (a pin table)". They were labelled `tabletop` by reading "table" out of "pin table".

So the heading maps to `countertop`, `tabletop` is retired, and the two legged machines are corrected.

## The patches

| patch | what |
| --- | --- |
| `0307-pin-table-cabinets.yaml` | `floor` for the two legged pin tables previously called `tabletop` |
| `0308-pure-mechanical-description.yaml` | unlinks the retiring cabinet from the one description that referenced it |
| `0309-retire-tabletop-cabinet.yaml` | soft-deletes the `tabletop` cabinet |
| `0310-countertop-games.yaml` | `countertop` on all 308 members with an empty slot, cited to each listing's Specialty row |

`gen.py` emits 0307 and 0310 from `counter_games.sql`. 0308 and 0309 are hand-written: a rehydrated description re-edit and a delete, neither of which patchkit emits.

**Order matters.** The delete planner refuses while an active PROTECT referrer would dangle, so the two models must move off `tabletop` (0307) and the prose link must go (0308) before 0309 lands.

## Why `floor` for the two, and not an empty slot

Both machines are positively evidenced as free-standing — `lucky-star-3` on its own legs, `betcha-ball-2` on the radio table it was sold mounted to — and the cabinet vocabulary uses `floor` as the general counterpart to `countertop` in its own prose ("the countertop format gradually gave way to the `floor` cabinet"). The dimensions in `floor`'s description (six feet, 200–300 lb, "stable since the 1950s") are the modern norm, not a boundary.

**This is the one genuine judgment call in the series.** The alternative reading is that a 1932 legged pin table is nothing our vocabulary names, and the two should carry `retract: [cabinet]` and no value — the state the other 308 were in until 0310. Flip `counter_pin_tables` in `counter_games.sql` and the `fields=` line in `gen.py` to change it; nothing else in the series depends on which way it goes.

## The 308 rest on IPDB's own classification

0310 is attributed to `ipdb` and each entry cites its own listing's Specialty row as `Specialty: [...] Table Top/Counter Game`. The quote names one specialty and leans on the `[...]` ellipsis, per `scripts/quotes/sources.py`: the census records *which* specialties a machine carries, not the order the page prints them, so a quote asserting two are adjacent would assert something the store cannot back. All 308 verify with `make verify-quote-verbatim ARGS="0310"`.

No member is overwritten: all 308 had an empty cabinet slot, and `counter_checks` fails the run if any member ever holds a cabinet other than `countertop` — a real disagreement with the source is not something a blanket assertion is entitled to paper over.

## Gates

`counter_games.sql` carries six, all clean at authoring time:

- `specialty_absent_from_census` — an empty population means the census moved, not that the work is done
- `member_holds_a_non_counter_cabinet` — a real disagreement with IPDB
- `pin_table_now_carries_the_specialty` — asserts 0307's premise rather than assuming it: IPDB must keep the two legged models out of the heading
- `pin_table_does_not_resolve` — drift guard on the literal two-row relation
- `tabletop_referrer_unaccounted` / `tabletop_wikilink_unaccounted` — every referrer the delete would strand must be one 0307 or 0308 clears

## Also changed outside `patches/`

- `pinexplore/sql/05_reference.sql` — `Table Top/Counter Game` now maps to `countertop` instead of the display string. **Needs a pinexplore rebuild** before the comparison layer stops reporting the specialty under `ipdb_specialty_vocabulary_absent` and starts tracking these 308 as ordinary carried assertions.
- `flipcommons/docs/DomainModel.md` — `tabletop` removed from Cabinet, with the reason it is not coming back.

## Still open

The other unmapped specialties — Cue Game, Horserace Game, Not A Pinball, Payout Machine, Shaker Ball Machine — are untouched. `Payout Machine` is the one that still has the shape this heading was thought to have: IPDB's single word over our `cash-payout` and `merchant-paid`, where the page does not say which.
