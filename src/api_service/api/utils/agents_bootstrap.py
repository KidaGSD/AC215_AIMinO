"""Bootstrap integration with backend agents (canonical src path)."""

from __future__ import annotations

from typing import Any, Tuple


def build_runner() -> Tuple[Any, Any]:
    # Use the canonical src path
    from api_service.api.agents.lead_manager import build_runner as _build  # type: ignore
    return _build()
