"""Shapes layer handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...command_models import (
    CmdShapesCurrentEdgeColor,
    CmdShapesCurrentEdgeWidth,
    CmdShapesCurrentFaceColor,
    CmdShapesEdgeColor,
    CmdShapesEdgeWidth,
    CmdShapesFaceColor,
    CmdShapesText,
    CmdShapesZIndex,
)
from ...errors import CommandExecutionError
from ...registry import register_handler
from ..layer_management.layer_list import find_layer, list_layers

if TYPE_CHECKING:
    from napari.layers import Shapes
    from napari.viewer import Viewer


def _get_shapes_layer(viewer: "Viewer", name: str) -> "Shapes":
    layer = find_layer(viewer, name)
    if layer is None:
        raise CommandExecutionError(
            f"Layer '{name}' not found. Layers: {', '.join(list_layers(viewer)) or '(none)'}"
        )
    if not hasattr(layer, "shape_type"):  # Basic check for Shapes-like layer
        raise CommandExecutionError(f"Layer '{name}' is not a Shapes layer.")
    return layer


@register_handler("shapes_edge_width")
def handle_shapes_edge_width(command: CmdShapesEdgeWidth, viewer: "Viewer") -> str:
    layer = _get_shapes_layer(viewer, command.layer_name)
    layer.edge_width = command.width
    return f"Set edge width for '{layer.name}' to {command.width}"


@register_handler("shapes_edge_color")
def handle_shapes_edge_color(command: CmdShapesEdgeColor, viewer: "Viewer") -> str:
    layer = _get_shapes_layer(viewer, command.layer_name)
    layer.edge_color = command.color
    return f"Set edge color for '{layer.name}' to {command.color}"


@register_handler("shapes_face_color")
def handle_shapes_face_color(command: CmdShapesFaceColor, viewer: "Viewer") -> str:
    layer = _get_shapes_layer(viewer, command.layer_name)
    layer.face_color = command.color
    return f"Set face color for '{layer.name}' to {command.color}"


@register_handler("shapes_z_index")
def handle_shapes_z_index(command: CmdShapesZIndex, viewer: "Viewer") -> str:
    layer = _get_shapes_layer(viewer, command.layer_name)
    layer.z_index = command.index
    return f"Set z-index for '{layer.name}' to {command.index}"


@register_handler("shapes_text")
def handle_shapes_text(command: CmdShapesText, viewer: "Viewer") -> str:
    layer = _get_shapes_layer(viewer, command.layer_name)
    layer.text = command.text
    return f"Set text for '{layer.name}' to {command.text}"


@register_handler("shapes_current_edge_width")
def handle_shapes_current_edge_width(
    command: CmdShapesCurrentEdgeWidth, viewer: "Viewer"
) -> str:
    layer = _get_shapes_layer(viewer, command.layer_name)
    layer.current_edge_width = command.width
    return f"Set current edge width for '{layer.name}' to {command.width}"


@register_handler("shapes_current_edge_color")
def handle_shapes_current_edge_color(
    command: CmdShapesCurrentEdgeColor, viewer: "Viewer"
) -> str:
    layer = _get_shapes_layer(viewer, command.layer_name)
    layer.current_edge_color = command.color
    return f"Set current edge color for '{layer.name}' to {command.color}"


@register_handler("shapes_current_face_color")
def handle_shapes_current_face_color(
    command: CmdShapesCurrentFaceColor, viewer: "Viewer"
) -> str:
    layer = _get_shapes_layer(viewer, command.layer_name)
    layer.current_face_color = command.color
    return f"Set current face color for '{layer.name}' to {command.color}"


__all__ = [
    "handle_shapes_current_edge_color",
    "handle_shapes_current_edge_width",
    "handle_shapes_current_face_color",
    "handle_shapes_edge_color",
    "handle_shapes_edge_width",
    "handle_shapes_face_color",
    "handle_shapes_text",
    "handle_shapes_z_index",
]
