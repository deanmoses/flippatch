# 0297 — IPDB `Specialty`, full corpus

Lands IPDB's `Specialty:` row on the catalog's own classification vocabulary, over every listing IPDB assigns one: **1,605 assertions over 1,467 models**. The full-corpus re-run of [0290](../0290-ipdb-specialties/README.md).

- `specialties.sql` — the analysis: the specialty mapping, the single-valued safety gate, the conflict adjudications, the anchors.
- `gen.py` — the emitter, one entry per `spec_patch_rows` row.
- `patches/0297-ipdb-specialties-census.yaml` — 1,605 entries, attribution `ipdb`.
- `patches/0296-wwii-contract-tag.yaml` — the one new term this corpus needs, minted alone under `flipcommons-catalog`. It lands first because a tag must exist before anything can be tagged with it.
- `patches/0298-wwii-contract-machines.yaml` — the three machines that carry it, under `ipdb`. Separate from 0296 because they are separate sources: coining the term is ours, and who it applies to is IPDB's.

## What changed since 0290

0290 read the same field off archive.org captures of IPDB machine pages, and could only see the listings that happened to have one — 151 of them, a cohort fetched for the 0268 project-date work and skewed toward dateless, never-produced, bingo and EM machines. Its README called that out: "A model with no row here **has not been cleared, it has not been looked at**."

IPDB's **advanced search** answers the question directly — one query per specialty returns every machine carrying it. Those result pages are what pinexplore now ingests, and `px.ipdb.model_specialties` is the census built from them.

| | 0290 (captures) | 0297 (census) |
| --- | ---: | ---: |
| listings covered | 151 | 3,291 |
| assignments | 188 | 4,186 |
| already carried | 79 | 954 |
| **emitted** | **75** | **1,605** |

The census is also **newer** than any capture, and it is one read taken at one moment rather than eight years of drift. It is a strict **superset** of what the captures held — zero archive rows are absent from it — so this is a widening, not a revision, and 0290's assertions stand. `reasserts_a_0290_row` in the checks pins that: its rows must land in `catalog_already_carries`, never here.

## The quote had to move with it

0290's cite form is unchanged — `ipdb:158` with `Specialty: [...] Flipperless` — but what resolves it is not.

flippatch's `ipdb:` resolver used to render `Specialty:` from the cached machine page, as one of the few labels the Xantari dump has no column for. That reached 156 listings. Every quote on the other 3,135 would have failed the verbatim gate against a line that never rendered.

So `scripts/quotes/sources.py` now renders the line from the census instead — the same rows this analysis reads, which is why a quote here is checked against its own source. The move is the module's own standing rule ("the mart is the newer source and always wins") applied the moment a column appeared.

One property of that rendering is load-bearing here. The census records *which* specialties a machine has, not the order IPDB lists them in, and that order is not recoverable — across the 32 captured multi-specialty machines it is neither alphabetical nor by IPDB's specialty id. The resolver therefore renders alphabetically and says so. **The `[...]` ellipsis is what makes that safe**: it absorbs whatever precedes the quoted name, so a one-specialty quote matches whether the name sits first on the line or last. Quoting two specialties as adjacent would not be safe, and nothing here does.

## What is emitted

| heading | field | value | rows |
| --- | --- | --- | ---: |
| Flipperless | tag | `flipperless` | 670 |
| One Ball Game | game_format | `one-ball` | 153 |
| Mechanical Backbox Animation | gameplay_feature | `mechanical-backbox-animations` | 136 |
| Bat Game | game_format | `pitch-and-bat` | 129 |
| Add-A-Ball | reward_type | `add-a-ball` | 94 |
| Bagatelle | game_format | `bagatelle` | 87 |
| Gun Game | game_format | `gun-game` | 72 |
| Novelty Play | reward_type | `novelty` | 65 |
| Bingo Machine | game_format | `bingo-pinball` | 49 |
| Non-Commercial Machine [Home Model] | tag | `home-use` | 41 |
| Widebody | tag | `widebody` | 33 |
| Redemption Game | reward_type | `ticket-payout` | 30 |
| Rolldown Game | game_format | `rolldown` | 29 |
| Cocktail Table | cabinet | `cocktail` | 10 |
| Zipper Flippers | gameplay_feature | `zipper-flippers` | 6 |
| Head-to-Head Play | gameplay_feature | `head-to-head` | 1 |

**Two headings are newly mapped**, and neither needed new vocabulary — only enough rows to be worth mapping. `Gun Game` → `gun-game` (the captures held 8; the census holds 77) and `Redemption Game` → `ticket-payout`, a machine that pays the player in tickets.

The 954 already-carried rows are the corroboration set: classifications somebody had already made by hand from IPDB's prose, with nobody having read a `Specialty:` row.

## The one inference

Unchanged from 0290. A machine IPDB calls a widebody has a wider-than-standard **pinball** cabinet and playfield, so `game_format: pinball` follows from the designation and rides the same changeset as the tag — 24 rows. It is withheld wherever the format slot is otherwise spoken for, by the catalog or by another specialty on the same page. `anchor_big_inning_called_a_pinball` still pins the case the rule was written for: a 1947 Bally automatic-pitch baseball game reading `Specialty: Bat Game Widebody`, which takes the tag and `pitch-and-bat` and must never be called a pinball.

## The single-valued trap, and where it finally bit

`game_format` and `cabinet` hold one value; `tag`, `reward_type` and `gameplay_feature` hold many. For a multi-valued field, not-carried is a gap and asserting fills it. For a single-valued field it can instead mean **the slot is taken**, and asserting would overwrite. This campaign only ever fills an empty slot — 18 rows are refused on that ground.

**The trap has a second face, which 0290's corpus never showed.** Both branches above compare IPDB against a value the catalog already holds. `sockit` (`ipdb:3291`) reads `Specialty: Bat Game One Ball Game` with an EMPTY format slot and both headings mapped — so a naive replay emits two entries setting `game_format` on one record, which the apply engine rejects outright ("field set by more than one entry on this record"). That is the right answer: choosing between two of IPDB's own headings is a reading of the machine, not a replay of the source. `siblings_contest_an_empty_slot` withholds both (2 rows), and `emitted_two_values_into_one_slot` now fails the analysis rather than letting a replay discover it hundreds of assertions in.

0290 argued those refusals are never catalog defects: in all 8 of its cases the value we held was one IPDB also asserted on the same page, so the disagreement was between two of IPDB's own headings. `conflict_value_unsupported_by_page` asserted that property rather than assuming it.

**Across the census it holds for 13 of 18, and five are real disagreements** — the catalog says `bingo-pinball` and IPDB never says it anywhere on the listing. Nothing is emitted for them either way, so `_spec_conflict_adjudicated` records the human ruling rather than deleting an inconvenient check, and `stale_conflict_adjudication` fires if an exemption outlives what it exempts.

One is worth a second look and is flagged rather than resolved here: **`contest`** (`ipdb:563`), a 1941 Keeney the catalog calls `bingo-pinball`. That predates the bingo format entirely — Bally's *Bright Lights*, 1951 — so IPDB's `One Ball Game` is very likely right and the catalog very likely wrong. Correcting it means superseding a live claim, which is a different patch than this one and needs the machine read.

## What is deferred, and why

1,605 rows across 11 headings. A deferral is a decision to emit nothing, not an oversight: `unmapped_specialty` fires the day IPDB prints a heading the reference table has never seen, so the corpus cannot grow a new classification silently.

| heading | rows | why |
| --- | ---: | --- |
| `Payout Machine` | 434 | spans `cash-payout`, `merchant-paid` and `ticket-payout` |
| `Table Top/Counter Game` | 320 | spans the `tabletop` and `countertop` cabinets |
| `Not A Pinball` | 270 | says what a machine is not; what it *is* comes from elsewhere |
| `Converted Game` | 224 | a relationship edge needs a target and a `license_status` |
| `Conversion Kit` | 165 | " |
| `Horserace Game` | 79 | may be a kind of `one-ball` rather than a peer of it |
| `Cue Game` | 41 | no catalog format for a cue-and-ball table |
| `Re-themed Game` | 37 | a relationship edge needs a target and a `license_status` |
| `Vertical Pinball Machine` | 27 | no catalog cabinet for a vertical playfield |
| `Shaker Ball Machine` | 5 | five machines is too thin a base to mint a format from |
| `WWII Contract` | 3 | already asserted, in 0298 |

The three **relationship** headings are deferred on shape rather than vocabulary, and permanently so on this evidence: `model_relationship:` requires a target (`target_machine` XOR `target_label`) and a `license_status`, and IPDB's one word supplies neither — it says a machine was converted, never from what, nor under whose authority. 0290 emitted none of these either.

`Not A Pinball` is the one deferral with a visible exit. Where the catalog has already spoken it **agrees every time** — 53 `miscellaneous`, 51 `slot-machine`, 21 `shuffle`, 7 `video-game`, and zero `pinball` — and 59 models with an empty slot would take `miscellaneous` ("Miscellaneous Non-Pinball Game") on that evidence. It is held back for a later pass because the heading is worth understanding before 270 rows rest on it. The three WWII machines in 0298 are the exception, asserted there because IPDB states `Not A Pinball` on the same row that earns them the tag.

## Coverage

**Effectively complete, and that is the change.** The census covers every listing IPDB assigns a specialty: 3,291 of 6,671. The remaining 3,385 are listings IPDB assigns **no** specialty at all — an absence stated by the source, not a gap in our reading. That is the difference from 0290, where a model with no row simply had not been looked at.

## Totals

From `spec_summary`, against the dev DB at `0295-hearts-spades-sea-belles-names` (6,945 live models):

| metric | value |
| --- | ---: |
| listings_with_a_specialty | 3,291 |
| candidates | 4,184 |
| candidate_models | 3,289 |
| **patch_rows** | **1,605** |
| patch_models | 1,467 |
| patch_rows_implying_pinball | 24 |
| rejected | 2,579 |
| rejected_already_carried | 954 |
| rejected_conflicting | 18 |
| rejected_deferred | 1,605 |
| rejected_sibling_contest | 2 |
