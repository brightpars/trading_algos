#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="/home/mohammad/development/trading_algos"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"
SHUTDOWN_TIMEOUT_SECS="${SHUTDOWN_TIMEOUT_SECS:-5}"
APP_PID=""
STOPPING=0

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Project virtual environment not found at $VENV_PYTHON"
  echo "Create it with: python3 -m venv /home/mohammad/development/trading_algos/.venv"
  exit 1
fi

export FLASK_APP="trading_algos_dashboard.app:create_app"
export FLASK_ENV="${FLASK_ENV:-development}"
export FLASK_DEBUG="${FLASK_DEBUG:-1}"
export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
export TRADING_ALGOS_DASHBOARD_MONGO_URI="${TRADING_ALGOS_DASHBOARD_MONGO_URI:-mongodb://127.0.0.1:27017}"
export TRADING_ALGOS_DASHBOARD_MONGO_DB="${TRADING_ALGOS_DASHBOARD_MONGO_DB:-trading_algos_dashboard}"
export TRADING_ALGOS_DASHBOARD_REPORT_PATH="${TRADING_ALGOS_DASHBOARD_REPORT_PATH:-dashboard_reports}"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-2000}"

resolve_service_ports() {
  "$VENV_PYTHON" - <<'PY'
from __future__ import annotations

import os

definitions = {
    "central": 6000,
    "data": 6010,
    "fake_datetime": 7100,
    "broker": 7101,
    "engines_control": 7102,
}

try:
    from pymongo import MongoClient

    mongo_uri = os.environ["TRADING_ALGOS_DASHBOARD_MONGO_URI"]
    mongo_db_name = os.environ["TRADING_ALGOS_DASHBOARD_MONGO_DB"]
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
    document = client[mongo_db_name]["dashboard_server_control_settings"].find_one(
        {"settings_id": "dashboard_service_control"}
    ) or {}
    stored_ports = document.get("ports") or {}
    ports = [int(stored_ports.get(name, default)) for name, default in definitions.items()]
    client.close()
except Exception:
    ports = list(definitions.values())

print(" ".join(str(port) for port in ports))
PY
}

collect_pids_for_port() {
  local port="$1"
  lsof -t -nP -iTCP:"${port}" -sTCP:LISTEN 2>/dev/null | sort -u || true
}

release_ports() {
  local ports_string="$1"
  read -r -a ports <<< "$ports_string"

  for port in "${ports[@]}"; do
    [[ -z "$port" ]] && continue
    local pids
    pids="$(collect_pids_for_port "$port")"
    if [[ -z "$pids" ]]; then
      continue
    fi

    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill -TERM "$pid" 2>/dev/null || true
    done <<< "$pids"

    sleep 1

    local remaining
    remaining="$(collect_pids_for_port "$port")"
    if [[ -n "$remaining" ]]; then
      while IFS= read -r pid; do
        [[ -z "$pid" ]] && continue
        kill -KILL "$pid" 2>/dev/null || true
      done <<< "$remaining"
    fi
  done
}

cleanup() {
  local signal="${1:-EXIT}"
  local exit_code=0

  if [[ "$signal" != "EXIT" ]]; then
    exit_code=128
    case "$signal" in
      INT) exit_code=$((128 + 2)) ;;
      TERM) exit_code=$((128 + 15)) ;;
    esac
  fi

  if [[ "$STOPPING" -eq 1 ]]; then
    return "$exit_code"
  fi
  STOPPING=1

  trap - EXIT INT TERM

  if [[ -n "$APP_PID" ]] && kill -0 "$APP_PID" 2>/dev/null; then
    echo
    echo "Stopping dashboard app (PID $APP_PID) due to $signal..."
    kill -TERM "$APP_PID" 2>/dev/null || true

    local elapsed=0
    while kill -0 "$APP_PID" 2>/dev/null; do
      if (( elapsed >= SHUTDOWN_TIMEOUT_SECS )); then
        echo "Dashboard app still running after ${SHUTDOWN_TIMEOUT_SECS}s, forcing stop..."
        kill -KILL "$APP_PID" 2>/dev/null || true
        break
      fi
      sleep 1
      elapsed=$((elapsed + 1))
    done

    wait "$APP_PID" 2>/dev/null || true
  fi

  local service_ports
  local ports_to_release
  service_ports="$(resolve_service_ports)"
  ports_to_release="$PORT${service_ports:+ $service_ports}"
  release_ports "$ports_to_release"

  return "$exit_code"
}

trap 'cleanup INT; exit $?' INT
trap 'cleanup TERM; exit $?' TERM
trap 'cleanup EXIT' EXIT

cd "$REPO_ROOT"
echo "Starting dashboard on http://$HOST:$PORT"
"$VENV_PYTHON" -m flask run --host "$HOST" --port "$PORT" &
APP_PID=$!
wait "$APP_PID"