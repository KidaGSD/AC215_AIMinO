"""Shared utilities for handler implementations."""

from __future__ import annotations

from typing import Iterable, Optional, TYPE_CHECKING

from ..errors import CommandExecutionError

if TYPE_CHECKING:
    from napari.layers import Layer
    from napari.viewer import Viewer


def list_layers(viewer: "Viewer") -> list[str]:
    return [layer.name for layer in viewer.layers]


def iter_layers(viewer: "Viewer") -> Iterable["Layer"]:
    for layer in viewer.layers:
        yield layer


def find_layer(viewer: "Viewer", name: str) -> Optional["Layer"]:
    query = name.strip().lower()
    if not query:
        return None

    for layer in viewer.layers:
        if layer.name.lower() == query:
            return layer

    matches = [layer for layer in viewer.layers if query in layer.name.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(layer.name for layer in matches)
        raise CommandExecutionError(f"Layer name '{name}' is ambiguous: {names}")
    return None


def get_vispy_camera(viewer: "Viewer"):
    window = getattr(viewer, "window", None)
    if window is None:
        return None

    qt_viewer = getattr(window, "_qt_viewer", None) or getattr(window, "qt_viewer", None)
    if qt_viewer is None:
        return None

    canvas = getattr(qt_viewer, "canvas", None)
    if canvas is not None and hasattr(canvas, "scene"):
        scene = getattr(canvas, "scene", None)
        return getattr(scene, "camera", None)

    view = getattr(qt_viewer, "view", None)
    if view is not None:
        return getattr(view, "camera", None)
    return None


def set_view_box(viewer: "Viewer", x1: float, y1: float, x2: float, y2: float) -> str:
    xlo, xhi = sorted([float(x1), float(x2)])
    ylo, yhi = sorted([float(y1), float(y2)])

    camera = get_vispy_camera(viewer)
    if camera and hasattr(camera, "set_range"):
        camera.set_range(x=(xlo, xhi), y=(ylo, yhi))

    viewer.camera.center = ((xlo + xhi) / 2.0, (ylo + yhi) / 2.0)
    return f"Zoomed to ({xlo:.1f}, {ylo:.1f})–({xhi:.1f}, {yhi:.1f})"


__all__ = [
    "find_layer",
    "get_vispy_camera",
    "iter_layers",
    "list_layers",
    "set_view_box",
]
