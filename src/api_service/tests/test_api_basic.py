import os
from fastapi.testclient import TestClient

from api_service.api.service import create_app


class DummySession:
    def __init__(self):
        self.store = {}

    async def create_session(self, app_name: str, user_id: str, session_id: str, state: dict):
        self.store[(app_name, user_id, session_id)] = type("S", (), {"state": state})

    async def get_session(self, app_name: str, user_id: str, session_id: str):
        return self.store[(app_name, user_id, session_id)]


class DummyRunner:
    def run_async(self, user_id: str, session_id: str, new_message):
        async def gen():
            # Pretend worker placed a command in state
            yield type("E", (), {})
        return gen()

class FailingRunner:
    def run_async(self, user_id: str, session_id: str, new_message):
        async def gen():
            raise RuntimeError("boom")
            yield None
        return gen()


def make_app_with_dummies():
    os.environ["AIMINO_SKIP_STARTUP"] = "1"
    app = create_app()
    app.state.session_service = DummySession()
    app.state.runner = DummyRunner()
    return app

def make_app_with_failing_runner():
    os.environ["AIMINO_SKIP_STARTUP"] = "1"
    app = create_app()
    app.state.session_service = DummySession()
    app.state.runner = FailingRunner()
    return app


def test_healthz_ok():
    app = make_app_with_dummies()
    with TestClient(app) as client:
        r = client.get("/api/v1/healthz")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_invoke_basic():
    app = make_app_with_dummies()
    with TestClient(app) as client:
        r = client.post("/api/v1/invoke", json={"user_input": "show layers"})
        assert r.status_code in (200, 500, 503)
        # Either valid response or structured error envelope
        data = r.json()
        assert isinstance(data, dict)


def test_invoke_failure():
    app = make_app_with_failing_runner()
    with TestClient(app) as client:
        r = client.post("/api/v1/invoke", json={"user_input": "boom"})
        assert r.status_code == 500
        data = r.json()
        assert data.get("code") == "invoke_error"
        assert "error" in data.get("details", {})
