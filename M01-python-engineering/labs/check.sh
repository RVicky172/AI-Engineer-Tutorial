#!/usr/bin/env bash
# Run every quality gate for every M01 lab. Exit non-zero on the first failure.
set -euo pipefail

cd "$(dirname "$0")"
BIN="$(pwd)/.venv/bin"

for lab in lab-0*/; do
  echo "=== ${lab%/} ==="
  (
    cd "$lab"
    "$BIN/pytest" -q
    "$BIN/ruff" check .
    "$BIN/ruff" format --check .
    "$BIN/mypy" src tests
  )
done
echo "All M01 labs green."
