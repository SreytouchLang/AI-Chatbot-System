#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Missing project virtualenv at $VENV_PYTHON"
  echo "Create it first with: python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt"
  exit 1
fi

cd "$SCRIPT_DIR"
exec "$VENV_PYTHON" -m uvicorn main:app --reload
