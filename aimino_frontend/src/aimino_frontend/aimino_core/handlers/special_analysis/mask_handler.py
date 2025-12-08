"""Mask-related command handlers."""

from typing import TYPE_CHECKING

from ...command_models import CmdLoadMarkerData, CmdShowMask
from ...data_store import resolve_dataset_context
from ...errors import CommandExecutionError
from ...registry import register_handler
from .utils import (
    add_marker_mask_from_h5ad,
    _set_binary_labels_color,
    _parse_color,
)
from ..layer_management.layer_list import find_layer

if TYPE_CHECKING:
    from napari.viewer import Viewer


@register_handler("special_load_marker_data")
def handle_load_marker_data(command: CmdLoadMarkerData, viewer: "Viewer") -> str:
    """Load marker data from TIFF and h5ad files."""
    try:
        ctx = resolve_dataset_context(
            command.dataset_id,
            command.image_path,
            command.h5ad_path,
            command.output_root,
        )
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise CommandExecutionError(str(exc)) from exc

    try:
        add_marker_mask_from_h5ad(
            viewer,
            str(ctx.image_path),
            str(ctx.h5ad_path),
            command.marker_col,
            str(ctx.output_root),
            force_recompute=command.force_recompute,
        )
        return f"Loaded marker data for {command.marker_col} from {ctx.h5ad_path.name}"
    except Exception as e:
        raise CommandExecutionError(f"Failed to load marker data: {e}") from e


@register_handler("special_show_mask")
def handle_show_mask(command: CmdShowMask, viewer: "Viewer") -> str:
    """Show mask layer for given marker."""
    lname = f"{command.marker_col}_mask"
    ly = find_layer(viewer, lname)
    if not ly:
        raise CommandExecutionError(
            f"Mask layer '{lname}' not found. Please load marker data first."
        )
    
    ly.visible = True
    viewer.layers.selection.active = ly
    
    if command.color:
        try:
            rgba = _parse_color(command.color)
            _set_binary_labels_color(ly, rgba)
            return f"Showing mask '{lname}' with color {command.color}."
        except Exception as e:
            return f"Showing mask '{lname}'. [Color error: {e}]"
    
    return f"Showing mask '{lname}'."


__all__ = [
    "handle_load_marker_data",
    "handle_show_mask",
]
