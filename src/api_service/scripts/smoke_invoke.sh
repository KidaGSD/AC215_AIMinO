#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
BASE="http://$HOST:$PORT/api/v1"

has_jq=0
if command -v jq >/dev/null 2>&1; then
  has_jq=1
fi

echo "# Healthz"
if [ "$has_jq" -eq 1 ]; then
  curl -sS "$BASE/healthz" | jq . || true
else
  curl -sS "$BASE/healthz" || true
  echo
fi

echo "# Invoke (placeholder)"
if [ "$has_jq" -eq 1 ]; then
  curl -sS -X POST "$BASE/invoke" -H 'Content-Type: application/json' -d '{"user_input":"hello"}' | jq . || true
else
  curl -sS -X POST "$BASE/invoke" -H 'Content-Type: application/json' -d '{"user_input":"hello"}' || true
  echo
fi
