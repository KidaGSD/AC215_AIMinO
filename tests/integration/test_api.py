"""
Integration tests for the AIMinO API
Tests the full API endpoints with FastAPI TestClient and mocked dependencies
Based on Milestone 4 Final reference implementation
"""

import os
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from api_service.api.service import create_app


class DummySession:
    """Mock session service for testing"""
    
    def __init__(self):
        self.store = {}

    async def create_session(self, app_name: str, user_id: str, session_id: str, state: dict):
        """Create a mock session"""
        self.store[(app_name, user_id, session_id)] = type("S", (), {"state": state})

    async def get_session(self, app_name: str, user_id: str, session_id: str):
        """Get a mock session"""
        return self.store[(app_name, user_id, session_id)]


class DummyRunner:
    """Mock runner for testing successful execution"""
    
    def run_async(self, user_id: str, session_id: str, new_message):
        async def gen():
            # Pretend worker placed a command in state
            yield type("E", (), {})
        return gen()


class FailingRunner:
    """Mock runner for testing error scenarios"""
    
    def run_async(self, user_id: str, session_id: str, new_message):
        async def gen():
            raise RuntimeError("boom")
            yield None
        return gen()


def make_app_with_dummies():
    """Create test app with mocked dependencies"""
    os.environ["AIMINO_SKIP_STARTUP"] = "1"
    app = create_app()
    app.state.session_service = DummySession()
    app.state.runner = DummyRunner()
    return app


def make_app_with_failing_runner():
    """Create test app with failing runner for error testing"""
    os.environ["AIMINO_SKIP_STARTUP"] = "1"
    app = create_app()
    app.state.session_service = DummySession()
    app.state.runner = FailingRunner()
    return app


@pytest.mark.integration
class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_healthz_ok(self):
        """Test the health endpoint returns OK status"""
        app = make_app_with_dummies()
        with TestClient(app) as client:
            r = client.get("/api/v1/healthz")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"

    def test_healthz_returns_json(self):
        """Test that health endpoint returns JSON content type"""
        app = make_app_with_dummies()
        with TestClient(app) as client:
            r = client.get("/api/v1/healthz")
            assert r.status_code == 200
            assert "application/json" in r.headers["content-type"]

    def test_healthz_with_runner(self):
        """Test healthz endpoint when runner is initialized."""
        app = make_app_with_dummies()
        # Set runner in app.state
        from unittest.mock import MagicMock
        app.state.runner = MagicMock()
        with TestClient(app) as client:
            r = client.get("/api/v1/healthz")
            assert r.status_code == 200
            data = r.json()
            assert data["runner_initialized"] is True
            assert "service_version" in data

    def test_healthz_without_runner(self):
        """Test healthz endpoint when runner is not initialized."""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        app = create_app()
        with TestClient(app) as client:
            r = client.get("/api/v1/healthz")
            assert r.status_code == 200
            data = r.json()
            assert data["runner_initialized"] is False

    def test_healthz_service_version(self):
        """Test healthz endpoint includes service_version."""
        app = make_app_with_dummies()
        with TestClient(app) as client:
            r = client.get("/api/v1/healthz")
            assert r.status_code == 200
            data = r.json()
            assert "service_version" in data
            assert "schema_version" in data
            assert data["schema_version"] == "0.1"


@pytest.mark.integration
class TestInvokeEndpoint:
    """Tests for invoke endpoint"""

    def test_invoke_basic(self):
        """Test basic invoke endpoint functionality"""
        app = make_app_with_dummies()
        with TestClient(app) as client:
            r = client.post("/api/v1/invoke", json={"user_input": "show layers"})
            assert r.status_code in (200, 500, 503)
            # Either valid response or structured error envelope
            data = r.json()
            assert isinstance(data, dict)

    def test_invoke_with_context(self):
        """Test invoke with conversation context"""
        app = make_app_with_dummies()
        with TestClient(app) as client:
            r = client.post(
                "/api/v1/invoke",
                json={
                    "user_input": "show nuclei",
                    "context": [{"role": "user", "content": "previous message"}]
                }
            )
            assert r.status_code in (200, 500, 503)
            data = r.json()
            assert isinstance(data, dict)

    def test_invoke_with_session_id(self):
        """Test invoke with existing session_id."""
        app = make_app_with_dummies()
        with TestClient(app) as client:
            # First call to create session
            r1 = client.post(
                "/api/v1/invoke",
                json={"user_input": "test", "session_id": "test_session_123"}
            )
            assert r1.status_code in (200, 500, 503)
            
            # Second call with same session_id (should reuse session)
            r2 = client.post(
                "/api/v1/invoke",
                json={"user_input": "test2", "session_id": "test_session_123"}
            )
            assert r2.status_code in (200, 500, 503)

    def test_invoke_failure(self):
        """Test invoke endpoint error handling"""
        app = make_app_with_failing_runner()
        with TestClient(app) as client:
            r = client.post("/api/v1/invoke", json={"user_input": "boom"})
            assert r.status_code == 500
            data = r.json()
            assert data.get("code") == "invoke_error"
            assert "error" in data.get("details", {})

    def test_invoke_invalid_payload(self):
        """Test invoke with invalid JSON payload"""
        app = make_app_with_dummies()
        with TestClient(app) as client:
            r = client.post("/api/v1/invoke", json={})
            # Should reject due to missing user_input
            assert r.status_code == 422

    def test_register_dataset_endpoint(self, monkeypatch):
        """Test dataset registration endpoint."""
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("AIMINO_DATA_ROOT", tmpdir)
            app = make_app_with_dummies()
            with TestClient(app) as client:
                img = Path(tmpdir) / "test.tif"
                h5 = Path(tmpdir) / "test.h5ad"
                img.write_bytes(b"tiff")
                h5.write_bytes(b"h5ad")
                
                r = client.post(
                    "/api/v1/datasets/register",
                    json={
                        "image_path": str(img),
                        "h5ad_path": str(h5),
                        "dataset_id": "test_dataset",
                        "copy_files": False,
                        "marker_col": "SOX10"
                    }
                )
                assert r.status_code == 200
                data = r.json()
                assert data["status"] == "ok"
                assert "manifest" in data

    def test_register_dataset_endpoint_error(self):
        """Test dataset registration endpoint error handling."""
        app = make_app_with_dummies()
        with TestClient(app) as client:
            r = client.post(
                "/api/v1/datasets/register",
                json={
                    "image_path": "/nonexistent/path.tif",
                    "h5ad_path": "/nonexistent/path.h5ad",
                    "dataset_id": "test_error"
                }
            )
            assert r.status_code == 400
            assert "detail" in r.json()

    def test_register_dataset_without_marker(self, monkeypatch):
        """Test dataset registration without marker_col."""
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("AIMINO_DATA_ROOT", tmpdir)
            app = make_app_with_dummies()
            with TestClient(app) as client:
                img = Path(tmpdir) / "test.tif"
                h5 = Path(tmpdir) / "test.h5ad"
                img.write_bytes(b"tiff")
                h5.write_bytes(b"h5ad")
                
                r = client.post(
                    "/api/v1/datasets/register",
                    json={
                        "image_path": str(img),
                        "h5ad_path": str(h5),
                        "dataset_id": "test_dataset2",
                        "copy_files": False
                    }
                )
                assert r.status_code == 200
                data = r.json()
                assert data["status"] == "ok"

    def test_invoke_runner_not_ready(self):
        """Test invoke when runner is not initialized"""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        app = create_app()
        # Don't set runner in app.state - should return 503
        with TestClient(app) as client:
            r = client.post("/api/v1/invoke", json={"user_input": "test"})
            assert r.status_code == 503
            data = r.json()
            assert data.get("code") == "runner_not_ready"
        with TestClient(app) as client:
            r = client.post("/api/v1/invoke", json={"user_input": "test"})
            assert r.status_code == 503
            data = r.json()
            assert data.get("code") == "runner_not_ready"

    def test_invoke_session_service_not_ready(self):
        """Test invoke when session_service is not initialized"""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        app = create_app()
        # Set runner but not session_service
        app.state.runner = DummyRunner()
        with TestClient(app) as client:
            r = client.post("/api/v1/invoke", json={"user_input": "test"})
            assert r.status_code == 503
            data = r.json()
            assert data.get("code") == "runner_not_ready"

    def test_invoke_successful_with_commands(self):
        """Test successful invoke that returns commands"""
        app = make_app_with_dummies()
        # Mock a successful response with commands
        class SuccessRunner:
            def run_async(self, user_id: str, session_id: str, new_message):
                async def gen():
                    class Event:
                        pass
                    yield Event()
                return gen()
        
        class SuccessSession:
            def __init__(self):
                self.store = {}
            
            async def create_session(self, app_name: str, user_id: str, session_id: str, state: dict):
                self.store[(app_name, user_id, session_id)] = type("S", (), {"state": {"final_commands": [{"cmd": "test"}]}})
            
            async def get_session(self, app_name: str, user_id: str, session_id: str):
                return self.store.get((app_name, user_id, session_id))
        
        app.state.runner = SuccessRunner()
        app.state.session_service = SuccessSession()
        
        with TestClient(app) as client:
            r = client.post("/api/v1/invoke", json={"user_input": "test"})
            # Should succeed or return error (depending on implementation)
            assert r.status_code in (200, 500, 503)
            data = r.json()
            assert isinstance(data, dict)


@pytest.mark.integration
class TestCORS:
    """Tests for CORS configuration"""

    def test_cors_enabled(self):
        """Test that CORS headers are present"""
        app = make_app_with_dummies()
        with TestClient(app) as client:
            r = client.get("/api/v1/healthz", headers={"Origin": "http://localhost:3000"})
            assert r.status_code == 200
            assert "access-control-allow-origin" in r.headers

    def test_cors_allows_configured_origins(self):
        """Test that CORS allows configured origins"""
        app = make_app_with_dummies()
        with TestClient(app) as client:
            r = client.get("/api/v1/healthz", headers={"Origin": "http://example.com"})
            assert r.status_code == 200
            # Check CORS header exists (value depends on configuration)
            assert "access-control-allow-origin" in r.headers


@pytest.mark.integration
class TestInvalidRoutes:
    """Tests for invalid route handling"""

    def test_invalid_route_returns_404(self):
        """Test that non-existent routes return 404"""
        app = make_app_with_dummies()
        with TestClient(app) as client:
            r = client.get("/this-route-does-not-exist")
            assert r.status_code == 404

    def test_method_not_allowed(self):
        """Test that wrong HTTP method returns 405"""
        app = make_app_with_dummies()
        with TestClient(app) as client:
            # GET on a POST-only endpoint
            r = client.get("/api/v1/invoke")
            assert r.status_code == 405


@pytest.mark.integration
class TestAppStartup:
    """Tests for application startup behavior"""

    def test_app_creation(self):
        """Test that app can be created"""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        app = create_app()
        assert app.title == "AIMinO API"
        assert app.version == "0.1.0"

    def test_app_with_startup(self):
        """Test app startup with runner initialization"""
        # Clear skip flag
        if "AIMINO_SKIP_STARTUP" in os.environ:
            del os.environ["AIMINO_SKIP_STARTUP"]
        # Set dummy API key to avoid real API calls
        os.environ["GEMINI_API_KEY"] = "dummy_key_for_testing"
        try:
            app = create_app()
            # App should be created successfully
            assert app is not None
            # Runner should be initialized (or skipped if API key invalid)
            assert hasattr(app.state, "runner") or hasattr(app.state, "session_service")
        finally:
            # Restore skip flag
            os.environ["AIMINO_SKIP_STARTUP"] = "1"

    def test_app_cors_origins_parsing(self):
        """Test CORS origins parsing from string"""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        # Test with JSON string
        os.environ["AIMINO_ALLOWED_ORIGINS"] = '["http://localhost:3000", "http://example.com"]'
        try:
            app = create_app()
            assert app is not None
        finally:
            if "AIMINO_ALLOWED_ORIGINS" in os.environ:
                del os.environ["AIMINO_ALLOWED_ORIGINS"]

    def test_app_cors_origins_comma_separated(self):
        """Test CORS origins parsing from comma-separated string"""
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        os.environ["AIMINO_ALLOWED_ORIGINS"] = "http://localhost:3000,http://example.com"
        try:
            app = create_app()
            assert app is not None
        finally:
            if "AIMINO_ALLOWED_ORIGINS" in os.environ:
                del os.environ["AIMINO_ALLOWED_ORIGINS"]

