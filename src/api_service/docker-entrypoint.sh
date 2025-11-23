#!/usr/bin/env sh
set -e

HOST="0.0.0.0"
PORT="${AIMINO_SERVER_PORT:-8000}"
export PYTHONPATH="${PYTHONPATH:-/app}"

# Optional .env load if present
if [ -f /app/.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /app/.env
  set +a
fi

exec uvicorn src.api_service.api.service:create_app \
  --factory --host "$HOST" --port "$PORT"
