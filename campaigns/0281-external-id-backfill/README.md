# 0281 — External ID backfill, 2023 and newer

Links catalog records to their IPDB and OPDB counterparts for machines from 2023 onward. Part of a four-patch pass: `0280` (manufacturer id), `0281` (model ids, generated here), `0282` (title group ids), `0283` (two models OPDB lists that the catalog lacked).

## What went in

| population     | rows | evidence                                                                     |
| -------------- | ---- | ---------------------------------------------------------------------------- |
| `opdb_named`   | 9    | the comparison layer offers it — name, manufacturer and year all resolve      |
| `opdb_edition` | 9    | hand-approved: same machine, OPDB's own wording for the edition               |
| `ipdb`         | 7    | the layer offers it, and the listing is citable — real `ipdb:` cite and quote |
| **total**      | 25   |                                                                              |

Alongside: one manufacturer id (0280), eight title group ids (0282), two created models (0283). Verified after applying — models with an OPDB id 2311 → 2331, with an IPDB id 6664 → 6671, titles 1690 → 1698.

## The scope line, and why it is 2023

Only machines dated 2023 or later. These are the ones that changed since the last acquisition; older disagreements are re-litigations of matches adjudicated once already, and several are entangled with unresolved title-grouping splits where linking would silently take a side.

The band 2020–2022 is **empty** in every bucket, so 2023 is a natural seam rather than an arbitrary cut. Checked before choosing it: the next rows below the line are one 2013 model and four 2010–19 records, then the pre-2010 backlog.

## Judgment calls

**The nine edition pairs are a human override.** The layer classifies these listings `absent` — it matches names through `name_norm`, which only lowercases and strips punctuation, so it cannot bridge `(CE)` to `(Collector's Edition)`. No re-run will ever surface them, and left alone they would eventually be created as duplicates of machines the catalog already holds. The pairs are approved row by row in `bf_edition_pairs` and gated on the two legs a machine *can* be checked on — manufacturer and year. Nothing can machine-verify that `(CE)` means `(Collector's Edition)`; that judgment is what the table records. Note OPDB is sometimes the *longer* of the two names (`Houdini: Master of Mystery (100th Anniversary)` against `Houdini 100th Anniversary`).

**No OPDB cite anywhere.** An `opdb:` cite resolves to a cached `opdb.org/machines/<id>` page, and that URL is keyed by a numeric database id the published export does not carry — the Group-Model-Alias identifier is not addressable there. The OPDB rows carry their provenance in the note instead. The IPDB rows have no such problem and are cited properly, each quote cut from the same mart columns the resolver renders, so it is verbatim by construction.

**Models were linked before titles**, inverting the layer's documented stage order. That order exists because a group verdict normally reads its machines' links; here the model links are decided by name-and-maker and need nothing from the titles, while landing them first upgraded **all eight** titles from name-and-year evidence to linked-machine evidence. Before: one title backed by a linked machine, seven weaker, two resting on name and year alone. After: eight of eight. The inversion is specific to this clean set and would not hold for the pre-2010 rows.

**One row was unlocked mid-pass.** `alice-goes-to-wonderland` was `maker_unresolved` — Wonderland Amusements carried no OPDB id, so no candidate search ran at all. Applying 0280 supplied it, and the re-run reclassified the model as a clean backfill. It is the ninth `opdb_named` row, and it exists only because the manufacturer patch ran first.

## Deliberately left out

- **Ten models whose IPDB chain is blocked** (`ipdb_id_chain = 'titles_disagree'`): `cobra-2`, `cowboy-eight-ball`, `cowboy-eight-ball-2`, `defender`, `flush`, `star-king`, `time-machine-2`, `top-sound`, `trick-shooter`, `viking-king`. Each carries an IPDB number that OPDB's record also cites, so the identity is not in doubt at model grain — but OPDB groups them into a family the catalog splits across titles, and the guard refuses to let a model link paper over that. All are pre-2010 and out of scope. Worth knowing: dismissing the split finding will **not** unblock them, because the guard compares live title links rather than adjudications, so they need deliberately hand-authored entries whose notes name the disagreement.
- **The pre-2010 backlog** — 22 model ids and the older title work.
- **Two genuinely absent records**, `Pokémon (Home Edition)` and `Predator (Trophy Edition)`, created as stubs in 0283 and awaiting a fill-out pass.

## Re-running

The analysis gates on `bf_checks`, which asserts every target still holds no id in the field being set. Once this patch is applied those checks **fail by design** — that guard is what stops a second emission overwriting live links. Regenerating therefore requires a database restored to before 0281.
