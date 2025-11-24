# AIMinO Worker Instructions

Workers convert a single, well-scoped subtask into one validated command JSON. This document summarizes available workers, their prompts, and onboarding steps for new worker classes.

---

## 1. Worker Contract

```python
from google.adk.agents import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from aimino_core.command_models import BaseCommandAdapter
from aimino_core.registry import register_handler

class BaseWorker(LlmAgent):
    async def run_and_validate(self, ctx: InvocationContext) -> dict:
        async for event in self.run_async(ctx):
            yield event  # forward streaming updates
        raw = ctx.session.state.get(self.output_key, "")
        command = BaseCommandAdapter.validate_python(raw)
        return command
```

Rules:
1. **Single command per invocation**: workers must not return lists.
2. **Strict JSON**: enforce `response_mime_type="application/json"` or ADK function calling to avoid fallback parsing.
3. **Stateless**: rely on `ctx.session.state` for necessary context; avoid mutable globals.
4. **Explain failure**: upon parsing/validation errors, emit an `Event` with a helpful message and return `{"action":"help"}` or raise to let the manager decide.

---

## 2. Current Worker Catalog

| Worker Name | Category Manager | Instruction Summary | Output Action(s) |
|-------------|------------------|---------------------|------------------|
| `LayerPanelWorker` | LayerManagementManager | Converts sentences like “show nuclei layer” or “open layers panel” into visibility/toggle commands. | `layer_visibility`, `panel_toggle` |
| `ViewZoomWorker` | ViewerControlManager | Handles “center on”, “zoom to box”, and absolute zoom requests. | `center_on`, `zoom_box`, `set_zoom` |

> These workers originate from `napariAgent.py`. Move their instruction strings into standalone markdown (e.g., `handbooks/layer_panel_worker.md`) so future updates stay consistent.

---

## 3. Prompt Best Practices

1. **Explicit Schema**: start instructions with “You ONLY speak JSON objects matching ...”.
2. **Example Coverage**: include positive/negative examples covering edge cases (ambiguous layer names, invalid coordinates).
3. **Fail Safe**: instruct the model to return `{"action":"help"}` when unsure.
4. **Contextual Variables**: use templated placeholders (`{{sub_task}}`) and inject via ADK.

Example snippet (LayerPanelWorker):
```
You only know two schemas:
1. {"action":"layer_visibility","op":"show|hide|toggle","name":"<layer name>"}
2. {"action":"panel_toggle","op":"open|close","name":"<panel name>"}
Respond with JSON ONLY. Task: {{sub_task}}
```

---

## 4. Adding a Worker

1. **Determine Action Coverage**: ensure schema support and there is a registered handler in `aimino_core/handlers/` (or add one with `@register_handler`).
2. **Write Handbook Entry**: add a markdown in `handbooks/` describing responsibilities and field definitions. `src/server/workers` will load it at runtime.
3. **Define Worker**: In `src/server/workers/__init__.py`, call `_build_worker` to create the LlmAgent and add it to the `get_workers()` dictionary.
4. **Registar Manager**: Adjust `NapariLeadManager`'s `workers` dictionary，make sure `worker_type` can find that instance。
5. **Document**: add to the table above, update tests, and record the change in `Integration_Progress.md`.

---

## 5. Testing Checklist
- Unit test: feed representative `sub_task` strings and assert the worker returns the expected command dict after validation.
- Integration test: ensure the corresponding manager correctly handles worker failure and produces a user-facing explanation.
- Regression guard: confirm new instructions do not break existing sub_tasks (e.g., via snapshot testing of generated JSON).

Maintaining clean worker boundaries keeps the agent system scalable and easier to reason about as capabilities expand. 
