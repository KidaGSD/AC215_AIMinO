# AIMinO API Service

## Run (local)
- Dev (reload): `PYTHONPATH=$PWD/src:$PWD/aimino_frontend/src/aimino_frontend/aimino_core src/api_service/scripts/run_api.sh`
- Docker dev shell (mount + reload): `HOST_PORT=8030 src/api_service/scripts/docker-shell.sh` (mounts repo + aimino_core)

## Health & Invoke
- Health: `curl http://127.0.0.1:8000/api/v1/healthz`
- Invoke: `curl -X POST http://127.0.0.1:8000/api/v1/invoke -H 'Content-Type: application/json' -d '{"user_input":"show layers"}'`

## Env
- `AIMINO_API_PREFIX` (default `/api/v1`)
- `AIMINO_SERVER_PORT` (default `8000`)
- `AIMINO_ALLOWED_ORIGINS` (JSON list or comma list, e.g., `["http://localhost:3000"]` or `http://localhost:3000`)
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` (optional; if set, google.genai configured best-effort)

## Docker (uv only)
- Build: `DOCKER_BUILDKIT=1 docker build --progress=plain -t aimino-api:dev -f src/api_service/Dockerfile .`
- Run: `docker run --rm -p 8000:8000 --env-file .env aimino-api:dev`
- Dev reload with mount: `HOST_PORT=8030 src/api_service/scripts/docker-shell.sh`
- Publish multi-arch: `src/api_service/scripts/docker-hub.sh` (set `DOCKER_USER`, `IMAGE_NAME`)

## Notes
- App name unified to `aimino_app` to avoid runner warnings.
- `aimino_core` is copied directly into the Docker image at `/app/aimino_core` (no pip install needed, PYTHONPATH includes it).
- For local development, install the frontend package: `cd aimino_frontend && pip install -e .`
