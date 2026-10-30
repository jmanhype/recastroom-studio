#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required (brew install ffmpeg or apt-get install ffmpeg)" >&2
  exit 1
fi

if command -v uv >/dev/null 2>&1; then
  echo "Using uv for the local Python environment."
  [ -d .venv ] || uv venv -p "${RECASTROOM_PYTHON:-3.11}" .venv
  uv pip install -p .venv --upgrade pip
  uv pip install -p .venv -e ".[dev]"
else
  echo "uv not found; falling back to python3 -m venv and pip."
  [ -d .venv ] || python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install ".[dev]"
fi
.venv/bin/python -m json.tool workflows/recastroom_h3_workflow.json >/dev/null

cat <<'EOF'
Setup complete.

Start the studio:
  ./run.sh
EOF
