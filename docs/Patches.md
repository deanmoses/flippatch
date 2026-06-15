# Data Patches

A **data patch** is a small YAML files that corrects or extends the pinball catalog data in already-seeded downstream databases. Patches are the schema-migration model applied to data: the catalog seed is an immutable baseline, and patches are an append-only, numbered log replayed on top of it in every environment.

**This repo is the authoring home and the transport — not the apply engine.** Patches are authored here, their generator artifacts live in [`patches/authoring/`](../patches/authoring/), they are validated _structurally_ here, and `make push` ships them to R2. However, the authoritative apply model — attribution resolution, the assert/create/retract/remove/delete operations, citation sources, the per-database ledger, and immutability hashing — lives in the consumer that applies them (flipcommons' `ingest_patches`), not here.

The baseline seed catalog these patches target lives in a separate repo, [pindata](https://github.com/deanmoses/pindata) (`../pindata`).

## Read the canonical docs before authoring

This file is a thin local pointer. The authoritative, current patch documentation lives in **flipcommons** and cross-links itself — **do not author a patch from flippatch's docs alone.** In `../flipcommons/docs/`:

- **DataPatches.md** — the full patch file format and apply model: every operation (assert/create/retract/remove/delete), reserved keys (`expect:`/`note:`/`cite:`), citation `sources:`, the ledger, and limitations.
- **DataPatchAuthoring.md** — authoring a _good_ patch: attribution, `expect:` guards, verbatim `note:`, record descriptions, and the localhost snapshot-validate loop.
- **DataPatchKit.md** — generating large curated patches with the shared `patchkit` helper (which lives here at [`patches/authoring/patchkit.py`](../patches/authoring/patchkit.py)).
- **DataPatchReviewing.md** — the patch review checklist.
- **DomainModel.md** — the catalog entity hierarchy claims target.

For the repo topology (flippatch / pindata / flipcommons / pinexplore) and the end-to-end authoring loop, see the **Data Patches** section of [AGENTS.src.md](AGENTS.src.md) (rendered into [CLAUDE.md](../CLAUDE.md) and [AGENTS.md](../AGENTS.md)).

## Location and naming

Patches live at the top level in `patches/`, named `NNNN-slug.yaml`:

- The four-digit `NNNN` prefix **orders application** and must be unique.
- The filename stem (e.g. `0001-prototype-tags`) is the **patch id**.

They ride the `make push` → R2 path, shipped **verbatim** (not exported to JSON) under the `flippatch/patches/` prefix, with a `flippatch/manifest.json` for download integrity and the file list. Downstream databases fetch them with `make pull-patches` (defined in the consuming repo) and apply with `ingest_patches`.

## What flippatch validates

```bash
make validate
# or directly:
uv run python3 scripts/patch_validation/validate_patches.py
uv run python3 scripts/patch_validation/lint_patches.py
```

`scripts/patch_validation/validate_patches.py` is a fast **structural** gate so a typo is caught before publishing: filename format, unique numeric prefixes, strict JSON-shaped YAML, and conformance to `schema/patch.schema.json`. Strict parsing mirrors the downstream loader — duplicate mapping keys error, and values must be JSON-shaped (YAML 1.1 coercion is off, so a bare `1996-01-01` stays a string and `no` stays `"no"`). `scripts/patch_validation/lint_patches.py` adds editorial authoring checks (citation hygiene, public-note discipline, drift-guard coverage, description rules).

Authoritative validation — entity resolution, the `expect:` drift guard, field classification, attribution existence — happens downstream when the patch is applied. Preview that locally with the flipcommons SQLite snapshot loop (see DataPatchAuthoring.md), not with flippatch's structural gate alone.

## What flippatch does _not_ do

Applying patches, resolving attribution, the per-database applied-once ledger, and immutability checks are all the consumer's responsibility (flipcommons' `ingest_patches`). Flippatch validates and ships; it never applies.
