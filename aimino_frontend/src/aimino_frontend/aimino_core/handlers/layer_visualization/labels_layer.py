"""Labels layer handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...command_models import (
    CmdLabelsBrushSize,
    CmdLabelsColormap,
    CmdLabelsContiguous,
    CmdLabelsContour,
    CmdLabelsIsoGradientMode,
    CmdLabelsMode,
    CmdLabelsNEditDimensions,
    CmdLabelsRendering,
    CmdLabelsSelectedLabel,
)
from ...errors import CommandExecutionError
from ...registry import register_handler
from ..layer_management.layer_list import find_layer, list_layers

if TYPE_CHECKING:
    from napari.layers import Labels
    from napari.viewer import Viewer


def _get_labels_layer(viewer: "Viewer", name: str) -> "Labels":
    layer = find_layer(viewer, name)
    if layer is None:
        raise CommandExecutionError(
            f"Layer '{name}' not found. Layers: {', '.join(list_layers(viewer)) or '(none)'}"
        )
    if not hasattr(layer, "num_colors"):  # Basic check for Labels-like layer
        raise CommandExecutionError(f"Layer '{name}' is not a Labels layer.")
    return layer


@register_handler("labels_contour")
def handle_labels_contour(command: CmdLabelsContour, viewer: "Viewer") -> str:
    layer = _get_labels_layer(viewer, command.layer_name)
    layer.contour = command.contour
    return f"Set contour for '{layer.name}' to {command.contour}"


@register_handler("labels_n_edit_dimensions")
def handle_labels_n_edit_dimensions(
    command: CmdLabelsNEditDimensions, viewer: "Viewer"
) -> str:
    layer = _get_labels_layer(viewer, command.layer_name)
    layer.n_edit_dimensions = command.n_edit_dimensions
    return f"Set n_edit_dimensions for '{layer.name}' to {command.n_edit_dimensions}"


@register_handler("labels_brush_size")
def handle_labels_brush_size(command: CmdLabelsBrushSize, viewer: "Viewer") -> str:
    layer = _get_labels_layer(viewer, command.layer_name)
    layer.brush_size = command.size
    return f"Set brush size for '{layer.name}' to {command.size}"


@register_handler("labels_colormap")
def handle_labels_colormap(command: CmdLabelsColormap, viewer: "Viewer") -> str:
    layer = _get_labels_layer(viewer, command.layer_name)
    # Napari Labels layer colormap handling can be complex (CyclicLabelColormap etc.)
    # But often users just pass a name or we can try setting it.
    # If it fails, napari will raise an error which we can catch or let bubble up.
    # For now, we assume simple string assignment works or the user knows what they are doing.
    # Note: napari.utils.colormaps.label_colormap might be needed for more advanced usage.
    layer.colormap = command.colormap
    return f"Set colormap for '{layer.name}' to '{command.colormap}'"


@register_handler("labels_contiguous")
def handle_labels_contiguous(command: CmdLabelsContiguous, viewer: "Viewer") -> str:
    layer = _get_labels_layer(viewer, command.layer_name)
    layer.contiguous = command.contiguous
    return f"Set contiguous for '{layer.name}' to {command.contiguous}"


@register_handler("labels_rendering")
def handle_labels_rendering(command: CmdLabelsRendering, viewer: "Viewer") -> str:
    layer = _get_labels_layer(viewer, command.layer_name)
    layer.rendering = command.rendering
    return f"Set rendering for '{layer.name}' to '{command.rendering}'"


@register_handler("labels_iso_gradient_mode")
def handle_labels_iso_gradient_mode(
    command: CmdLabelsIsoGradientMode, viewer: "Viewer"
) -> str:
    layer = _get_labels_layer(viewer, command.layer_name)
    layer.iso_gradient_mode = command.mode
    return f"Set iso_gradient_mode for '{layer.name}' to '{command.mode}'"


@register_handler("labels_selected_label")
def handle_labels_selected_label(
    command: CmdLabelsSelectedLabel, viewer: "Viewer"
) -> str:
    layer = _get_labels_layer(viewer, command.layer_name)
    layer.selected_label = command.label
    return f"Set selected label for '{layer.name}' to {command.label}"


@register_handler("labels_mode")
def handle_labels_mode(command: CmdLabelsMode, viewer: "Viewer") -> str:
    layer = _get_labels_layer(viewer, command.layer_name)
    layer.mode = command.mode
    return f"Set mode for '{layer.name}' to '{command.mode}'"


__all__ = [
    "handle_labels_brush_size",
    "handle_labels_colormap",
    "handle_labels_contiguous",
    "handle_labels_contour",
    "handle_labels_iso_gradient_mode",
    "handle_labels_mode",
    "handle_labels_n_edit_dimensions",
    "handle_labels_rendering",
    "handle_labels_selected_label",
]
