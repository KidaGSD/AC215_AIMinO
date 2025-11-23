# AIMinO API Service (cheese-style)

## Run (local)
- `src/api_service/scripts/run_api.sh` (auto-loads `.env`, sets `/api/v1` prefix)
- Health: `curl http://127.0.0.1:8000/api/v1/healthz`
- Invoke: `curl -X POST http://127.0.0.1:8000/api/v1/invoke -H 'Content-Type: application/json' -d '{"user_input":"show layer panel"}'`

## Env
- `GOOGLE_API_KEY` (preferred) or `GEMINI_API_KEY`
- `AIMINO_API_PREFIX` (default `/api/v1`)
- `AIMINO_ALLOWED_ORIGINS` (comma-separated list or JSON list)

## Docker
- Build: `docker build -t aimino-api:dev -f src/api_service/Dockerfile .`
- Run: `docker run --rm -p 8000:8000 --env-file .env aimino-api:dev`

## Notes
- Agents live under `src/api_service/api/agents`.
- Structured errors from `/invoke` follow `{code,message,details}`.
