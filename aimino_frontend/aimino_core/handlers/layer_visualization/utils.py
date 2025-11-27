"""Shared utilities for layer visualization handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from napari.layers import Layer
    import numpy as np


def get_layer_property(layer: "Layer", prop: str) -> Any:
    """Get a property value from a layer."""
    return getattr(layer, prop)


def set_layer_property(layer: "Layer", prop: str, value: Any) -> None:
    """Set a property value on a layer."""
    setattr(layer, prop, value)


def toggle_layer_visibility(layer: "Layer") -> bool:
    """Toggle layer visibility and return the new state."""
    layer.visible = not layer.visible
    return layer.visible


def set_layer_opacity(layer: "Layer", opacity: float) -> None:
    """Set layer opacity (0.0 to 1.0)."""
    layer.opacity = max(0.0, min(1.0, float(opacity)))


def set_layer_blending(layer: "Layer", blending: str) -> None:
    """Set layer blending mode."""
    layer.blending = blending


def set_layer_scale(layer: "Layer", scale: "list[float] | tuple[float, ...]") -> None:
    """Set layer scale factors."""
    layer.scale = scale


def set_layer_translate(layer: "Layer", translate: "list[float] | tuple[float, ...]") -> None:
    """Set layer translation values."""
    layer.translate = translate


def set_layer_rotate(layer: "Layer", rotate: Any) -> None:
    """Set layer rotation."""
    layer.rotate = rotate


def set_layer_shear(layer: "Layer", shear: Any) -> None:
    """Set layer shear."""
    layer.shear = shear


def set_layer_affine(layer: "Layer", affine: Any) -> None:
    """Set layer affine transform."""
    layer.affine = affine


def rename_layer(layer: "Layer", name: str) -> None:
    """Rename a layer."""
    layer.name = name


def get_layer_data_to_world(layer: "Layer", position: "tuple[float, ...]") -> "tuple[float, ...]":
    """Convert from data coordinates to world coordinates."""
    return layer.data_to_world(position)


def get_layer_world_to_data(layer: "Layer", position: "tuple[float, ...]") -> "tuple[float, ...]":
    """Convert from world coordinates to data coordinates."""
    return layer.world_to_data(position)


__all__ = [
    "get_layer_data_to_world",
    "get_layer_property",
    "get_layer_world_to_data",
    "rename_layer",
    "set_layer_affine",
    "set_layer_blending",
    "set_layer_opacity",
    "set_layer_property",
    "set_layer_rotate",
    "set_layer_scale",
    "set_layer_shear",
    "set_layer_translate",
    "toggle_layer_visibility",
]
