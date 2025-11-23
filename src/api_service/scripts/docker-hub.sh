#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-your-dockerhub-username/aimino-api}"
TAG="${TAG:-dev}"

docker build -t "$REPO:$TAG" -f src/api_service/Dockerfile .
echo "Built image: $REPO:$TAG"
echo "Run: docker push $REPO:$TAG"
