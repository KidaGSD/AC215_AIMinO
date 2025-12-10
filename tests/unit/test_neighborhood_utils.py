import os
import numpy as np
import pandas as pd
import pytest
import anndata as ad
from pathlib import Path


def _write_h5ad(path: Path, obs: pd.DataFrame) -> Path:
    ad.AnnData(np.zeros((len(obs), 1), dtype=np.float32), obs=obs).write_h5ad(path)
    return path


def _prep_env(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ["NAPARI_CONFIG_DIR"] = str(tmp_path / "napari_config")
    os.environ["NAPARI_CACHE_DIR"] = str(tmp_path / "napari_cache")
    os.environ["XDG_CACHE_HOME"] = str(tmp_path / "xdg_cache")
    os.environ["NUMBA_CACHE_DIR"] = str(tmp_path / "numba_cache")


def test_neighborhood_missing_columns(tmp_path: Path):
    _prep_env(tmp_path)
    try:
        napari = pytest.importorskip("napari")
    except Exception as exc:  # pragma: no cover - environment-specific guard
        pytest.skip(f"napari unavailable: {exc}")
    from aimino_frontend.aimino_core.handlers.special_analysis.utils.neighborhood import (
        compute_tumor_neighborhood_layers,
    )

    h5_path = _write_h5ad(tmp_path / "no_coords.h5ad", pd.DataFrame({"tumor_positive": [True, False]}))
    viewer = napari.components.ViewerModel()

    with pytest.raises(ValueError) as excinfo:
        compute_tumor_neighborhood_layers(
            viewer,
            raw_image_path=str(tmp_path / "img.tif"),
            h5ad_path=str(h5_path),
            marker_col="tumor_positive",
            output_root=str(tmp_path / "out"),
            radius=50,
            force_recompute=True,
        )
    assert "Missing required columns" in str(excinfo.value)


def test_neighborhood_no_tumor_returns_message(tmp_path: Path):
    _prep_env(tmp_path)
    try:
        napari = pytest.importorskip("napari")
    except Exception as exc:  # pragma: no cover - environment-specific guard
        pytest.skip(f"napari unavailable: {exc}")
    from aimino_frontend.aimino_core.handlers.special_analysis.utils.neighborhood import (
        compute_tumor_neighborhood_layers,
    )

    obs = pd.DataFrame(
        {
            "X_centroid": [10.0, 20.0],
            "Y_centroid": [10.0, 20.0],
            "tumor_positive": [False, False],
        }
    )
    h5_path = _write_h5ad(tmp_path / "no_tumor.h5ad", obs)
    viewer = napari.components.ViewerModel()

    msg = compute_tumor_neighborhood_layers(
        viewer,
        raw_image_path=str(tmp_path / "img.tif"),
        h5ad_path=str(h5_path),
        marker_col="tumor_positive",
        output_root=str(tmp_path / "out"),
        radius=50,
        force_recompute=True,
    )
    assert isinstance(msg, str)
    assert "No tumor cells" in msg
