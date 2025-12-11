"""Unit tests for command executor."""

import pytest
from unittest.mock import MagicMock, patch

from aimino_frontend.aimino_core.command_models import CmdListLayers
from aimino_frontend.aimino_core.executor import execute_command
from aimino_frontend.aimino_core.errors import CommandExecutionError


@pytest.mark.unit
class TestExecutor:
    """Test command execution."""

    def test_execute_command_with_command_object(self):
        """Test executing a command object directly."""
        mock_viewer = MagicMock()
        cmd = CmdListLayers(action="list_layers")
        
        with patch("aimino_frontend.aimino_core.executor.dispatch") as mock_dispatch:
            mock_handler = MagicMock(return_value="success")
            mock_dispatch.return_value = mock_handler
            
            result = execute_command(cmd, mock_viewer)
            
            assert result == "success"
            mock_dispatch.assert_called_once_with("list_layers")
            mock_handler.assert_called_once_with(cmd, mock_viewer)

    def test_execute_command_with_dict(self):
        """Test executing a command from a dictionary."""
        mock_viewer = MagicMock()
        cmd_dict = {"action": "list_layers"}
        
        with patch("aimino_frontend.aimino_core.executor.dispatch") as mock_dispatch:
            mock_handler = MagicMock(return_value="success")
            mock_dispatch.return_value = mock_handler
            
            result = execute_command(cmd_dict, mock_viewer)
            
            assert result == "success"
            mock_dispatch.assert_called_once_with("list_layers")

