"""Image layer handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...command_models import (
    CmdImageAttenuation,
    CmdImageColormap,
    CmdImageContrastLimits,
    CmdImageGamma,
    CmdImageInterpolation,
    CmdImageIsoThreshold,
    CmdImageRendering,
)
from ...errors import CommandExecutionError
from ...registry import register_handler
from ..layer_management.layer_list import find_layer, list_layers

if TYPE_CHECKING:
    from napari.layers import Image
    from napari.viewer import Viewer


def _get_image_layer(viewer: "Viewer", name: str) -> "Image":
    layer = find_layer(viewer, name)
    if layer is None:
        raise CommandExecutionError(
            f"Layer '{name}' not found. Layers: {', '.join(list_layers(viewer)) or '(none)'}"
        )
    if not hasattr(layer, "contrast_limits"):  # Basic check for Image-like layer
        raise CommandExecutionError(f"Layer '{name}' is not an Image layer.")
    return layer


@register_handler("image_contrast_limits")
def handle_image_contrast_limits(command: CmdImageContrastLimits, viewer: "Viewer") -> str:
    layer = _get_image_layer(viewer, command.layer_name)
    layer.contrast_limits = command.limits
    return f"Set contrast limits for '{layer.name}' to {command.limits}"


@register_handler("image_gamma")
def handle_image_gamma(command: CmdImageGamma, viewer: "Viewer") -> str:
    layer = _get_image_layer(viewer, command.layer_name)
    layer.gamma = command.gamma
    return f"Set gamma for '{layer.name}' to {command.gamma}"


@register_handler("image_colormap")
def handle_image_colormap(command: CmdImageColormap, viewer: "Viewer") -> str:
    layer = _get_image_layer(viewer, command.layer_name)
    layer.colormap = command.colormap
    return f"Set colormap for '{layer.name}' to '{command.colormap}'"


@register_handler("image_interpolation")
def handle_image_interpolation(command: CmdImageInterpolation, viewer: "Viewer") -> str:
    layer = _get_image_layer(viewer, command.layer_name)
    # Handle both 2D and 3D interpolation if possible, or just set the property that matches current dims
    # Napari exposes interpolation2d and interpolation3d.
    # Usually users just want "interpolation". Let's set both or check dims.
    # For simplicity, let's try setting both if they exist, or just one.
    # But the API usually exposes 'interpolation' as a proxy property in some contexts,
    # but the Layer class has interpolation2d and interpolation3d.
    # Let's assume the user intent is "how it looks now".
    if viewer.dims.ndisplay == 2:
        layer.interpolation2d = command.interpolation
        return f"Set 2D interpolation for '{layer.name}' to '{command.interpolation}'"
    else:
        layer.interpolation3d = command.interpolation
        return f"Set 3D interpolation for '{layer.name}' to '{command.interpolation}'"


@register_handler("image_rendering")
def handle_image_rendering(command: CmdImageRendering, viewer: "Viewer") -> str:
    layer = _get_image_layer(viewer, command.layer_name)
    layer.rendering = command.rendering
    return f"Set rendering for '{layer.name}' to '{command.rendering}'"


@register_handler("image_iso_threshold")
def handle_image_iso_threshold(command: CmdImageIsoThreshold, viewer: "Viewer") -> str:
    layer = _get_image_layer(viewer, command.layer_name)
    layer.iso_threshold = command.threshold
    return f"Set iso_threshold for '{layer.name}' to {command.threshold}"


@register_handler("image_attenuation")
def handle_image_attenuation(command: CmdImageAttenuation, viewer: "Viewer") -> str:
    layer = _get_image_layer(viewer, command.layer_name)
    layer.attenuation = command.attenuation
    return f"Set attenuation for '{layer.name}' to {command.attenuation}"


__all__ = [
    "handle_image_attenuation",
    "handle_image_colormap",
    "handle_image_contrast_limits",
    "handle_image_gamma",
    "handle_image_interpolation",
    "handle_image_iso_threshold",
    "handle_image_rendering",
]
