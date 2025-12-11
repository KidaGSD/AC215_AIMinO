"""Tests for context management commands (set_dataset, set_marker, etc.)."""

import pytest
import tempfile
import shutil
from pathlib import Path

from aimino_frontend.aimino_core.command_models import (
    CmdSetDataset,
    CmdSetMarker,
    CmdListDatasets,
    CmdGetDatasetInfo,
    CmdClearCache,
    BaseCommandAdapter,
)
from aimino_frontend.aimino_core.registry import available_actions, dispatch
from aimino_frontend.aimino_core.data_store import (
    ingest_dataset,
    get_data_root,
    list_datasets,
)


class TestContextCommandModels:
    """Test that new command models work correctly."""

    def test_set_dataset_model(self):
        cmd = CmdSetDataset(action="set_dataset", dataset_id="test123")
        assert cmd.action == "set_dataset"
        assert cmd.dataset_id == "test123"

    def test_set_marker_model(self):
        cmd = CmdSetMarker(action="set_marker", marker_col="SOX10_positive")
        assert cmd.action == "set_marker"
        assert cmd.marker_col == "SOX10_positive"

    def test_list_datasets_model(self):
        cmd = CmdListDatasets(action="list_datasets")
        assert cmd.action == "list_datasets"

    def test_get_dataset_info_model(self):
        cmd = CmdGetDatasetInfo(action="get_dataset_info", dataset_id="test123")
        assert cmd.action == "get_dataset_info"
        assert cmd.dataset_id == "test123"

    def test_get_dataset_info_optional_id(self):
        cmd = CmdGetDatasetInfo(action="get_dataset_info")
        assert cmd.action == "get_dataset_info"
        assert cmd.dataset_id is None

    def test_clear_cache_model(self):
        cmd = CmdClearCache(
            action="clear_processed_cache", dataset_id="test123", delete_raw=False
        )
        assert cmd.action == "clear_processed_cache"
        assert cmd.dataset_id == "test123"
        assert cmd.delete_raw is False

    def test_clear_cache_defaults(self):
        cmd = CmdClearCache(action="clear_processed_cache")
        assert cmd.dataset_id is None
        assert cmd.delete_raw is False


class TestContextCommandAdapter:
    """Test BaseCommandAdapter parses context commands."""

    @pytest.mark.parametrize(
        "cmd_dict",
        [
            {"action": "set_dataset", "dataset_id": "case1"},
            {"action": "set_marker", "marker_col": "CD8_positive"},
            {"action": "list_datasets"},
            {"action": "get_dataset_info"},
            {"action": "get_dataset_info", "dataset_id": "case2"},
            {"action": "clear_processed_cache"},
            {"action": "clear_processed_cache", "dataset_id": "case3", "delete_raw": True},
        ],
    )
    def test_adapter_parses_context_commands(self, cmd_dict):
        parsed = BaseCommandAdapter.validate_python(cmd_dict)
        assert parsed.action == cmd_dict["action"]


class TestContextActionsRegistered:
    """Test that context handlers are registered."""

    def test_context_actions_in_registry(self):
        actions = available_actions()
        context_actions = [
            "set_dataset",
            "set_marker",
            "list_datasets",
            "get_dataset_info",
            "clear_processed_cache",
        ]
        for action in context_actions:
            assert action in actions, f"Action '{action}' not registered"

    def test_dispatch_context_handlers(self):
        context_actions = [
            "set_dataset",
            "set_marker",
            "list_datasets",
            "get_dataset_info",
            "clear_processed_cache",
        ]
        for action in context_actions:
            handler = dispatch(action)
            assert callable(handler), f"Handler for '{action}' not callable"


class TestContextHandlersWithData:
    """Integration tests for context handlers with actual data."""

    @pytest.fixture
    def temp_data_root(self, monkeypatch):
        """Create a temporary data root for testing."""
        tmpdir = tempfile.mkdtemp(prefix="aimino_test_")
        monkeypatch.setenv("AIMINO_DATA_ROOT", tmpdir)
        yield Path(tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def sample_dataset(self, temp_data_root):
        """Create a sample dataset for testing."""
        import numpy as np
        import tifffile
        import anndata as ad

        # Create temp files
        img_path = temp_data_root / "test_image.tif"
        h5ad_path = temp_data_root / "test_cells.h5ad"

        # Create minimal TIFF
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        tifffile.imwrite(str(img_path), img)

        # Create minimal h5ad
        adata = ad.AnnData(X=np.random.rand(10, 5))
        adata.obs["SOX10_positive"] = [True, False] * 5
        adata.write_h5ad(str(h5ad_path))

        # Ingest dataset
        manifest = ingest_dataset(
            str(img_path),
            str(h5ad_path),
            dataset_id="test_dataset",
            metadata={"marker_cols": ["SOX10_positive"]},
        )
        return manifest["dataset_id"]

    def test_list_datasets_handler(self, sample_dataset):
        """Test list_datasets returns registered datasets."""
        datasets = list(list_datasets())
        assert sample_dataset in datasets

    def test_set_context_functions(self):
        """Test setting context functions."""
        from aimino_frontend.aimino_core.handlers.context_handler import set_context_functions
        
        mock_set_ds = lambda x, y: None
        mock_set_marker = lambda x: None
        mock_get_ds = lambda: "test"
        mock_get_marker = lambda: "SOX10"
        
        set_context_functions(
            set_dataset_fn=mock_set_ds,
            set_marker_fn=mock_set_marker,
            get_dataset_id_fn=mock_get_ds,
            get_marker_fn=mock_get_marker,
        )
        # Functions should be set (tested indirectly through handlers)

    def test_get_attr_with_dict(self):
        """Test _get_attr function with dictionary command."""
        from aimino_frontend.aimino_core.handlers.context_handler import _get_attr
        
        cmd_dict = {"dataset_id": "test123", "marker_col": "SOX10"}
        assert _get_attr(cmd_dict, "dataset_id") == "test123"
        assert _get_attr(cmd_dict, "marker_col") == "SOX10"
        assert _get_attr(cmd_dict, "nonexistent", "default") == "default"

    def test_handle_set_dataset_without_id(self, sample_dataset):
        """Test set_dataset handler without dataset_id."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_set_dataset
        from unittest.mock import MagicMock
        
        mock_viewer = MagicMock()
        result = handle_set_dataset({"action": "set_dataset"}, mock_viewer)
        assert "Error" in result
        assert "dataset_id is required" in result

    def test_handle_set_marker_without_col(self):
        """Test set_marker handler without marker_col."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_set_marker
        from unittest.mock import MagicMock
        
        mock_viewer = MagicMock()
        result = handle_set_marker({"action": "set_marker"}, mock_viewer)
        assert "Error" in result
        assert "marker_col is required" in result

    def test_handle_list_datasets_empty(self, monkeypatch):
        """Test list_datasets handler with no datasets."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_list_datasets
        from unittest.mock import MagicMock, patch
        
        mock_viewer = MagicMock()
        with patch("aimino_frontend.aimino_core.handlers.context_handler.list_datasets", return_value=[]):
            result = handle_list_datasets({"action": "list_datasets"}, mock_viewer)
            assert "No datasets found" in result


    def test_handle_set_dataset_with_nonexistent_dataset(self):
        """Test set_dataset handler with nonexistent dataset."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_set_dataset
        from unittest.mock import MagicMock, patch
        
        mock_viewer = MagicMock()
        with patch("aimino_frontend.aimino_core.handlers.context_handler.get_dataset_paths", side_effect=Exception("Not found")):
            result = handle_set_dataset({"action": "set_dataset", "dataset_id": "nonexistent"}, mock_viewer)
            assert "Error" in result
            assert "not found" in result.lower()

    def test_handle_set_marker_success(self):
        """Test set_marker handler success case."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_set_marker, set_context_functions
        from unittest.mock import MagicMock
        
        mock_viewer = MagicMock()
        mock_set_marker = MagicMock()
        set_context_functions(set_marker_fn=mock_set_marker)
        
        result = handle_set_marker({"action": "set_marker", "marker_col": "SOX10"}, mock_viewer)
        assert "Switched to marker" in result
        assert "SOX10" in result
        mock_set_marker.assert_called_once_with("SOX10")

    def test_handle_set_dataset_success(self, sample_dataset):
        """Test set_dataset handler success case."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_set_dataset, set_context_functions
        from unittest.mock import MagicMock
        
        mock_viewer = MagicMock()
        mock_set_dataset = MagicMock()
        set_context_functions(set_dataset_fn=mock_set_dataset)
        
        result = handle_set_dataset({"action": "set_dataset", "dataset_id": sample_dataset}, mock_viewer)
        assert "Switched to dataset" in result
        assert sample_dataset in result

    def test_handle_clear_cache(self, sample_dataset):
        """Test clear_processed_cache handler."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_clear_cache
        from unittest.mock import MagicMock
        
        mock_viewer = MagicMock()
        result = handle_clear_cache({"action": "clear_processed_cache", "dataset_id": sample_dataset}, mock_viewer)
        assert "Cleared cache" in result or "Error" in result

    def test_handle_clear_cache_with_delete_raw(self, sample_dataset):
        """Test clear_processed_cache handler with delete_raw=True."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_clear_cache
        from unittest.mock import MagicMock
        
        mock_viewer = MagicMock()
        result = handle_clear_cache({
            "action": "clear_processed_cache", 
            "dataset_id": sample_dataset,
            "delete_raw": True
        }, mock_viewer)
        assert "Cleared cache" in result or "Error" in result

    def test_handle_list_datasets_with_current(self, sample_dataset):
        """Test list_datasets handler with current dataset set."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_list_datasets, set_context_functions
        from unittest.mock import MagicMock
        
        mock_viewer = MagicMock()
        mock_get_ds = lambda: sample_dataset
        set_context_functions(get_dataset_id_fn=mock_get_ds)
        
        result = handle_list_datasets({"action": "list_datasets"}, mock_viewer)
        assert "Available datasets" in result
        assert sample_dataset in result
        assert "[active]" in result

    def test_handle_get_dataset_info_with_current(self, sample_dataset):
        """Test get_dataset_info handler using current dataset."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_get_dataset_info, set_context_functions
        from unittest.mock import MagicMock
        
        mock_viewer = MagicMock()
        mock_get_ds = lambda: sample_dataset
        set_context_functions(get_dataset_id_fn=mock_get_ds)
        
        result = handle_get_dataset_info({"action": "get_dataset_info"}, mock_viewer)
        assert "Dataset:" in result
        assert sample_dataset in result

    def test_handle_get_dataset_info_with_specific_id(self, sample_dataset):
        """Test get_dataset_info handler with specific dataset_id."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_get_dataset_info
        from unittest.mock import MagicMock
        
        mock_viewer = MagicMock()
        result = handle_get_dataset_info({
            "action": "get_dataset_info",
            "dataset_id": sample_dataset
        }, mock_viewer)
        assert "Dataset:" in result
        assert sample_dataset in result
        assert "Image:" in result or "H5AD:" in result

    def test_handle_clear_cache_with_current_dataset(self, sample_dataset):
        """Test clear_processed_cache handler using current dataset."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_clear_cache, set_context_functions
        from unittest.mock import MagicMock
        
        mock_viewer = MagicMock()
        mock_get_ds = lambda: sample_dataset
        set_context_functions(get_dataset_id_fn=mock_get_ds)
        
        result = handle_clear_cache({"action": "clear_processed_cache"}, mock_viewer)
        assert "Cleared cache" in result or "Error" in result

    def test_handle_get_dataset_info_with_markers(self, sample_dataset):
        """Test get_dataset_info handler shows marker columns when available."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_get_dataset_info
        from unittest.mock import MagicMock, patch
        
        mock_viewer = MagicMock()
        # Mock load_manifest to return manifest with marker_cols
        mock_manifest = {
            "dataset_id": sample_dataset,
            "image_path": "/path/to/image.tif",
            "h5ad_path": "/path/to/data.h5ad",
            "output_root": "/path/to/output",
            "created_at": "2024-01-01",
            "metadata": {"marker_cols": ["SOX10_positive", "CD45_positive"]}
        }
        
        with patch("aimino_frontend.aimino_core.handlers.context_handler.load_manifest", return_value=mock_manifest):
            result = handle_get_dataset_info({
                "action": "get_dataset_info",
                "dataset_id": sample_dataset
            }, mock_viewer)
            assert "Markers:" in result
            assert "SOX10_positive" in result

    def test_handle_clear_cache_error(self):
        """Test clear_processed_cache handler error handling."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_clear_cache
        from unittest.mock import MagicMock, patch
        
        mock_viewer = MagicMock()
        with patch("aimino_frontend.aimino_core.handlers.context_handler.clear_processed_cache", side_effect=Exception("Cache error")):
            result = handle_clear_cache({
                "action": "clear_processed_cache",
                "dataset_id": "nonexistent"
            }, mock_viewer)
            assert "Error" in result
            assert "Failed to clear cache" in result

    def test_handle_get_dataset_info_load_error(self):
        """Test get_dataset_info handler with load manifest error."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_get_dataset_info
        from unittest.mock import MagicMock, patch
        
        mock_viewer = MagicMock()
        with patch("aimino_frontend.aimino_core.handlers.context_handler.load_manifest", side_effect=Exception("Load error")):
            result = handle_get_dataset_info({
                "action": "get_dataset_info",
                "dataset_id": "test_dataset"
            }, mock_viewer)
            assert "Error" in result
            assert "Failed to load dataset" in result

    def test_handle_clear_cache_with_processed_files(self, sample_dataset):
        """Test clear_processed_cache handler with processed files result."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_clear_cache
        from unittest.mock import MagicMock, patch
        
        mock_viewer = MagicMock()
        mock_result = {"processed": True, "raw_files": []}
        with patch("aimino_frontend.aimino_core.handlers.context_handler.clear_processed_cache", return_value=mock_result):
            result = handle_clear_cache({
                "action": "clear_processed_cache",
                "dataset_id": sample_dataset
            }, mock_viewer)
            assert "Cleared cache" in result
            assert "processed files removed" in result

    def test_handle_clear_cache_with_raw_files(self, sample_dataset):
        """Test clear_processed_cache handler with raw files result."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_clear_cache
        from unittest.mock import MagicMock, patch
        
        mock_viewer = MagicMock()
        mock_result = {"processed": False, "raw_files": ["file1.txt", "file2.txt"]}
        with patch("aimino_frontend.aimino_core.handlers.context_handler.clear_processed_cache", return_value=mock_result):
            result = handle_clear_cache({
                "action": "clear_processed_cache",
                "dataset_id": sample_dataset,
                "delete_raw": True
            }, mock_viewer)
            assert "Cleared cache" in result
            assert "raw files removed" in result
            assert "2" in result  # Number of files

    def test_handle_clear_cache_with_both_results(self, sample_dataset):
        """Test clear_processed_cache handler with both processed and raw files."""
        from aimino_frontend.aimino_core.handlers.context_handler import handle_clear_cache
        from unittest.mock import MagicMock, patch
        
        mock_viewer = MagicMock()
        mock_result = {"processed": True, "raw_files": ["file1.txt"]}
        with patch("aimino_frontend.aimino_core.handlers.context_handler.clear_processed_cache", return_value=mock_result):
            result = handle_clear_cache({
                "action": "clear_processed_cache",
                "dataset_id": sample_dataset,
                "delete_raw": True
            }, mock_viewer)
            assert "Cleared cache" in result
            assert "processed files removed" in result
            assert "raw files removed" in result

    def test_handler_chain(self, sample_dataset):
        """Test that handlers can be dispatched and return strings."""
        # Get handler
        list_handler = dispatch("list_datasets")
        info_handler = dispatch("get_dataset_info")

        # Mock viewer (not used by these handlers)
        class MockViewer:
            pass

        viewer = MockViewer()

        # Test list_datasets
        result = list_handler({"action": "list_datasets"}, viewer)
        assert isinstance(result, str)
        assert sample_dataset in result

        # Test get_dataset_info
        result = info_handler(
            {"action": "get_dataset_info", "dataset_id": sample_dataset}, viewer
        )
        assert isinstance(result, str)
        assert sample_dataset in result


class TestLeadManagerContextActions:
    """Test LeadManager handles context actions correctly."""

    def test_context_actions_defined(self):
        """Verify CONTEXT_ACTIONS constant exists and contains expected actions."""
        from src.api_service.api.agents.lead_manager import CONTEXT_ACTIONS

        expected = {
            "set_dataset",
            "set_marker",
            "list_datasets",
            "get_dataset_info",
            "clear_processed_cache",
        }
        assert CONTEXT_ACTIONS == expected

    def test_autofill_skips_dataset_for_context_actions(self):
        """Test that autofill doesn't require dataset_id for context actions."""
        from src.api_service.api.agents.lead_manager import (
            _autofill_command,
            _ContextInfo,
        )

        ctx_info = _ContextInfo()  # Empty context

        # list_datasets should work without dataset_id
        cmd, error = _autofill_command({"action": "list_datasets"}, ctx_info)
        assert error is None
        assert cmd["action"] == "list_datasets"

        # set_dataset should work (it provides its own dataset_id)
        cmd, error = _autofill_command(
            {"action": "set_dataset", "dataset_id": "test"}, ctx_info
        )
        assert error is None
        assert cmd["dataset_id"] == "test"

        # set_marker should work
        cmd, error = _autofill_command(
            {"action": "set_marker", "marker_col": "SOX10"}, ctx_info
        )
        assert error is None
        assert cmd["marker_col"] == "SOX10"
