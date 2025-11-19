# Milestone 4 Implementation Plan (AIMinO)

> Note: Documents/MS4_Requirements.md and Documents/Meeting_breakdown.md were not found in the repository at the time of writing. This plan is derived from the current codebase, the latest architecture, and the team TODO list provided.

## Current State (baseline)
- Client-side
  - `napari_app/`: minimal launcher with Command Dock; `ClientAgent` calls Lead Manager in-process.
  - `aimino_core/`: shared command models + registry-driven handlers + executor (viewer/layer/ui basics).
- Server-side (cloud-ready skeleton)
  - `src/server/agents/napari_manager.py`: Lead Manager with TaskParser and predefined workers (layer_panel, view_zoom).
  - `src/server/handbooks/`: TaskParser & worker prompts.
  - `src/server/workers/`: worker factories loading handbooks.
- Documentation
  - `MD_Instructions/`: command spec, workflow, manager/worker guides, integration progress.
- Environment
  - `environment.yml` with napari/pyqt/ADK/GenAI.

Gaps vs. MS4 targets inferred: server–client boundary still in-process; minimal set of commands; no durable context/memory; not containerized yet; demo uses random data rather than real datasets; no robust logging/telemetry.

---

## Phase 0 — Repo Hygiene (urgent, 0.5d) - Kida
- Finalize directory boundaries
  - Keep client-only runtime in `aimino_core` (handlers/executor) and Napari app in `napari_app/`.
  - Keep server-only ADK code in `src/server/`.
- Add a lightweight `pyproject.toml` or `setup.cfg` for `aimino_core` (editable install in dev).
- Tighten `.gitignore` (logs, cache, .env, build artifacts).

Deliverables:
- `aimino_core` installable locally; updated README quickstart remains valid.

---

## Phase 1 — Minimal Remote-Ready Server (urgent, 1d) - Yinuo (server I/O), Yuan (packaging, Containarizing), Kida (File Restructure)

- API surface
  - Add `src/server/api.py` with a HTTP endpoint `/invoke` (FastAPI or Flask) receiving `{user_input, context?}` and returning `{final_commands}`.
  - Wrap existing `NapariLeadManager` runner inside the API handler.
- Client shim
  - Add `napari_app/client_agent.py` HTTP mode behind a feature flag (env `SERVER_URL`).
  - Fallback to in-process mode when `SERVER_URL` is not set.
- Config/secrets
  - Server reads LLM keys from env; client does not need to ship keys once remote is used.
- Logging
  - Request/response logging (structured JSON) at server; simple console logs at client.

Deliverables:
- `/invoke` returns commands for basic flows; Napari app can toggle remote/local with an env var.

Risks/Mitigations:
- Cold-start latency of LLM backends → add simple health endpoint and client retries.

---

## Phase 2 — Agent Function Scale-up (2d) - Yuan, Kida

- Extend command schema + handlers (aimino_core)
  - Viewer: layout/grid, scalebar/axes toggle.
  - Layers: select/rename/reorder; basic transforms (opacity, colormap, blending).
- Extend workers/prompts (server handbooks)
  - Add `layer_visualization` worker; revise TaskParser mapping.
- Validation & Safety
  - Expand Pydantic models; add unit tests for parser/handlers.

Deliverables:
- New actions registered in `aimino_core/handlers/*` and covered by workers/handbooks.

---

## Phase 3 — Real Data Path (urgent, 2–3d) - TK

- Data loading in Napari client
  - Add simple file-open flow in `napari_app` (choose TIFF/Zarr/H5AD paths) and load into layers.
- Minimal dataset config
  - Add `configs/sample_data.yaml` for common paths; prompt TaskParser to use actual layer names.
- Performance
  - Ensure big images lazy-load (dask/tifffile) where feasible.

Deliverables:
- Demo scenario using a real TIFF + optional H5AD-derived layers.

---

## Phase 4 — Context & Memory (urgent, 2–4d) -  Yinuo (storage), Yuan (client logs)

- Client-side context sender
  - Log executed commands and minimal viewer state (active layer, camera center/zoom) to a rotating JSONL file.
  - Include last-N commands as `context` in `/invoke` requests when available.
- Server-side context receiver
  - Accept `context` in payload; store per-session logs to local filesystem or SQLite (Phase 4a).
  - Expose retrieval API `/session/{id}` to fetch recent context.
- Agent-aware context
  - Lead Manager uses the last-N commands to bias TaskParser; add a small “system facts” section to prompts.
- Definition:
  - Context: What we are sending to the AI agent at the moment(Current session **user action** + Command(**Right now** + session history(?))
  - Memory: Storage of multiple sessions

Deliverables:
- Round trip context capture and basic retrieval; unit tests on server storage layer.

---

## Phase 5 — Manager Improvements (reasoning coverage, complex taks coverage 2–3d) - Kida

- TaskParser
  - Improve splitting for compound requests; add priority ordering and basic conflict checks.
- Lead Manager policies
  - Deduplicate equivalent commands; error aggregation.
- Prompts
  - Update handbooks with tricky examples; add negative examples and fallback to `help`.

Deliverables:
- Better accuracy on multi-step instructions; fewer no-op or unsupported actions.

---

## Phase 6 — Containerization (1–2d) - Yuan

- Add `src/server/Dockerfile` and runtime entry script.
- Publish a `docker-compose.server.yml` for local run.
- Build-time injection of handbooks; runtime env for keys.

Deliverables:
- Server container serving `/invoke`; client connects via `SERVER_URL`.

---

## Phase 7 — Advanced Functions, and function schema(ongoing) - TK


- Design new schemas for analysis/annotation flows (mask/density, shapes editing), document as “extensions” in command spec.
- Implement staged handlers guarded by feature flags; add corresponding workers/prompts.
- Plan eval scenarios and metrics.

---

## Ownership Matrix (consolidated)
- Containerize server: Yuan
- Agent function scale-up (viewer/layer basics): Yuan, Kida
- Real data demo: TK
- Context storage + transport: Yinuo (server), Yuan (client)
- Context-aware parsing (manager/worker prompts): Yinuo, Kida
- Server–client communication: Yinuo
- Advanced functions + schemas: TK

---

## Checklists

### Server readiness
- [ ] `/invoke` implemented with input validation and error responses
- [ ] Lead Manager wired; workers loaded; env-driven model keys
- [ ] Log to file; session id returned; health endpoint ready

### Client readiness
- [ ] Env toggle for remote/local
- [ ] Command Dock: logs to JSONL; send last-N context
- [ ] Real data open dialog + layer naming

### Schema/handlers
- [ ] New actions added to `aimino_core/command_models.py`
- [ ] Handlers in `aimino_core/handlers/*`
- [ ] Workers + handbooks mapping in `src/server/workers/` and `src/server/handbooks/`

---

## Risks & Mitigations
- LLM variability → strict JSON output, `response_mime_type=application/json`, Pydantic validation.
- Large data performance → lazy loading, avoid blocking UI; measure with real files early.
- Drift between server prompts and handlers → single source of truth in command spec; handbook generation scripts (future).





