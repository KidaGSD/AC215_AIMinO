"""Start the Napari Agent API server."""

from __future__ import annotations

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.server.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
    )

