"""Helper utilities for layer management, colors, and paths."""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from napari.viewer import Viewer


def _basename_noext(p: str) -> str:
    """Get basename without extension."""
    b = os.path.basename(p)
    return os.path.splitext(b)[0]


def _output_dir_for_image(raw_image_path: str, output_root: str) -> str:
    """Get output directory for image processing results."""
    sub = _basename_noext(raw_image_path)
    outdir = os.path.join(output_root, sub)
    os.makedirs(outdir, exist_ok=True)
    return outdir


def get_output_paths(raw_image_path: str, marker_col: str, output_root: str, sigma: float):
    """Get all output file paths for a given image and marker."""
    outdir = _output_dir_for_image(raw_image_path, output_root)
    base = _basename_noext(raw_image_path)
    sigma_tag = int(round(float(sigma)))
    labels_tif = os.path.join(outdir, f"{base}_rebuilt_labels.tif")
    mask_tif = os.path.join(outdir, f"{base}_{marker_col}_mask.tif")
    dens_npy = os.path.join(outdir, f"{base}_{marker_col}_density_sigma{sigma_tag}.npy")
    bnd_npz = os.path.join(outdir, f"{base}_{marker_col}_density_boundary_sigma{sigma_tag}_p95.npz")
    return outdir, labels_tif, mask_tif, dens_npy, bnd_npz


def find_layer_simple(viewer: "Viewer", name: str):
    """Find layer by name (case-insensitive, partial match). Simple version without error handling."""
    q = name.lower().strip()
    for ly in viewer.layers:
        if ly.name.lower() == q:
            return ly
    candidates = [ly for ly in viewer.layers if q in ly.name.lower()]
    if len(candidates) == 1:
        return candidates[0]
    return None


def list_layers(viewer: "Viewer"):
    """List all layer names."""
    return [l.name for l in viewer.layers]


def _parse_color(c, alpha: float | None = None):
    """Parse color string or tuple to RGBA tuple."""
    if isinstance(c, str):
        # let napari handle color names/colormap names when strings are used
        return c
    if hasattr(c, "__iter__"):
        vals = list(c)
        if len(vals) == 3:
            r, g, b = vals
            a = 1 if alpha is None else float(alpha)
        elif len(vals) == 4:
            r, g, b, a = vals
        else:
            raise ValueError("Color tuple must have length 3 or 4.")
        if max(r, g, b, a) > 1:
            r, g, b, a = r / 255, g / 255, b / 255, a / 255
        return (float(r), float(g), float(b), float(a))
    raise ValueError(f"Unrecognized color: {c!r}")


def _set_binary_labels_color(ly, rgba):
    """Set binary labels layer color map."""
    cmap = {0: (0, 0, 0, 0), 1: tuple(map(float, rgba))}
    try:
        ly.color = cmap
    except Exception:
        ly.colors = cmap
    try:
        ly.color_mode = "direct"
    except Exception:
        pass
    try:
        ly.refresh()
    except Exception:
        vis = ly.visible
        ly.visible = False
        ly.visible = vis


def _get_vispy_camera(viewer: "Viewer"):
    """Get vispy camera object from viewer."""
    qtv = getattr(viewer.window, "_qt_viewer", None) or getattr(
        viewer.window, "qt_viewer", None
    )
    if qtv is None:
        return None
    canvas = getattr(qtv, "canvas", None)
    if canvas is not None and hasattr(canvas, "scene"):
        return getattr(canvas.scene, "camera", None)
    view = getattr(qtv, "view", None)
    if view is not None and hasattr(view, "camera"):
        return view.camera
    return None


def set_view_box(viewer: "Viewer", x1, y1, x2, y2):
    """Set viewer view box to specified coordinates."""
    xlo, xhi = sorted([float(x1), float(x2)])
    ylo, yhi = sorted([float(y1), float(y2)])
    cam = _get_vispy_camera(viewer)
    if cam is not None and hasattr(cam, "set_range"):
        cam.set_range(x=(xlo, xhi), y=(ylo, yhi))
    viewer.camera.center = ((xlo + xhi) / 2, (ylo + yhi) / 2)
    return f"Zoomed to ({xlo:.1f},{ylo:.1f})–({xhi:.1f},{yhi:.1f})"

