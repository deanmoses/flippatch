# 0227 — Document publisher roots

Seeds the publisher roots for the new `document` citation type ([DocumentCitations.md](../../../flipcommons/docs/plans/citations/DocumentCitations.md)) — the "roots first" slice of its recommended scope. 53 manufacturer publisher roots plus the USPTO patent-office root, roots only: no documents are seeded here. What the patch buys is that every subsequent `<publisher>:<document-slug>` cite (`williams:wpc-95-schematic-manual`, `uspto:us4373731`) has a root to resolve under; the documents themselves arrive with the patches that cite them.

## Files

- [publishers.csv](publishers.csv) — the hand-reviewed mapping: IPDB filename prefix(es) → catalog manufacturer slug, with the point-in-time document counts and the judgement notes.
- [roots.sql](roots.sql) — the analysis gate: joins the mapping back to the live catalog. `roots_checks` fails on a slug that is not a live manufacturer or a duplicate mapping; root names are read live from the catalog so a rename never drifts a root.
- [gen.py](gen.py) — pure emitter: rows → `sources:` nodes via patchkit's `source_root(slug=…)`, plus the explicit USPTO node.

## Where the publisher list comes from

IPDB document filenames lead with the publisher (`Williams_1996_Tales_of_the_Arabian_Nights_Operations_Manual…`), and pinexplore's `ipdb_documents` view parses that prefix out as `publisher_prefix`. The list is every prefix with **≥ 2 distinct document basenames** in the full trove (53 prefixes as of 2026-08-12), merged where several prefixes name one publisher and mapped by hand to catalog manufacturer slugs. Root slugs are the catalog manufacturer slugs **verbatim** — a naming convention only, never a join key (DocumentCitations.md § Naming and slugs).

Counts in the CSV are distinct basenames over the whole trove, recorded as point-in-time evidence for review ordering — they are not re-derived by the gate, and they will drift as IPDB grows. The prefix parse has a long tail of junk (filenames whose "prefix" is a whole title because no year follows the publisher); those one-off prefixes were inspected and either folded into their real publisher's row or dropped, and single-document publishers (Arkon, Barni, Joctronic, JVH, Mills, Stoner, …) are deferred — each is one `sources:` node whenever a cite first needs it.

## Judgement calls (regroup decisions of 2026-08-12)

- **Every mapped publisher, not a volume cutoff.** All ≥ 2-doc prefixes that map to a catalog manufacturer are included (~50 roots rather than the plan's "roughly 40"). A root is one hand-reviewable node; inclusive avoids a second roots patch.
- **Both Sterns.** The `Stern` prefix spans two catalog manufacturers: `stern-electronics` (1977–1985) and the modern `stern-pinball`. Both get roots; the 692 shared documents split by era when they are seeded. Their descriptions state the eras, since both roots render as "Stern"-ish names in a picker.
- **Gottlieb is included with zero IPDB documents.** IPDB hosts no Gottlieb files at all — its rights holder enforces copyright — so a strictly trove-derived list would omit one of the big three. Gottlieb manuals exist elsewhere (archive.org, Pinball Resource reproductions), and an empty publisher root is a legitimate long-term state by design.
- **USPTO only.** The one patent-office root; IPDB's patent population is US 46, ES 2, GB 1, and an office root is one node added on demand (DocumentCitations.md § Patents). Its slug is minted (`uspto`) — the office is not a manufacturer.
- **Prefix merges settled against the catalog** (each verified by checking where the prefixed games' models actually sit): `Atari` + `Atari_Inc` → `atari`; `Lowen` + `NSM` → `nsm` (Löwen-Automaten — Cosmic Flash 1985, Hot Fire Birds, The Games 1985 are all `nsm` models); `Bell` + `Nuova` + `Nuova_Bell` → `bell-games` (Cosmic Flash 1984, Saturn 2, Space Hawks, F1 Grand Prix, U-Boat 65 are all `bell-games` models); `Juegos` + `Juegos_Populares` → `juegos-populares`; `Petaco_S_A` → `petaco`.
- **Sega stays one root.** The prefix spans 1970s Sega (Japan) and 1990s Sega Pinball, but the catalog holds both eras as one `sega` manufacturer, and the root follows the catalog.
- **Strategy guides and rulesheets get no roots.** They stay `web` citations per the plan (§ Third-party guides stay web for now) — at 18% publisher-prefix coverage, a publisher root would be an invented issuing body.
- **Jersey Jack is undercounted** (year-first filenames the prefix regex misses: WOZ, The Hobbit, Dialed In manuals). It makes the list anyway; the undercount only affects its position in the table.

## Reproducing the derivation

The publisher distribution, against pinexplore's `explore.duckdb`:

```sql
SELECT publisher_prefix, count(DISTINCT file_basename) AS docs
FROM ipdb_documents
WHERE publisher_prefix IS NOT NULL
GROUP BY 1 HAVING docs >= 2 ORDER BY docs DESC;
```

The mapping gate, from this repo:

```bash
make analyze FILE=../flippatch/campaigns/0227-document-publisher-roots/roots.sql PREFIX=roots
```
