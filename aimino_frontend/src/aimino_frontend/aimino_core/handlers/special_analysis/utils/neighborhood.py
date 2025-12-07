"""Tumor neighborhood analysis utilities."""

import os
import numpy as np
from scipy.spatial import cKDTree, Delaunay
import anndata as ad
import napari
import logging

from .helpers import find_layer_simple as find_layer

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_NEIGH_RADIUS = 50.0
NEIGH_POINT_SIZE = 40  # tumor neighbors
GLOBAL_POINT_SIZE = 20  # other neighbor classes

# Explicit RGBA colors for neighborhood layers (0–1 floats)
NEIGH_COLORS = {
    "tumor": (1.0, 0.0, 0.0, 1.0),   # red
    "immune": (0.0, 1.0, 0.0, 1.0),   # green
    "B": (1.0, 0.8, 0.0, 1.0),   # gold-ish
    "T": (0.0, 1.0, 1.0, 1.0),   # cyan
    "other": (0.5, 0.5, 0.5, 1.0),   # grey
}


def compute_tumor_neighborhood_layers(
    viewer: napari.Viewer,
    raw_image_path: str,
    h5ad_path: str,
    marker_col: str,
    output_root: str,
    radius: float = DEFAULT_NEIGH_RADIUS,
    force_recompute: bool = False,
):
    """
    Compute tumor neighborhood within a given radius and overlay as napari layers.

    Uses (y, x) order for coordinates to match napari's image indexing.
    """
    logger.info(
        f"[neigh] compute_tumor_neighborhood_layers radius={radius}, force={force_recompute}"
    )

    from .helpers import _basename_noext, _output_dir_for_image

    outdir = _output_dir_for_image(raw_image_path, output_root)
    base = _basename_noext(raw_image_path)
    tag = int(round(radius))
    cache_path = os.path.join(outdir, f"{base}_{marker_col}_neighborhood_yx_r{tag}.npz")

    if os.path.exists(cache_path) and not force_recompute:
        logger.info(f"[neigh] loading cached neighborhood from {cache_path}")
        data = np.load(cache_path, allow_pickle=True)
        all_points = data["all_points"]
        mask_tumor = data["mask_tumor"]
        mask_immune = data["mask_immune"]
        mask_B = data["mask_B"]
        mask_T = data["mask_T"]
        mask_other = data["mask_other"]
        segments = data["segments"]
    else:
        logger.info(f"[neigh] reading h5ad: {h5ad_path}")
        adata = ad.read_h5ad(h5ad_path)
        obs = adata.obs.copy()

        # coordinates as (y, x) to match napari image
        x_all = obs["X_centroid"].to_numpy()
        y_all = obs["Y_centroid"].to_numpy()
        all_points = np.column_stack([y_all, x_all]).astype(float)

        tumor_raw = obs[marker_col]
        if tumor_raw.dtype == bool:
            tumor_mask = tumor_raw.to_numpy()
        else:
            tumor_mask = (
                tumor_raw.astype(str)
                .str.strip()
                .str.lower()
                .isin(["true", "t", "yes", "y", "1"])
                .to_numpy()
            )

        tumor_indices = np.where(tumor_mask)[0]
        tumor_points = all_points[tumor_mask]
        n_tumor = len(tumor_points)
        logger.info(f"[neigh] tumor cells = {n_tumor}")

        if n_tumor == 0:
            logger.warning("[neigh] no tumor cells found; nothing to compute.")
            return "No tumor cells found."

        tree_all = cKDTree(all_points)
        logger.info(f"[neigh] querying neighbors within radius={radius}")
        neighbor_indices = tree_all.query_ball_point(tumor_points, r=float(radius))
        flat_neighbors = set()
        for inds in neighbor_indices:
            flat_neighbors.update(inds)
        flat_neighbors -= set(tumor_indices)
        flat_neighbors = sorted(flat_neighbors)
        logger.info(f"[neigh] neighbor cells (non-tumor) = {len(flat_neighbors)}")

        n = len(all_points)
        mask_tumor = np.zeros(n, dtype=bool)
        mask_tumor[tumor_indices] = True

        mask_neighbor = np.zeros(n, dtype=bool)
        if flat_neighbors:
            mask_neighbor[flat_neighbors] = True

        def col_bool(colname: str) -> np.ndarray:
            if colname not in obs.columns:
                return np.zeros(n, dtype=bool)
            s = obs[colname]
            if s.dtype == bool:
                return s.to_numpy()
            return (
                s.astype(str)
                .str.strip()
                .str.lower()
                .isin(["true", "t", "yes", "y", "1"])
                .to_numpy()
            )

        mask_cd45 = col_bool("CD45_positive")
        mask_cd20 = col_bool("CD20_positive")
        mask_cd3e = col_bool("CD3E_positive")

        mask_immune = mask_neighbor & mask_cd45
        mask_B = mask_neighbor & mask_cd20
        mask_T = mask_neighbor & mask_cd3e
        mask_other = ~(mask_tumor | mask_neighbor)

        n_neigh = mask_neighbor.sum()
        n_immune = mask_immune.sum()
        n_B = mask_B.sum()
        n_T = mask_T.sum()
        if n_neigh > 0:
            logger.info(
                f"[neigh] neighbors: {n_neigh}, "
                f"immune: {n_immune} ({n_immune/n_neigh:.1%}), "
                f"B: {n_B} ({n_B/n_neigh:.1%}), "
                f"T: {n_T} ({n_T/n_neigh:.1%})"
            )
        else:
            logger.info("[neigh] neighbors: 0")

        logger.info("[neigh] computing Delaunay triangulation on tumor points")
        if n_tumor >= 3:
            tri = Delaunay(tumor_points)
            Ttri = tri.simplices
            edges = np.vstack(
                [Ttri[:, [0, 1]], Ttri[:, [1, 2]], Ttri[:, [2, 0]]]
            )
            edges = np.sort(edges, axis=1)
            edges = np.unique(edges, axis=0)
            p0 = tumor_points[edges[:, 0]]
            p1 = tumor_points[edges[:, 1]]
            segments = np.stack([p0, p1], axis=1)
            logger.info(f"[neigh] Delaunay edges kept: {segments.shape[0]}")
        else:
            logger.warning("[neigh] not enough tumor points for triangulation.")
            segments = np.empty((0, 2, 2), dtype=float)

        np.savez_compressed(
            cache_path,
            all_points=all_points,
            mask_tumor=mask_tumor,
            mask_immune=mask_immune,
            mask_B=mask_B,
            mask_T=mask_T,
            mask_other=mask_other,
            segments=segments,
        )
        logger.info(f"[neigh] cached neighborhood to {cache_path}")

    # --- Add / update napari layers ---------------------------------

    def add_points_layer(name: str, mask: np.ndarray, rgba, size: float):
        """Add or update a Points layer with a single RGBA color."""
        coords = all_points[mask]
        if coords.size == 0:
            logger.info(f"[neigh] {name}: no points to draw.")
            return

        ly = find_layer(viewer, name)
        if ly is None:
            viewer.add_points(
                coords,
                size=size,
                face_color=rgba,
                name=name,
                blending="translucent",
                opacity=rgba[3],
            )
        else:
            ly.data = coords
            ly.size = size
            ly.face_color = rgba
            ly.opacity = rgba[3]

    add_points_layer(
        f"{marker_col}_neigh_tumor",
        mask_tumor,
        NEIGH_COLORS["tumor"],
        NEIGH_POINT_SIZE,
    )
    add_points_layer(
        f"{marker_col}_neigh_immune",
        mask_immune,
        NEIGH_COLORS["immune"],
        GLOBAL_POINT_SIZE,
    )
    add_points_layer(
        f"{marker_col}_neigh_B",
        mask_B,
        NEIGH_COLORS["B"],
        GLOBAL_POINT_SIZE,
    )
    add_points_layer(
        f"{marker_col}_neigh_T",
        mask_T,
        NEIGH_COLORS["T"],
        GLOBAL_POINT_SIZE,
    )
    add_points_layer(
        f"{marker_col}_neigh_other",
        mask_other,
        NEIGH_COLORS["other"],
        GLOBAL_POINT_SIZE,
    )

    name_edges = f"{marker_col}_neigh_edges"
    ly_edges = find_layer(viewer, name_edges)
    if segments.size > 0:
        if ly_edges is not None:
            viewer.layers.remove(ly_edges)
        viewer.add_shapes(
            segments,
            shape_type="path",
            edge_color="white",
            face_color=(0, 0, 0, 0),
            edge_width=0.4,
            name=name_edges,
            blending="translucent",
            visible=True,
        )

    logger.info("[neigh] neighborhood layers added/updated in napari.")
    return "Tumor neighborhood computed and layers updated."

