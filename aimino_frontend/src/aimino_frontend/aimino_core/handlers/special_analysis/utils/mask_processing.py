"""Mask generation and processing utilities."""

import os
import numpy as np
from tifffile import imread, imwrite, TiffFile
import anndata as ad
import napari
import logging

from .image_processing import load_image_for_mask
from .helpers import find_layer_simple as find_layer, list_layers, _parse_color, get_output_paths
from .density_processing import (
    _ensure_density_layer,
    density_to_boundary_paths,
    load_boundary_paths_npz,
    save_boundary_paths_npz,
)

logger = logging.getLogger(__name__)

# Configuration constants
ELLIPSE_VERTS = 36
ORIENTATION_IS_DEGREES = False


def rebuild_labels_from_obs_safe(obs, shape, ellipse_verts=ELLIPSE_VERTS, orientation_is_degrees=ORIENTATION_IS_DEGREES):
    """Rebuild label image from observation dataframe with ellipse shapes."""
    from skimage.draw import polygon
    
    H, W = shape
    labels = np.zeros((H, W), np.int32)
    cx = obs["X_centroid"]
    cy = obs["Y_centroid"]
    maj = obs["MajorAxisLength"]
    minr = obs["MinorAxisLength"]
    theta = obs["Orientation"]
    a = np.maximum(maj / 2, 1)
    b = np.maximum(minr / 2, 1)
    if orientation_is_degrees:
        theta = np.deg2rad(theta)
    angles = np.linspace(0, 2 * np.pi, ellipse_verts, endpoint=False)
    cosA, sinA = np.cos(angles), np.sin(angles)
    for x, y, aa, bb, th, cid in zip(cx, cy, a, b, theta, obs["CellID"]):
        ex = x + aa * cosA * np.cos(th) - bb * sinA * np.sin(th)
        ey = y + aa * cosA * np.sin(th) + bb * sinA * np.cos(th)
        rr, cc = polygon(ey, ex, shape=(H, W))
        bg = labels[rr, cc] == 0
        labels[rr[bg], cc[bg]] = int(cid)
    return labels


def _ensure_labels(raw_image_path: str, obs, output_root: str, force_recompute: bool = False):
    """Ensure labels image exists, rebuilding if necessary."""
    img = load_image_for_mask(raw_image_path)
    H, W = img.shape
    _, labels_tif, _, _, _ = get_output_paths(raw_image_path, "", output_root, 0)
    if (not force_recompute) and os.path.exists(labels_tif):
        labels = imread(labels_tif)
        if labels.shape == (H, W):
            logger.info(f"[labels] loaded from {labels_tif}")
            return labels
    logger.info("[labels] rebuilding from obs")
    labels = rebuild_labels_from_obs_safe(obs, (H, W))
    try:
        imwrite(labels_tif, labels, dtype=np.int32)
        logger.info(f"[labels] saved to {labels_tif}")
    except Exception as e:
        logger.warning(f"[labels] could not save labels_tif: {e}")
    return labels


def _ensure_mask(
    raw_image_path: str,
    obs,
    marker_col: str,
    output_root: str,
    force_recompute: bool = False,
):
    """Ensure mask exists for given marker column, building if necessary."""
    logger.info(f"[mask] _ensure_mask for {marker_col} (force={force_recompute})")
    img = load_image_for_mask(raw_image_path)
    H, W = img.shape

    _, labels_tif, mask_tif, _, _ = get_output_paths(raw_image_path, marker_col, output_root, 0)

    if (not force_recompute) and os.path.exists(labels_tif):
        labels = imread(labels_tif)
    else:
        labels = _ensure_labels(raw_image_path, obs, output_root, force_recompute=force_recompute)

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
    pos_ids = np.unique(obs.loc[pos_bool, "CellID"].astype(int))

    if (not force_recompute) and os.path.exists(mask_tif):
        m = imread(mask_tif).astype(np.uint8)
        if m.shape == (H, W):
            logger.info(f"[mask] loaded mask from {mask_tif}")
            return m

    logger.info("[mask] building new mask")
    m = np.isin(labels, pos_ids).astype(np.uint8)
    try:
        imwrite(mask_tif, m, dtype=np.uint8)
        logger.info(f"[mask] saved to {mask_tif}")
    except Exception as e:
        logger.warning(f"[mask] could not save mask: {e}")
    return m


def add_marker_mask_from_h5ad(
    viewer: napari.Viewer,
    raw_image_path: str,
    h5ad_path: str,
    marker_col: str,
    output_root: str,
    force_recompute: bool = False,
):
    """Add marker mask layer from h5ad file to napari viewer."""
    logger.info(f"[main] add_marker_mask_from_h5ad → outputs in {output_root}")

    img = load_image_for_mask(raw_image_path)
    base_name = os.path.basename(raw_image_path)
    if find_layer(viewer, base_name) is None:
        viewer.add_image(img, name=base_name, visible=True)
        logger.info(f"[image] added base image layer '{base_name}'")

    logger.info(f"[H5AD] reading {h5ad_path}")
    adata = ad.read_h5ad(h5ad_path)
    obs = adata.obs.copy()

    # Main marker mask
    pos_mask = _ensure_mask(
        raw_image_path, obs, marker_col, output_root, force_recompute=force_recompute
    )
    fg_rgba = _parse_color((1, 0, 0, 1))
    bg_rgba = (0, 0, 0, 0.0)
    color_map = {0: bg_rgba, 1: fg_rgba}
    lname = f"{marker_col}_mask"
    ly = find_layer(viewer, lname)
    if ly is None:
        ly = viewer.add_labels(
            pos_mask, name=lname, opacity=1.0, blending="translucent", visible=False
        )
    else:
        ly.data = pos_mask
        ly.visible = False
    try:
        ly.color = color_map
    except Exception:
        ly.colors = color_map
    try:
        ly.color_mode = "direct"
    except Exception:
        pass

    # Density layer + boundary
    density, dname = _ensure_density_layer(
        viewer,
        raw_image_path,
        obs,
        marker_col,
        output_root,
        sigma=200.0,
        colormap="magma",
        force_recompute=force_recompute,
        layer_name=f"{marker_col}_density",
        visible=False,
    )
    _, _, _, _, bnd_npz = get_output_paths(raw_image_path, marker_col, output_root, 200.0)
    paths = []
    if (not force_recompute) and os.path.exists(bnd_npz):
        paths = load_boundary_paths_npz(bnd_npz)
    else:
        paths = density_to_boundary_paths(
            density, percentile=95.0, simplify_tol=4.0, min_vertices=20
        )
        save_boundary_paths_npz(paths, bnd_npz)
    if paths:
        edge_rgba = _parse_color((1, 1, 1, 1))
        edge_colors = np.tile(np.array(edge_rgba, dtype=float), (len(paths), 1))
        face_colors = np.tile(np.array([0, 0, 0, 0], dtype=float), (len(paths), 1))
        bname = f"{marker_col}_density_boundary"
        b_layer = find_layer(viewer, bname)
        if b_layer is not None:
            viewer.layers.remove(b_layer)
        viewer.add_shapes(
            paths,
            shape_type="path",
            edge_color=edge_colors,
            face_color=face_colors,
            edge_width=2.0,
            name=bname,
            blending="translucent",
            visible=False,
        )

    # Extra masks for CD45, CD20, CD3E
    extra_markers = {
        "CD45_positive": (0, 1, 0, 0.9),   # immune, green
        "CD20_positive": (1, 0.5, 0, 0.9), # B cells, orange
        "CD3E_positive": (1, 0, 1, 0.9),   # T cells, magenta
    }
    for col, rgba in extra_markers.items():
        if col not in obs.columns:
            logger.warning(f"[extra mask] column {col} not in obs; skipping.")
            continue
        m = _ensure_mask(raw_image_path, obs, col, output_root, force_recompute=force_recompute)
        lname = f"{col}_mask"
        ly = find_layer(viewer, lname)
        if ly is None:
            ly = viewer.add_labels(
                m, name=lname, opacity=1.0, blending="translucent", visible=False
            )
        else:
            ly.data = m
            ly.visible = False
        fg = _parse_color(rgba)
        cmap = {0: (0, 0, 0, 0), 1: fg}
        try:
            ly.color = cmap
        except Exception:
            ly.colors = cmap
        try:
            ly.color_mode = "direct"
        except Exception:
            pass

    logger.info("[main] layers now: " + ", ".join(list_layers(viewer)))
    return

