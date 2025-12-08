from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:  # Prefer namespaced import when available
    from aimino_frontend.aimino_core.data_store import ingest_dataset
except ImportError:  # pragma: no cover - fallback inside Docker image
    from aimino_core.data_store import ingest_dataset  # type: ignore


router = APIRouter()


class DatasetRegisterRequest(BaseModel):
    image_path: str
    h5ad_path: str
    dataset_id: str | None = None
    copy_files: bool = False
    marker_col: str | None = None


@router.post("/datasets/register")
async def register_dataset(payload: DatasetRegisterRequest):
    try:
        metadata = {"marker_cols": [payload.marker_col]} if payload.marker_col else None
        manifest = ingest_dataset(
            payload.image_path,
            payload.h5ad_path,
            dataset_id=payload.dataset_id,
            copy_files=payload.copy_files,
            metadata=metadata,
        )
        return {"status": "ok", "manifest": manifest}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
