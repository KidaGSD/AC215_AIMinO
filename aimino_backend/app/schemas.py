"""Pydantic schemas for FastAPI server payloads (stubs)."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class InvokeRequest(BaseModel):
    user_input: str = Field(..., description="Raw user instruction")
    context: Optional[List[dict]] = Field(None, description="Recent client-side context entries")
    session_id: Optional[str] = Field(None, description="Client-provided session identifier")


class InvokeResponse(BaseModel):
    final_commands: List[dict] = Field(default_factory=list)
    session_id: str
    latency_ms: int = 0


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[dict[str, Any]] = None


__all__ = ["InvokeRequest", "InvokeResponse", "ErrorResponse"]

