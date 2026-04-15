#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Project virtual environment is missing. Create it with:" >&2
  echo "  python -m venv $ROOT_DIR/.venv" >&2
  exit 1
fi

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

echo "> Running pytest"
"$VENV_PYTHON" -m pytest

if "$VENV_PYTHON" -m ruff --version >/dev/null 2>&1; then
  echo "> Running ruff check"
  "$VENV_PYTHON" -m ruff check .

  echo "> Running ruff format --check"
  "$VENV_PYTHON" -m ruff format --check .
else
  echo "> Skipping ruff (not installed in .venv)"
fi

if "$VENV_PYTHON" -m mypy --version >/dev/null 2>&1; then
  echo "> Running mypy"
  "$VENV_PYTHON" -m mypy .
else
  echo "> Skipping mypy (not installed in .venv)"
fi

echo "> All available checks completed successfully"