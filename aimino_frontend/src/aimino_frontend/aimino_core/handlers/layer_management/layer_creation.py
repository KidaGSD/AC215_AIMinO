"""Layer creation command handlers for adding layers to the viewer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...command_models import (
    CmdViewerModelAddImage,
    CmdViewerModelAddLabels,
    CmdViewerModelAddLayer,
    CmdViewerModelAddPoints,
    CmdViewerModelAddShapes,
    CmdViewerModelAddSurface,
    CmdViewerModelAddTracks,
    CmdViewerModelAddVectors,
)
from ...errors import CommandExecutionError
from ...registry import register_handler

if TYPE_CHECKING:
    from napari.viewer import Viewer


@register_handler("viewer_model_add_layer")
def handle_viewer_model_add_layer(command: CmdViewerModelAddLayer, viewer: "Viewer") -> str:
    """Add a layer to the viewer."""
    # Note: This requires the actual layer object to be passed
    # In practice, you might need to construct the layer from the command data
    # This is a simplified implementation
    if not hasattr(command, "layer") or command.layer is None:
        raise CommandExecutionError("Layer object is required for viewer_model_add_layer")
    
    # For now, we'll assume the layer is passed as a dict that can be used to construct it
    # In a real implementation, you'd need to handle layer creation properly
    layer_data = command.layer if hasattr(command, "layer") else {}
    # This would need proper layer construction logic
    return "Layer addition requires proper layer object construction"


@register_handler("viewer_model_add_image")
def handle_viewer_model_add_image(command: CmdViewerModelAddImage, viewer: "Viewer") -> str:
    """Add one or more Image layers to the layer list."""
    data = command.data
    if data is None:
        raise CommandExecutionError("Data is required for viewer_model_add_image")
    
    kwargs = command.kwargs or {}
    layers = viewer.add_image(data, **kwargs)
    
    if isinstance(layers, list):
        layer_names = [layer.name for layer in layers]
        return f"Added {len(layers)} image layer(s): {', '.join(layer_names)}"
    else:
        return f"Added image layer: {layers.name}"


@register_handler("viewer_model_add_labels")
def handle_viewer_model_add_labels(command: CmdViewerModelAddLabels, viewer: "Viewer") -> str:
    """Add a Labels layer to the layer list."""
    data = command.data
    if data is None:
        raise CommandExecutionError("Data is required for viewer_model_add_labels")
    
    kwargs = command.kwargs or {}
    layer = viewer.add_labels(data, **kwargs)
    return f"Added labels layer: {layer.name}"


@register_handler("viewer_model_add_points")
def handle_viewer_model_add_points(command: CmdViewerModelAddPoints, viewer: "Viewer") -> str:
    """Add a Points layer to the layer list."""
    data = command.data
    kwargs = command.kwargs or {}
    layer = viewer.add_points(data, **kwargs)
    return f"Added points layer: {layer.name}"


@register_handler("viewer_model_add_shapes")
def handle_viewer_model_add_shapes(command: CmdViewerModelAddShapes, viewer: "Viewer") -> str:
    """Add a Shapes layer to the layer list."""
    data = command.data
    kwargs = command.kwargs or {}
    layer = viewer.add_shapes(data, **kwargs)
    return f"Added shapes layer: {layer.name}"


@register_handler("viewer_model_add_surface")
def handle_viewer_model_add_surface(command: CmdViewerModelAddSurface, viewer: "Viewer") -> str:
    """Add a Surface layer to the layer list."""
    data = command.data
    if data is None:
        raise CommandExecutionError("Data is required for viewer_model_add_surface")
    
    kwargs = command.kwargs or {}
    layer = viewer.add_surface(data, **kwargs)
    return f"Added surface layer: {layer.name}"


@register_handler("viewer_model_add_tracks")
def handle_viewer_model_add_tracks(command: CmdViewerModelAddTracks, viewer: "Viewer") -> str:
    """Add a Tracks layer to the layer list."""
    data = command.data
    if data is None:
        raise CommandExecutionError("Data is required for viewer_model_add_tracks")
    
    kwargs = command.kwargs or {}
    layer = viewer.add_tracks(data, **kwargs)
    return f"Added tracks layer: {layer.name}"


@register_handler("viewer_model_add_vectors")
def handle_viewer_model_add_vectors(command: CmdViewerModelAddVectors, viewer: "Viewer") -> str:
    """Add a Vectors layer to the layer list."""
    data = command.data
    kwargs = command.kwargs or {}
    layer = viewer.add_vectors(data, **kwargs)
    return f"Added vectors layer: {layer.name}"


__all__ = [
    "handle_viewer_model_add_image",
    "handle_viewer_model_add_labels",
    "handle_viewer_model_add_layer",
    "handle_viewer_model_add_points",
    "handle_viewer_model_add_shapes",
    "handle_viewer_model_add_surface",
    "handle_viewer_model_add_tracks",
    "handle_viewer_model_add_vectors",
]

