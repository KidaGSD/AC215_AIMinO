"""Client-side shim for invoking the server lead manager."""

from __future__ import annotations

import json
import uuid
from typing import List

from google.genai import types

# call the build runner from the server to build
from src.server.agents.napari_manager import build_runner

APP_NAME = "napari_adk_app"
USER_ID = "local_user"


class AgentClient:
    def __init__(self) -> None:
        self.session_service, self.runner = build_runner()

    async def invoke(self, user_input: str) -> List[dict]:
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
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=user_input)],
            ),
        )

        async for _event in events:
            pass

        final_session = await self.session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
        commands = final_session.state.get("final_commands", [])
        if isinstance(commands, str):
            try:
                commands = json.loads(commands)
            except json.JSONDecodeError:
                commands = []
        return commands
