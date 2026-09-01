# 0319–0320 — IPDB's `Payout Machine` specialty, and the `payout` reward type

IPDB's Specialty field carries 27 values; this campaign works the largest one the comparison layer still reports as pointing at absent target vocabulary: **Payout Machine**, on 434 listings, every one of which matches a live model.

## The finding that shaped it

pinexplore mapped the heading to the display string `Payout Machine` rather than a slug, on the reading that it spans two of our reward types — `cash-payout` and `merchant-paid` — and needs per-model research to split them. That research is this campaign, and its answer is that **the heading is not a parent of our specific terms, and the residue cannot be sorted.**

**IPDB defines the heading by who dispenses, not by what.** Its glossary: "These machines have the ability to dispense an award to players who achieved a goal … The awards have taken many forms (free games, tickets, candy, merchandise, etc.), but the most popular was probably coins." The discriminator is that the *machine* pays; what it pays is explicitly open.

**So our three specific terms sit wrong under it, and the catalog's own memberships say so.**

| our reward type | inside the specialty | outside |
| --- | --- | --- |
| `cash-payout` | **7** | 1 |
| `merchant-paid` | 2 | **14** |
| `ticket-payout` | 1 | **31** |

`merchant-paid` is the definitional opposite — its own description reads "the machine identifies a winner but pays nothing itself" — and the two overlaps (`golden-arrow-2`, `vend-a-gift`) are prize-display counter games IPDB filed loosely. `ticket-payout` has its own IPDB heading, `Redemption Game`, where 31 of our 32 live; IPDB treats ticket and payout as siblings. Only `cash-payout` is a real subset.

**And the residue cannot be sorted.** 238 of the 434 IPDB notes say nothing about the reward beyond the flag itself, and there is no second source: 1 of the 434 carries an OPDB id. Where the notes do speak, they usually describe a factory *ordering option* rather than the machine's reward — `zipper`, "Ticket, cash, or check models were available"; `preakness`, "Payout version sold for $149.50. Ticket version sold for $159.50." One IPDB listing covers every configuration, so cash-versus-ticket is not a fact this grain holds.

That last shape needs no new vocabulary: `reward_type` is many-to-many, and the catalog already answers multi-configuration machines by attaching several (`bally-bonus` holds `cash-payout` + `free-play` + `ticket-payout`). What is left over is not variance but ignorance of which form applied — and `payout` is the claim IPDB actually makes and we can actually check: **the machine dispensed the award.**

## The patches

| patch | what |
| --- | --- |
| `0319-payout-reward-type.yaml` | creates `payout` at display order 4, with `Payout Machine` as its alias, and shifts the four terms it displaces down one |
| `0320-payout-machines.yaml` | `payout` on all 434 members, cited to each listing's Specialty row |

`gen.py` emits both from `payout.sql`.

**The record is named `Payout`, not `Payout Machine`.** The vocabulary names the *reward* — Replay, Add-a-Ball, Cash Payout, Merchant-Paid Award — not the machine kind. The machine wording rides as the record's alias, which is also what lets the comparison layer resolve IPDB's phrasing without waiting on a pinexplore rebuild.

**Display order.** `payout` seats at 4, ahead of the specific terms it generalizes, pushing `cash-payout` → 5, `ticket-payout` → 6, `merchant-paid` → 7, `free-play` → 8. This is the same move 0266 made when it inserted `merchant-paid`, under the same `flipcommons-catalog` source that holds the claims being superseded.

## All 434, not just the empty slots

0307 emitted only models with an empty `cabinet`, because a scalar's second value overwrites the first. `reward_type` is a **relationship**: asserting a member adds it, and the resolver unions `exists=true` across sources. So the 23 members that already carry a reward type keep it and gain `payout` beside it — which is the true statement about a machine known to pay cash *and* known to be a payout machine. Nothing is superseded, and **`cash-payout` is left exactly as it was**, on its 8 models.

## What this deliberately does not do

**It does not make reward types hierarchical.** `RewardType` is flat (`../flipcommons/backend/apps/catalog/models/taxonomy.py:327`) while `Theme` carries a claim-controlled `parents` M2M, so a DAG is a flipcommons schema change, not a patch. `payout` and `cash-payout` on one model is the catalog's first coarse-plus-specific pairing — every existing multi-value model holds *alternatives* — and that generalization relation stays unexpressed until somebody decides the DAG is worth it. If it ever is, the tree is `payout → {cash-payout, ticket-payout}` with `merchant-paid` a **sibling**, not a child.

**It does not sort anyone into `cash-payout`.** The ~65 members with explicit coin wording and the ~21 with a priced ticket variant are real, evidenced refinements, and they remain available as later work on top of `payout`.

## Gates

`payout.sql` carries seven, all clean at authoring time:

- `specialty_absent_from_census` — an empty population means the census moved, not that the work is done
- `listing_matches_no_live_model` — the join would drop it silently
- `model_claimed_by_two_listings` — two listings on one model would emit the same entry ref twice
- `member_already_holds_payout` — a no-op diff under a provenance-bearing entry is a hard error at apply
- `payout_slug_already_live` — 0319 creates the record, so the slug must be free
- `display_order_not_as_expected` / `displaced_term_does_not_resolve` — asserts the shift's premise rather than assuming it
- `new_display_order_collides` — the result must be a clean permutation

## Also changed outside `patches/`

- `pinexplore/sql/05_reference.sql` — `Payout Machine` now maps to `payout` instead of the display string. The alias in 0319 means the comparison layer resolves the heading either way; this is the direct statement, and takes effect on the next pinexplore rebuild.
- `flipcommons/docs/DomainModel.md` — `payout` added to RewardType, with the note that `merchant-paid` is its counterpart rather than a narrowing of it. The foundation's `undocumented_vocab` check gates this: a live term the doc never defines fails the build.

## Verified against the dev DB

Replayed 0302–0321 onto the `db.prod.patch-0301.2026-08-31` snapshot. `payout` lands at display order 4 on 434 models with the four displaced terms at 5–8; `cash-payout` still holds its 8. `bally-bonus` is the shape the many-to-many argument predicted — it now carries `payout` beside `cash-payout`, `ticket-payout` and `free-play`, the `payout` claim attributed to `ipdb` and cited to its Specialty row.

In the comparison layer, `Payout Machine` has left `ipdb_specialty_vocabulary_absent` (5 values → 4) and all 434 assignments read as carried, with no finding left open on the heading — through the alias, without waiting on a pinexplore rebuild.

`make validate-in-db` audits clean on these patches. Its two `reward-type.cash-payout` warnings are pre-existing prose in that record's own description, surfaced only because 0319 touched the record's display order; one of them ("New York") would resolve to a machine of that name, not a place.

## Still open

The other unmapped specialties — `Cue Game`, `Horserace Game`, `Not A Pinball`, `Shaker Ball Machine` — are untouched. `Not A Pinball` is the largest remaining at 270 models, and 20 of them are in this campaign's population.
