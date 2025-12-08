"""Dataset storage helpers for AIMinO.

Centralizes ingestion paths so that Napari + agent workflows can access
TIFF / h5ad inputs and derived artifacts without relying on ad-hoc paths.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

DATA_ROOT_ENV = "AIMINO_DATA_ROOT"
DEFAULT_DATA_ROOT = Path.home() / "AIMINO_DATA"
MANIFEST_NAME = "manifest.json"
RAW_DIR = "raw"
PROCESSED_DIR = "processed"


def _expand_path(value: str | Path) -> Path:
    """Resolve user/home relative paths."""
    if isinstance(value, Path):
        return value.expanduser().resolve()
    return Path(value).expanduser().resolve()


def get_data_root() -> Path:
    """Return the configured data root, ensuring it exists."""
    root = os.getenv(DATA_ROOT_ENV, str(DEFAULT_DATA_ROOT))
    path = _expand_path(root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sanitize_dataset_id(raw: str | None) -> str:
    text = (raw or "").strip()
    text = re.sub(r"[^A-Za-z0-9_-]+", "-", text)
    text = text.strip("-") or "dataset"
    return text.lower()


def _dataset_dir(dataset_id: str) -> Path:
    ds = _sanitize_dataset_id(dataset_id)
    return get_data_root() / ds


def _ensure_dataset_dirs(dataset_id: str) -> Path:
    base = _dataset_dir(dataset_id)
    (base / RAW_DIR).mkdir(parents=True, exist_ok=True)
    (base / PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
    return base


def _file_signature(path: Path) -> dict:
    stat = path.stat()
    return {
        "path": str(path),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
    }


def _matches_signature(signature: dict, path: Path) -> bool:
    if not signature:
        return False
    if not path.exists():
        return False
    stat = path.stat()
    return (
        signature.get("size") == stat.st_size
        and abs(signature.get("mtime", 0.0) - stat.st_mtime) < 1e-6
    )


def _make_unique_dataset_id(preferred: str) -> str:
    root = get_data_root()
    sanitized = _sanitize_dataset_id(preferred)
    candidate = sanitized
    counter = 1
    while (root / candidate / MANIFEST_NAME).exists():
        candidate = f"{sanitized}-{counter}"
        counter += 1
    return candidate


def suggest_dataset_id(image_path: str | Path | None) -> str:
    """Generate a unique dataset_id suggestion based on the image filename."""
    if image_path:
        base = Path(image_path).stem or "dataset"
    else:
        base = "dataset"
    return _make_unique_dataset_id(base)


def manifest_path(dataset_id: str) -> Path:
    return _dataset_dir(dataset_id) / MANIFEST_NAME


def save_manifest(dataset_id: str, payload: dict) -> None:
    target = manifest_path(dataset_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_manifest(dataset_id: str) -> dict:
    target = manifest_path(dataset_id)
    with target.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_datasets() -> Iterable[str]:
    root = get_data_root()
    if not root.exists():
        return []
    for entry in root.iterdir():
        if entry.is_dir() and (entry / MANIFEST_NAME).exists():
            yield entry.name


def ingest_dataset(
    image_path: str | Path,
    h5ad_path: str | Path,
    dataset_id: Optional[str] = None,
    *,
    copy_files: bool = False,
    metadata: Optional[dict] = None,
) -> dict:
    """Register a TIFF + h5ad pair and write a manifest (copying files only if requested)."""
    src_image = _expand_path(image_path)
    src_h5ad = _expand_path(h5ad_path)
    if not src_image.exists():
        raise FileNotFoundError(f"Image file not found: {src_image}")
    if not src_h5ad.exists():
        raise FileNotFoundError(f"h5ad file not found: {src_h5ad}")

    if dataset_id:
        dataset_id = _sanitize_dataset_id(dataset_id)
        manifest_file = manifest_path(dataset_id)
        if manifest_file.exists():
            existing = load_manifest(dataset_id)
            src_info = existing.get("source_info", {})
            image_ok = _matches_signature(src_info.get("image"), _expand_path(existing["image_path"]))
            h5ad_ok = _matches_signature(src_info.get("h5ad"), _expand_path(existing["h5ad_path"]))
            if not (image_ok and h5ad_ok):
                raise ValueError(
                    f"Dataset id '{dataset_id}' already exists with different data. "
                    "Choose another dataset_id."
                )
    else:
        dataset_id = suggest_dataset_id(src_image)

    base = _ensure_dataset_dirs(dataset_id)
    raw_dir = base / RAW_DIR
    processed_dir = base / PROCESSED_DIR

    if copy_files:
        dst_image = raw_dir / src_image.name
        dst_h5ad = raw_dir / src_h5ad.name
        shutil.copy2(src_image, dst_image)
        shutil.copy2(src_h5ad, dst_h5ad)
    else:
        dst_image = src_image
        dst_h5ad = src_h5ad

    manifest = {
        "dataset_id": dataset_id,
        "image_path": str(dst_image),
        "h5ad_path": str(dst_h5ad),
        "output_root": str(processed_dir),
        "source_info": {
            "image": {**_file_signature(dst_image), "original_path": str(src_image)},
            "h5ad": {**_file_signature(dst_h5ad), "original_path": str(src_h5ad)},
            "copied": copy_files,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if metadata:
        manifest["metadata"] = metadata
    save_manifest(dataset_id, manifest)
    return manifest


@dataclass(slots=True)
class DatasetContext:
    dataset_id: Optional[str]
    image_path: Path
    h5ad_path: Path
    output_root: Path


def _ensure_sources_intact(dataset_id: str, manifest: dict) -> None:
    src_info = manifest.get("source_info", {})
    for key in ("image", "h5ad"):
        info = src_info.get(key)
        if not info:
            continue
        path = _expand_path(manifest[f"{key}_path"])
        if not _matches_signature(info, path):
            raise RuntimeError(
                f"Dataset '{dataset_id}' {key} file changed or missing ({path}). "
                "Re-ingest or copy the dataset to refresh caches."
            )


def get_dataset_paths(dataset_id: str) -> DatasetContext:
    """Return manifest-backed paths for an existing dataset, validating source integrity."""
    manifest = load_manifest(dataset_id)
    img = _expand_path(manifest["image_path"])
    h5ad = _expand_path(manifest["h5ad_path"])
    out_root = _expand_path(manifest.get("output_root", _dataset_dir(dataset_id) / PROCESSED_DIR))
    if not img.exists():
        raise FileNotFoundError(f"Dataset '{dataset_id}' image missing: {img}")
    if not h5ad.exists():
        raise FileNotFoundError(f"Dataset '{dataset_id}' h5ad missing: {h5ad}")
    _ensure_sources_intact(dataset_id, manifest)
    out_root.mkdir(parents=True, exist_ok=True)
    return DatasetContext(dataset_id, img, h5ad, out_root)


def resolve_dataset_context(
    dataset_id: Optional[str],
    image_path: Optional[str],
    h5ad_path: Optional[str],
    output_root: Optional[str] = None,
) -> DatasetContext:
    """Resolve file paths from dataset_id or explicit arguments."""
    if dataset_id:
        return get_dataset_paths(dataset_id)

    if not image_path or not h5ad_path:
        raise ValueError("image_path and h5ad_path are required when dataset_id is not provided")

    img = _expand_path(image_path)
    h5ad = _expand_path(h5ad_path)
    if not img.exists():
        raise FileNotFoundError(f"Image file not found: {img}")
    if not h5ad.exists():
        raise FileNotFoundError(f"h5ad file not found: {h5ad}")

    if output_root:
        out_root = _expand_path(output_root)
    else:
        out_root = get_data_root() / "legacy"
    out_root.mkdir(parents=True, exist_ok=True)
    return DatasetContext(None, img, h5ad, out_root)


def clear_processed_cache(dataset_id: str, *, delete_raw: bool = False) -> dict:
    """Remove processed outputs (and optionally raw copies) for a dataset."""
    manifest = load_manifest(dataset_id)
    base = _dataset_dir(dataset_id)
    processed_root = _expand_path(manifest.get("output_root", base / PROCESSED_DIR))
    removed = {"processed": False, "raw_files": []}
    if processed_root.exists():
        shutil.rmtree(processed_root, ignore_errors=True)
        removed["processed"] = True
    processed_root.mkdir(parents=True, exist_ok=True)

    if delete_raw:
        for key in ("image_path", "h5ad_path"):
            path = _expand_path(manifest.get(key, ""))
            if path.exists():
                try:
                    path.unlink()
                    removed["raw_files"].append(str(path))
                except Exception:
                    pass
    return removed


__all__ = [
    "DatasetContext",
    "get_data_root",
    "get_dataset_paths",
    "ingest_dataset",
    "list_datasets",
    "manifest_path",
    "resolve_dataset_context",
    "clear_processed_cache",
    "suggest_dataset_id",
    "load_manifest",
    "save_manifest",
]
