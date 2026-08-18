# Gameplay feature descriptions — playbook

Working notes for the sessions writing the remaining gameplay-feature descriptions. The brief is [GameplayFeatureDescriptions.md](GameplayFeatureDescriptions.md); the authoring rules live in `~/dev/flipcommons/docs/DataPatchDescriptionAuthoring.md` and are current — several of its rules (factual sentence-case headings, hyperlinking named sites in the text) were added from review feedback on this campaign's first two patches. Read it fresh; don't assume this file repeats it.

## State (as of 2026-08-15)

- **Done**: 0251 (calibration pair: shaker-motors, magic-squares), 0252 (bingo card family: bingo-cards, super-cards, magic-lines, magic-screen, mystic-lines, bally-hole). Both reviewed by the user through several feedback rounds — copy their register.
- **Remaining**: ~134 features without descriptions. Worklist: `make analyze FILE=campaigns/0239-descriptions/candidates.sql Q="FROM desc_candidates WHERE entity_type='gameplay-feature';"`
- Patches 0245/0249 are open slots reserved for catalog-fill work (see [gaps.jsonl](gaps.jsonl)); do NOT reserve new holes. Description patches take the next fresh number.
- 0244 (2026-08-18) filled the bingo/vocabulary gaps rows: created gameplay-feature records `next-game-award`, `in-line-scoring`, `section-scoring`, `backglasses`; parented `bally-hole` under trap-holes + next-game-award and the two backglass variants under `backglasses`. All four new records still need descriptions under this campaign (they surface on the worklist query). The roto gaps row (united-bingos) was presented and not approved — it stays in gaps.jsonl.

## Classification → register

The catalog's own hierarchy (`gameplay_features.parents`/`children`) does the classifying:

- **Root features** (no parent) get the mechanism register: definitional lead, then whatever story the feature actually has. Story dictates length — no character targets, no paragraph quotas. Historically specific mechanisms (the bingo family, Bally Hole) carry footnotes like anything else.
- **Positional/count variants** (parent carries the story) get a short defining paragraph: what differs — position, count, consequence. Write parents before or alongside children; every parent not yet described is itself on the worklist.
- **Branded names** (InvisiGlass, the Expression Lighting family, LumaLift, …) get a cited gloss: who brands it, what generic thing it is (wikilinked to its parent), when it appeared. Not a full entry.

## Batch plan (family-grouped; consistency within a family beats everything)

1. Backbox animations (backbox-animations + mechanical/light children; n>100 each)
2. Lane/gate/post positional variants — the biggest cluster (~50): kickback/kicker/drop lanes, ball-return gates and rollunders, dual/triple inlanes-outlanes, posts. Mostly variant register, catalog-data-heavy.
3. Toys family (toys → interactive/static → bash/ball-holding/animatronic/pop-up); order the parent chain.
4. Modern lighting + glass: interactive-lighting tree, Stern Expression family, the anti-reflection-glass family with its branded children. Maker marketing pages, many already cached.
5. Audio + universal parts: speakers, subwoofers, stereo-sound, speech, bells, chimes, knockers (0251's shaker-motors is the register model).
6. Bingo-adjacent stragglers: roulette-wheels, time-clocks, numbered-plaques, magic-glass… cdyn sources already cached.

## Process per batch

1. Anchor from the catalog first: first carrier per feature (`model_gameplay_features` joined to `models`), sibling features, counts. Catalog facts need no cites.
2. Research through the pinexplore web cache (`web_fetch.py` / `web_cache.py search|section|quote`); for bingo material, bingo.cdyn.com machine pages plus its `machines/features.html` and `machines/glossary.html`, the Kineticist bingo guide and IPDB entries are all cached and seeded as roots.
3. Verify every quote span BEFORE writing it into the patch: `make show-source ARGS="<ref> --check '<span>'"`.
4. One patch per family, `flipcommons-ai-desc-gameplay-feature`, descriptions only.
5. `make validate` + `make verify-quote-verbatim ARGS="<NNNN>"`, then apply via the snapshot loop — **ask the user which snapshot**; this campaign has been using `db.prod.patch-0238.2026-08-13.sqlite3`.
6. Research bycatch (missing records, missing fields, missing parents) appends rows to [gaps.jsonl](gaps.jsonl) — fields: `group`, `kind` (missing-field | new-record), `entity_type`, `target`, `field`, `claimed_value`, `source_urls`, `evidence_note`. Group by manufacturer/family so an acquisition session gets all its sources together.

## Decisions the user has made (don't relitigate)

- **Story dictates length.** The doc's old 600–900 char band is dead; don't anchor on size, don't pack facts "where there's room". One job per block; sections when the story has more than one chapter.
- **Lead sentence is a standalone definition** — enforced by the `description-definitional-lead` lint (first sentence must carry is/are/was/were, from patch 0239 on).
- **Anecdotes prefer two roots.** Where only one root exists, flag it; the user decides. **Approved cdyn-only claims (2026-08-15)**: the "turning corners" nickname, Palm Beach as first super cards, Broadway introducing the Bally Hole, Variety as first Magic Lines.
- **Gameplay features are lint-exempt from inline-cite/two-source rules** but cite specific facts (dates, firsts, named machines beyond catalog data) anyway.
- **Gloss jargon in place or link it**: a term the reader can't be assumed to know (in-line scoring, columns of the card, backglass) is either wikilinked to its record or defined in a clause. If the vocabulary lacks the record, that's a gaps.jsonl row.
- **Machine mentions link the `title` by default** — `model` only when the claim is specific to one build within a multi-model title (per the doc's Model vs title rule; the dating example `*[[title:medieval-madness]]* (1997, …)` is the default form). Example: 0251 keeps `model:earthshaker` because that title also holds a 2013 retheme and the first-shaker claim belongs to the 1989 build; every single-model-title machine mention links the title.
