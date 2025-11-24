<<<<<<< HEAD
# AIMinO
Agentic AI for Conversational Imaging Control and Cell Type Modeling with OMERO
=======
# AIMinO (Napari + Agentic Control)

## Project layout
```
aimino_frontend/aimino_core/   # shared command schema + handlers + executor (client-side runtime)
aimino_frontend/napari_app/    # Napari UI + ClientAgent (HTTP or local runner)
src/api_service/               # FastAPI app factory + routers + agents (cheese-style, uv-only)
src/deployment/                # reverse proxy, deployment assets
MD_Instructions/               # specs/workflows/agent guides
archive/                       # legacy implementation (inactive)
environment.yml                # conda env for frontend + genai tooling
```

Data flow: user types into the Napari dock → ClientAgent sends text/context to Lead Manager (server) → TaskParser + Workers produce JSON commands → `aimino_core.executor.execute_command()` runs them locally via registered handlers (layer visibility, camera, panel toggle, etc.).

## Local development
```bash
conda env create -f environment.yml
conda activate aimino
pip install -e aimino_frontend/aimino_core                # install shared package locally
export GEMINI_API_KEY=...                                 # or GOOGLE_API_KEY / OPENAI_API_KEY
export SERVER_URL=http://127.0.0.1:8000                   # backend HTTP endpoint
# Backend (reload): PYTHONPATH=$PWD/src:$PWD/aimino_frontend/aimino_core \
    src/api_service/scripts/run_api.sh
# Frontend (Napari): python -m aimino_frontend.napari_app.main
```
Run commands in the dock, e.g. `show nuclei layer`, `center on 200,300`.

## Docker (uv)
- Build: `DOCKER_BUILDKIT=1 docker build -t aimino-api:dev -f src/api_service/Dockerfile .`
- Run: `docker run --rm -p 8000:8000 --env-file .env aimino-api:dev`
- Dev hot-reload with source/core mounts: `HOST_PORT=8030 src/api_service/scripts/docker-shell.sh`
  - Mounts repo to `/app` and `aimino_frontend/aimino_core` to `/app/aimino_core`
  - PYTHONPATH inside container: `/app/src:/app/aimino_core`; `AIMINO_RELOAD=1`

## API quick reference
- Health: `curl http://127.0.0.1:8000/api/v1/healthz`
- Invoke: `curl -X POST http://127.0.0.1:8000/api/v1/invoke -H 'Content-Type: application/json' -d '{"user_input":"show layers"}'`
- Smoke script: `src/api_service/scripts/smoke_invoke.sh`
- Key env vars: `AIMINO_API_PREFIX` (default `/api/v1`), `AIMINO_SERVER_PORT` (default `8000`), `AIMINO_ALLOWED_ORIGINS`, `AIMINO_RELOAD`
- Runner app name is unified to `aimino_app`

## Testing
```bash
conda activate aimino
pip install pytest
PYTHONPATH=$PWD/src:$PWD/aimino_frontend/aimino_core python -m pytest src/api_service/tests
```

## Notes / next actions
- Keep `uv.lock` tracked; Dockerfile is uv-only (no requirements.txt).
- If you see the app_name warning, align the google-adk loader/root agent to `aimino_app`.
- Add CI (GitHub Actions: build/lint/test/coverage) and deployment docs (compose/GCP) per Milestone4.
>>>>>>> integrate_agentV1_api
