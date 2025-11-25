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

See [TESTING.md](TESTING.md) for detailed testing documentation.

### Quick Start

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock requests

# Run all tests
pytest

# Run with coverage
pytest --cov=src/api_service --cov=aimino_frontend/aimino_core --cov-report=html

# Run by category
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m system        # System tests (requires running API)
```

### CI/CD

The project includes a GitHub Actions CI pipeline (`.github/workflows/ci.yml`) that:

- ✅ Runs linting checks
- ✅ Tests across Python 3.10, 3.11, 3.12
- ✅ Builds and tests Docker image
- ✅ Runs unit, integration, and system tests
- ✅ Generates coverage reports (minimum 50% required)
- ✅ Uploads coverage artifacts

See the Actions tab in GitHub for CI status and coverage reports.

## Docker Compose Testing

### Run All Tests with Service Orchestration
```bash
# Build and run all tests (recommended)
docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test_runner

# View detailed logs
docker-compose -f docker-compose.test.yml logs

# Clean up after tests
docker-compose -f docker-compose.test.yml down -v
```

## Notes
- Keep `uv.lock` tracked; Dockerfile is uv-only (no requirements.txt).
- If you see the app_name warning, align the google-adk loader/root agent to `aimino_app`.
