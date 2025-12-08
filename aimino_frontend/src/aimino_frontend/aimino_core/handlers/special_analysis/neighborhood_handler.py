"""Neighborhood analysis command handlers."""

from typing import TYPE_CHECKING

from ...command_models import CmdComputeNeighborhood
from ...data_store import resolve_dataset_context
from ...errors import CommandExecutionError
from ...registry import register_handler
from .utils import compute_tumor_neighborhood_layers

if TYPE_CHECKING:
    from napari.viewer import Viewer


@register_handler("special_compute_neighborhood")
def handle_compute_neighborhood(command: CmdComputeNeighborhood, viewer: "Viewer") -> str:
    """Compute tumor neighborhood analysis."""
    try:
        ctx = resolve_dataset_context(
            command.dataset_id,
            command.image_path,
            command.h5ad_path,
            command.output_root,
        )
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise CommandExecutionError(str(exc)) from exc

    radius = float(command.radius) if command.radius is not None else 50.0
    
    try:
        result = compute_tumor_neighborhood_layers(
            viewer,
            str(ctx.image_path),
            str(ctx.h5ad_path),
            command.marker_col,
            str(ctx.output_root),
            radius=radius,
            force_recompute=command.force_recompute,
        )
        return result
    except Exception as e:
        raise CommandExecutionError(f"Failed to compute neighborhood: {e}") from e


__all__ = [
    "handle_compute_neighborhood",
]
