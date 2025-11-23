# AIMinO Agent Workflow Guide

This guide describes how the local Napari client, Google ADK agent stack, and shared command executor cooperate. Follow it when validating new integrations or onboarding contributors.

---

## 1. High-Level Flow

1. **User Interaction (Napari Desktop)**  
   - The user enters a natural language instruction in the Napari command dock (local plugin or script).  
   - A light-weight regex parser tries to resolve trivial commands locally. Fallback requests are forwarded to the Client Agent.

2. **Client Agent (Tool Executor)**  
   - Packages the user input, current viewer context (optional), and session metadata.  
   - Sends the payload to the Server Agent via WebSocket/gRPC (API surface TBD).  
   - Receives structured commands, validates them with `BaseCommandAdapter`, then calls `aimino_core.executor.execute_command`.

3. **Server Agent (Lead Manager + Managers + Workers)**  
   - Lead Manager records the request in memory, invokes `TaskParser` (LLM) to break the instruction into subtasks.  
   - Each subtask is routed to a category manager, which selects the appropriate worker.  
   - Workers produce validated JSON commands. Managers may enrich them (priority, grouping) before returning to the lead manager.

4. **Execution & Feedback**  
   - Commands run on the local Napari viewer.  
   - Execution results (success/failure + details) are sent back to the server to update memory and improve future task ranking.  
   - Final response appears in the Napari UI (and server logs) with a concise status message.

---

## 2. Component Map

| Layer | Key Modules | Notes |
|-------|-------------|-------|
| Napari Client | `napari_app/main.py` launcher (random demo data), `aimino_core.executor`, command dock widget | Provides real-time viewer control using the shared command registry. |
| Client Agent | `napari_app.AgentClient` | Creates ADK sessions per request and forwards commands to the executor. |
| Server Lead | `src/server/agents/napari_manager.py` (`NapariLeadManager`) | Hosts TaskParser + worker registry; validates outputs against `COMMAND_REGISTRY`. |
| Managers | See `Manager_Instructions.md` | Each manager has a handbook and worker registry. |
| Workers | See `Worker_Instructions.md` | LLM micro-agents returning single commands. |
| Shared Utilities | `aimino_core/command_models.py`, `aimino_core/executor.py` | Single source of truth for schemas and command execution logic. |

---

## 3. Required Setup Steps

1. Create and activate the Conda environment: `conda env create -f environment.yml && conda activate aimino` (for existing env run `conda env update -f environment.yml --prune` to sync dependencies).  
2. (Optional) Add the repo root to `PYTHONPATH` or run commands from the root so `aimino_core` is importable.  
3. Set environment variables (`OPENAI_API_KEY`, `GEMINI_API_KEY`, etc.) via `.env` or OS-level secrets.  
4. Run `python -m napari_app.main` to start the local Napari launcher; confirm the dock widget appears.  
5. The launcher internally instantiates `NapariLeadManager` via `build_runner()`; ensure API keys are in place before issuing commands.  
6. Establish client-server connectivity. For early testing the launcher calls the manager directly; later replace with WebSocket.

---

## 4. Deployment Targets

| Environment | Purpose | Notes |
|-------------|---------|-------|
| Local Dev | Rapid iteration, debugging | Napari + Agent stack run on developer machine. |
| Containerized Demo | Backward-compatible showcase (noVNC) | Useful for demos but not the final architecture. |
| GCP Kubernetes | Production-style deployment | Host the ADK server agents and memory services. Napari client remains on user workstation. |

---

## 5. Testing Strategy

1. **Unit Tests**  
   - Validate command models (serialization, validation errors).  
   - Verify executor functions manipulate the viewer correctly (use Napari testing utilities with dummy layers).  
   - Mock ADK agents to ensure managers route tasks to workers as expected.

2. **Integration Tests**  
   - End-to-end scenario: user command → TaskParser → manager → worker → command execution.  
   - Smoke suite for canonical commands (`show layer`, `center on`, `set zoom`).  
   - Negative tests (unknown layer, invalid syntax) verifying `help` responses.

3. **Manual QA**  
   - Run Napari UI; issue sample commands; confirm viewer updates; inspect agent logs for clean events.  
   - Test failure handling by disconnecting server or injecting invalid commands.

---

## 6. Future Enhancements

1. Integrate advanced mask/density commands after the executor exposes safe APIs.  
2. Introduce asynchronous data fetchers (e.g., Napari DB lookups) that managers can trigger.  
3. Implement persistent memory (Redis, Firestore) to share context across sessions.  
4. Expand agent instructions to support cell annotation workflows once the modeling pipeline is ready.

Keep this guide updated whenever the workflow changes (new protocol, additional handshake steps, etc.). Link updates in `Integration_Progress.md` so teammates can follow the latest process. 
