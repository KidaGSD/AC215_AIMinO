"""Utility modules for special analysis: image processing, mask generation, and neighborhood analysis."""

from .image_processing import (
    load_image_for_mask,
    _to_2d_gray_safe,
)
from .mask_processing import (
    rebuild_labels_from_obs_safe,
    _ensure_labels,
    _ensure_mask,
    add_marker_mask_from_h5ad,
)
from .density_processing import (
    density_to_boundary_paths,
    save_boundary_paths_npz,
    load_boundary_paths_npz,
    _ensure_density_layer,
    zoom_to_dense_region,
)
from .neighborhood import (
    compute_tumor_neighborhood_layers,
)
from .helpers import (
    find_layer_simple,
    list_layers,
    _parse_color,
    _set_binary_labels_color,
    set_view_box,
    get_output_paths,
)

__all__ = [
    "load_image_for_mask",
    "_to_2d_gray_safe",
    "rebuild_labels_from_obs_safe",
    "_ensure_labels",
    "_ensure_mask",
    "add_marker_mask_from_h5ad",
    "density_to_boundary_paths",
    "save_boundary_paths_npz",
    "load_boundary_paths_npz",
    "_ensure_density_layer",
    "zoom_to_dense_region",
    "compute_tumor_neighborhood_layers",
    "find_layer_simple",
    "list_layers",
    "_parse_color",
    "_set_binary_labels_color",
    "set_view_box",
    "get_output_paths",
]

