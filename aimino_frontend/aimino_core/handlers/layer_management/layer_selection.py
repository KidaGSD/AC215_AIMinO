"""Layer selection command handlers for managing layer selection and visibility."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...command_models import (
    CmdLayerSelectionAdd,
    CmdLayerSelectionClear,
    CmdLayerSelectionDiscard,
    CmdLayerSelectionRemove,
    CmdLayerSelectionSelectOnly,
    CmdLayerSelectionSetActive,
    CmdLayerSelectionToggle,
    CmdLayerSelectionVisibility,
)
from ...errors import CommandExecutionError
from ...registry import register_handler
from .layer_list import find_layer

if TYPE_CHECKING:
    from napari.viewer import Viewer


@register_handler("layer_selection_add")
def handle_layer_selection_add(command: CmdLayerSelectionAdd, viewer: "Viewer") -> str:
    """Add layer(s) to the selection."""
    layer_names = command.layer_names
    if not layer_names:
        raise CommandExecutionError("Layer names are required for layer_selection_add")
    
    layers = []
    for name in layer_names:
        layer = find_layer(viewer, name)
        if layer is None:
            raise CommandExecutionError(f"Layer '{name}' not found")
        layers.append(layer)
    
    for layer in layers:
        viewer.layers.selection.add(layer)
    
    layer_name_str = ", ".join(layer.name for layer in layers)
    return f"Added {len(layers)} layer(s) to selection: {layer_name_str}"


@register_handler("layer_selection_remove")
def handle_layer_selection_remove(command: CmdLayerSelectionRemove, viewer: "Viewer") -> str:
    """Remove layer(s) from the selection."""
    layer_names = command.layer_names
    if not layer_names:
        raise CommandExecutionError("Layer names are required for layer_selection_remove")
    
    layers = []
    for name in layer_names:
        layer = find_layer(viewer, name)
        if layer is None:
            raise CommandExecutionError(f"Layer '{name}' not found")
        layers.append(layer)
    
    for layer in layers:
        viewer.layers.selection.remove(layer)
    
    layer_name_str = ", ".join(layer.name for layer in layers)
    return f"Removed {len(layers)} layer(s) from selection: {layer_name_str}"


@register_handler("layer_selection_toggle")
def handle_layer_selection_toggle(command: CmdLayerSelectionToggle, viewer: "Viewer") -> str:
    """Toggle selection state of layer(s)."""
    layer_names = command.layer_names
    if not layer_names:
        raise CommandExecutionError("Layer names are required for layer_selection_toggle")
    
    layers = []
    for name in layer_names:
        layer = find_layer(viewer, name)
        if layer is None:
            raise CommandExecutionError(f"Layer '{name}' not found")
        layers.append(layer)
    
    results = []
    for layer in layers:
        was_selected = layer in viewer.layers.selection
        viewer.layers.selection.toggle(layer)
        is_selected = layer in viewer.layers.selection
        state = "selected" if is_selected else "deselected"
        results.append(f"'{layer.name}' {state}")
    
    return f"Toggled selection: {', '.join(results)}"


@register_handler("layer_selection_clear")
def handle_layer_selection_clear(command: CmdLayerSelectionClear, viewer: "Viewer") -> str:
    """Clear all selections."""
    count = len(viewer.layers.selection)
    viewer.layers.selection.clear()
    return f"Cleared {count} layer(s) from selection"


@register_handler("layer_selection_select_only")
def handle_layer_selection_select_only(command: CmdLayerSelectionSelectOnly, viewer: "Viewer") -> str:
    """Select only the specified layer(s), deselecting all others."""
    layer_names = command.layer_names
    if not layer_names:
        raise CommandExecutionError("Layer names are required for layer_selection_select_only")
    
    layers = []
    for name in layer_names:
        layer = find_layer(viewer, name)
        if layer is None:
            raise CommandExecutionError(f"Layer '{name}' not found")
        layers.append(layer)
    
    viewer.layers.selection.select_only(*layers)
    
    layer_name_str = ", ".join(layer.name for layer in layers)
    return f"Selected only {len(layers)} layer(s): {layer_name_str}"


@register_handler("layer_selection_set_active")
def handle_layer_selection_set_active(command: CmdLayerSelectionSetActive, viewer: "Viewer") -> str:
    """Set the active layer in the selection."""
    layer_name = command.layer_name
    layer = find_layer(viewer, layer_name)
    if layer is None:
        raise CommandExecutionError(f"Layer '{layer_name}' not found")
    
    # Add to selection if not already selected
    if layer not in viewer.layers.selection:
        viewer.layers.selection.add(layer)
    
    viewer.layers.selection.active = layer
    return f"Set active layer to '{layer.name}'"


@register_handler("layer_selection_discard")
def handle_layer_selection_discard(command: CmdLayerSelectionDiscard, viewer: "Viewer") -> str:
    """Discard layer(s) from the selection (does not raise error if not selected)."""
    layer_names = command.layer_names
    if not layer_names:
        raise CommandExecutionError("Layer names are required for layer_selection_discard")
    
    layers = []
    for name in layer_names:
        layer = find_layer(viewer, name)
        if layer is None:
            raise CommandExecutionError(f"Layer '{name}' not found")
        layers.append(layer)
    
    discarded = []
    for layer in layers:
        if layer in viewer.layers.selection:
            viewer.layers.selection.discard(layer)
            discarded.append(layer.name)
    
    if discarded:
        return f"Discarded {len(discarded)} layer(s) from selection: {', '.join(discarded)}"
    else:
        return "No layers were discarded (none were selected)"


@register_handler("layer_selection_visibility")
def handle_layer_selection_visibility(command: CmdLayerSelectionVisibility, viewer: "Viewer") -> str:
    """Set visibility of selected layers."""
    visible = command.visible
    
    selected_layers = list(viewer.layers.selection)
    if not selected_layers:
        return "No layers are currently selected"
    
    for layer in selected_layers:
        layer.visible = visible
    
    state = "shown" if visible else "hidden"
    layer_names = [layer.name for layer in selected_layers]
    return f"{state.capitalize()} {len(selected_layers)} selected layer(s): {', '.join(layer_names)}"


__all__ = [
    "handle_layer_selection_add",
    "handle_layer_selection_clear",
    "handle_layer_selection_discard",
    "handle_layer_selection_remove",
    "handle_layer_selection_select_only",
    "handle_layer_selection_set_active",
    "handle_layer_selection_toggle",
    "handle_layer_selection_visibility",
]

