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
