"""LayerList command handlers for napari.components.LayerList methods and properties."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...command_models import (
    CmdLayerListAppend,
    CmdLayerListClear,
    CmdLayerListExtend,
    CmdLayerListGetExtent,
    CmdLayerListIndex,
    CmdLayerListInsert,
    CmdLayerListLinkLayers,
    CmdLayerListMove,
    CmdLayerListMoveMultiple,
    CmdLayerListPop,
    CmdLayerListRemove,
    CmdLayerListRemoveSelected,
    CmdLayerListReverse,
    CmdLayerListSave,
    CmdLayerListSelectAll,
    CmdLayerListSelectNext,
    CmdLayerListSelectPrevious,
    CmdLayerListToggleSelectedVisibility,
    CmdLayerListUnlinkLayers,
    CmdLayerVisibility,
    CmdListLayers,
)
from ...errors import CommandExecutionError
from ...registry import register_handler

if TYPE_CHECKING:
    from napari.viewer import Viewer
    from napari.layers import Layer
    from typing import Iterable, Optional


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


@register_handler("layer_list_append")
def handle_layer_list_append(command: CmdLayerListAppend, viewer: "Viewer") -> str:
    """Append a layer to the end of the layer list.
    
    Note: This method is typically used internally. For adding new layers,
    use the add_* methods (e.g., add_image, add_labels).
    """
    layer_name = command.layer_name
    layer = find_layer(viewer, layer_name)
    if layer is None:
        raise CommandExecutionError(f"Layer '{layer_name}' not found")
    
    # Check if layer is already in the list
    if layer in viewer.layers:
        # Move to end instead of appending duplicate
        current_index = viewer.layers.index(layer)
        viewer.layers.move(current_index, len(viewer.layers) - 1)
        return f"Moved layer '{layer.name}' to the end of the list"
    else:
        viewer.layers.append(layer)
        return f"Appended layer '{layer.name}' to the end of the list"


@register_handler("layer_list_clear")
def handle_layer_list_clear(command: CmdLayerListClear, viewer: "Viewer") -> str:
    """Clear all layers from the layer list."""
    count = len(viewer.layers)
    viewer.layers.clear()
    return f"Cleared {count} layer(s) from the list"


@register_handler("layer_list_extend")
def handle_layer_list_extend(command: CmdLayerListExtend, viewer: "Viewer") -> str:
    """Extend the layer list by appending layers from an iterable."""
    layer_names = command.layer_names
    if not layer_names:
        raise CommandExecutionError("Layer names are required for layer_list_extend")
    
    layers = []
    for name in layer_names:
        layer = find_layer(viewer, name)
        if layer is None:
            raise CommandExecutionError(f"Layer '{name}' not found")
        layers.append(layer)
    
    viewer.layers.extend(layers)
    return f"Extended list with {len(layers)} layer(s): {', '.join(layer.name for layer in layers)}"


@register_handler("layer_list_insert")
def handle_layer_list_insert(command: CmdLayerListInsert, viewer: "Viewer") -> str:
    """Insert a layer before the specified index.
    
    Note: This method is typically used internally. For adding new layers,
    use the add_* methods (e.g., add_image, add_labels).
    """
    index = command.index
    layer_name = command.layer_name
    layer = find_layer(viewer, layer_name)
    if layer is None:
        raise CommandExecutionError(f"Layer '{layer_name}' not found")
    
    if index < 0 or index > len(viewer.layers):
        raise CommandExecutionError(f"Index {index} is out of range (0-{len(viewer.layers)})")
    
    # Check if layer is already in the list
    if layer in viewer.layers:
        # Move to new position instead of inserting duplicate
        current_index = viewer.layers.index(layer)
        viewer.layers.move(current_index, index)
        return f"Moved layer '{layer.name}' to index {index}"
    else:
        viewer.layers.insert(index, layer)
        return f"Inserted layer '{layer.name}' at index {index}"


@register_handler("layer_list_remove")
def handle_layer_list_remove(command: CmdLayerListRemove, viewer: "Viewer") -> str:
    """Remove the first occurrence of a layer from the list."""
    layer_name = command.layer_name
    layer = find_layer(viewer, layer_name)
    if layer is None:
        raise CommandExecutionError(f"Layer '{layer_name}' not found")
    
    viewer.layers.remove(layer)
    return f"Removed layer '{layer.name}' from the list"


@register_handler("layer_list_pop")
def handle_layer_list_pop(command: CmdLayerListPop, viewer: "Viewer") -> str:
    """Remove and return the layer at the specified index (default last)."""
    index = command.index if command.index is not None else -1
    
    if len(viewer.layers) == 0:
        raise CommandExecutionError("Cannot pop from an empty layer list")
    
    if index < -len(viewer.layers) or index >= len(viewer.layers):
        raise CommandExecutionError(f"Index {index} is out of range")
    
    layer = viewer.layers.pop(index)
    return f"Popped layer '{layer.name}' from index {index}"


@register_handler("layer_list_move")
def handle_layer_list_move(command: CmdLayerListMove, viewer: "Viewer") -> str:
    """Move a layer from src_index to dest_index."""
    src_index = command.src_index
    dest_index = command.dest_index if command.dest_index is not None else 0
    
    if src_index < 0 or src_index >= len(viewer.layers):
        raise CommandExecutionError(f"Source index {src_index} is out of range")
    
    if dest_index < 0 or dest_index > len(viewer.layers):
        raise CommandExecutionError(f"Destination index {dest_index} is out of range")
    
    success = viewer.layers.move(src_index, dest_index)
    if success:
        layer_name = viewer.layers[dest_index].name if dest_index < len(viewer.layers) else "unknown"
        return f"Moved layer from index {src_index} to {dest_index}"
    else:
        raise CommandExecutionError(f"Failed to move layer from index {src_index} to {dest_index}")


@register_handler("layer_list_move_multiple")
def handle_layer_list_move_multiple(command: CmdLayerListMoveMultiple, viewer: "Viewer") -> str:
    """Move multiple layers to a single destination index."""
    sources = command.sources
    dest_index = command.dest_index if command.dest_index is not None else 0
    
    if not sources:
        raise CommandExecutionError("Sources are required for layer_list_move_multiple")
    
    if dest_index < 0 or dest_index > len(viewer.layers):
        raise CommandExecutionError(f"Destination index {dest_index} is out of range")
    
    # Convert sources to proper format (list of ints or slices)
    # Sources can be list of ints or list of lists (representing slices)
    processed_sources = []
    for source in sources:
        if isinstance(source, int):
            processed_sources.append(source)
        elif isinstance(source, list) and len(source) == 2:
            # Represent slice as [start, stop]
            processed_sources.append(slice(source[0], source[1]))
        elif isinstance(source, list) and len(source) == 3:
            # Represent slice as [start, stop, step]
            processed_sources.append(slice(source[0], source[1], source[2]))
        else:
            raise CommandExecutionError(f"Invalid source format: {source}")
    
    count = viewer.layers.move_multiple(processed_sources, dest_index)
    return f"Moved {count} layer(s) to index {dest_index}"


@register_handler("layer_list_remove_selected")
def handle_layer_list_remove_selected(command: CmdLayerListRemoveSelected, viewer: "Viewer") -> str:
    """Remove selected layers from the layer list."""
    count_before = len(viewer.layers)
    viewer.layers.remove_selected()
    count_after = len(viewer.layers)
    removed_count = count_before - count_after
    return f"Removed {removed_count} selected layer(s) from the list"


@register_handler("layer_list_reverse")
def handle_layer_list_reverse(command: CmdLayerListReverse, viewer: "Viewer") -> str:
    """Reverse the layer list in place."""
    viewer.layers.reverse()
    return "Reversed the layer list"


@register_handler("layer_list_save")
def handle_layer_list_save(command: CmdLayerListSave, viewer: "Viewer") -> str:
    """Save all or selected layers to a path."""
    path = command.path
    if not path:
        raise CommandExecutionError("Path is required for layer_list_save")
    
    selected = command.selected if command.selected is not None else False
    plugin = command.plugin
    
    file_paths = viewer.layers.save(path, selected=selected, plugin=plugin)
    return f"Saved layer(s) to {len(file_paths)} file(s): {', '.join(file_paths)}"


@register_handler("layer_list_link_layers")
def handle_layer_list_link_layers(command: CmdLayerListLinkLayers, viewer: "Viewer") -> str:
    """Link the specified layers."""
    layer_names = command.layer_names if command.layer_names is not None else None
    attributes = command.attributes if command.attributes is not None else []
    
    layers = None
    if layer_names:
        layers = []
        for name in layer_names:
            layer = find_layer(viewer, name)
            if layer is None:
                raise CommandExecutionError(f"Layer '{name}' not found")
            layers.append(layer)
    
    viewer.layers.link_layers(layers, attributes)
    if layer_names:
        return f"Linked {len(layers)} layer(s): {', '.join(layer.name for layer in layers)}"
    else:
        return "Linked selected layers"


@register_handler("layer_list_unlink_layers")
def handle_layer_list_unlink_layers(command: CmdLayerListUnlinkLayers, viewer: "Viewer") -> str:
    """Unlink previously linked layers."""
    layer_names = command.layer_names if command.layer_names is not None else None
    attributes = command.attributes if command.attributes is not None else []
    
    layers = None
    if layer_names:
        layers = []
        for name in layer_names:
            layer = find_layer(viewer, name)
            if layer is None:
                raise CommandExecutionError(f"Layer '{name}' not found")
            layers.append(layer)
    
    viewer.layers.unlink_layers(layers, attributes)
    if layer_names:
        return f"Unlinked {len(layers)} layer(s): {', '.join(layer.name for layer in layers)}"
    else:
        return "Unlinked selected layers"


@register_handler("layer_list_select_all")
def handle_layer_list_select_all(command: CmdLayerListSelectAll, viewer: "Viewer") -> str:
    """Select all layers in the list."""
    viewer.layers.select_all()
    return f"Selected all {len(viewer.layers)} layer(s)"


@register_handler("layer_list_select_next")
def handle_layer_list_select_next(command: CmdLayerListSelectNext, viewer: "Viewer") -> str:
    """Select the next layer in the list."""
    step = command.step if command.step is not None else 1
    shift = command.shift if command.shift is not None else False
    
    viewer.layers.select_next(step=step, shift=shift)
    if viewer.layers.selection.active:
        return f"Selected next layer: '{viewer.layers.selection.active.name}'"
    else:
        return "Selected next layer (no active selection)"


@register_handler("layer_list_select_previous")
def handle_layer_list_select_previous(command: CmdLayerListSelectPrevious, viewer: "Viewer") -> str:
    """Select the previous layer in the list."""
    shift = command.shift if command.shift is not None else False
    
    viewer.layers.select_previous(shift=shift)
    if viewer.layers.selection.active:
        return f"Selected previous layer: '{viewer.layers.selection.active.name}'"
    else:
        return "Selected previous layer (no active selection)"


@register_handler("layer_list_toggle_selected_visibility")
def handle_layer_list_toggle_selected_visibility(
    command: CmdLayerListToggleSelectedVisibility, viewer: "Viewer"
) -> str:
    """Toggle visibility of selected layers."""
    viewer.layers.toggle_selected_visibility()
    selected_count = len(viewer.layers.selection)
    return f"Toggled visibility of {selected_count} selected layer(s)"


@register_handler("layer_list_get_extent")
def handle_layer_list_get_extent(command: CmdLayerListGetExtent, viewer: "Viewer") -> str:
    """Get the extent for specified layers."""
    layer_names = command.layer_names if command.layer_names is not None else None
    
    if layer_names:
        layers = []
        for name in layer_names:
            layer = find_layer(viewer, name)
            if layer is None:
                raise CommandExecutionError(f"Layer '{name}' not found")
            layers.append(layer)
        extent = viewer.layers.get_extent(layers)
    else:
        extent = viewer.layers.extent
    
    return f"Extent: {extent}"


@register_handler("layer_list_index")
def handle_layer_list_index(command: CmdLayerListIndex, viewer: "Viewer") -> str:
    """Get the index of a layer in the list."""
    layer_name = command.layer_name
    layer = find_layer(viewer, layer_name)
    if layer is None:
        raise CommandExecutionError(f"Layer '{layer_name}' not found")
    
    start = command.start if command.start is not None else 0
    stop = command.stop
    
    index = viewer.layers.index(layer, start=start, stop=stop)
    return f"Layer '{layer.name}' is at index {index}"


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


@register_handler("list_layers")
def handle_list_layers(command: CmdListLayers, viewer: "Viewer") -> str:  # noqa: ARG001
    return "Layers: " + (", ".join(list_layers(viewer)) or "(none)")


__all__ = [
    "handle_layer_list_append",
    "handle_layer_list_clear",
    "handle_layer_list_extend",
    "handle_layer_list_get_extent",
    "handle_layer_list_index",
    "handle_layer_list_insert",
    "handle_layer_list_link_layers",
    "handle_layer_list_move",
    "handle_layer_list_move_multiple",
    "handle_layer_list_pop",
    "handle_layer_list_remove",
    "handle_layer_list_remove_selected",
    "handle_layer_list_reverse",
    "handle_layer_list_save",
    "handle_layer_list_select_all",
    "handle_layer_list_select_next",
    "handle_layer_list_select_previous",
    "handle_layer_list_toggle_selected_visibility",
    "handle_layer_list_unlink_layers",
    "handle_layer_visibility",
    "handle_list_layers",
    "find_layer",
    "iter_layers",
    "list_layers",
]

