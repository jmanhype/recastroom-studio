#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

export RECASTROOM_COMFY_URL="${RECASTROOM_COMFY_URL:-http://127.0.0.1:8188}"
export RECASTROOM_WORKFLOW="${RECASTROOM_WORKFLOW:-$PWD/workflows/recastroom_h3_workflow.json}"
export RECASTROOM_BACKEND="${RECASTROOM_BACKEND:-dry_run}"
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
PORT="${PORT:-8768}"

if [[ ! -x .venv/bin/uvicorn ]]; then
  echo "Run ./setup.sh first" >&2
  exit 1
fi

exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$PORT"
