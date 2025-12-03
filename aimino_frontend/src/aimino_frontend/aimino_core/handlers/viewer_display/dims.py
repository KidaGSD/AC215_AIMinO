"""Dims command handlers for napari.components.Dims methods and properties."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...command_models import (
    CmdDimsAxisLabels,
    CmdDimsNdisplay,
    CmdDimsOrder,
    CmdDimsPoint,
    CmdDimsRange,
    CmdDimsReset,
    CmdDimsRoll,
    CmdDimsSetAxisLabel,
    CmdDimsSetPoint,
    CmdDimsSetRange,
    CmdDimsTranspose,
    CmdDimsUpdate,
)
from ...errors import CommandExecutionError
from ...registry import register_handler

if TYPE_CHECKING:
    from napari.viewer import Viewer


@register_handler("dims_point")
def handle_dims_point(command: CmdDimsPoint, viewer: "Viewer") -> str:
    """Set the point (position) for dimensions in world coordinates."""
    axis = command.axis
    value = command.value
    
    if isinstance(axis, int):
        if isinstance(value, (int, float)):
            viewer.dims.set_point(axis, float(value))
            return f"Set point for axis {axis} to {float(value):.2f}"
        else:
            raise CommandExecutionError(f"Value must be a single number for single axis, got {type(value)}")
    elif isinstance(axis, list):
        if isinstance(value, list):
            if len(axis) != len(value):
                raise CommandExecutionError(f"Number of axes ({len(axis)}) must match number of values ({len(value)})")
            viewer.dims.set_point(axis, [float(v) for v in value])
            formatted_values = [f"{float(v):.2f}" for v in value]
            return f"Set points for axes {axis} to {formatted_values}"
        else:
            raise CommandExecutionError(f"Value must be a list for multiple axes, got {type(value)}")
    else:
        raise CommandExecutionError(f"Axis must be an int or list of ints, got {type(axis)}")


@register_handler("dims_range")
def handle_dims_range(command: CmdDimsRange, viewer: "Viewer") -> str:
    """Set the range (min, max, step) for dimensions."""
    axis = command.axis
    _range = command.range
    
    if isinstance(axis, int):
        if isinstance(_range, list) and len(_range) == 3:
            viewer.dims.set_range(axis, (float(_range[0]), float(_range[1]), float(_range[2])))
            return f"Set range for axis {axis} to (min={float(_range[0]):.2f}, max={float(_range[1]):.2f}, step={float(_range[2]):.2f})"
        else:
            raise CommandExecutionError(f"Range must be a list of 3 values [min, max, step], got {_range}")
    elif isinstance(axis, list):
        if isinstance(_range, list):
            # Multiple axes with multiple ranges
            if len(axis) != len(_range):
                raise CommandExecutionError(f"Number of axes ({len(axis)}) must match number of ranges ({len(_range)})")
            ranges = []
            for r in _range:
                if isinstance(r, list) and len(r) == 3:
                    ranges.append((float(r[0]), float(r[1]), float(r[2])))
                else:
                    raise CommandExecutionError(f"Each range must be a list of 3 values [min, max, step], got {r}")
            viewer.dims.set_range(axis, ranges)
            return f"Set ranges for axes {axis}"
        else:
            raise CommandExecutionError(f"Range must be a list for multiple axes, got {type(_range)}")
    else:
        raise CommandExecutionError(f"Axis must be an int or list of ints, got {type(axis)}")


@register_handler("dims_set_axis_label")
def handle_dims_set_axis_label(command: CmdDimsSetAxisLabel, viewer: "Viewer") -> str:
    """Set axis labels for dimensions."""
    axis = command.axis
    label = command.label
    
    if isinstance(axis, int):
        if isinstance(label, str):
            viewer.dims.set_axis_label(axis, label)
            return f"Set label for axis {axis} to '{label}'"
        else:
            raise CommandExecutionError(f"Label must be a string for single axis, got {type(label)}")
    elif isinstance(axis, list):
        if isinstance(label, list):
            if len(axis) != len(label):
                raise CommandExecutionError(f"Number of axes ({len(axis)}) must match number of labels ({len(label)})")
            viewer.dims.set_axis_label(axis, label)
            return f"Set labels for axes {axis} to {label}"
        else:
            raise CommandExecutionError(f"Label must be a list for multiple axes, got {type(label)}")
    else:
        raise CommandExecutionError(f"Axis must be an int or list of ints, got {type(axis)}")


@register_handler("dims_set_point")
def handle_dims_set_point(command: CmdDimsSetPoint, viewer: "Viewer") -> str:
    """Set point to slice dimension in world coordinates (alias for dims_point)."""
    return handle_dims_point(command, viewer)


@register_handler("dims_set_range")
def handle_dims_set_range(command: CmdDimsSetRange, viewer: "Viewer") -> str:
    """Set ranges for dimensions (alias for dims_range)."""
    return handle_dims_range(command, viewer)


@register_handler("dims_order")
def handle_dims_order(command: CmdDimsOrder, viewer: "Viewer") -> str:
    """Set the order of dimensions for display."""
    order = command.order
    if not isinstance(order, list):
        raise CommandExecutionError(f"Order must be a list of integers, got {type(order)}")
    
    viewer.dims.order = tuple(int(o) for o in order)
    return f"Set dimension order to {viewer.dims.order}"


@register_handler("dims_axis_labels")
def handle_dims_axis_labels(command: CmdDimsAxisLabels, viewer: "Viewer") -> str:
    """Set axis labels for all dimensions."""
    labels = command.labels
    if not isinstance(labels, list):
        raise CommandExecutionError(f"Labels must be a list of strings, got {type(labels)}")
    
    if len(labels) != viewer.dims.ndim:
        raise CommandExecutionError(
            f"Number of labels ({len(labels)}) must match number of dimensions ({viewer.dims.ndim})"
        )
    
    viewer.dims.axis_labels = tuple(str(l) for l in labels)
    return f"Set axis labels to {viewer.dims.axis_labels}"


@register_handler("dims_ndisplay")
def handle_dims_ndisplay(command: CmdDimsNdisplay, viewer: "Viewer") -> str:
    """Set the number of displayed dimensions."""
    ndisplay = command.ndisplay
    if ndisplay not in (2, 3):
        raise CommandExecutionError(f"ndisplay must be 2 or 3, got {ndisplay}")
    
    viewer.dims.ndisplay = ndisplay
    return f"Set number of displayed dimensions to {ndisplay}"


@register_handler("dims_reset")
def handle_dims_reset(command: CmdDimsReset, viewer: "Viewer") -> str:
    """Reset dims values to initial states."""
    viewer.dims.reset()
    return "Dims reset to initial states"


@register_handler("dims_roll")
def handle_dims_roll(command: CmdDimsRoll, viewer: "Viewer") -> str:
    """Roll order of dimensions for display."""
    viewer.dims.roll()
    return f"Rolled dimension order to {viewer.dims.order}"


@register_handler("dims_transpose")
def handle_dims_transpose(command: CmdDimsTranspose, viewer: "Viewer") -> str:
    """Transpose displayed dimensions (swaps the last two displayed dimensions)."""
    viewer.dims.transpose()
    return f"Transposed displayed dimensions. New order: {viewer.dims.order}"


@register_handler("dims_update")
def handle_dims_update(command: CmdDimsUpdate, viewer: "Viewer") -> str:
    """Update dims properties in place."""
    if not command.values:
        raise CommandExecutionError("Values are required for dims_update")
    
    viewer.dims.update(command.values)
    return f"Updated dims with values: {command.values}"


__all__ = [
    "handle_dims_axis_labels",
    "handle_dims_ndisplay",
    "handle_dims_order",
    "handle_dims_point",
    "handle_dims_range",
    "handle_dims_reset",
    "handle_dims_roll",
    "handle_dims_set_axis_label",
    "handle_dims_set_point",
    "handle_dims_set_range",
    "handle_dims_transpose",
    "handle_dims_update",
]

