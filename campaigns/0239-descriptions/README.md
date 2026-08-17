# Descriptions

We haven't written descriptions for some of our newer records. Let's figure out how to do that.

## Scope

We want descriptions for all these records:

- **Bounded vocab**: cabinet, display type, display subtype, game format, production status, reward type, tag, technology generation, technology subgeneration
- **Unbounded vocab**: gameplay features
- **Non-vocab**: systems, active manufacturers

Excluded: titles, models, people, corporate entities.

Do NOT replace any descriptions that have already been written. Only create descriptions for records without any.

Priority is the order they are listed in this doc, even within a category.

The list is at [candidates.sql](./candidates.sql).

## Authoring guidance

We aim to improve quality over our past descriptions.

We just wrote this doc about how to author good descriptions: `~/dev/flipcommons/docs/DataPatchDescriptionAuthoring.md`. It supplements the usual docs like `~/dev/flipcommons/docs/DataPatches.md` and `~/dev/flipcommons/docs/DataPatchAuthoring.md`. We're not sure if the new doc is useful or not. Give feedback on it. I'm not confident about the per-entity-type guidance; that portion of the doc was AI-generated and I suspect simply restates what previous data patches have done, rather than what actually makes for a good description. And apparently it used "exemplar" which implies that the previous examples are perfect, which they are not. Write a length that feels right to give the entry a real encyclopedia entry. I expect it will be longer than previous records.

`DataPatchDescriptionAuthoring.md` requires a MINIMUM of 4 citation sources. We have historically not been good about meeting that bar. However, since we last wrote descriptions, Pinexplore's [web cache system](~dev/pinexplore/docs/WebCache.md) has gotten much better at fetching and reading docs. So the 4 bar stands. The user may grant an exception for a legitimately sparse subject. These exceptions make it difficult to create a deterministic lint for this.

Also: we are trying to lessen our dependence on IPDB. When quoting from IPDB, try to also find another source. Treat IPDB as corroborating and the other(s) as the backbone.

## Linting

As we author descriptions, if we find that they don't meet the bar in whatever way (such as user feedback), let's try to add deterministic (not AI) linting to prevent the failure from recurring.

## Analytics

We recently substantially changed the Flipcommons analytics system; it should now be simpler to use. LMK if there's any issues in understanding it or using it, or if you have ideas for improving it.

## Gameplay feature descriptions

See [GameplayFeatureDescriptions.md](./GameplayFeatureDescriptions.md).
