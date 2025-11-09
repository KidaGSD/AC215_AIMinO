# AIMinO Manager Instructions

This document captures the expectations, responsibilities, and configuration surface for every manager class in the AIMinO agent stack. The structure mirrors Google ADK guidance (see https://google.github.io/adk-docs/agents/) so new contributors can extend the hierarchy without breaking existing flows.

---

## 1. Lead Manager (Server Agent)

| Item | Details |
|------|---------|
| Purpose | Owns the end-to-end conversation loop. Receives user requests, gathers context, ranks tasks, and delegates work to specialized managers. |
| ADK Base Class | `BaseAgent` (custom subclass `NapariLeadManager` in `src/server/agents/napari_manager.py`) |
| Inputs | `InvocationContext` containing user message, session metadata, cached viewer state, memory snapshot |
| Outputs | Streaming `Event` objects (progress updates) and a final `state_delta` payload with an ordered list of commands validated against `BaseCommandAdapter`. Commands are executed client-side via `aimino_core.executor.execute_command`, which routes through `COMMAND_REGISTRY`. |
| Memory Usage | Persist high-level task summaries, successful command recipes, and failure cases. Expose retrieval hooks to subordinate managers. |
| Scalability Hook | Register manager instances via a configuration map, e.g. `MANAGER_REGISTRY = {"viewer_control": ViewerControlManager(...)}. The lead manager iterates the registry instead of hard-coding worker names. |

### Execution Outline
1. Accept message from Client Agent (includes viewer context snapshot when available).
2. Run TaskParser (LLM Agent) to transform natural language into structured subtasks (`worker_type`, `task_description`, `priority`).
3. For each subtask:
   - Lookup the target manager in `MANAGER_REGISTRY`. If missing, emit a warning event and skip.
   - Provide latest memory/context to the manager via ADK invocation parameters.
   - Collect the manager response (structured commands or escalations).
4. Consolidate all commands, deduplicate when possible, and publish as the final response.
5. Update memory store with results (success/failure) for future ranking.

---

## 2. Category Managers

Three core categories align with `Multi-agent system - Sheet1.csv`. Each manager may wrap multiple workers internally; managers return one or more validated commands.

### 2.1 ViewerControlManager
| Item | Details |
|------|---------|
| Scope | Global viewer state (zoom, camera, layout toggles). |
| Default Workers | `ZoomCenterWorker`, `LayoutWorker` (layout worker is planned; initial version can forward directly to baseline workers). |
| Required Inputs | `task_description`, optional `viewer_state` snippet (camera center, zoom). |
| Output | Single command from `BaseNapariCommand`. |
| Prompt Assets | `src/server/handbooks/view_zoom_worker.md` (loaded by `src/server/workers.get_workers()` at startup). |

### 2.2 LayerManagementManager
| Scope | Create/delete/reorder/select layers. Initial integration will focus on visibility toggles to keep MVP scoped.
| Notes | Start with pass-through to existing `layer_visibility` command; plan subsequent workers for creation/deletion when API is ready. Current implementation uses `handbooks/layer_panel_worker.md`.

### 2.3 LayerVisualizationManager
| Scope | Per-layer styling (opacity, colormap, blending). For MVP this manager can be stubbed and only return `help` until executor support is added.

---

## 3. Manager Interface Contract

All managers should extend a shared base class to ensure consistency:

```python
from google.adk.agents import LlmAgent

class BaseCategoryManager:
    def __init__(self, llm_agent: LlmAgent, handbook: str) -> None:
        self.llm_agent = llm_agent
        self.handbook = handbook

    async def handle_task(self, ctx, task) -> list[dict]:
        """Return a list of serialized commands."""
        raise NotImplementedError
```

Key rules:
1. Managers must validate every produced command via `BaseCommandAdapter`.
2. Managers should emit ADK `Event` messages for transparency (`starting`, `completed`, `error`).
3. Managers can request additional context (e.g., “list layers”) by enqueuing auxiliary tasks; such requests must be documented to avoid loops.

---

## 4. Adding a New Manager

1. **Define Scope**: Document responsibilities and dependencies in this file.
2. **Implement Executor Support**: Add the required command(s) to `Agent_Command_Spec.md`, then register handler(s) under `aimino_core/handlers/` via `@register_handler`.
3. **Create Handbook**: Add a markdown file under `handbooks/` describing capabilities, safety rules, schema hints.
4. **Instantiate Worker**: Call `_build_worker` in `src/server/workers/__init__.py` to create the LlmAgent and place it into the `get_workers()` dictionary.
5. **Register Manager**: Update `NapariLeadManager`'s `workers` dict (or `MANAGER_REGISTRY`) to point at the new key.
6. **Update Documentation**: Extend this file and the workflow guide; add smoke tests.

By keeping manager definitions declarative and referencing shared registries, the architecture remains scalable as we introduce additional capabilities (e.g., Cell Annotation Manager). 
