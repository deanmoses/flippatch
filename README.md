# Flippatch

Flippatch is the authoring home for **data patches** — small YAML files that correct or extend catalog data in already-seeded downstream databases.

This repo holds the patch files (`patches/`), their generator artifacts (`patches/authoring/`), the patch JSON schema, structural validation, and the tooling to publish the patches to Cloudflare R2.

**Flippatch is not the apply engine.** Patches are validated _structurally_ here and shipped verbatim to R2. The authoritative apply model — attribution resolution, the assert/create/retract/remove/delete operations, citation sources, the per-database ledger, and immutability hashing — lives in the consumer that applies them (flipcommons' `ingest_patches`).

## Repos in the ecosystem

- **flippatch** (here) — data patches + authoring generators + transport.
- **flipcommons** (`../flipcommons`) — the live catalog (Django + SvelteKit) and the `ingest_patches` apply engine; the canonical patch documentation.
- **pinexplore** (`../pinexplore`) — research/evidence stores (web scrape cache + DuckDB analysis DB) used to source `note:`/`cite:` text.
- **pindata** (`../pindata`) — the immutable baseline seed catalog (markdown entity files).

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Getting Started

```bash
cp .env.example .env
uv sync
```

## Commands

```bash
make validate   # Structural patch gate + editorial authoring lint
make push       # Push patches to Cloudflare R2 under the flippatch/ prefix
make agent-docs # Regenerate CLAUDE.md and AGENTS.md from docs/AGENTS.src.md
```

## Layout

```text
patches/          Data patches — NNNN-slug.yaml claim corrections
  authoring/      patchkit generator + one dir per generated patch set (audit trail)
schema/           patch.schema.json — structural validation
scripts/          Python tooling, grouped by concern
  patch_validation/ validate_patches.py + lint_patches.py
  cloud_store/    push_to_r2.py
  agent_docs/     build_agent_docs.py + check_agent_docs_edit.sh
docs/             Patches.md (local pointer) + AGENTS.src.md (agent-docs source)
```

See [docs/Patches.md](docs/Patches.md) for more info.
