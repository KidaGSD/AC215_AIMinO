"""Density map computation and visualization utilities."""

import os
import numpy as np
from tifffile import imread
from scipy.ndimage import gaussian_filter
from skimage import measure
from skimage.measure import approximate_polygon
import napari
import logging

from .image_processing import load_image_for_mask
from .helpers import find_layer_simple as find_layer, get_output_paths, set_view_box

logger = logging.getLogger(__name__)


def density_to_boundary_paths(density, percentile=95.0, simplify_tol=4.0, min_vertices=20):
    """Convert density map to boundary paths using contour detection."""
    vals = density[density > 0]
    if vals.size == 0:
        return []
    level = np.quantile(vals, percentile / 100.0)
    raw = measure.find_contours(density, level=level)
    out = []
    for c in raw:
        if len(c) > min_vertices:
            c = approximate_polygon(c, simplify_tol)
            if len(c) > min_vertices:
                out.append(c)
    return out


def save_boundary_paths_npz(paths, out_path: str):
    """Save boundary paths to compressed NPZ file."""
    np.savez_compressed(out_path, **{f"p{i}": arr for i, arr in enumerate(paths)})


def load_boundary_paths_npz(path: str):
    """Load boundary paths from NPZ file."""
    if not os.path.exists(path):
        return []
    with np.load(path, allow_pickle=False) as z:
        keys = sorted([k for k in z.files if k.startswith("p")], key=lambda s: int(s[1:]))
        return [z[k] for k in keys]


def _ensure_density_layer(
    viewer: napari.Viewer,
    raw_image_path: str,
    obs,
    marker_col: str,
    output_root: str,
    sigma=200.0,
    colormap="magma",
    force_recompute=False,
    layer_name=None,
    visible=False,
):
    """Ensure density layer exists, computing if necessary."""
    img = load_image_for_mask(raw_image_path)
    H, W = img.shape
    _, _, _, dens_npy, _ = get_output_paths(raw_image_path, marker_col, output_root, sigma)

    if (not force_recompute) and os.path.exists(dens_npy):
        logger.info(f"[density] loading from {dens_npy}")
        density = np.load(dens_npy)
    else:
        logger.info("[density] computing density map")
        if marker_col not in obs.columns:
            raise ValueError(f"obs missing '{marker_col}'")
        s = obs[marker_col]
        if s.dtype == bool:
            pos_bool = s.to_numpy()
        else:
            pos_bool = (
                s.astype(str)
                .str.strip()
                .str.lower()
                .isin(["true", "t", "yes", "y", "1"])
                .to_numpy()
            )
        pos_cells = obs.loc[pos_bool]
        density = np.zeros((H, W), np.float32)
        if len(pos_cells) > 0:
            y = np.clip(pos_cells["Y_centroid"].astype(int), 0, H - 1)
            x = np.clip(pos_cells["X_centroid"].astype(int), 0, W - 1)
            density[y, x] = 1
            density = gaussian_filter(density, float(sigma))
            mx = float(density.max())
            if mx > 0:
                density /= mx
        np.save(dens_npy, density)
        logger.info(f"[density] saved to {dens_npy}")

    lname = layer_name or f"{marker_col}_density"
    existing = find_layer(viewer, lname)
    if existing is None:
        viewer.add_image(
            density,
            name=lname,
            colormap=colormap,
            opacity=0.6,
            blending="additive",
            contrast_limits=(0, 1),
            visible=visible,
        )
    else:
        existing.data = density
        existing.colormap = colormap
        existing.opacity = 0.6
        existing.contrast_limits = (0, 1)
        existing.blending = "additive"
        existing.visible = visible or existing.visible
    return density, lname


def zoom_to_dense_region(viewer: napari.Viewer, density_layer_name: str, zoom_margin=300):
    """Zoom viewer to the densest region in density layer."""
    ly = find_layer(viewer, density_layer_name)
    if ly is None:
        return f"[warn] Density layer '{density_layer_name}' not found."
    data = np.asarray(ly.data)
    if data.ndim != 2 or data.max() <= 0:
        return "[warn] density map empty."
    y, x = np.unravel_index(np.argmax(data), data.shape)
    H, W = data.shape
    x1, x2 = max(0, x - zoom_margin), min(W, x + zoom_margin)
    y1, y2 = max(0, y - zoom_margin), min(H, y + zoom_margin)
    set_view_box(viewer, x1, y1, x2, y2)
    return f"Zoomed to dense region near ({x},{y})."

