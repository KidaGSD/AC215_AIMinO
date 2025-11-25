"""
System/End-to-End tests for AIMinO API
Tests the actual API endpoints with HTTP requests against a running server
Based on Milestone 4 Final reference implementation
"""

import pytest
import requests
import time
import os


# Base URL for the API - uses environment variable for docker-compose
# In docker-compose test network, use service name: http://api_service:8000
# For local testing against localhost, use: http://localhost:8000
API_BASE_URL = os.getenv("API_BASE_URL", "http://api_service:8000")


def is_api_running():
    """Check if API is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/healthz", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


@pytest.mark.system
@pytest.mark.skipif(not is_api_running(), reason=f"API not running at {API_BASE_URL}")
class TestAPIEndpoints:
    """System tests for API endpoints with running server"""

    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f"{API_BASE_URL}/api/v1/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_check_response_time(self):
        """Test that health check responds quickly"""
        response = requests.get(f"{API_BASE_URL}/api/v1/healthz")
        assert response.status_code == 200
        # Should respond in less than 1 second
        assert response.elapsed.total_seconds() < 1.0

    def test_invoke_endpoint_basic(self):
        """Test basic invoke endpoint functionality"""
        response = requests.post(
            f"{API_BASE_URL}/api/v1/invoke",
            json={"user_input": "show layers"},
            timeout=10
        )
        assert response.status_code in (200, 500, 503)
        data = response.json()
        assert isinstance(data, dict)

    def test_invoke_endpoint_with_context(self):
        """Test invoke with conversation context"""
        response = requests.post(
            f"{API_BASE_URL}/api/v1/invoke",
            json={
                "user_input": "show nuclei layer",
                "context": [{"role": "user", "content": "previous message"}]
            },
            timeout=10
        )
        assert response.status_code in (200, 500, 503)
        data = response.json()
        assert isinstance(data, dict)

    def test_invalid_endpoint_returns_404(self):
        """Test that invalid endpoints return 404"""
        response = requests.get(f"{API_BASE_URL}/api/v1/nonexistent")
        assert response.status_code == 404

    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses"""
        response = requests.get(
            f"{API_BASE_URL}/api/v1/healthz",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


@pytest.mark.system
@pytest.mark.skipif(not is_api_running(), reason=f"API not running at {API_BASE_URL}")
class TestAPILoad:
    """Basic load testing for API"""

    def test_multiple_health_checks(self):
        """Test that API can handle multiple rapid health checks"""
        results = []
        for _ in range(10):
            response = requests.get(f"{API_BASE_URL}/api/v1/healthz", timeout=2)
            results.append(response.status_code)
        
        # All requests should succeed
        assert all(status == 200 for status in results)


# Standalone tests that don't require running API
@pytest.mark.system
class TestAPIWithoutServer:
    """Tests that can run without a live server"""

    def test_api_module_structure(self):
        """Test that we can import the API module"""
        from api_service.api.service import create_app
        
        app = create_app()
        assert app.title == "AIMinO API"
        assert app.version == "0.1.0"

    def test_api_routes_configured(self):
        """Test that expected routes are configured"""
        import os
        os.environ["AIMINO_SKIP_STARTUP"] = "1"
        
        from api_service.api.service import create_app
        
        app = create_app()
        routes = [route.path for route in app.routes]
        
        # Check that key routes exist
        assert any("/api/v1/healthz" in route for route in routes)
        assert any("/api/v1/invoke" in route for route in routes)

