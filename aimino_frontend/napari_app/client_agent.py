"""Client-side shim for invoking the server lead manager.

Adds a transport abstraction to enable future HTTP communication without
changing the caller code in the UI.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import List, Optional, Protocol

from google.genai import types

from aimino_backend.agents.lead_manager import build_runner

APP_NAME = "napari_adk_app"
USER_ID = "local_user"


class BaseTransport(Protocol):
    async def invoke(self, user_input: str, context: Optional[list[dict]] = None) -> List[dict]:
        ...


class LocalRunnerTransport:
    def __init__(self) -> None:
        self.session_service, self.runner = build_runner()

    async def invoke(self, user_input: str, context: Optional[list[dict]] = None) -> List[dict]:
        session_id = uuid.uuid4().hex
        initial_state = {"user_input": user_input}
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

        final_session = await self.session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        commands = final_session.state.get("final_commands", [])
        if isinstance(commands, str):
            try:
                commands = json.loads(commands)
            except json.JSONDecodeError:
                commands = []
        return commands


class HttpTransport:
    """HTTP transport to a remote FastAPI server (skeleton).

    TODO:
    - serialize payload using src/server/schemas.InvokeRequest
    - send request with httpx/aiohttp and implement retries/backoff
    - handle non-200 responses and map to user-facing messages
    - add auth headers if required
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def invoke(self, user_input: str, context: Optional[list[dict]] = None) -> List[dict]:
        raise NotImplementedError("HttpTransport is not implemented yet")


class AgentClient:
    def __init__(self) -> None:
        server_url = os.getenv("SERVER_URL", "").strip()
        if server_url:
            self.transport: BaseTransport = HttpTransport(server_url)
        else:
            self.transport = LocalRunnerTransport()

    async def invoke(self, user_input: str) -> List[dict]:
        return await self.transport.invoke(user_input)
