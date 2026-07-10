.PHONY: validate verify-quotes lint-descriptions verify-citations extract-page push agent-docs lint typecheck test check

# Validate data patches against the patch schema (structural gate) plus the
# editorial authoring lint. Run this before push.
validate:
	uv run python3 scripts/patch_validation/validate_patches.py
	uv run python3 scripts/patch_validation/lint_patches.py

# ── Citation quote verifier ────────────────────────
# Verify every cite: quote is verbatim against its cached source text.
# Needs the sister pinexplore repo as a sibling checkout (override with
# PINEXPLORE_DIR) with its web cache pulled and explore.duckdb built.
# Not part of the `make validate` commit gate.
verify-quotes:
	uv run python3 scripts/quote_verify/verify_quotes.py

# ── AI description linter ────────────────────────
# Needs ANTHROPIC_API_KEY, the flipcommons dev DB,  pinexplore caches.
# Not part of the `make validate` commit gate.
#
#   make lint-descriptions ARGS="0059"
#   make lint-descriptions ARGS="--rules plagiarism,single-source-spine"
lint-descriptions:
	PYTHONPATH=scripts uv run python3 -m ai_lint.description_check.cli $(ARGS)

# ── AI citation verifier ────────────────────────
# Validate that the quote actually backs up the claim.
# Needs ANTHROPIC_API_KEY, the flipcommons dev DB,  pinexplore caches.
# Not part of the `make validate` commit gate.
#
#   make verify-citations  ARGS="0059 0114"   # must name at least one patch id
verify-citations:
	PYTHONPATH=scripts uv run python3 -m ai_lint.citation_verify.cli $(ARGS)

# ── AI page-data extractor ────────────────────────
# Extracts a packet of candidate claims with quote-checked evidence.
# Needs ANTHROPIC_API_KEY + the pinexplore web cache.
#
#   make extract-page ARGS="ipdb:5632"
#   make extract-page ARGS="https://example.com/page"
extract-page:
	@PYTHONPATH=scripts uv run python3 -m ai_page_extract.cli $(ARGS)

# Lint + format-check the Python tooling (same ruff config pre-commit uses).
lint:
	uv run ruff check .
	uv run ruff format --check .

# Strict type-check the Python tooling.
typecheck:
	uv run mypy .

# Run the tooling unit tests.
test:
	uv run pytest

# Everything pre-commit gates on, in one shot.
check: lint typecheck test validate

# Push data patches (patches/*.yaml) verbatim to Cloudflare R2 under the
# flippatch/ prefix, with a manifest. Requires R2_* credentials in the
# environment or .env.
push:
	uv run python3 scripts/cloud_store/push_to_r2.py

# Regenerate CLAUDE.md and AGENTS.md from docs/AGENTS.src.md.
agent-docs:
	python3 scripts/agent_docs/build_agent_docs.py
