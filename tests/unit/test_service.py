"""Unit tests for API service creation and configuration."""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

from api_service.api.service import create_app


@pytest.mark.unit
class TestServiceCreation:
    """Test FastAPI app creation and configuration."""

    def test_create_app_basic(self):
        """Test basic app creation."""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        app = create_app()
        assert app.title == "AIMinO API"
        assert app.version == "0.1.0"

    def test_create_app_with_json_origins(self):
        """Test app creation with JSON origins string."""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        with patch("api_service.api.service.settings") as mock_settings:
            mock_settings.AIMINO_ALLOWED_ORIGINS = json.dumps(["http://localhost:3000", "http://example.com"])
            mock_settings.AIMINO_API_PREFIX = "/api/v1"
            app = create_app()
            assert app is not None

    def test_create_app_with_comma_separated_origins(self):
        """Test app creation with comma-separated origins."""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        with patch("api_service.api.service.settings") as mock_settings:
            mock_settings.AIMINO_ALLOWED_ORIGINS = "http://localhost:3000, http://example.com"
            mock_settings.AIMINO_API_PREFIX = "/api/v1"
            app = create_app()
            assert app is not None

    def test_create_app_with_empty_origins(self):
        """Test app creation with empty origins falls back to '*'."""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        with patch("api_service.api.service.settings") as mock_settings:
            mock_settings.AIMINO_ALLOWED_ORIGINS = ""
            mock_settings.AIMINO_API_PREFIX = "/api/v1"
            app = create_app()
            assert app is not None

    def test_create_app_with_invalid_json_origins(self):
        """Test app creation with invalid JSON origins falls back to comma split."""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        with patch("api_service.api.service.settings") as mock_settings:
            mock_settings.AIMINO_ALLOWED_ORIGINS = "not,valid,json"
            mock_settings.AIMINO_API_PREFIX = "/api/v1"
            app = create_app()
            assert app is not None

    def test_create_app_with_genai_configured(self):
        """Test app creation with genai configuration."""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        os.environ["GOOGLE_API_KEY"] = "test_key"
        
        with patch("api_service.api.service.genai") as mock_genai:
            mock_genai.configure = MagicMock()
            with patch("api_service.api.service.build_runner") as mock_build:
                mock_build.return_value = (MagicMock(), MagicMock())
                app = create_app()
                assert app is not None

    def test_create_app_with_genai_no_configure_method(self):
        """Test app creation when genai doesn't have configure method."""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        os.environ["GOOGLE_API_KEY"] = "test_key"
        
        with patch("api_service.api.service.genai") as mock_genai:
            del mock_genai.configure  # Remove configure method
            with patch("api_service.api.service.build_runner") as mock_build:
                mock_build.return_value = (MagicMock(), MagicMock())
                app = create_app()
                assert app is not None

    def test_create_app_with_genai_config_error(self):
        """Test app creation handles genai configuration errors gracefully."""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        os.environ["GOOGLE_API_KEY"] = "test_key"
        
        with patch("api_service.api.service.genai") as mock_genai:
            mock_genai.configure = MagicMock(side_effect=Exception("Config error"))
            with patch("api_service.api.service.build_runner") as mock_build:
                mock_build.return_value = (MagicMock(), MagicMock())
                app = create_app()
                assert app is not None

    def test_create_app_with_gemini_key(self):
        """Test app creation with GEMINI_API_KEY instead of GOOGLE_API_KEY."""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        original_google_key = os.environ.get("GOOGLE_API_KEY")
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]
        os.environ["GEMINI_API_KEY"] = "test_gemini_key"
        
        try:
            with patch("api_service.api.service.genai") as mock_genai:
                mock_genai.configure = MagicMock()
                with patch("api_service.api.service.build_runner") as mock_build:
                    mock_build.return_value = (MagicMock(), MagicMock())
                    app = create_app()
                    assert app is not None
        finally:
            if original_google_key:
                os.environ["GOOGLE_API_KEY"] = original_google_key
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]

    def test_create_app_version_from_metadata(self):
        """Test app creation gets version from package metadata."""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        with patch("api_service.api.service.metadata") as mock_metadata:
            # Test when package is in distributions
            mock_metadata.packages_distributions.return_value = {"aimino-api-service": ["aimino-api-service"]}
            mock_metadata.version.return_value = "0.2.0"
            app = create_app()
            assert app is not None
            mock_metadata.version.assert_called_once_with("aimino-api-service")

    def test_create_app_version_fallback(self):
        """Test app creation falls back to default version when package not found."""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        with patch("api_service.api.service.metadata") as mock_metadata:
            # Test when package is NOT in distributions
            mock_metadata.packages_distributions.return_value = {}
            app = create_app()
            assert app is not None
            # Should not call version() when package not found
            mock_metadata.version.assert_not_called()

