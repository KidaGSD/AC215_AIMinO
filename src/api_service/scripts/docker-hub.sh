#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-aimino-api}"
DOCKER_USER="${DOCKER_USER:-$(whoami)}"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "Docker user: $DOCKER_USER"

# Remove existing builder if any
if docker buildx inspect aimino-multi >/dev/null 2>&1; then
  docker buildx rm aimino-multi
fi

docker buildx create --driver-opt network=host --use --name aimino-multi

echo "Building multi-arch image..."
docker buildx build --platform linux/amd64,linux/arm64 -t "$DOCKER_USER/$IMAGE_NAME" -f "$BASE_DIR/src/api_service/Dockerfile" "$BASE_DIR"

echo "Pushing multi-arch image..."
docker buildx build --platform linux/amd64,linux/arm64 --push -t "$DOCKER_USER/$IMAGE_NAME" -f "$BASE_DIR/src/api_service/Dockerfile" "$BASE_DIR"

echo "Done."
