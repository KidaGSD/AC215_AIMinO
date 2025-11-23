"""Client-side shim for invoking the server lead manager.

Adds a transport abstraction to enable future HTTP communication without
changing the caller code in the UI.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import List, Optional, Protocol
from collections import deque
from datetime import datetime
import pathlib

import httpx
from google.genai import types

APP_NAME = "napari_adk_app"
USER_ID = "local_user"


class BaseTransport(Protocol):
    async def invoke(self, user_input: str, context: Optional[list[dict]] = None) -> List[dict]:
        ...


class LocalRunnerTransport:
    """Development-only in-process runner; not used in production."""

    def __init__(self) -> None:
        # delayed import to avoid frontend depending on backend at import time
        from src.api_service.api.agents.lead_manager import build_runner  # type: ignore

        self.session_service, self.runner = build_runner()

    async def invoke(self, user_input: str, context: Optional[list[dict]] = None) -> List[dict]:
        session_id = uuid.uuid4().hex
        initial_state = {"user_input": user_input}
        if context:
            initial_state["context"] = context

        await self.session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
            state=initial_state,
        )

        events = self.runner.run_async(
            user_id=USER_ID,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=user_input)]),
        )
        async for _event in events:
            pass

        final_session = await self.session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
        commands = final_session.state.get("final_commands", [])
        if isinstance(commands, str):
            try:
                commands = json.loads(commands)
            except json.JSONDecodeError:
                commands = []
        return commands


class HttpTransport:
    """HTTP transport to the FastAPI backend."""

    def __init__(self, base_url: str, timeout_s: float = 30.0, retries: int = 2) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.retries = retries

    async def healthz(self) -> dict:
        url = f"{self.base_url}/api/v1/healthz"
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()

    async def invoke(self, user_input: str, context: Optional[list[dict]] = None) -> List[dict]:
        url = f"{self.base_url}/api/v1/invoke"
        payload = {"user_input": user_input}
        if context:
            payload["context"] = context

        last_err: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    commands = data.get("final_commands", [])
                    if isinstance(commands, str):
                        try:
                            commands = json.loads(commands)
                        except json.JSONDecodeError:
                            commands = []
                    return commands
            except Exception as e:  # network/HTTP error
                last_err = e
        # after retries exhausted
        raise RuntimeError(f"HTTP invoke failed (check /healthz and server logs): {last_err}")


class AgentClient:
    def __init__(self) -> None:
        server_url = os.getenv("SERVER_URL", "").strip().rstrip("/")
        dev_local = os.getenv("DEV_LOCAL_RUNNER", "0").strip() == "1"
        self._context_buffer: deque[dict] = deque(maxlen=20)
        if server_url:
            self.transport: BaseTransport = HttpTransport(server_url)
        elif dev_local:
            self.transport = LocalRunnerTransport()
        else:
            raise RuntimeError("SERVER_URL not set and DEV_LOCAL_RUNNER!=1; cannot contact backend.")

    async def invoke(self, user_input: str) -> List[dict]:
        # attach last-N context
        context = list(self._context_buffer)
        commands = await self.transport.invoke(user_input, context=context)
        # log entry
        self._append_client_log(user_input, commands)
        # update context buffer (simple record)
        self._context_buffer.append({
            "ts": datetime.utcnow().isoformat() + "Z",
            "user_input": user_input,
            "commands_count": len(commands),
        })
        return commands

    def _append_client_log(self, user_input: str, commands: List[dict]) -> None:
        try:
            date = datetime.utcnow().strftime("%Y%m%d")
            path = pathlib.Path("logs/client/") / f"client_{date}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            rec = {
                "ts": datetime.utcnow().isoformat() + "Z",
                "user_input": user_input,
                "final_commands": commands,
            }
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass
