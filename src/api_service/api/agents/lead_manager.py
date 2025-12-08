"""Simplified Napari lead manager using predefined workers (migrated)."""

from __future__ import annotations

import json
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from typing_extensions import override
from pydantic import BaseModel, ValidationError

from aimino_core.command_models import BaseCommandAdapter
from aimino_core.registry import available_actions

from .workers import get_workers
from .handbooks import load_text


GEMINI_MODEL = "gemini-2.5-pro"
SUPPORTED_ACTIONS = set(available_actions())
REQUIRED_DATASET_ACTIONS = {
    "data_ingest",
    "special_load_marker_data",
    "special_show_mask",
    "special_show_density",
    "special_update_density",
    "special_compute_neighborhood",
}

# Actions that don't require dataset_id (can use current context or none)
CONTEXT_ACTIONS = {
    "set_dataset",
    "set_marker",
    "list_datasets",
    "get_dataset_info",
    "clear_processed_cache",
}


class _ContextInfo:
    def __init__(self) -> None:
        self.dataset_candidates: Set[str] = set()
        self.marker_candidates: Set[str] = set()
        self.last_dataset: Optional[str] = None
        self.last_marker: Optional[str] = None
        self.last_sigma: Optional[float] = None
        self.last_radius: Optional[float] = None

    def register_dataset(self, value: Optional[str]) -> None:
        if not value:
            return
        self.dataset_candidates.add(value)
        if self.last_dataset is None:
            self.last_dataset = value

    def register_marker(self, value: Optional[str]) -> None:
        if not value:
            return
        self.marker_candidates.add(value)
        if self.last_marker is None:
            self.last_marker = value


def _extract_context_info(state: Any) -> _ContextInfo:
    info = _ContextInfo()
    if not isinstance(state, dict):
        return info

    ctx_entries = state.get("context")
    if isinstance(ctx_entries, list):
        for entry in reversed(ctx_entries):
            if not isinstance(entry, dict):
                continue
            info.register_dataset(entry.get("dataset_id"))
            info.register_marker(entry.get("marker_col") or entry.get("marker"))
            if info.last_sigma is None and entry.get("sigma") is not None:
                info.last_sigma = float(entry["sigma"])
            if info.last_radius is None and entry.get("radius") is not None:
                info.last_radius = float(entry["radius"])

    history = state.get("history")
    if isinstance(history, list):
        for turn in reversed(history):
            commands = turn.get("final_commands")
            if not isinstance(commands, list):
                continue
            for cmd in reversed(commands):
                if not isinstance(cmd, dict):
                    continue
                info.register_dataset(cmd.get("dataset_id"))
                info.register_marker(cmd.get("marker_col"))
                if info.last_sigma is None and cmd.get("sigma") is not None:
                    info.last_sigma = float(cmd["sigma"])
                if info.last_radius is None and cmd.get("radius") is not None:
                    info.last_radius = float(cmd["radius"])
            if info.last_dataset and info.last_marker and info.last_sigma is not None and info.last_radius is not None:
                break
    return info


def _pick_candidate(last_value: Optional[str], candidates: Set[str]) -> Optional[str]:
    if last_value:
        return last_value
    if len(candidates) == 1:
        return next(iter(candidates))
    return None


def _autofill_command(
    command: dict,
    ctx_info: _ContextInfo,
) -> tuple[Optional[dict], Optional[str]]:
    action = command.get("action")
    if not isinstance(action, str):
        return command, None
    updated = dict(command)

    # Context actions don't require dataset_id (they manage context themselves)
    if action in CONTEXT_ACTIONS:
        # For get_dataset_info and clear_processed_cache, optionally fill dataset_id
        if action in {"get_dataset_info", "clear_processed_cache"} and not updated.get("dataset_id"):
            dataset = _pick_candidate(ctx_info.last_dataset, ctx_info.dataset_candidates)
            if dataset:
                updated["dataset_id"] = dataset
            # OK if missing - these commands can work without dataset_id
        return updated, None

    # dataset_id handling for other actions
    if action in REQUIRED_DATASET_ACTIONS and not updated.get("dataset_id"):
        dataset = _pick_candidate(ctx_info.last_dataset, ctx_info.dataset_candidates)
        if dataset:
            updated["dataset_id"] = dataset
        else:
            if ctx_info.dataset_candidates:
                candidates_str = ", ".join(sorted(ctx_info.dataset_candidates)[:5])
                return None, f"Multiple datasets detected ({candidates_str}). Please specify `dataset_id` in your command."
            return None, "No dataset selected. Please import or select a dataset first using 'set_dataset' or 'data_ingest'."

    # marker handling
    if action in {
        "special_load_marker_data",
        "special_show_mask",
        "special_show_density",
        "special_update_density",
        "special_compute_neighborhood",
    } and not updated.get("marker_col"):
        marker = _pick_candidate(ctx_info.last_marker, ctx_info.marker_candidates)
        if marker:
            updated["marker_col"] = marker
        else:
            if ctx_info.marker_candidates:
                markers_str = ", ".join(sorted(ctx_info.marker_candidates)[:5])
                return None, f"Multiple markers available ({markers_str}). Please specify `marker_col` in your command."
            return None, "No marker selected. Please specify a marker column (e.g., 'SOX10_positive') or use 'set_marker'."

    # sigma / radius fallback
    if action == "special_update_density" and updated.get("sigma") is None and ctx_info.last_sigma is not None:
        updated["sigma"] = ctx_info.last_sigma
    if action == "special_compute_neighborhood" and updated.get("radius") is None and ctx_info.last_radius is not None:
        updated["radius"] = ctx_info.last_radius

    return updated, None


class TaskParserInput(BaseModel):
    user_input: str


def _build_task_parser() -> LlmAgent:
    instruction = load_text("task_parser.md")
    return LlmAgent(
        name="TaskParser",
        model=GEMINI_MODEL,
        instruction=instruction,
        input_schema=TaskParserInput,
        output_key="task_plan",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.05,
            response_mime_type="application/json",
        ),
    )


def _extract_json(raw: object) -> dict:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    text = raw if isinstance(raw, str) else json.dumps(raw)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}


class NapariLeadManager(BaseAgent):
    task_parser: LlmAgent
    workers: Dict[str, LlmAgent]

    def __init__(self) -> None:
        workers = get_workers()
        task_parser = _build_task_parser()
        super().__init__(
            name="NapariLeadManager",
            sub_agents=[task_parser, *workers.values()],
            task_parser=task_parser,
            workers=workers,
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        user_input = ctx.session.state.get("user_input", "")
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=f"Parsing: {user_input}")]),
        )

        tasks = []
        async for event in self.task_parser.run_async(ctx):
            yield event

        plan = _extract_json(ctx.session.state.get("task_plan", ""))
        for entry in plan.get("tasks", []):
            desc = entry.get("task_description")
            worker_type = entry.get("worker_type")
            if desc and worker_type:
                tasks.append((desc, worker_type))

        if not tasks:
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text="No valid tasks found.")]),
                turn_complete=True,
                actions={"state_delta": {"final_commands": []}},
            )
            return

        commands: List[dict] = []
        ctx_info = _extract_context_info(ctx.session.state)
        for description, worker_type in tasks:
            worker = self.workers.get(worker_type)
            if worker is None:
                yield Event(
                    author=self.name,
                    content=types.Content(parts=[types.Part(text=f"No worker for type {worker_type}")]),
                )
                continue

            ctx.session.state["sub_task"] = description
            async for event in worker.run_async(ctx):
                yield event

            raw_cmd = ctx.session.state.get("command_json", "")
            try:
                command = _extract_json(raw_cmd)
                if not isinstance(command, dict):
                    raise ValidationError("command_json missing", BaseModel)
                command, autofill_error = _autofill_command(command, ctx_info)
                if autofill_error:
                    yield Event(
                        author=self.name,
                        content=types.Content(parts=[types.Part(text=autofill_error)]),
                    )
                    continue
                if command is None:
                    continue
                model = BaseCommandAdapter.validate_python(command)
                if model.action not in SUPPORTED_ACTIONS:
                    yield Event(
                        author=self.name,
                        content=types.Content(parts=[types.Part(text=f"Unsupported action: {model.action}")]),
                    )
                    continue
                normalized = model.model_dump()
                commands.append(normalized)
                # update context cache with latest values for downstream tasks
                ctx_info.register_dataset(normalized.get("dataset_id"))
                ctx_info.register_marker(normalized.get("marker_col"))
                if normalized.get("sigma") is not None:
                    ctx_info.last_sigma = float(normalized["sigma"])
                if normalized.get("radius") is not None:
                    ctx_info.last_radius = float(normalized["radius"])
            except ValidationError as exc:
                yield Event(
                    author=worker.name,
                    content=types.Content(parts=[types.Part(text=f"Validation error: {exc}")]),
                )

        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=f"Generated {len(commands)} command(s)")]),
            turn_complete=True,
            actions={"state_delta": {"final_commands": commands}},
        )


def build_runner() -> tuple[InMemorySessionService, Runner]:
    manager = NapariLeadManager()
    session_service = InMemorySessionService()
    runner = Runner(agent=manager, app_name="aimino_app", session_service=session_service)
    return session_service, runner


__all__ = ["NapariLeadManager", "build_runner"]
