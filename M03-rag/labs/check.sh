#!/usr/bin/env bash
# Run every quality gate for the shared package and every M03 lab. Exit non-zero on the first
# failure. No model calls and no AWS calls; the store tests need the local pgvector container,
# so this starts it first. The local embedding model test downloads ~130 MB once.
set -euo pipefail

cd "$(dirname "$0")"
BIN="$(pwd)/.venv/bin"
[ -d "$BIN" ] || BIN="$(pwd)/.venv/Scripts"

docker compose up -d --wait

for project in common lab-0*/; do
  [ -f "$project/pyproject.toml" ] || continue  # labs not built yet
  echo "=== ${project%/} ==="
  (
    cd "$project"
    "$BIN/pytest" -q -p no:cacheprovider
    "$BIN/ruff" check .
    "$BIN/ruff" format --check .
    "$BIN/mypy" src tests
  )
done
echo "All M03 labs green."
