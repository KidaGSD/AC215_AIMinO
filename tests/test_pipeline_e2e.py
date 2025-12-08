import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import anndata as ad
from tifffile import imwrite


@pytest.mark.skipif(os.environ.get("SKIP_E2E", "0") == "1", reason="e2e skipped by env")
def test_ingest_load_density_neighborhood(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        monkeypatch.setenv("AIMINO_DATA_ROOT", str(root / "data"))
        monkeypatch.setenv("HOME", str(root))
        monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
        monkeypatch.setenv("NAPARI_CACHE_DIR", str(root / "napari_cache"))
        monkeypatch.setenv("NAPARI_CONFIG_DIR", str(root / "napari_config"))
        monkeypatch.setenv("XDG_CACHE_HOME", str(root / "xdg_cache"))

        napari = pytest.importorskip("napari")

        # create tiny image and h5ad
        img = np.zeros((128, 128), dtype=np.float32)
        img[30:40, 30:40] = 1.0
        img_path = root / "sample.tif"
        imwrite(img_path, img)

        obs = pd.DataFrame(
            {
                "CellID": [1, 2, 3, 4, 5],
                "X_centroid": [32, 34, 80, 90, 60],
                "Y_centroid": [32, 36, 70, 90, 30],
                "MajorAxisLength": [8, 8, 8, 8, 8],
                "MinorAxisLength": [6, 6, 6, 6, 6],
                "Orientation": [0, 0, 0, 0, 0],
                "tumor_positive": [True, True, True, False, False],
                "CD45_positive": [False, True, False, True, False],
                "CD20_positive": [False, False, True, False, False],
                "CD3E_positive": [False, False, False, True, False],
            }
        )
        adata = ad.AnnData(np.zeros((len(obs), 1), dtype=np.float32), obs=obs)
        h5_path = root / "sample.h5ad"
        adata.write_h5ad(h5_path)

        from aimino_frontend.aimino_core.data_store import ingest_dataset
        from aimino_frontend.aimino_core import execute_command
        import aimino_frontend.aimino_core.handlers.special_analysis.density_handler as dh
        import aimino_frontend.aimino_core.handlers.special_analysis.neighborhood_handler as nh

        manifest = ingest_dataset(img_path, h5_path, dataset_id="case_e2e", copy_files=False)

        # Use headless ViewerModel to avoid GUI/dpi issues in CI
        viewer = napari.components.ViewerModel()

        # Avoid zoom/camera operations in headless mode
        monkeypatch.setattr(dh, "zoom_to_dense_region", lambda viewer, lname: "skip zoom", raising=False)
        # Simplify neighborhood computation to avoid vispy/points color issues in headless CI
        monkeypatch.setattr(
            nh, "compute_tumor_neighborhood_layers", lambda *args, **kwargs: "neighborhood computed (stub)", raising=False
        )

        # load marker
        msg1 = execute_command(
            {"action": "special_load_marker_data", "dataset_id": manifest["dataset_id"], "marker_col": "tumor_positive"},
            viewer,
        )
        assert "Loaded marker data" in msg1
        assert "tumor_positive_mask" in viewer.layers
        assert "tumor_positive_density" in viewer.layers

        # update density
        msg2 = execute_command(
            {
                "action": "special_update_density",
                "dataset_id": manifest["dataset_id"],
                "marker_col": "tumor_positive",
                "sigma": 30.0,
                "force": True,
            },
            viewer,
        )
        assert "Density updated" in msg2

        # neighborhood
        msg3 = execute_command(
            {
                "action": "special_compute_neighborhood",
                "dataset_id": manifest["dataset_id"],
                "marker_col": "tumor_positive",
                "radius": 20.0,
                "force_recompute": True,
            },
            viewer,
        )
        assert "neighborhood" in msg3.lower() or "stub" in msg3.lower()
