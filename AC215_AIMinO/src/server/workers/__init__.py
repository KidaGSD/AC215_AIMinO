"""Predefined worker agents for Napari commands."""

from __future__ import annotations

from functools import lru_cache
from typing import Dict

from google.adk.agents import LlmAgent
from google.genai import types
from pydantic import BaseModel

from ..handbooks import load_text


GEMINI_MODEL = "gemini-2.0-flash"


class WorkerInput(BaseModel):
    sub_task: str


def _build_worker(name: str, handbook: str) -> LlmAgent:
    instruction = load_text(handbook)
    return LlmAgent(
        name=name,
        model=GEMINI_MODEL,
        instruction=instruction,
        input_schema=WorkerInput,
        output_key="command_json",
        generate_content_config=types.GenerateContentConfig(
            temperature=0.05,
            response_mime_type="application/json",
        ),
    )


@lru_cache(maxsize=None)
def get_workers() -> Dict[str, LlmAgent]:
    return {
        "layer_panel": _build_worker("LayerPanelWorker", "layer_panel_worker.md"),
        "view_zoom": _build_worker("ViewZoomWorker", "view_zoom_worker.md"),
    }


__all__ = ["get_workers", "WorkerInput"]
