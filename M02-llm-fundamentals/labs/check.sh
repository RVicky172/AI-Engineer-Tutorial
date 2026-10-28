#!/usr/bin/env bash
# Run every quality gate for the shared package and every M02 lab. Exit non-zero on the first
# failure. Offline only: no model calls, no spend. Live runs are separate (see SETUP.md).
set -euo pipefail

cd "$(dirname "$0")"
# venv layout differs: bin/ on macOS and Linux, Scripts/ on Windows (Git Bash)
BIN="$(pwd)/.venv/bin"
[ -d "$BIN" ] || BIN="$(pwd)/.venv/Scripts"

for project in common lab-0*/; do
  echo "=== ${project%/} ==="
  (
    cd "$project"
    "$BIN/pytest" -q
    "$BIN/ruff" check .
    "$BIN/ruff" format --check .
    "$BIN/mypy" src tests $([ -d evals ] && echo evals)
  )
done
echo "All M02 labs green."
