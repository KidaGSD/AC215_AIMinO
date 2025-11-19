"""HTTP API server for remote Napari agent invocation."""

from __future__ import annotations

import json
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google.genai import types

from .agents.napari_manager import build_runner

APP_NAME = "napari_adk_app"
USER_ID = "remote_user"

# Initialize FastAPI app
app = FastAPI(title="Napari Agent API", version="1.0.0")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize runner once at startup
_session_service = None
_runner = None


@app.on_event("startup")
async def startup_event():
    """Initialize the runner on server startup."""
    global _session_service, _runner
    _session_service, _runner = build_runner()


class InvokeRequest(BaseModel):
    """Request model for /invoke endpoint."""
    user_input: str
    context: Optional[dict] = None


class InvokeResponse(BaseModel):
    """Response model for /invoke endpoint."""
    final_commands: list[dict]


@app.post("/invoke", response_model=InvokeResponse)
async def invoke(request: InvokeRequest) -> InvokeResponse:
    """
    Invoke the Napari lead manager with user input.
    
    Args:
        request: Contains user_input and optional context
        
    Returns:
        Response containing final_commands list
    """
    print(request)
    if _runner is None or _session_service is None:
        raise HTTPException(
            status_code=503,
            detail="Server not initialized. Runner not available."
        )
    
    try:
        # Create a new session for this request
        session_id = uuid.uuid4().hex
        initial_state = {"user_input": request.user_input}
        
        # Merge context if provided
        if request.context:
            initial_state.update(request.context)
        
        await _session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
            state=initial_state,
        )
        
        # Run the agent
        events = _runner.run_async(
            user_id=USER_ID,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=request.user_input)],
            ),
        )
        
        # Consume all events
        async for _event in events:
            pass
        
        # Get final session state
        final_session = await _session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
        
        # Extract final_commands
        commands = final_session.state.get("final_commands", [])
        if isinstance(commands, str):
            try:
                commands = json.loads(commands)
            except json.JSONDecodeError:
                commands = []
        
        return InvokeResponse(final_commands=commands)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "runner_initialized": _runner is not None}

