.PHONY: validate push agent-docs lint typecheck test check

# Validate data patches against the patch schema (structural gate) plus the
# editorial authoring lint. Run this before push.
validate:
	uv run python3 scripts/patch_validation/validate_patches.py
	uv run python3 scripts/patch_validation/lint_patches.py

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
