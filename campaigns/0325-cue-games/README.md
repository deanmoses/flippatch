# 0325–0327 — IPDB's `Cue Game` and `Horserace Game` specialties

IPDB's Specialty field carries 27 values. This campaign works the two "game format" headings the comparison layer still reported as pointing at absent target vocabulary — **Cue Game** (41 listings) and **Horserace Game** (79) — and finds that only one of them is a format.

## Cue Game is a format the catalog lacked

A cue game is a coin-operated table on which the player drives the ball with a hand-held cue, pool-fashion, rather than launching it with a plunger. The population is coherent: the 1931 Karom Golf tables and their carom cousins, the 1955–56 electric-pool wave from Williams, Genco, United and Chicago Coin, and US Billiards' 1966 *Electro-Pool*. Nothing in the format vocabulary said that, so `cue-game` is minted (it rides `0302-new-vocab-terms`, seated at display order 11 with `miscellaneous` bumped to 12 so it stays last) and asserted on every member with an empty format slot.

**The single-valued slot rule holds, as in 0297 and 0310: only an empty slot is filled.** Ten members already hold a format and are left alone. Eight are Witzig Corinthian tables on which IPDB asserts `Bagatelle` too — a contest between two of IPDB's own headings, not a disagreement with us. Two are live claims that would need superseding by hand after reading the machine: `spot-pool-3` (`miscellaneous`) and `hi-score-pool-3` (`rolldown`). `member_holds_unexplained_format` fails the run if a member ever holds a format the analysis does not account for.

## Horserace Game is a theme, not a format

68 of the 79 listings also carry `One Ball Game`, 69 of the 79 catalog models hold `one-ball`, and every one of the 10 with an empty format slot is a listing IPDB itself declines to call a one-ball ("we cannot find any information … to verify if it was a one-ball payout"). The heading names the machine's *subject*, and the catalog already agrees: 71 of the 79 carry the `horse-racing` theme. So the heading lands as that theme on the 8 that do not, asserts nothing about format, and the 10 empty slots stay empty on IPDB's own evidence. `horserace_member_holds_non_one_ball_format` pins the premise: a member holding any format other than `one-ball` would be a heading meaning something this campaign has not read.

## The patches

| patch | attribution | what |
| --- | --- | --- |
| `0302-new-vocab-terms.yaml` (existing, unapplied) | `flipcommons-catalog` | creates `cue-game`; bumps `miscellaneous` to stay last |
| `0325-cue-game-description.yaml` | `flipcommons-ai-desc-game-format` | a deliberately minimal description, enough to satisfy validation |
| `0326-cue-game-machines.yaml` | `ipdb` | `cue-game` on the 31 members with an empty slot |
| `0327-horserace-themes.yaml` | `ipdb` | `horse-racing` on the 8 unthemed members |

`gen.py` emits 0326 and 0327 from `cue_games.sql`; the mint and the description are hand-written. **Order matters**: the format must exist before anything carries it. That is not gated in the analysis — 0302 lands in the same rebuild as 0326, so the summary reports `cue_game_vocabulary_present` instead and the apply engine refuses 0326 on its own if the mint is missing.

Each assertion cites its own listing's Specialty row as `Specialty: [...] Cue Game` / `Specialty: [...] Horserace Game`, leaning on the `[...]` ellipsis per `scripts/quotes/sources.py`: the census records *which* specialties a listing carries, not the order the page prints them. All 31 + 8 verify with `make verify-quote-verbatim ARGS="0326"` and `ARGS="0327"`; the description's 2 with `ARGS="0325"`.

## Totals

From `cue_summary`, against the dev DB at `0324` (0302 not yet applied):

| metric | value |
| --- | ---: |
| cue_population | 41 |
| cue_slot_empty / **cue_patch_rows** | **31** |
| cue_ipdb_also_bagatelle | 8 |
| cue_held_back | 2 |
| hr_population | 79 |
| hr_ipdb_also_one_ball | 68 |
| hr_already_themed | 71 |
| **hr_patch_rows** | **8** |

## Also changed outside `patches/`

- `pinexplore/sql/05_reference.sql` — `Cue Game` now maps to `cue-game` instead of the display string. **Needs a pinexplore rebuild** before the comparison layer stops reporting it under `ipdb_specialty_vocabulary_absent`. `Horserace Game` is left mapped to its display string: the layer's carriage CASE in `assertions.sql` has no `theme` branch, and adding one is a layer change, not a mapping edit.
- `flipcommons/docs/DomainModel.md` — `cue-game` added to GameFormat.

## Still open

`Not A Pinball` (270) — where the catalog has spoken it agrees every time; the 56 empty slots want a format read off the notes or IPDB's other headings, with `miscellaneous` as the honest fallback. `Payout Machine` (434) now has `payout` to land on (0319–0320).
