# 0173 — Rolldown game format

Classifies the catalog's rolldown machines. First campaign spawned from the non-pinball format probe ([0173-nonpinball-formats](../0173-nonpinball-formats/README.md)); rolldown was the pilot — smallest clean new genre, zero prior coverage, anchored on Williams' *Jolly Joker*.

A rolldown is a flipperless game where the player **rolls balls down** an inclined field into scoring pockets (Skee-Ball kin), often mapped to poker hands or baseball. No plunger — the rolldown-cabinet versions used a ball dispenser. They shared the arcade floor and the factories with pinball, so IPDB catalogs them as pinball.

## The patch: [`patches/0173-rolldown-game-format.yaml`](../../0173-rolldown-game-format.yaml)

One `flipcommons-catalog` patch, hand-written (9 rows — below the generator threshold), assigning nine models to `rolldown`. The format vocabulary itself — the `game-format.rolldown` create at display_order 9, and the bump of `miscellaneous` to 10 so the catch-all stays last — lives in the shared `patches/0110-game-formats.yaml` alongside bingo-pinball, so it exists before this patch's assignments reference it. Every row here is a `cite:` to IPDB free text (rolldown has no structured signal, unlike bingo's trap-hole grid), verbatim-checked by `make verify-quotes`.

```bash
make validate        # structural + editorial lint
make verify-quotes   # every cite quote verbatim vs the IPDB corpus
```

## How the candidate set was vetted

The probe's keyword detector (`rolldown` / `roll-down`) is recall-lossy at both ends, so the nine were hand-vetted from the full candidate pool, and three boundary questions went to the museum. The calls:

### Included (9)

- **Self-described (7)** — the model's own IPDB record names it a rolldown: *Bumper Bowling* (Daval 1937, "might be the first rolldown game"), *Tally Roll* (Firestone 1946), *Box Score* (Williams 1948), *Bubbles (Rolldown)* (Genco 1948), *Hi-Score Pool* (Sebring 1949, a cue-stick rolldown), *Jolly Joker* (Williams 1955), *Baseball* (Genco, via a distributor ad it quotes: "Roll Down Baseball Game, like Genco Playball").
- **Cross-referenced (2)** — the model's own record is silent on format; another Genco record names it a rolldown, so the `cite:` targets that record (DataPatchAuthoring: "the cite can target a different record than the claim"). *Total Roll* (Genco 1945) via *Step-Up*'s note; *Play Ball* (Genco 1942) via *Baseball*'s note. Only findable this way — the same recall gap bingo hit with its cross-refs.

### Excluded

- **Variant-cabinet pinballs** — *Hawaii* (United 1947), *Singapore* (United 1947), *Nudgy* (Bally): primarily flipperless **pinballs** that were *also available* in a rolldown cabinet. Museum call: the model's identity is the pinball; the rolldown was a secondary cabinet, so leave them (untyped) pinball, don't type rolldown.
- **Referential false positives** — *Step-Up* (Genco 1946) and *Bubbles* (Genco 1947): the word "rolldown" in their notes is about a *different* game (*Total Roll*, and the 1948 *Bubbles (Rolldown)* respectively), not themselves.
- **Held for later** — *Baby In The Hole* (Data East 1989): "based on rolldown games" ≠ "is a rolldown". Museum call: don't type it on that evidence; revisit once the certain ones are in.

## Status

- **Patch written, validates, quotes verified** (`0173-rolldown-game-format.yaml`, 9 assignments). Not yet committed/pushed — that's the user's call.
- **Open follow-ups**: a cited encyclopedia description for the format — added to the shared `patches/0174-game-format-descriptions.yaml` (the `flipcommons-ai-desc-game-format` patch that already carries bingo-pinball's); and a second look at *Baby In The Hole* and any other 1980s+ rolldown-mechanic redemption games.
