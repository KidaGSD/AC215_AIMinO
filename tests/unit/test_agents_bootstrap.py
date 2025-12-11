"""Unit tests for agents bootstrap."""

import pytest
from unittest.mock import patch, MagicMock

from api_service.api.utils.agents_bootstrap import build_runner


@pytest.mark.unit
class TestAgentsBootstrap:
    """Test agents bootstrap functionality."""

    def test_build_runner(self):
        """Test build_runner function calls lead_manager.build_runner."""
        with patch("api_service.api.agents.lead_manager.build_runner") as mock_lead_build:
            mock_session = MagicMock()
            mock_runner = MagicMock()
            mock_lead_build.return_value = (mock_session, mock_runner)
            
            result = build_runner()
            
            assert len(result) == 2
            assert result[0] == mock_session
            assert result[1] == mock_runner
            mock_lead_build.assert_called_once()

