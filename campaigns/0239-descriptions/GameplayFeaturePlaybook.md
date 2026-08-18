# Gameplay feature descriptions — playbook

Working notes for the sessions writing the remaining gameplay-feature descriptions. The brief is [GameplayFeatureDescriptions.md](GameplayFeatureDescriptions.md); the authoring rules live in `~/dev/flipcommons/docs/DataPatchDescriptionAuthoring.md` and are current — several of its rules (factual sentence-case headings, hyperlinking named sites in the text) were added from review feedback on this campaign's first two patches. Read it fresh; don't assume this file repeats it.

## State (as of 2026-08-18)

- **Remaining worklist**: `make analyze FILE=campaigns/0239-descriptions/candidates.sql Q="FROM desc_candidates WHERE entity_type='gameplay-feature';"`
- Patches 0245/0249 are open slots reserved for catalog-fill work (see [gaps.jsonl](gaps.jsonl)); do NOT reserve new holes. Description patches take the next fresh number.

## Classification → register

The catalog's own hierarchy (`gameplay_features.parents`/`children`) does the classifying:

- **Root features** (no parent) get the mechanism register: definitional lead, then whatever story the feature actually has. Story dictates length — no character targets, no paragraph quotas. Historically specific mechanisms (the bingo family, Bally Hole) carry footnotes like anything else.
- **Positional/count variants** (parent carries the story) get a short defining paragraph: what differs — position, count, consequence. Write parents before or alongside children; every parent not yet described is itself on the worklist.
- **Branded names** (InvisiGlass, the Expression Lighting family, LumaLift, …) get a cited gloss: who brands it, what generic thing it is (wikilinked to its parent), when it appeared. Not a full entry.

## Remaining batches

- **Modern lighting + glass**: interactive-lighting tree, Stern Expression family, the anti-reflection-glass family with its branded children. Maker marketing pages, many already cached.
- **Audio + universal parts**: speakers, subwoofers, stereo-sound, speech, bells, chimes, knockers (0251's shaker-motors is the register model).

## Process per batch

1. Anchor from the catalog first: first carrier per feature (`model_gameplay_features` joined to `models`), sibling features, counts. Catalog facts need no cites.
2. Research through the pinexplore web cache (`web_fetch.py` / `web_cache.py search|section|quote`); for bingo material, bingo.cdyn.com machine pages plus its `machines/features.html` and `machines/glossary.html`, the Kineticist bingo guide and IPDB entries are all cached and seeded as roots.
3. Verify every quote span BEFORE writing it into the patch: `make show-source ARGS="<ref> --check '<span>'"`.
4. One patch per family, `flipcommons-ai-desc-gameplay-feature`, descriptions only.
5. `make validate` + `make verify-quote-verbatim ARGS="<NNNN>"`, then apply via the snapshot loop — **ask the user which snapshot**; this campaign has been using `db.prod.patch-0238.2026-08-13.sqlite3`.
6. `make validate-in-db` — the DB-aware catalog audit. Fix its **errors** (wrong-grain links, parenthetical year/maker mismatches); triage its **warnings** with the user (uncarried-link fires on deliberate contrast mentions too). Several standing warnings on 0243/0250/0251 are confirmed-deliberate (Bright Lights, Humpty Dumpty, Melody, Cover Girl, Variety, "Star Wars") — leave them. From 0260/0261, four more are confirmed-deliberate: `in-line-scoring` → Border Beauty (the machine that abolished it), `section-scoring` → Carnival Queen and `time-clocks` → _Time_, both real attachment gaps now in gaps.jsonl, and `numbered-plaques` → Funhouse (Remake Limited Edition), whose model grain is deliberate per the Model vs title rule below.
7. Research bycatch (missing records, missing fields, missing parents) appends rows to [gaps.jsonl](gaps.jsonl) — fields: `group`, `kind` (missing-field | new-record), `entity_type`, `target`, `field`, `claimed_value`, `source_urls`, `evidence_note`. Group by manufacturer/family so an acquisition session gets all its sources together.

## Sources

Beyond the per-family research, three pages carry most of the definitional weight for the lane/gate/post vocabulary and are cached:

- **[IPDB's own glossary](https://www.ipdb.org/glossary.php)** — the catalog's feature vocabulary is largely IPDB's, so its glossary is the definition of record for terms nothing else defines (drop lane, crossover return lane, free ball return lane, dual outlanes, lane change, blocking gate, up-post, mini-post screw). IPDB **403s the fetcher**, so it is cached through the Wayback `id_` form and cited as `ref: https://www.ipdb.org/glossary.php` + `archive: https://web.archive.org/web/20240118022958id_/…`, which resolves for `verify-quote-verbatim` and attributes to the IPDB root.
- **[Wikipedia's Glossary of pinball terms](https://en.wikipedia.org/wiki/Glossary_of_pinball_terms)** — the independent second root for kickback, inlane, outlane, peg, stopper, magic post, rollunder.
- **[Pinball News, "It's in the post"](https://www.pinballnews.com/learn/ukposts.html)** — the UK All-Skill system, the whole story behind 0255's centre up-post.

## Decisions the user has made (don't relitigate)

- **Story dictates length.** Don't anchor on size, don't pack facts "where there's room". One job per block; sections when the story has more than one chapter.
- **Lead sentence is a standalone definition** — enforced by the `description-definitional-lead` lint (first sentence must carry is/are/was/were, from patch 0239 on).
- **Anecdotes prefer two roots.** Where only one root exists, flag it; the user decides. **Approved cdyn-only claims (2026-08-15)**: the "turning corners" nickname, Palm Beach as first super cards, Broadway introducing the Bally Hole, Variety as first Magic Lines.
- **Gameplay features are lint-exempt from inline-cite/two-source rules** but cite specific facts (dates, firsts, named machines beyond catalog data) anyway.
- **Gloss jargon in place or link it**: a term the reader can't be assumed to know is either wikilinked to its record or defined in a clause. If the vocabulary lacks the record, that's a gaps.jsonl row. Since 0244, `in-line-scoring`, `section-scoring`, `backglasses` and `next-game-award` ARE records — link them instead of glossing. (Optional cleanup: 0251/0252 predate those records and still gloss these terms in bare prose; they are mutable and could be retrofitted with links.)
- **Never narrate the record set.** No "the machines recorded here", "this entry", "listed below" — a description is an essay about the thing, and the reader is on one page and cannot resolve "here". Say what is true of the machines instead. Enforced by the `prose-record-set` lint over descriptions and notes, from patch 0255 on.
- **A "first …" claim needs an inline cite in its own sentence** — enforced by the `description-unsourced-first` lint. The catalog cannot establish firsts; only a source can say it.
- **Machine mentions link the `title` by default** — `model` only when the claim is specific to one build within a multi-model title (per the doc's Model vs title rule; the dating example `*[[title:medieval-madness]]* (1997, …)` is the default form). Example: 0251 keeps `model:earthshaker` because that title also holds a 2013 retheme and the first-shaker claim belongs to the 1989 build; every single-model-title machine mention links the title.
