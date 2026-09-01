# 0322–0324 — IPDB's `Shaker Ball Machine` specialty

IPDB's Specialty field carries 27 values; this campaign works the smallest one the comparison layer still reported as pointing at absent target vocabulary: **Shaker Ball Machine**, on 5 listings, all 5 matching a live model.

## The finding that shaped it

pinexplore mapped the heading to an absent `game-format` value, on the reading that IPDB's Specialty row names what KIND of machine a listing is. Reading all five ruled that out: every member is an ordinary machine of some other format carrying an extra **control**. Three already hold `bingo-pinball` correctly and the two Allied Leisure games are flipper pinballs with pop bumpers and slingshots, so spending the single-valued format slot on the control would have overwritten a correct value on three and misdescribed the other two.

So the heading is a **gameplay feature**, and a root one. Every parent in that DAG is a generic device whose children are varieties of it — `flippers` → kinds of flipper, `playfields` → kinds of playfield — and a device that *acts on* the playfield is not a kind of playfield. Every other player-operated device sits at the root for the same reason: `flippers`, `kickback`, `ball-save`, `magna-save`, `shaker-motors`.

## Why two terms

**`Shaker Ball` is Allied Leisure's marketing name**, quoted as such in IPDB's own Notable Features on *Sea Hunt* and *Spooksville*: the joysticks "manually push up to electromechanically nudge the playfield upwards in a jolting 'Shaker Ball' action". IPDB then borrowed the phrase as its generic heading and hung it on three machines that never used the words — a 1954 Bally bingo with a "Bump-feature" (`ipdb:1166`) and two c.1971 Japanese payout machines with a "Skill Bumper feature" (`ipdb:6759`, `ipdb:6763`).

So the catalog takes a generic term for the heading, `playfield-shakers`, and keeps Allied's name as a child of it. Two gates assert that split rather than assuming it: `allied_wording_absent` (both Allied listings must carry the quoted sentence) and `non_allied_uses_allied_wording` (the other three must not say "Shaker Ball" anywhere). Both are clean.

**The parent is asserted on all five, including the two Allied machines**, rather than left to be inferred from the child. The comparison layer's gameplay-feature carriage is an exact slug match with no descendant walk (`assertions.sql`), so a member carrying only `shaker-ball` would be reported as missing the assertion forever. Co-carrying a feature and its parent is ordinary here — 102 models carry both `kickback` and `left-outlane-kickbacks`.

## The mechanism, and what it is not

A playfield shaker is a player-operated control that jolts or shifts the playfield to influence a ball already in play. The impulse is deliberate and discrete — Sega's jolts "the playfield forward about an inch", Hi-Fi's moves the surface far enough that a fixed post strikes a rolling ball — and on three of the five it is rationed (ten per game on Hi-Fi; 2/4/7 on the Japanese pair, bought with the tokens that start the game).

It is often interlocked with the tilt circuit, in **both** directions: Bally suppresses the tilt so the bump is safe, Allied leaves it armed so too sharp a push tilts the ball.

Two disambiguations earn their place in the description:

- **Not a `shaker-motors`.** A shaker motor shakes the playfield too — it is bolted into the same cabinet — so the two are *not* told apart by what moves. They are told apart by who moves it and why: the motor is fired by the game program and exists for sensation. The description deliberately does **not** claim a shaker motor cannot move the ball; nothing sourced supports that.
- **Not a `tilting-playfields`.** Agency does not separate these either — all four tilting-playfield machines are player-worked. The axis is impulse against steering: a tilting playfield is held at an angle to aim, in as many directions as the machine allows, while Allied's listings rule that out in as many words ("The joysticks do not nudge the playfield in any other direction except upwards").

## The patches

| patch | attribution | what |
| --- | --- | --- |
| `0322-playfield-shaker-features.yaml` | `flipcommons-catalog` | creates `playfield-shakers` and `shaker-ball` under it |
| `0323-playfield-shaker-machines.yaml` | `ipdb` | the feature on all 5, plus Allied's name on 2 |
| `0324-playfield-shaker-descriptions.yaml` | `flipcommons-ai-desc-gameplay-feature` | both descriptions |

`gen.py` emits 0323 from `shakers.sql`; 0322 and 0324 are hand-written. **Order matters** — the vocabulary must exist before anything carries it, which `feature_vocabulary_absent` enforces.

Each of the five cites its own listing's Specialty row as `Specialty: [...] Shaker Ball Machine`, leaning on the `[...]` ellipsis per `scripts/quotes/sources.py`: the census records *which* specialties a machine carries, not the order the page prints them. On *Sea Hunt* and *Spooksville* the heading is the only specialty on the line, and the ellipsis absorbs an empty prefix — checked, not assumed. Those two carry a second cite, the Notable Features sentence that earns them `shaker-ball`. All 7 verify with `make verify-quote-verbatim ARGS="0323"`, and 0324's 8 quotes with `ARGS="0324"`.

No member is overwritten: all five had neither feature.

## Gates

`shakers.sql` carries six, all clean:

- `specialty_absent_from_census` — an empty population means the census moved, not that the work is done
- `listing_matches_no_model` — a member with nowhere to land
- `allied_wording_absent` / `non_allied_uses_allied_wording` — the two-term split, asserted in both directions
- `allied_does_not_resolve` — drift guard on the literal two-row relation
- `feature_vocabulary_absent` — 0322 must land before 0323

`shk_patch_rows` is **deliberately not filtered** on what the catalog already carries. An applied patch is immutable, so a generator has to be able to re-render it and byte-compare; an emit set that empties itself the moment the patch applies can never prove it would still emit the same file.

## Also changed outside `patches/`

- `pinexplore/sql/05_reference.sql` — `Shaker Ball Machine` now maps to the `playfield-shakers` gameplay feature instead of an absent game format. **Needs a pinexplore rebuild** (done) before the comparison layer stops reporting it under `ipdb_specialty_vocabulary_absent`.
- `flipcommons/docs/DomainModel.md` — unchanged. Its GameplayFeature section describes the DAG rather than enumerating its 327 members.

## Still open

The other unmapped specialties — `Cue Game` (41), `Horserace Game` (79), `Not A Pinball` (270) — are untouched. `Not A Pinball` is the one with a visible exit: where the catalog has already spoken it agrees every time.
