"""Layer-related command handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..command_models import CmdFitToLayer, CmdLayerVisibility
from ..errors import CommandExecutionError
from ..registry import register_handler
from .shared import find_layer, list_layers, set_view_box

if TYPE_CHECKING:
    from napari.viewer import Viewer
    from ..command_models import BaseNapariCommand


@register_handler("layer_visibility")
def handle_layer_visibility(command: CmdLayerVisibility, viewer: "Viewer") -> str:
    layer = find_layer(viewer, command.name)
    if layer is None:
        raise CommandExecutionError(
            f"Layer '{command.name}' not found. Layers: {', '.join(list_layers(viewer)) or '(none)'}"
        )

    if command.op == "show":
        layer.visible = True
    elif command.op == "hide":
        layer.visible = False
    else:
        layer.visible = not layer.visible

    state = "Shown" if layer.visible else "Hidden"
    return f"{state} layer '{layer.name}'"


@register_handler("fit_to_layer")
def handle_fit_to_layer(command: CmdFitToLayer, viewer: "Viewer") -> str:
    layer = find_layer(viewer, command.name)
    if layer is None:
        raise CommandExecutionError(
            f"Layer '{command.name}' not found. Layers: {', '.join(list_layers(viewer)) or '(none)'}"
        )

    world_extent = getattr(layer.extent, "world", None)
    if world_extent is None:
        raise CommandExecutionError(f"Layer '{layer.name}' does not expose world extent.")

    (ymin, xmin), (ymax, xmax) = world_extent[0][:2], world_extent[1][:2]
    return set_view_box(viewer, xmin, ymin, xmax, ymax)


__all__ = [
    "handle_fit_to_layer",
    "handle_layer_visibility",
]
