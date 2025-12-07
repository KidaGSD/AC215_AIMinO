"""Neighborhood analysis command handlers."""

import os
from typing import TYPE_CHECKING

from ...command_models import CmdComputeNeighborhood
from ...errors import CommandExecutionError
from ...registry import register_handler
from .utils import compute_tumor_neighborhood_layers

if TYPE_CHECKING:
    from napari.viewer import Viewer


def _get_default_output_root() -> str:
    """Get default output root directory."""
    return os.path.expanduser("~/Desktop/AC215/Milestone2/processed")


@register_handler("special_compute_neighborhood")
def handle_compute_neighborhood(command: CmdComputeNeighborhood, viewer: "Viewer") -> str:
    """Compute tumor neighborhood analysis."""
    output_root = command.output_root or _get_default_output_root()
    
    if not os.path.exists(command.image_path):
        raise CommandExecutionError(f"Image file not found: {command.image_path}")
    if not os.path.exists(command.h5ad_path):
        raise CommandExecutionError(f"H5AD file not found: {command.h5ad_path}")
    
    radius = float(command.radius) if command.radius is not None else 50.0
    
    try:
        result = compute_tumor_neighborhood_layers(
            viewer,
            command.image_path,
            command.h5ad_path,
            command.marker_col,
            output_root,
            radius=radius,
            force_recompute=command.force_recompute,
        )
        return result
    except Exception as e:
        raise CommandExecutionError(f"Failed to compute neighborhood: {e}") from e


__all__ = [
    "handle_compute_neighborhood",
]

