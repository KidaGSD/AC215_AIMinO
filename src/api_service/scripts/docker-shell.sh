#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-aimino-api:dev}"
docker run --rm -it -p 8000:8000 --env-file .env "$IMAGE" /bin/sh
