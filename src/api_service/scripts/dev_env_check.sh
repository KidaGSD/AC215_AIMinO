#!/usr/bin/env bash
set -euo pipefail

echo "Checking Python deps..."
python -c "import fastapi,uvicorn,pydantic; print('OK: fastapi/uvicorn/pydantic')"

echo "Checking env keys..."
if [ -z "${GOOGLE_API_KEY:-}" ] && [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "WARN: GOOGLE_API_KEY/GEMINI_API_KEY not set"
else
  echo "OK: LLM key present"
fi

echo "Checking API health (if running)..."
curl -sS http://127.0.0.1:8000/api/v1/healthz || true
