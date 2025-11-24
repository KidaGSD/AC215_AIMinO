#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="${PYTHONPATH:-${REPO_ROOT}/src:${REPO_ROOT}/aimino_frontend/aimino_core}"
export AIMINO_API_PREFIX="${AIMINO_API_PREFIX:-/api/v1}"
export AIMINO_SERVER_PORT="${AIMINO_SERVER_PORT:-8000}"

# Load .env into environment if present (for GOOGLE_API_KEY, etc.)
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

exec uvicorn api_service.api.service:create_app --factory --host 0.0.0.0 --port "$AIMINO_SERVER_PORT" --reload
