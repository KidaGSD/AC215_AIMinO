#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-aimino-api:dev}"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ENV_FILE="${ENV_FILE:-$BASE_DIR/.env}"
HOST_PORT="${HOST_PORT:-8000}"

# Build image if not present
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  DOCKER_BUILDKIT=1 docker build --progress=plain -t "$IMAGE_NAME" -f "$BASE_DIR/src/api_service/Dockerfile" "$BASE_DIR"
fi

# Run with source mounted (dev mode)
RUN_ENV=(-e AIMINO_RELOAD=1 -e PYTHONPATH=/app/src:/app/aimino_core)
if [ -f "$ENV_FILE" ]; then
  RUN_ENV+=(--env-file "$ENV_FILE")
fi

DOCKER_FLAGS=(--rm -i)
if [ -t 0 ]; then
  DOCKER_FLAGS+=(-t)
fi

docker run "${DOCKER_FLAGS[@]}" \
  --entrypoint /usr/local/bin/docker-entrypoint.sh \
  -v "$BASE_DIR":/app \
  -v "$BASE_DIR/aimino_frontend/aimino_core":/app/aimino_core \
  -p "${HOST_PORT}:8000" \
  ${RUN_ENV[@]+"${RUN_ENV[@]}"} \
  "$IMAGE_NAME"
