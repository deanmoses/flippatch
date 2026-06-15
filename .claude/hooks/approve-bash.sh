#!/bin/bash
# PreToolUse hook: auto-approve Bash commands that match allowed prefixes,
# bypassing Claude Code's broken quote-tracking in prefix matching.
#
# This fixes a known bug where single quotes in commands cause
# permission prompts even when the command prefix is explicitly allowed.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Allowed command prefixes — add more as needed
ALLOWED_PREFIXES=(
  "uv run"
  "uv sync"
  "uv add"
  "python3"
  "make validate"
  "make export"
  "make push"
  "make clean"
  "make agent-docs"
  "grep"
  "find"
  "ls"
  "curl"
  "git add"
  "git commit"
  "git push"
  "git status"
  "git diff"
  "git log"
  "git branch"
  "git checkout"
  "git switch"
  "git stash"
  "git show"
  "git fetch"
  "git merge"
  "git rebase"
  "git cherry-pick"
  "git tag"
  "git remote"
  "git rev-parse"
  "git rev-list"
  "git mv"
  "gh pr"
  "gh repo"
  "uvx detect-secrets"
)

for prefix in "${ALLOWED_PREFIXES[@]}"; do
  if [[ "$COMMAND" == "$prefix"* ]]; then
    echo '{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}'
    exit 0
  fi
done

# Not matched — fall through to normal permission handling
exit 0
