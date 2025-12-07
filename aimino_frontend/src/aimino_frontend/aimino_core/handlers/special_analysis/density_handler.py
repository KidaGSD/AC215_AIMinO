"""Density map command handlers."""

import os
from typing import TYPE_CHECKING
import anndata as ad

from ...command_models import CmdShowDensity, CmdUpdateDensity
from ...errors import CommandExecutionError
from ...registry import register_handler
from .utils import (
    _ensure_density_layer,
    density_to_boundary_paths,
    zoom_to_dense_region,
    load_boundary_paths_npz,
    save_boundary_paths_npz,
    get_output_paths,
)
from ..layer_management.layer_list import find_layer

if TYPE_CHECKING:
    from napari.viewer import Viewer


def _get_default_output_root() -> str:
    """Get default output root directory."""
    return os.path.expanduser("~/Desktop/AC215/Milestone2/processed")


@register_handler("special_show_density")
def handle_show_density(command: CmdShowDensity, viewer: "Viewer") -> str:
    """Show density layer for given marker."""
    lname = f"{command.marker_col}_density"
    ly = find_layer(viewer, lname)
    if not ly:
        raise CommandExecutionError(
            f"Density layer '{lname}' not found. Please load marker data first."
        )
    
    ly.visible = True
    viewer.layers.selection.active = ly
    msg = zoom_to_dense_region(viewer, lname)
    return f"Showing density layer '{lname}'. {msg}"


@register_handler("special_update_density")
def handle_update_density(command: CmdUpdateDensity, viewer: "Viewer") -> str:
    """Update density layer with new parameters."""
    output_root = command.output_root or _get_default_output_root()
    
    if not os.path.exists(command.image_path):
        raise CommandExecutionError(f"Image file not found: {command.image_path}")
    if not os.path.exists(command.h5ad_path):
        raise CommandExecutionError(f"H5AD file not found: {command.h5ad_path}")
    
    sigma = float(command.sigma) if command.sigma is not None else 200.0
    cmap = command.colormap or "magma"
    force = bool(command.force)
    
    try:
        adata = ad.read_h5ad(command.h5ad_path)
        obs = adata.obs.copy()
        
        density, lname = _ensure_density_layer(
            viewer,
            command.image_path,
            obs,
            command.marker_col,
            output_root,
            sigma=sigma,
            colormap=cmap,
            force_recompute=force,
            layer_name=f"{command.marker_col}_density",
            visible=True,
        )
        
        # Update boundary if needed
        bname = f"{command.marker_col}_density_boundary"
        b_layer = find_layer(viewer, bname)
        if b_layer is not None:
            viewer.layers.remove(b_layer)
        
        _, _, _, _, bnd_npz = get_output_paths(
            command.image_path, command.marker_col, output_root, sigma
        )
        paths = []
        if (not force) and os.path.exists(bnd_npz):
            paths = load_boundary_paths_npz(bnd_npz)
        else:
            paths = density_to_boundary_paths(
                density, percentile=95.0, simplify_tol=4.0, min_vertices=20
            )
            save_boundary_paths_npz(paths, bnd_npz)
        
        if paths:
            edge_colors = [[1.0, 1.0, 1.0, 1.0]] * len(paths)
            face_colors = [[0.0, 0.0, 0.0, 0.0]] * len(paths)
            viewer.add_shapes(
                paths,
                shape_type="path",
                edge_color=edge_colors,
                face_color=face_colors,
                edge_width=2.0,
                name=bname,
                blending="translucent",
                visible=True,
            )
        
        msg = zoom_to_dense_region(viewer, lname)
        return f"Density updated (sigma={sigma}, cmap={cmap}, force={force}). {msg}"
    except Exception as e:
        raise CommandExecutionError(f"Failed to update density: {e}") from e


__all__ = [
    "handle_show_density",
    "handle_update_density",
]

