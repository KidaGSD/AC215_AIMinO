"""Viewer (camera) command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..command_models import CmdCenterOn, CmdSetZoom, CmdZoomBox
from ..registry import register_handler
from .shared import set_view_box

if TYPE_CHECKING:
    from napari.viewer import Viewer


@register_handler("zoom_box")
def handle_zoom_box(command: CmdZoomBox, viewer: "Viewer") -> str:
    x1, y1, x2, y2 = command.box
    return set_view_box(viewer, x1, y1, x2, y2)


@register_handler("center_on")
def handle_center_on(command: CmdCenterOn, viewer: "Viewer") -> str:
    x, y = command.point
    viewer.camera.center = (float(x), float(y))
    return f"Centered on ({float(x):.1f}, {float(y):.1f})"


@register_handler("set_zoom")
def handle_set_zoom(command: CmdSetZoom, viewer: "Viewer") -> str:
    viewer.camera.zoom = float(command.zoom)
    return f"Set zoom to {float(command.zoom):.2f}"


__all__ = [
    "handle_center_on",
    "handle_set_zoom",
    "handle_zoom_box",
]
