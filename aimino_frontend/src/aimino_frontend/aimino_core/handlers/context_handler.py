"""Handlers for context management commands (set_dataset, set_marker, etc.)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ..registry import register_handler
from ..data_store import (
    list_datasets,
    load_manifest,
    clear_processed_cache,
    get_dataset_paths,
)

if TYPE_CHECKING:
    from napari.viewer import Viewer

# Import context functions - these will be set by the napari_app module
_context_setters = {
    "set_dataset": None,
    "set_marker": None,
    "get_dataset_id": None,
    "get_marker": None,
}


def set_context_functions(
    set_dataset_fn=None,
    set_marker_fn=None,
    get_dataset_id_fn=None,
    get_marker_fn=None,
):
    """Allow napari_app to inject context management functions."""
    if set_dataset_fn:
        _context_setters["set_dataset"] = set_dataset_fn
    if set_marker_fn:
        _context_setters["set_marker"] = set_marker_fn
    if get_dataset_id_fn:
        _context_setters["get_dataset_id"] = get_dataset_id_fn
    if get_marker_fn:
        _context_setters["get_marker"] = get_marker_fn


def _get_attr(command, attr, default=None):
    """Get attribute from command (works with dict or Pydantic model)."""
    if hasattr(command, attr):
        return getattr(command, attr)
    elif isinstance(command, dict):
        return command.get(attr, default)
    return default


@register_handler("set_dataset")
def handle_set_dataset(command, viewer: "Viewer") -> str:
    """Switch active dataset context."""
    dataset_id = _get_attr(command, "dataset_id")
    if not dataset_id:
        return "Error: dataset_id is required"

    # Verify dataset exists
    try:
        get_dataset_paths(dataset_id)
    except Exception as e:
        return f"Error: Dataset '{dataset_id}' not found: {e}"

    # Set context if function is available
    set_fn = _context_setters.get("set_dataset")
    if set_fn:
        set_fn(dataset_id, None)

    return f"Switched to dataset: {dataset_id}"


@register_handler("set_marker")
def handle_set_marker(command, viewer: "Viewer") -> str:
    """Switch active marker column."""
    marker_col = _get_attr(command, "marker_col")
    if not marker_col:
        return "Error: marker_col is required"

    # Set marker if function is available
    set_fn = _context_setters.get("set_marker")
    if set_fn:
        set_fn(marker_col)

    return f"Switched to marker: {marker_col}"


@register_handler("list_datasets")
def handle_list_datasets(command, viewer: "Viewer") -> str:
    """List all available datasets."""
    datasets = sorted(list(list_datasets()))
    if not datasets:
        return "No datasets found. Use 'data_ingest' to register a dataset."

    # Get current dataset for highlighting
    get_ds_fn = _context_setters.get("get_dataset_id")
    current_ds = get_ds_fn() if get_ds_fn else None

    result = f"Available datasets ({len(datasets)}):\n"
    for ds in datasets:
        marker = ""
        if ds == current_ds:
            marker = " [active]"
        result += f"  - {ds}{marker}\n"

    return result.strip()


@register_handler("get_dataset_info")
def handle_get_dataset_info(command, viewer: "Viewer") -> str:
    """Get information about a dataset."""
    dataset_id = _get_attr(command, "dataset_id")

    # Use current dataset if not specified
    if not dataset_id:
        get_ds_fn = _context_setters.get("get_dataset_id")
        dataset_id = get_ds_fn() if get_ds_fn else None

    if not dataset_id:
        return "Error: No dataset specified and no active dataset"

    try:
        manifest = load_manifest(dataset_id)
    except Exception as e:
        return f"Error: Failed to load dataset '{dataset_id}': {e}"

    # Format info
    info = {
        "dataset_id": manifest.get("dataset_id"),
        "image_path": manifest.get("image_path"),
        "h5ad_path": manifest.get("h5ad_path"),
        "output_root": manifest.get("output_root"),
        "created_at": manifest.get("created_at"),
        "marker_cols": manifest.get("metadata", {}).get("marker_cols", []),
    }

    result = f"Dataset: {dataset_id}\n"
    result += f"  Image: {info['image_path']}\n"
    result += f"  H5AD: {info['h5ad_path']}\n"
    result += f"  Output: {info['output_root']}\n"
    if info['marker_cols']:
        result += f"  Markers: {', '.join(info['marker_cols'])}\n"
    result += f"  Created: {info['created_at']}"

    return result


@register_handler("clear_processed_cache")
def handle_clear_cache(command, viewer: "Viewer") -> str:
    """Clear processed cache for a dataset."""
    dataset_id = _get_attr(command, "dataset_id")

    # Use current dataset if not specified
    if not dataset_id:
        get_ds_fn = _context_setters.get("get_dataset_id")
        dataset_id = get_ds_fn() if get_ds_fn else None

    if not dataset_id:
        return "Error: No dataset specified and no active dataset"

    delete_raw = _get_attr(command, "delete_raw", False)

    try:
        result = clear_processed_cache(dataset_id, delete_raw=delete_raw)
        msg = f"Cleared cache for dataset '{dataset_id}'"
        if result.get("processed"):
            msg += " (processed files removed)"
        if result.get("raw_files"):
            msg += f" (raw files removed: {len(result['raw_files'])})"
        return msg
    except Exception as e:
        return f"Error: Failed to clear cache for '{dataset_id}': {e}"


__all__ = [
    "handle_set_dataset",
    "handle_set_marker",
    "handle_list_datasets",
    "handle_get_dataset_info",
    "handle_clear_cache",
    "set_context_functions",
]
