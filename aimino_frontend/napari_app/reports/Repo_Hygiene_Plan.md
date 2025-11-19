# Repo Hygiene and Structure Plan (Frontend/Backend)

> Note: Documents/Meeting_breakdown.md was not found in the repo. This plan encodes a clear frontend/backend split per our latest architecture and prepares for FastAPI without blocking current local flows.

## 1) Target Folder Structure

- frontend/
  - aimino_core/ (package)
    - command_models.py
    - handlers/ (viewer.py, layers.py, ui.py, shared.py, __init__.py)
    - executor.py, registry.py, errors.py, __init__.py
    - pyproject.toml (packaging for editable install)
  - napari_app/
    - main.py (Napari launcher + UI dock)
    - client_agent.py (transports)
    - ui/ (optional, dock widgets)
- backend/
  - src/server/
    - agents/napari_manager.py (Lead Manager)
    - workers/__init__.py (predefined workers)
    - handbooks/ (task_parser.md, worker md files)
    - api/ (__init__.py placeholder for FastAPI app)
    - schemas.py (InvokeRequest/Response, ErrorResponse)
    - config.py (Settings via pydantic-settings)
    - logging.py (structured logging helpers)

Notes:
- We already have equivalent directories in place: `aimino_core/`, `napari_app/`, and `src/server/` (agents, workers, handbooks). This hygiene step formalizes and documents the split and adds the missing server scaffolding files.

## 2) Frontend Responsibilities

- Execute commands locally via Napari API using `aimino_core.executor.execute_command`.
- Build request payloads for server (`InvokeRequest`), including recent command context when available.
- Provide transport abstraction:
  - LocalRunnerTransport (current in-process flow)
  - HttpTransport (FastAPI-ready; added as a stub with TODOs)
- Minimal logging (JSONL) of user commands and execution results under `logs/client/`.

## 3) Backend Responsibilities

- Accept `POST /invoke` requests with `{user_input, context?, session_id?}`.
- Use Lead Manager + Workers to produce `final_commands`.
- Return `InvokeResponse` and log events under `logs/server/`.
- Expose `GET /healthz` and (later) `GET /session/{id}` for context retrieval.

## 4) FastAPI Readiness (Scaffold Only)

- Add files with docstrings and type definitions only (no logic yet):
  - src/server/schemas.py
  - src/server/config.py
  - src/server/logging.py
  - src/server/api/__init__.py (FastAPI app placeholder)
  - src/server/api/contracts.md (endpoint contracts, payload schema)
- environment.yml: include `fastapi`, `uvicorn[standard]`, `pydantic-settings`.

## 5) Client Transports (Design + TODOs)

In `napari_app/client_agent.py`:
- Introduce `BaseTransport` with `async invoke(user_input: str, context: list[dict] | None) -> list[dict]`.
- Keep `LocalRunnerTransport` (current code path) as default when `SERVER_URL` is empty.
- Add `HttpTransport` skeleton:
  - TODO: serialize payload by `InvokeRequest` from `src/server/schemas.py`.
  - TODO: handle retries/backoff and non-200 responses.
  - TODO: map server `ErrorResponse` to user-friendly messages in the dock.

## 6) Schema Versioning & Compatibility

- Add `SCHEMA_VERSION = "0.1"` to `aimino_core/__init__.py`.
- Server `/healthz` should return `{schema_version: "0.1"}` (TODO) to detect mismatches.

## 7) Logging & Context

- Client JSONL: `logs/client/{date}.jsonl` entries with `{ts, session_id, user_input, commands, result}`.
- Server JSON: `logs/server/{date}.jsonl` with `{ts, session_id, latency_ms, tasks_count, final_commands}`.
- TODO: include last-N client commands as `context` in `HttpTransport` payloads once HTTP is wired.

## 8) Hygiene Tasks (Actionable List)

- Packaging
  - [ ] Add `aimino_core/pyproject.toml` (name, version, minimal deps)
- Server stubs
  - [ ] Add `src/server/schemas.py`, `config.py`, `logging.py`, `api/__init__.py`, `api/contracts.md`
  - [ ] Update `environment.yml` with `fastapi`, `uvicorn[standard]`, `pydantic-settings`
- Client refactor
  - [ ] Refactor `napari_app/client_agent.py` to `BaseTransport` + `LocalRunnerTransport`
  - [ ] Add `HttpTransport` class with TODOs
- Docs
  - [ ] Update `README.md` “How to run (local/remote)” toggles
  - [ ] Update `MD_Instructions/Agent_Workflow_Guide.md` to reference transports and schemas
- Logging
  - [ ] Create `logs/` in `.gitignore`; add simple JSONL appender utilities

## 9) Acceptance Criteria

- From repo root, `PYTHONPATH=$PWD python -m napari_app.main` still launches the local app.
- `aimino_core` importable in both client and server code paths.
- New server files exist with clear TODO markers and type signatures; FastAPI can be added without restructuring.
- README clearly shows how to toggle server modes once FastAPI routes are implemented.
