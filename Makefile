.PHONY: validate lint-patches-all verify-quotes lint-descriptions verify-citations extract-page sweep analyze push agent-docs lint typecheck test check

# Validate data patches against the patch schema (structural gate) plus the
# editorial authoring lint. Run this before push.
validate:
	uv run python3 scripts/patch_validation/validate_patches.py
	uv run python3 scripts/patch_validation/lint_patches.py

# Review mode: run the editorial lint over EVERY patch under EVERY rule,
# ignoring RULE_SINCE grandfathering — for seeing what a new rule would have
# caught in immutable history. Expect old-rule noise from pre-0039 patches;
# filter to the prose word-choice findings with:
#   make lint-patches-all 2>&1 | grep -E "uses '|cross-reference"
lint-patches-all:
	uv run python3 scripts/patch_validation/lint_patches.py --all

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

# ── AI corpus sweep ────────────────────────
# Judge a candidate set's corpus-vs-catalog deltas: one trusted-tier call per
# candidate over its full source note, deterministic gates, then REVIEW.md +
# results.json artifacts. Needs the flipcommons dev DB; judging also needs
# ANTHROPIC_API_KEY + the pinexplore evidence stores. --no-ai reconciles free.
#
#   make sweep ARGS="patches/authoring/0128-relationships/sweep/candidates.jsonl --no-ai"
#   make sweep ARGS="patches/authoring/0128-relationships/sweep/candidates.jsonl --limit 10"
sweep:
	@PYTHONPATH=scripts uv run python3 -m ai_corpus_sweep.cli $(ARGS)

# ── DuckDB catalog analysis ────────────────────────
# Read-only analysis over the LIVE flipcommons catalog — the way to ask the catalog
# anything, ad-hoc or as a patch campaign. Reuses flipcommons' shared DuckDB layer
# VERBATIM: the foundation (scripts/analysis/catalog.sql) and its runner
# (scripts/analysis/analysis). See flipcommons' scripts/analysis/README.md.
#
# FILE names a campaign's analysis file; omit it to query the foundation alone.
# Everything runs from the flipcommons checkout (override with FLIPCOMMONS_DIR) so an
# analysis file's `.read` and the foundation's `ATTACH backend/db.sqlite3` resolve — a
# FILE is abspath'd first, since it is given relative to YOUR cwd. duckdb must be on
# PATH. Nothing is written; not a commit gate.
#
#   make analyze Q="SELECT count(*) FROM models WHERE year IS NULL;"   # ad-hoc
#   make analyze CMD=describe                                         # the view reference
#   make analyze CMD=describe ARGS=models                             # one view + columns
#   make analyze FILE=patches/authoring/0172-bingo-game-format/bingo.sql PREFIX=bingo
#   make analyze FILE=.../bingo.sql PREFIX=bingo ARGS=--markdown
#   make analyze FILE=.../bingo.sql CMD=ui                 # live GUI at localhost:4213
#   make analyze FILE=.../bingo.sql Q="FROM bingo_review;" # one view from the analysis
# Q is exported so the recipe reads it as a shell variable ("$$Q"), not by Make
# text-interpolation ('$(Q)'). Interpolation pasted the query into a single-quoted
# guard, so any ' in the SQL (a 'string' literal, an IN ('a','b') list) closed the
# quote and broke the shell. Via the environment the value is never re-tokenized.
export Q
analyze:
	@FC="$$(PYTHONPATH=scripts uv run python3 -c 'import os; from common.paths import load_env, REPO_ROOT; load_env(); print(os.environ.get("FLIPCOMMONS_DIR") or (REPO_ROOT.parent / "flipcommons"))')"; \
	if [ -n '$(FILE)' ]; then AN="$(abspath $(FILE))"; else AN="$$FC/scripts/analysis/catalog.sql"; fi; \
	cd "$$FC" && \
	if [ -n "$$Q" ]; then scripts/analysis/analysis query "$$AN" "$$Q" $(ARGS); \
	elif [ '$(CMD)' = describe ]; then scripts/analysis/analysis describe "$$AN" $(ARGS); \
	else test -n "$(PREFIX)" -o -n '$(CMD)' || { echo 'usage: make analyze [FILE=<analysis.sql>] PREFIX=<name> | Q="<sql>" | CMD=describe|ui|snapshot [ARGS=...]'; exit 2; }; \
	  scripts/analysis/analysis $(or $(CMD),run) "$$AN" $(PREFIX) $(ARGS); fi

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
