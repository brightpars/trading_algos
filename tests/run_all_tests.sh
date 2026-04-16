#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
COVERAGE_JSON="$(mktemp)"

cleanup() {
  rm -f "$COVERAGE_JSON"
}

trap cleanup EXIT

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Project virtual environment is missing. Create it with:" >&2
  echo "  python -m venv $ROOT_DIR/.venv" >&2
  exit 1
fi

if ! "$VENV_PYTHON" -m pip show pytest-cov >/dev/null 2>&1; then
  echo "pytest-cov is missing from the project virtual environment. Install it with:" >&2
  echo "  $VENV_PYTHON -m pip install -r $ROOT_DIR/scripts/requirements.txt" >&2
  exit 1
fi

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

echo "> Running pytest with coverage"
"$VENV_PYTHON" -m pytest \
  --cov=trading_algos \
  --cov-report=term-missing \
  --cov-report="json:$COVERAGE_JSON"

COVERAGE_PERCENT="$($VENV_PYTHON - <<'PY' "$COVERAGE_JSON"
import json
import sys
from pathlib import Path

coverage_path = Path(sys.argv[1])
data = json.loads(coverage_path.read_text())
print(f"{data['totals']['percent_covered']:.2f}%")
PY
)"

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
echo "> Coverage summary: total test coverage is $COVERAGE_PERCENT"