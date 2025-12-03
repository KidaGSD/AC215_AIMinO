"""Points layer handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...command_models import (
    CmdPointsAntialiasing,
    CmdPointsBorderColor,
    CmdPointsBorderWidth,
    CmdPointsCanvasSizeLimits,
    CmdPointsFaceColor,
    CmdPointsOutOfSliceDisplay,
    CmdPointsShading,
    CmdPointsSize,
    CmdPointsSymbol,
)
from ...errors import CommandExecutionError
from ...registry import register_handler
from ..layer_management.layer_list import find_layer, list_layers

if TYPE_CHECKING:
    from napari.layers import Points
    from napari.viewer import Viewer


def _get_points_layer(viewer: "Viewer", name: str) -> "Points":
    layer = find_layer(viewer, name)
    if layer is None:
        raise CommandExecutionError(
            f"Layer '{name}' not found. Layers: {', '.join(list_layers(viewer)) or '(none)'}"
        )
    if not hasattr(layer, "symbol"):  # Basic check for Points-like layer
        raise CommandExecutionError(f"Layer '{name}' is not a Points layer.")
    return layer


@register_handler("points_size")
def handle_points_size(command: CmdPointsSize, viewer: "Viewer") -> str:
    layer = _get_points_layer(viewer, command.layer_name)
    layer.size = command.size
    return f"Set size for '{layer.name}' to {command.size}"


@register_handler("points_symbol")
def handle_points_symbol(command: CmdPointsSymbol, viewer: "Viewer") -> str:
    layer = _get_points_layer(viewer, command.layer_name)
    layer.symbol = command.symbol
    return f"Set symbol for '{layer.name}' to '{command.symbol}'"


@register_handler("points_face_color")
def handle_points_face_color(command: CmdPointsFaceColor, viewer: "Viewer") -> str:
    layer = _get_points_layer(viewer, command.layer_name)
    layer.face_color = command.color
    return f"Set face color for '{layer.name}' to {command.color}"


@register_handler("points_border_color")
def handle_points_border_color(command: CmdPointsBorderColor, viewer: "Viewer") -> str:
    layer = _get_points_layer(viewer, command.layer_name)
    layer.border_color = command.color
    return f"Set border color for '{layer.name}' to {command.color}"


@register_handler("points_border_width")
def handle_points_border_width(command: CmdPointsBorderWidth, viewer: "Viewer") -> str:
    layer = _get_points_layer(viewer, command.layer_name)
    layer.border_width = command.width
    return f"Set border width for '{layer.name}' to {command.width}"


@register_handler("points_out_of_slice_display")
def handle_points_out_of_slice_display(
    command: CmdPointsOutOfSliceDisplay, viewer: "Viewer"
) -> str:
    layer = _get_points_layer(viewer, command.layer_name)
    layer.out_of_slice_display = command.display
    return f"Set out_of_slice_display for '{layer.name}' to {command.display}"


@register_handler("points_shading")
def handle_points_shading(command: CmdPointsShading, viewer: "Viewer") -> str:
    layer = _get_points_layer(viewer, command.layer_name)
    layer.shading = command.shading
    return f"Set shading for '{layer.name}' to '{command.shading}'"


@register_handler("points_antialiasing")
def handle_points_antialiasing(command: CmdPointsAntialiasing, viewer: "Viewer") -> str:
    layer = _get_points_layer(viewer, command.layer_name)
    layer.antialiasing = command.antialiasing
    return f"Set antialiasing for '{layer.name}' to {command.antialiasing}"


@register_handler("points_canvas_size_limits")
def handle_points_canvas_size_limits(
    command: CmdPointsCanvasSizeLimits, viewer: "Viewer"
) -> str:
    layer = _get_points_layer(viewer, command.layer_name)
    layer.canvas_size_limits = command.limits
    return f"Set canvas size limits for '{layer.name}' to {command.limits}"


__all__ = [
    "handle_points_antialiasing",
    "handle_points_border_color",
    "handle_points_border_width",
    "handle_points_canvas_size_limits",
    "handle_points_face_color",
    "handle_points_out_of_slice_display",
    "handle_points_shading",
    "handle_points_size",
    "handle_points_symbol",
]
