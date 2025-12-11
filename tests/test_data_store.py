import tempfile
import os
from pathlib import Path

import pytest

from aimino_frontend.aimino_core.data_store import (
    get_data_root,
    _expand_path,
    ingest_dataset,
    get_dataset_paths,
    resolve_dataset_context,
    DATA_ROOT_ENV,
    suggest_dataset_id,
    clear_processed_cache,
)


def test_ingest_and_resolve_context(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        monkeypatch.setenv(DATA_ROOT_ENV, str(root))
        img = root / "sample.tif"
        h5 = root / "sample.h5ad"
        img.write_bytes(b"tiff")
        h5.write_bytes(b"h5ad")

        manifest = ingest_dataset(img, h5, dataset_id=None, copy_files=False)
        dataset_id = manifest["dataset_id"]
        assert dataset_id.startswith("sample")
        assert Path(manifest["image_path"]).resolve() == img.resolve()
        assert Path(manifest["h5ad_path"]).resolve() == h5.resolve()

        ctx = get_dataset_paths(dataset_id)
        assert ctx.dataset_id == dataset_id
        assert ctx.image_path.resolve() == img.resolve()
        assert ctx.h5ad_path.resolve() == h5.resolve()

        ctx2 = resolve_dataset_context(dataset_id, None, None)
        assert ctx2.image_path.resolve() == img.resolve()

        # direct path resolution when no dataset_id
        ctx3 = resolve_dataset_context(None, str(img), str(h5))
        assert ctx3.image_path.resolve() == img.resolve()


def test_dataset_signature_change(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        monkeypatch.setenv(DATA_ROOT_ENV, str(root))
        img = root / "sample.tif"
        h5 = root / "sample.h5ad"
        img.write_bytes(b"tiff")
        h5.write_bytes(b"h5ad")

        manifest = ingest_dataset(img, h5, "case001", copy_files=False)
        assert manifest["dataset_id"] == "case001"

        # Modify TIFF to trigger invalidation
        img.write_bytes(b"changed")
        with pytest.raises(RuntimeError):
            get_dataset_paths("case001")


def test_suggest_dataset_id_unique(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        monkeypatch.setenv(DATA_ROOT_ENV, str(root))
        img = root / "sample.tif"
        img.write_bytes(b"tiff")
        h5 = root / "sample.h5ad"
        h5.write_bytes(b"h5ad")

        id1 = ingest_dataset(img, h5, dataset_id=None)["dataset_id"]
        id2 = suggest_dataset_id(img)
        assert id1 != id2


def test_clear_processed_cache(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        monkeypatch.setenv(DATA_ROOT_ENV, str(root))
        img = root / "sample.tif"
        h5 = root / "sample.h5ad"
        img.write_bytes(b"tiff")
        h5.write_bytes(b"h5ad")

        manifest = ingest_dataset(img, h5, "case002", copy_files=False)
        processed = Path(manifest["output_root"])
        extra = processed / "temp.txt"
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_text("cache")
        assert extra.exists()

        result = clear_processed_cache("case002")
        assert result["processed"] is True
        assert not extra.exists()
        assert processed.exists() and not any(processed.iterdir())


@pytest.mark.unit
def test_data_ingest_handler(monkeypatch):
    """Test data_ingest handler."""
    from aimino_frontend.aimino_core.handlers.special_analysis.data_ingest_handler import handle_data_ingest
    from aimino_frontend.aimino_core.command_models import CmdDataIngest
    from unittest.mock import MagicMock
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("AIMINO_DATA_ROOT", tmpdir)
        img = Path(tmpdir) / "test.tif"
        h5 = Path(tmpdir) / "test.h5ad"
        img.write_bytes(b"tiff")
        h5.write_bytes(b"h5ad")
        
        mock_viewer = MagicMock()
        cmd = CmdDataIngest(
            action="data_ingest",
            image_path=str(img),
            h5ad_path=str(h5),
            dataset_id="test_ingest",
            copy_files=False,
            marker_col="SOX10"
        )
        
        result = handle_data_ingest(cmd, mock_viewer)
        assert "Ingested dataset" in result
        assert "test_ingest" in result


@pytest.mark.unit
def test_data_ingest_handler_without_marker(monkeypatch):
    """Test data_ingest handler without marker_col."""
    from aimino_frontend.aimino_core.handlers.special_analysis.data_ingest_handler import handle_data_ingest
    from aimino_frontend.aimino_core.command_models import CmdDataIngest
    from unittest.mock import MagicMock
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("AIMINO_DATA_ROOT", tmpdir)
        img = Path(tmpdir) / "test.tif"
        h5 = Path(tmpdir) / "test.h5ad"
        img.write_bytes(b"tiff")
        h5.write_bytes(b"h5ad")
        
        mock_viewer = MagicMock()
        cmd = CmdDataIngest(
            action="data_ingest",
            image_path=str(img),
            h5ad_path=str(h5),
            dataset_id="test_ingest2",
            copy_files=False,
            marker_col=None
        )
        
        result = handle_data_ingest(cmd, mock_viewer)
        assert "Ingested dataset" in result


@pytest.mark.unit
def test_get_data_root(monkeypatch):
    """Test get_data_root function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv(DATA_ROOT_ENV, tmpdir)
        root = get_data_root()
        assert root.exists()
        assert root == Path(tmpdir).resolve()


@pytest.mark.unit
def test_expand_path():
    """Test _expand_path function."""
    # Test with string path
    result = _expand_path("/tmp/test")
    assert isinstance(result, Path)
    
    # Test with Path object
    path_obj = Path("/tmp/test")
    result = _expand_path(path_obj)
    assert isinstance(result, Path)
    
    # Test with ~ expansion
    if os.path.expanduser("~") != "~":
        result = _expand_path("~/test")
        assert "~" not in str(result)


@pytest.mark.unit
def test_data_ingest_handler_error(monkeypatch):
    """Test data_ingest handler error handling."""
    from aimino_frontend.aimino_core.handlers.special_analysis.data_ingest_handler import handle_data_ingest
    from aimino_frontend.aimino_core.command_models import CmdDataIngest
    from aimino_frontend.aimino_core.errors import CommandExecutionError
    from unittest.mock import MagicMock
    
    mock_viewer = MagicMock()
    cmd = CmdDataIngest(
        action="data_ingest",
        image_path="/nonexistent/path.tif",
        h5ad_path="/nonexistent/path.h5ad",
        dataset_id="test_error",
        copy_files=False,
        marker_col=None
    )
    
    with pytest.raises(CommandExecutionError, match="Failed to ingest dataset"):
        handle_data_ingest(cmd, mock_viewer)
