"""Unit tests for logging utilities."""

import pytest
import logging
import sys
from unittest.mock import patch, MagicMock
import os

from api_service.api.utils.logging import configure_logging, write_jsonl


@pytest.mark.unit
class TestLogging:
    """Test logging utilities."""

    def test_configure_logging(self):
        """Test logging configuration."""
        logger = configure_logging()
        assert logger is not None
        assert logger.name == "aimino.api"

    def test_write_jsonl(self, tmp_path):
        """Test write_jsonl function."""
        log_file = tmp_path / "test.jsonl"
        
        # Write some log entries
        write_jsonl(log_file, {"event": "test", "data": "value1"})
        write_jsonl(log_file, {"event": "test2", "data": "value2"})
        
        # Read and verify
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert "test" in lines[0]
        assert "test2" in lines[1]

    def test_write_jsonl_with_nonexistent_dir(self, tmp_path):
        """Test write_jsonl creates directory if needed."""
        log_file = tmp_path / "subdir" / "test.jsonl"
        
        write_jsonl(log_file, {"event": "test"})
        
        assert log_file.exists()
        assert log_file.parent.exists()

    def test_write_jsonl_error_handling(self, tmp_path, monkeypatch):
        """Test write_jsonl error handling falls back to stdout."""
        log_file = tmp_path / "test.jsonl"
        
        # Mock open to raise exception, and mock print to capture output
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with patch("builtins.print") as mock_print:
                # Should not raise, but print to stdout instead
                write_jsonl(str(log_file), {"event": "test", "data": "value"})
                # Function should complete without error
                # Verify it tried to print to stdout
                mock_print.assert_called_once()
                # Check that the call includes the JSON data
                call_args = mock_print.call_args
                assert "test" in str(call_args) or "value" in str(call_args)

    def test_write_jsonl_with_root_path(self, tmp_path):
        """Test write_jsonl with file in root directory (no subdirectory)."""
        log_file = tmp_path / "root_file.jsonl"
        
        write_jsonl(str(log_file), {"event": "root_test"})
        
        assert log_file.exists()
        content = log_file.read_text()
        assert "root_test" in content

    def test_write_jsonl_append_mode(self, tmp_path):
        """Test that write_jsonl appends to existing file."""
        log_file = tmp_path / "append_test.jsonl"
        
        write_jsonl(str(log_file), {"entry": 1})
        write_jsonl(str(log_file), {"entry": 2})
        
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert "1" in lines[0]
        assert "2" in lines[1]

    def test_write_jsonl_with_root_file(self):
        """Test write_jsonl with file in root (dirname is empty)."""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file directly in root (no subdirectory)
            log_file = os.path.join(tmpdir, "root_file.jsonl")
            write_jsonl(log_file, {"event": "root_test"})
            
            assert os.path.exists(log_file)
            with open(log_file, "r") as f:
                content = f.read()
                assert "root_test" in content


    def test_configure_logging_with_level(self):
        """Test configure_logging with custom level."""
        logger = configure_logging(level="DEBUG")
        assert logger is not None
        assert logger.level == logging.DEBUG

    def test_configure_logging_with_env_level(self, monkeypatch):
        """Test configure_logging reads level from environment."""
        monkeypatch.setenv("AIMINO_LOG_LEVEL", "WARNING")
        logger = configure_logging()
        assert logger is not None
        assert logger.level == logging.WARNING

    def test_configure_logging_with_invalid_level(self):
        """Test configure_logging handles invalid level gracefully."""
        logger = configure_logging(level="INVALID_LEVEL")
        assert logger is not None
        # Should fall back to INFO
        assert logger.level == logging.INFO

