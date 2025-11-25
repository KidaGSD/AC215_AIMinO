# Testing Guide for AIMinO

This document describes the testing setup and how to run tests locally and in CI.

## Test Structure

The test suite is organized into three categories:

- **Unit Tests** (`tests/unit/`): Fast, isolated tests with no external dependencies
- **Integration Tests** (`tests/integration/`): Tests with mocked services and dependencies
- **System Tests** (`tests/system/`): End-to-end tests requiring a running API server

## Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock requests

# Or install from pyproject.toml
pip install -e "src/api_service[test]"
```

## Running Tests Locally

### Run All Tests

```bash
# From project root
pytest

# With coverage report
pytest --cov=src/api_service --cov=aimino_frontend/aimino_core --cov-report=html
```

### Run by Category

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# System tests only (requires running API)
pytest -m system
```

### Run Specific Test Files

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run system tests
pytest tests/system/
```

## Running System Tests

System tests require a running API server. You can start one using Docker:

```bash
# Build and run API server
DOCKER_BUILDKIT=1 docker build -t aimino-api:test -f src/api_service/Dockerfile .
docker run --rm -d -p 8000:8000 \
  -e AIMINO_SKIP_STARTUP=1 \
  -e GEMINI_API_KEY=dummy_key_for_testing \
  --name aimino-api \
  aimino-api:test

# Wait for server to be ready
sleep 5

# Run system tests
API_BASE_URL=http://localhost:8000 pytest tests/system/ -v

# Stop server
docker stop aimino-api
```

## Code Coverage

The test suite aims for at least 50% code coverage. Coverage reports are generated in multiple formats:

- **Terminal**: `--cov-report=term-missing`
- **HTML**: `--cov-report=html` (view in `htmlcov/index.html`)
- **XML**: `--cov-report=xml` (for CI integration)

### View Coverage Report

```bash
# Generate HTML report
pytest --cov=src/api_service --cov=aimino_frontend/aimino_core --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

## CI Pipeline

The CI pipeline (`.github/workflows/ci.yml`) automatically:

1. **Lints code** with ruff (if available)
2. **Runs unit tests** across Python 3.10, 3.11, 3.12
3. **Runs integration tests** with mocked dependencies
4. **Builds Docker image** and verifies it works
5. **Runs system tests** against a running container
6. **Generates coverage reports** and uploads to artifacts
7. **Fails if coverage < 50%**

### CI Triggers

- Push to `main`, `master`, or `develop` branches
- Pull requests to `main`, `master`, or `develop` branches

## Test Markers

Tests are marked with pytest markers for categorization:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.system`: System tests
- `@pytest.mark.slow`: Slow-running tests

## Writing New Tests

### Unit Test Example

```python
import pytest
from api_service.api.utils.config import Settings

@pytest.mark.unit
class TestSettings:
    def test_settings_defaults(self):
        settings = Settings()
        assert settings.AIMINO_API_PREFIX == "/api/v1"
```

### Integration Test Example

```python
import pytest
from fastapi.testclient import TestClient
from api_service.api.service import create_app

@pytest.mark.integration
def test_health_endpoint():
    app = create_app()
    with TestClient(app) as client:
        r = client.get("/api/v1/healthz")
        assert r.status_code == 200
```

### System Test Example

```python
import pytest
import requests

@pytest.mark.system
def test_health_check():
    response = requests.get("http://localhost:8000/api/v1/healthz")
    assert response.status_code == 200
```

## Troubleshooting

### Import Errors

If you see import errors, ensure PYTHONPATH is set:

```bash
export PYTHONPATH=$PWD/src:$PWD/aimino_frontend/aimino_core
pytest
```

### Coverage Below 50%

If coverage is below 50%, the tests will fail. To see what's not covered:

```bash
pytest --cov=src/api_service --cov=aimino_frontend/aimino_core --cov-report=term-missing
```

### System Tests Failing

Ensure the API server is running and accessible:

```bash
curl http://localhost:8000/api/v1/healthz
```

## Continuous Integration

The CI pipeline runs automatically on GitHub Actions. Check the Actions tab in your repository to see:

- Build status
- Test results
- Coverage reports
- Docker build status

All artifacts (coverage reports, logs) are available for download from the Actions page.

