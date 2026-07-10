# AI Lint Tool

## The problem

We've been using AI to author lots of data patches. I’ve had a headache trying to police AI-written descriptions of records, despite extensive documentation in how to do it correctly in the Flipcommons project's DataPatchAuthoring.md. I often see the AI doing the following:

- Fail to wikilink something that’s obviously linkable and in the Flipcommons project's DomainModel.md.
- Write sentences that are way too close to a sentence or phrase or unique turn of expression in the source material. That's a type of plagarism.
- Lift the narrative spine of the description from a single source. That’s a type of plagiarism.
- Simply write poorly. The description will lack good organization, one or more sentences will fail to be clear and understandable, it doesn't use paragraphs to separate different thoughts.
- Fail to use our in-house style rules, such as no Oxford commas.
- Write facts without including a citation.
- Not follow our standard format for a record type... for example, we have a standard formula that works pretty well for manufacturers, that starts by mentioning their geographic location.
- Mention a model that’s not yet in the catalog, which is good in the sense that we discover another model, but it doesn’t follow up and acquire the model.

Basically we want a way of enforcing good-journalism standards — attribution, corroboration, no lifting — and good writing style.

## The solution

I want some sort of checker that can be run on one or more descriptions or data patches, that vets the description(s) using a mix of static analysis and AI models.

This would be run on the developer's inner-loop, while the developer uses AI to iterate on data patches, to vet a patch's
`description:` fields and citation `quote:`s _before_ the patch is ingested. I imagine the tool would be mostly initiated by the interactive AI session itself (not the developer). The AI session would use the results to improve the description.

Eventually I’m thinking the nugget of this idea could grow into something we run in Flipcommons on every description save, grading the description. But that’s in the future, and in the Flipcommons repo, not here.

## Two tools

The solution consists of the following tools / scripts:

- [Description checker](#description-checker): checks descriptions
- [Citation verifier](#citation-verifier): verifies a citation

### Description checker

Run via `make lint-descriptions`. Toggle rules with `--rules a,b` / `--disable a,b`.

The rules fall into two families. The **provenance & journalism** family is built today; the **house-style & quality** family is planned — it covers the writing-quality and in-house-style complaints in [The problem](#the-problem) that the first four rules don't address. That family is a deliberate follow-on, not a dropped concern.

**Provenance & journalism (built):**

| rule                  | severity | what it catches                                                                                                 |
| --------------------- | -------- | --------------------------------------------------------------------------------------------------------------- |
| `missing-wikilink`    | warning  | prose names a catalog entity but doesn't `[[wikilink]]` it (dash/number/spacing-insensitive match; AI confirms) |
| `unknown-model`       | info     | prose names a real machine/manufacturer not in the catalog yet — a discovery to acquire                         |
| `plagiarism`          | warning  | a sentence copies its cited source's distinctive phrasing too closely (overlap prefilter → AI verdict)          |
| `single-source-spine` | warning  | the whole description's narrative spine is lifted from one dominant source                                      |

**House style & quality (planned):**

| rule               | tier         | what it catches                                                                                                                                                           |
| ------------------ | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `oxford-comma`     | static       | an Oxford comma, against house style — pure regex, no model                                                                                                               |
| `missing-citation` | static       | a fact-asserting sentence carrying no footnote cite                                                                                                                       |
| `paragraphing`     | static       | a multi-thought description shipped as one undivided block                                                                                                                |
| `prose-quality`    | AI (trusted) | unclear, disorganized, or awkward writing a human editor would send back                                                                                                  |
| `record-format`    | AI (trusted) | a record type's house formula unmet (e.g. a manufacturer description not opening with its geographic location); formula sourced from DataPatchAuthoring.md, not hardcoded |

The static rules are the cheapest, highest-signal wins; the two AI rules are subjective/semantic and run on the trusted tier (see [Environmental requirements](#environmental-requirements)).

```sh
make lint-descriptions ARGS="0059"                               # one patch
make lint-descriptions ARGS="--rules plagiarism,single-source-spine"
make lint-descriptions ARGS="--json --min-severity warning"
```

### Citation verifier

Run via `make verify-citations`

One rule, `quote-supports-claim`, spanning **both** description footnotes and
scalar/edit claim cites: for each `(claim, quote)` pair it first gates on
verify-quotes (the quote must be verbatim in its source), then asks the model
whether the quote actually _supports_ the claim — catching a real,
correctly-transcribed quote that nonetheless doesn't establish the value it's
cited for (e.g. a `game_format: pinball` cite whose quote never says pinball).

```sh
make verify-citations ARGS="0059"
```

## Exit codes & CI

Both exit non-zero when any `warning` finding exists (so they can gate a
pre-ingest workflow later) and zero otherwise. They are **not** part of
`make check` / `make validate` — run them deliberately.

## Regenerating the catalog table map

`scripts/common/catalog/entity_index.py` carries a generated mirror of flipcommons' wikilinkable-model registry (entity type → table, alias tables). AiLint imports `EntityIndex` from `common.catalog.entity_index` for `missing-wikilink` / `unknown-model`; regenerate the map if flipcommons adds an entity type — see that module's docstring for the one-liner.

## Environmental requirements

This can only be run on a developer's localhost because it requires multiple Github projects to be checked out.

- **Sibling checkouts** (shared-root convention; override with `FLIPCOMMONS_DIR`
  / `PINEXPLORE_DIR`):
  - `../flipcommons/backend/db.sqlite3` — the catalog registry (what's linkable
    / what exists). Needed for `missing-wikilink` and `unknown-model`.
  - `../pinexplore` with its web cache (`make pull`) + `explore.duckdb`
    (`make explore`) — the plagiarism/spine source corpus and the
    verify-quotes gate. When absent, plagiarism falls back to the patch's inline
    `quote:` and `single-source-spine` is skipped.
- **`ANTHROPIC_API_KEY`** — required. The tools fail fast without it; there is no 'graceful degradation' to some static-only mode.
  Model tier is per rule (see [AiCommon.md](AiCommon.md) §5): the description rules run on the cheap tier (Haiku 4.5), `quote-supports-claim` on the trusted tier for its polarity-sensitive judgment. There is no per-run model override — changing a tier means changing its `CHEAP_MODEL` / `TRUSTED_MODEL` constant, so a tool can't be silently re-tiered (e.g. the trusted judgment downgraded to cheap).
