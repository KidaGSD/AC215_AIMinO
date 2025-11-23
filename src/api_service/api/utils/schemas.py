from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class InvokeRequest(BaseModel):
    user_input: str
    # Accept a list of dicts to match client context buffer shape
    context: Optional[List[Dict[str, Any]]] = None


class InvokeResponse(BaseModel):
    final_commands: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
