"""``GET /health`` 与启动状态字段。"""

import dataclasses
import sys
import types

from fastapi.testclient import TestClient

fake_openai_module = types.ModuleType("openai")


class FakeOpenAI:
    def __init__(self, *args, **kwargs) -> None:
        pass


fake_openai_module.OpenAI = FakeOpenAI
sys.modules.setdefault("openai", fake_openai_module)

from app.config.settings import Settings  # noqa: E402
from app.main import app  # noqa: E402
from app.version import API_VERSION  # noqa: E402


def test_health_returns_status_and_flags() -> None:
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["api_version"] == API_VERSION
        assert "metrics_enabled" in data
        assert "agent_read_api_enabled" in data
        assert isinstance(data["metrics_enabled"], bool)
        assert isinstance(data["agent_read_api_enabled"], bool)


def test_health_reflects_read_api_disabled() -> None:
    with TestClient(app) as client:
        prev = getattr(app.state, "settings", None) or Settings.for_tests()
        app.state.settings = dataclasses.replace(
            prev, agent_read_api_enabled=False
        )
        try:
            r = client.get("/health")
            assert r.json()["agent_read_api_enabled"] is False
        finally:
            app.state.settings = prev
