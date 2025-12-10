"""Shared dataset selection context for Napari widgets."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class _DatasetContextState:
    dataset_id: Optional[str] = None
    marker_col: Optional[str] = None
    last_sigma: Optional[float] = None
    last_radius: Optional[float] = None
    available_datasets: list[str] = None  # type: ignore[assignment]
    available_markers: list[str] = None  # type: ignore[assignment]


_STATE = _DatasetContextState()


def get_current_dataset_id() -> Optional[str]:
    return _STATE.dataset_id


def set_current_dataset(dataset_id: Optional[str], marker_col: Optional[str] = None) -> None:
    _STATE.dataset_id = dataset_id
    if marker_col is not None:
        _STATE.marker_col = marker_col


def set_marker(marker_col: Optional[str]) -> None:
    _STATE.marker_col = marker_col


def get_current_marker() -> Optional[str]:
    return _STATE.marker_col


def set_sigma(value: Optional[float]) -> None:
    _STATE.last_sigma = value


def get_last_sigma() -> Optional[float]:
    return _STATE.last_sigma


def set_radius(value: Optional[float]) -> None:
    _STATE.last_radius = value


def get_last_radius() -> Optional[float]:
    return _STATE.last_radius


def set_available_datasets(values: Optional[list[str]]) -> None:
    _STATE.available_datasets = values or []


def get_available_datasets() -> list[str]:
    return _STATE.available_datasets or []


def set_available_markers(values: Optional[list[str]]) -> None:
    _STATE.available_markers = values or []


def get_available_markers() -> list[str]:
    return _STATE.available_markers or []


def get_context_payload() -> dict:
    payload = {}
    if _STATE.dataset_id:
        payload["dataset_id"] = _STATE.dataset_id
    if _STATE.marker_col:
        payload["marker_col"] = _STATE.marker_col
    if _STATE.last_sigma is not None:
        payload["sigma"] = _STATE.last_sigma
    if _STATE.last_radius is not None:
        payload["radius"] = _STATE.last_radius
    if _STATE.available_datasets:
        payload["dataset_candidates"] = list(_STATE.available_datasets)
    if _STATE.available_markers:
        payload["marker_candidates"] = list(_STATE.available_markers)
    return payload


def update_from_command(command: dict) -> None:
    action = command.get("action")
    marker = command.get("marker_col")
    if action == "special_load_marker_data" and marker:
        set_marker(marker)
    elif action == "special_update_density":
        if marker:
            set_marker(marker)
        sigma = command.get("sigma")
        if sigma is not None:
            set_sigma(float(sigma))
    elif action == "special_compute_neighborhood":
        if marker:
            set_marker(marker)
        radius = command.get("radius")
        if radius is not None:
            set_radius(float(radius))


__all__ = [
    "get_current_dataset_id",
    "set_current_dataset",
    "set_marker",
    "get_current_marker",
    "set_sigma",
    "get_last_sigma",
    "set_radius",
    "get_last_radius",
    "set_available_datasets",
    "get_available_datasets",
    "set_available_markers",
    "get_available_markers",
    "get_context_payload",
    "update_from_command",
]
