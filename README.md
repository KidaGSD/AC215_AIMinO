# AIMinO: Napari + Agentic Control

## Overview

The project now follows a “Napari client ↔ cloud-ready server” split (cheese-style backend under `src/`):

```
aimino_frontend/aimino_core/   # shared command schema + handler + executor (client-side runtime)
aimino_frontend/napari_app     # local Napari launcher + UI + ClientAgent
src/api_service/               # FastAPI app factory + routers + agents (cheese-style)
src/deployment/                # nginx reverse proxy (proxy → api_service:8000)
archive/                # legacy llm-agent implementation (no longer active)
MD_Instructions/        # design docs (command spec, workflow, manager/worker guides, progress log)
environment.yml         # conda environment with napari + google genai dependencies
```

* `aimino_core` (installed from `aimino_frontend/aimino_core`) exposes `execute_command()` and handler registry; this stays with the Napari desktop because only the client touches real viewer objects.
* `src/api_service/api/agents/lead_manager.py` hosts the Lead Manager + TaskParser + predefined workers. Container builds copy this folder plus dependencies.
* `aimino_frontend/napari_app` initializes the viewer, loads demo layers, and provides the command dock UI. Its `ClientAgent` can call the backend over HTTP (`SERVER_URL`) or use LocalRunner in DEV mode (`DEV_LOCAL_RUNNER=1`). Frontend remains local-only; install via `pip install -e aimino_frontend/aimino_core`.

## How It Works
1. User types a natural-language command in the Napari dock (`aimino_frontend/napari_app`).
2. `ClientAgent` packages the text/context and invokes the Lead Manager.
3. The Lead Manager (server) runs TaskParser + Workers (LLM) and returns a list of JSON commands.
4. `aimino_core.executor.execute_command()` runs each command locally, using registered handlers (layer visibility, camera control, panel toggle, etc.).

## Getting Started (Local Dev)
```bash
conda env create -f environment.yml
conda activate aimino
pip install -e aimino_frontend/aimino_core      # install shared package
export GEMINI_API_KEY=...                       # and any other keys (OPENAI_API_KEY, HF_TOKEN, ...)
export SERVER_URL=http://127.0.0.1:8000         # backend (HTTP mode)
PYTHONPATH=$PWD src/api_service/scripts/run_api.sh         # server (cheese-style, /api/v1)
PYTHONPATH=$PWD python -m aimino_frontend.napari_app.main  # frontend
```
When the Napari window appears, use the right-hand dock to issue commands such as `show nuclei layer` or `center on 200,300`.

New structure (cheese-style additions):
- Frontend: `aimino_frontend/napari_app` (Napari UI + ClientAgent)
- Backend: `src/api_service` (FastAPI app factory + routers + utils)
- Shared: `aimino_core/` (command models + handlers + executor)

## Current Functionality
- Command schema + validators (`aimino_core/command_models.py`)
- Registry-driven handlers for viewer control (layer visibility, panel toggle, zoom, center, set zoom, fit to layer, list layers, help)
- Lead Manager with TaskParser + two workers (layer panel, view/zoom) referencing markdown handbooks
- Napari desktop dock that runs the full round-trip locally (LLM call still requires valid API keys)
- Progress / instruction docs aligned with the new architecture

## API Service Cheatsheet
- Start dev: `src/api_service/scripts/run_api.sh`
- Health: `curl http://127.0.0.1:8000/api/v1/healthz`
- Smoke: `src/api_service/scripts/smoke_invoke.sh`
- Docker build: `docker build -t aimino-api:dev -f src/api_service/Dockerfile .`
- Docker run: `docker run --rm -p 8000:8000 --env-file .env aimino-api:dev`

## Next Steps (brief)
1. Stabilize transports: `/api/v1/healthz` probe + clearer 503/500 errors; LocalRunner shim uses `src.api_service`.
2. Harden API: structured `ErrorResponse`, CORS allowlist, richer logs.
3. Ensure Docker build installs full deps (`google-adk`/`google-genai` + aimino_core) and uses `.dockerignore`.
4. Expand worker + handler catalog (center_on/pan) and add tests for invoke flow with mocked runner and executor.
