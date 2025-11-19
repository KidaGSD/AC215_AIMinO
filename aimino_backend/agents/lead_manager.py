"""Simplified Napari lead manager using predefined workers."""

from __future__ import annotations

import json
from typing import AsyncGenerator, Dict, List

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

from ..workers import get_workers
from ..handbooks import load_text


GEMINI_MODEL = "gemini-2.0-flash"
SUPPORTED_ACTIONS = set(available_actions())


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
                model = BaseCommandAdapter.validate_python(command)
                if model.action not in SUPPORTED_ACTIONS:
                    yield Event(
                        author=self.name,
                        content=types.Content(parts=[types.Part(text=f"Unsupported action: {model.action}")]),
                    )
                    continue
                commands.append(model.model_dump())
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
    runner = Runner(agent=manager, app_name="napari_adk_app", session_service=session_service)
    return session_service, runner


__all__ = ["NapariLeadManager", "build_runner"]
