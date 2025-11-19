# AIMinO: Napari + Agentic Control

## Overview

The project now follows a “Napari client ↔ cloud-ready server” split:

```
aimino_core/            # shared command schema + handler + executor (client-side runtime)
napari_app/             # local Napari launcher + UI + ClientAgent shim
src/server/             # ADK Lead Manager, workers, handbooks (server-only code)
archive/                # legacy llm-agent implementation (no longer active)
MD_Instructions/        # design docs (command spec, workflow, manager/worker guides, progress log)
environment.yml         # conda environment with napari + google genai dependencies
```

* `aimino_core` exposes `execute_command()` and handler registry; this stays with the Napari desktop because only the client touches real viewer objects.
* `src/server/agents/napari_manager.py` hosts the Lead Manager + TaskParser + predefined workers. When containerized, only this folder (plus requirements) needs to ship.
* `napari_app` initializes the viewer, loads demo layers, and provides the command dock UI. Its `ClientAgent` currently calls the Lead Manager in-process but can be swapped for HTTP/WebSocket when the server runs remotely.

## How It Works
1. User types a natural-language command in the Napari dock (`napari_app`).
2. `ClientAgent` packages the text/context and invokes the Lead Manager.
3. The Lead Manager (server) runs TaskParser + Workers (LLM) and returns a list of JSON commands.
4. `aimino_core.executor.execute_command()` runs each command locally, using registered handlers (layer visibility, camera control, panel toggle, etc.).

## Getting Started (Local Dev)
```bash
conda env create -f environment.yml
conda activate aimino
export PYTHONPATH=/path/to/AIMinO   # or run commands from repo root
export GEMINI_API_KEY=...           # and any other keys (OPENAI_API_KEY, HF_TOKEN, ...)
python -m napari_app.main
```
When the Napari window appears, use the right-hand dock to issue commands such as `show nuclei layer` or `center on 200,300`.

New structure:
- Frontend: `aimino_frontend/napari_app` (Napari UI + ClientAgent)
- Backend: `aimino_backend/` (ADK Lead Manager + workers + FastAPI scaffolding)
- Shared: `aimino_core/` (command models + handlers + executor)

## Current Functionality
- Command schema + validators (`aimino_core/command_models.py`)
- Registry-driven handlers for viewer control (layer visibility, panel toggle, zoom, center, set zoom, fit to layer, list layers, help)
- Lead Manager with TaskParser + two workers (layer panel, view/zoom) referencing markdown handbooks
- Napari desktop dock that runs the full round-trip locally (LLM call still requires valid API keys)
- Progress / instruction docs aligned with the new architecture

## Next Steps (brief)
1. Add a thin API layer for `src/server/` so the Lead Manager can run in a separate process/container and communicate via HTTP/WebSocket.
2. Expand worker + handler catalog (layer visualization, analysis commands, mask/density tools).
3. Automate tests and smoke flows described in `MD_Instructions/Integration_Progress.md`.
