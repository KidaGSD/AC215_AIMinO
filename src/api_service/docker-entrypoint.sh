#!/usr/bin/env sh
set -e

HOST="0.0.0.0"
PORT="${AIMINO_SERVER_PORT:-8000}"
RELOAD="${AIMINO_RELOAD:-0}"
UV_VENV="${UV_PROJECT_ENVIRONMENT:-/home/app/.venv}"
UVICORN_BIN="${UV_VENV}/bin/uvicorn"
export PATH="${UV_VENV}/bin:${PATH}"
CORE_PATH="/app/aimino_core"
BASE_PYTHONPATH="/app/src"
mkdir -p /app/src
if [ -d "$CORE_PATH" ]; then
  BASE_PYTHONPATH="${BASE_PYTHONPATH}:${CORE_PATH}"
fi

# Optional .env load if present
if [ -f /app/.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /app/.env
  set +a
fi

# Ensure our source paths are always on PYTHONPATH, even if .env set it
if [ -n "${PYTHONPATH:-}" ]; then
  export PYTHONPATH="${PYTHONPATH}:${BASE_PYTHONPATH}"
else
  export PYTHONPATH="${BASE_PYTHONPATH}"
fi

EXTRA_ARGS=""
if [ "$RELOAD" = "1" ]; then
  EXTRA_ARGS="--reload --reload-dir /app/src"
fi

# Fallback if uvicorn not found in venv
if [ ! -x "$UVICORN_BIN" ]; then
  UVICORN_BIN="$(command -v uvicorn || true)"
fi

if [ -z "$UVICORN_BIN" ]; then
  echo "uvicorn not found; ensure dependencies are installed" >&2
  exit 1
fi

exec "$UVICORN_BIN" api_service.api.service:create_app \
  --factory --host "$HOST" --port "$PORT" \
  --app-dir /app/src \
  $EXTRA_ARGS
