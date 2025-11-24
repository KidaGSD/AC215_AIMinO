from __future__ import annotations

from fastapi import APIRouter, Request
import os

router = APIRouter()


@router.get("/healthz")
async def healthz(request: Request):
    app = request.app
    runner = getattr(app.state, "runner", None)
    version = getattr(app.state, "service_version", os.getenv("AIMINO_SERVICE_VERSION", "0.1.0"))
    return {
        "status": "ok",
        "runner_initialized": runner is not None,
        "schema_version": "0.1",
        "service_version": version,
    }
