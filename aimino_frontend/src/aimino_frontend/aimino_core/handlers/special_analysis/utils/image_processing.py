"""Image loading and processing utilities."""

import os
import numpy as np
from tifffile import imread, TiffFile
import logging

logger = logging.getLogger(__name__)


def _to_2d_gray_safe(arr):
    """Convert array to 2D grayscale, handling various input shapes."""
    a = np.squeeze(arr)
    if a.ndim == 2:
        return a
    if a.ndim == 3 and a.shape[-1] in (3, 4):
        rgb = a[..., :3].astype(float)
        return (
            0.2989 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
        ).astype(a.dtype)
    return _to_2d_gray_safe(a[0])


def load_image_for_mask(path: str) -> np.ndarray:
    """Load image from TIFF file for mask processing."""
    logger.info(f"[image] loading image for mask from {path}")
    with TiffFile(path) as tf:
        arr = tf.series[0].asarray()
    img = _to_2d_gray_safe(arr)
    return img

