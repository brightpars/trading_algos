#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/mohammad/development/trading_algos"
SMARTTRADE_ROOT="/home/mohammad/development/smarttrade"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"
SMARTTRADE_VENV_PYTHON="$SMARTTRADE_ROOT/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Project virtual environment not found at $VENV_PYTHON"
  echo "Create it with: python3 -m venv /home/mohammad/development/trading_algos/.venv"
  exit 1
fi

if [[ ! -d "$SMARTTRADE_ROOT" ]]; then
  echo "Smarttrade repository not found at $SMARTTRADE_ROOT"
  exit 1
fi

if [[ ! -x "$SMARTTRADE_VENV_PYTHON" ]]; then
  echo "Smarttrade virtual environment not found at $SMARTTRADE_VENV_PYTHON"
  echo "Create it with: python3 -m venv /home/mohammad/development/smarttrade/.venv"
  exit 1
fi

SMARTTRADE_SITE_PACKAGES="$($SMARTTRADE_VENV_PYTHON -c 'import sysconfig; print(sysconfig.get_path("purelib"))')"

if [[ ! -d "$SMARTTRADE_SITE_PACKAGES" ]]; then
  echo "Smarttrade site-packages directory not found at $SMARTTRADE_SITE_PACKAGES"
  exit 1
fi

export FLASK_APP="trading_algos_dashboard.app:create_app"
export FLASK_ENV="${FLASK_ENV:-development}"
export FLASK_DEBUG="${FLASK_DEBUG:-1}"
export PYTHONPATH="$REPO_ROOT/src:$SMARTTRADE_ROOT:$SMARTTRADE_SITE_PACKAGES${PYTHONPATH:+:$PYTHONPATH}"
export SMARTTRADE_PATH="$SMARTTRADE_ROOT"
export TRADING_ALGOS_DASHBOARD_MONGO_URI="${TRADING_ALGOS_DASHBOARD_MONGO_URI:-mongodb://127.0.0.1:27017}"
export TRADING_ALGOS_DASHBOARD_MONGO_DB="${TRADING_ALGOS_DASHBOARD_MONGO_DB:-trading_algos_dashboard}"
export TRADING_ALGOS_DASHBOARD_REPORT_PATH="${TRADING_ALGOS_DASHBOARD_REPORT_PATH:-dashboard_reports}"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-2000}"

cd "$REPO_ROOT"
echo "Starting dashboard on http://$HOST:$PORT"
echo "Using smarttrade root: $SMARTTRADE_ROOT"
echo "Using smarttrade site-packages: $SMARTTRADE_SITE_PACKAGES"
exec "$VENV_PYTHON" -m flask run --host "$HOST" --port "$PORT"