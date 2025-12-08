from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from importlib import metadata

from .utils.config import settings
from .utils.agents_bootstrap import build_runner
from .utils.logging import configure_logging
from .routers.invoke import router as invoke_router
from .routers.healthz import router as healthz_router
from .routers.datasets import router as datasets_router
import os
try:
    import google.genai as genai
except Exception:  # pragma: no cover
    genai = None  # type: ignore


def create_app() -> FastAPI:
    app = FastAPI(title="AIMinO API", version="0.1.0")
    logger = configure_logging()
    logger.info("Starting AIMinO API service")

    origins = settings.AIMINO_ALLOWED_ORIGINS or ["*"]
    if isinstance(origins, str):
        try:
            origins = json.loads(origins)
        except Exception:
            origins = [o.strip() for o in origins.split(",") if o.strip()]
    if not origins:
        origins = ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.app_name = "aimino_app"
    app.state.user_id = "remote_user"
    app.state.session_service = None
    app.state.runner = None
    app.state.service_version = metadata.version("aimino-api-service") if "aimino-api-service" in metadata.packages_distributions() else "0.1.0"

    @app.on_event("startup")
    async def _startup() -> None:
        # Allow tests to bypass heavy startup via env flag
        if os.getenv("AIMINO_SKIP_STARTUP", "") == "1":
            logger.warning("Startup skipped due to AIMINO_SKIP_STARTUP=1")
            return
        # Configure Google GenAI API key if available
        if genai is not None:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if api_key:
                try:
                    if hasattr(genai, "configure"):
                        genai.configure(api_key=api_key)  # type: ignore
                        logger.info("google.genai configured via API key env")
                    else:
                        logger.info("google.genai does not expose configure(); skipping explicit setup")
                except Exception:
                    logger.exception("Failed to configure google.genai; continuing without explicit setup")
        session_service, runner = build_runner()
        app.state.session_service = session_service
        app.state.runner = runner
        logger.info("Runner initialized and session service ready")

    app.include_router(invoke_router, prefix=settings.AIMINO_API_PREFIX)
    app.include_router(healthz_router, prefix=settings.AIMINO_API_PREFIX)
    app.include_router(datasets_router, prefix=settings.AIMINO_API_PREFIX)
    return app


app = create_app()
