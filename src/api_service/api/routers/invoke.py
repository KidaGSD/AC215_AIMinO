from __future__ import annotations

import json
import os
import time
import uuid
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from google.genai import types

from ..utils.schemas import InvokeRequest, InvokeResponse, ErrorResponse
from ..utils.logging import write_jsonl
import logging

router = APIRouter()


@router.post("/invoke", responses={500: {"model": ErrorResponse}})
async def invoke(request: Request, payload: InvokeRequest) -> InvokeResponse:
    app = request.app
    log = logging.getLogger("aimino.api")
    log.info("/invoke received", extra={"user_input": payload.user_input})
    session_service = getattr(app.state, "session_service", None)
    runner = getattr(app.state, "runner", None)
    if not session_service or not runner:
        return JSONResponse(
            status_code=503,
            content=ErrorResponse(
                code="runner_not_ready",
                message="Server not initialized. Runner not available.",
                details={"api_prefix": settings.AIMINO_API_PREFIX},
            ).model_dump(),
        )

    try:
        t0 = time.time()
        session_id = uuid.uuid4().hex
        initial_state = {"user_input": payload.user_input}
        if payload.context is not None:
            # Store context under a dedicated key to avoid dict.update on lists
            initial_state["context"] = payload.context

        await session_service.create_session(
            app_name=getattr(app.state, "app_name", "napari_adk_app"),
            user_id=getattr(app.state, "user_id", "remote_user"),
            session_id=session_id,
            state=initial_state,
        )
        log.info("session created", extra={"session_id": session_id})

        events = runner.run_async(
            user_id=getattr(app.state, "user_id", "remote_user"),
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=payload.user_input)]),
        )
        async for _event in events:
            pass
        log.info("runner completed", extra={"session_id": session_id})

        final_session = await session_service.get_session(
            app_name=getattr(app.state, "app_name", "napari_adk_app"),
            user_id=getattr(app.state, "user_id", "remote_user"),
            session_id=session_id,
        )
        commands = final_session.state.get("final_commands", [])
        if isinstance(commands, str):
            try:
                commands = json.loads(commands)
            except json.JSONDecodeError:
                commands = []
        write_jsonl(
            os.path.join("logs", "server", "server.jsonl"),
            {
                "ts": time.time(),
                "event": "invoke",
                "session_id": session_id,
                "user_input": payload.user_input,
                "final_commands_count": len(commands),
            },
        )
        log.info("commands ready", extra={"count": len(commands), "session_id": session_id})
        return InvokeResponse(final_commands=commands)
    except Exception as e:
        log.exception("invoke failed")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                code="invoke_error", message="Invocation failed", details={"error": repr(e)}
            ).model_dump(),
        )
