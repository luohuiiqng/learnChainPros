import dataclasses
import sys
import types
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

fake_openai_module = types.ModuleType("openai")


class FakeOpenAI:
    def __init__(self, *args, **kwargs) -> None:
        pass


fake_openai_module.OpenAI = FakeOpenAI
sys.modules.setdefault("openai", fake_openai_module)

from app.config.settings import Settings  # noqa: E402
from app.main import app  # noqa: E402
from app.routes import chat as chat_route  # noqa: E402
from app.schemas.agent_output import AgentOutput  # noqa: E402
from app.runtime.runtime_session import RuntimeSession  # noqa: E402
from app.runtime.transcript_entry import TranscriptEntry  # noqa: E402
from app.schemas.session_response import SessionResponse  # noqa: E402
from app.schemas.transcript_response import TranscriptEntryResponse  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class StubChatService:
    def __init__(self) -> None:
        self.calls: list[dict[str, str | None]] = []
        self.session_queries = 0
        self.session_get_queries: list[str] = []
        self.transcript_queries: list[str] = []

    def chat(self, message: str, session_id: str | None = None, **kwargs):
        self.calls.append(
            {
                "message": message,
                "session_id": session_id,
                "request_id": kwargs.get("request_id"),
            }
        )
        return AgentOutput(content="mock route reply", success=True), "route-session-id"

    def list_sessions(self):
        self.session_queries += 1
        return [
            SessionResponse(
                session_id="route-session-id",
                created_at="2026-04-09T10:00:00",
                updated_at="2026-04-09T10:05:00",
                metadata={},
            )
        ]

    def get_session(self, session_id: str):
        self.session_get_queries.append(session_id)
        if session_id == "route-session-id":
            return SessionResponse(
                session_id="route-session-id",
                created_at="2026-04-09T10:00:00",
                updated_at="2026-04-09T10:05:00",
                metadata={},
            )
        return None

    def get_transcript(self, session_id: str):
        self.transcript_queries.append(session_id)
        if session_id == "route-session-id":
            entry = TranscriptEntry(
                type="agent",
                user_input="你好",
                final_output="mock route reply",
                success=True,
                runtime_session=RuntimeSession(
                    session_id="route-session-id",
                    user_input="你好",
                ),
                timestamp="2026-04-09T10:06:00",
            )
            return [TranscriptEntryResponse.from_transcript_entry(entry)]
        return []

    def get_latest_runtime_markdown(self, session_id: str):
        self.transcript_queries.append(f"md:{session_id}")
        if session_id == "route-session-id":
            return "# RuntimeSession 导出\n\n- **session_id**: `route-session-id`\n"
        return None

    def get_runtime_markdown_at(self, session_id: str, entry_index: int) -> str | None:
        self.transcript_queries.append(f"md_at:{session_id}:{entry_index}")
        if session_id == "route-session-id" and entry_index == 0:
            return "# RuntimeSession 导出 idx0\n"
        return None


class StubErrorChatService:
    def chat(self, message: str, session_id: str | None = None, **kwargs):
        return (
            AgentOutput(
                content="",
                success=False,
                error_message="mock route error",
            ),
            "route-error-session-id",
        )


class StubRaiseChatService:
    def chat(self, message: str, session_id: str | None = None, **kwargs):
        raise RuntimeError("chat boom")


@pytest.fixture(autouse=True)
def restore_chat_service():
    original = chat_route.chat_service
    yield
    chat_route.chat_service = original


def test_chat_post_strips_and_forwards_session(client: TestClient) -> None:
    stub_service = StubChatService()
    chat_route.chat_service = stub_service
    response = client.post(
        "/agent_api/chat",
        json={"message": "  你好  ", "session_id": "input-session-id"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "mock route reply"
    assert data["session_id"] == "route-session-id"
    assert data["timestamp"]
    assert stub_service.calls[0]["message"] == "你好"
    assert stub_service.calls[0]["session_id"] == "input-session-id"
    rid = stub_service.calls[0]["request_id"]
    assert rid
    assert data.get("request_id") == rid
    assert response.headers.get("X-Request-ID") == rid


def test_chat_echoes_client_x_request_id(client: TestClient) -> None:
    stub_service = StubChatService()
    chat_route.chat_service = stub_service
    response = client.post(
        "/agent_api/chat",
        json={"message": "hi", "session_id": None},
        headers={"X-Request-ID": "client-rid-abc"},
    )
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "client-rid-abc"
    assert response.json()["request_id"] == "client-rid-abc"
    assert stub_service.calls[0]["request_id"] == "client-rid-abc"


def test_read_api_disabled_returns_403_on_get_not_post(client: TestClient) -> None:
    """关闭 ``agent_read_api_enabled`` 时，只读 GET 返回 403，``POST /chat`` 仍可用。"""
    stub_service = StubChatService()
    chat_route.chat_service = stub_service
    base = getattr(app.state, "settings", None) or Settings.for_tests()
    app.state.settings = dataclasses.replace(base, agent_read_api_enabled=False)
    try:
        assert client.get("/agent_api/sessions").status_code == 403
        err = client.get("/agent_api/sessions").json()
        assert err["error"]["code"] == "FORBIDDEN"
        assert client.get("/agent_api/sessions/any-id").status_code == 403
        assert client.get("/agent_api/sessions/any/transcript").status_code == 403
        assert (
            client.get("/agent_api/sessions/any/transcript/latest/markdown").status_code
            == 403
        )
        assert client.get("/agent_api/sessions/any/transcript/0/markdown").status_code == 403
        post = client.post(
            "/agent_api/chat", json={"message": "hi", "session_id": None}
        )
        assert post.status_code == 200
        assert post.json()["reply"] == "mock route reply"
    finally:
        app.state.settings = base


def test_chat_list_sessions(client: TestClient) -> None:
    stub_service = StubChatService()
    chat_route.chat_service = stub_service
    sessions_response = client.get("/agent_api/sessions")
    assert sessions_response.status_code == 200
    sessions_data = sessions_response.json()
    assert len(sessions_data) == 1
    assert sessions_data[0]["session_id"] == "route-session-id"
    assert stub_service.session_queries == 1


def test_chat_get_session_found_and_not_found(client: TestClient) -> None:
    stub_service = StubChatService()
    chat_route.chat_service = stub_service
    ok = client.get("/agent_api/sessions/route-session-id")
    assert ok.status_code == 200
    assert ok.json()["session_id"] == "route-session-id"
    assert stub_service.session_get_queries == ["route-session-id"]

    missing = client.get("/agent_api/sessions/missing-id")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"
    assert stub_service.session_get_queries == ["route-session-id", "missing-id"]


def test_chat_get_latest_runtime_markdown(client: TestClient) -> None:
    stub_service = StubChatService()
    chat_route.chat_service = stub_service
    md_response = client.get(
        "/agent_api/sessions/route-session-id/transcript/latest/markdown"
    )
    assert md_response.status_code == 200
    assert md_response.headers.get("content-type", "").startswith("text/markdown")
    assert "RuntimeSession" in md_response.text
    assert "md:route-session-id" in stub_service.transcript_queries

    missing_md = client.get("/agent_api/sessions/missing/transcript/latest/markdown")
    assert missing_md.status_code == 404
    assert missing_md.json()["error"]["code"] == "NOT_FOUND"


def test_chat_get_runtime_markdown_by_index(client: TestClient) -> None:
    stub_service = StubChatService()
    chat_route.chat_service = stub_service
    ok = client.get("/agent_api/sessions/route-session-id/transcript/0/markdown")
    assert ok.status_code == 200
    assert "idx0" in ok.text
    assert "md_at:route-session-id:0" in stub_service.transcript_queries

    missing_idx = client.get("/agent_api/sessions/route-session-id/transcript/1/markdown")
    assert missing_idx.status_code == 404
    assert missing_idx.json()["error"]["code"] == "NOT_FOUND"

    bad_neg = client.get("/agent_api/sessions/route-session-id/transcript/-1/markdown")
    assert bad_neg.status_code == 422


def test_chat_get_transcript_and_missing(client: TestClient) -> None:
    stub_service = StubChatService()
    chat_route.chat_service = stub_service
    transcript_response = client.get("/agent_api/sessions/route-session-id/transcript")
    assert transcript_response.status_code == 200
    transcript_data = transcript_response.json()
    assert len(transcript_data) == 1
    assert transcript_data[0]["type"] == "agent"
    assert stub_service.transcript_queries == ["route-session-id"]

    missing_transcript_response = client.get("/agent_api/sessions/missing/transcript")
    assert missing_transcript_response.status_code == 200
    assert missing_transcript_response.json() == []
    assert stub_service.transcript_queries == ["route-session-id", "missing"]


def test_chat_validation_empty_and_long_message(client: TestClient) -> None:
    stub_service = StubChatService()
    chat_route.chat_service = stub_service
    empty_response = client.post(
        "/agent_api/chat",
        json={"message": "   ", "session_id": "input-session-id"},
    )
    assert empty_response.status_code == 400
    assert empty_response.json()["error"]["code"] == "BAD_REQUEST"
    assert empty_response.json()["error"]["message"] == "message不能为空"

    long_response = client.post(
        "/agent_api/chat",
        json={"message": "a" * 2001, "session_id": "input-session-id"},
    )
    assert long_response.status_code == 400
    assert long_response.json()["error"]["code"] == "BAD_REQUEST"
    assert long_response.json()["error"]["message"] == "message长度不能超过2000"


def test_chat_agent_error_surfaces_as_reply(client: TestClient) -> None:
    chat_route.chat_service = StubErrorChatService()
    error_response = client.post(
        "/agent_api/chat",
        json={"message": "你好", "session_id": "input-session-id"},
    )
    assert error_response.status_code == 200
    error_data = error_response.json()
    assert error_data["reply"] == "mock route error"
    assert error_data["session_id"] == "route-error-session-id"
    assert error_data["timestamp"]


def test_chat_service_exception_logs_chat_failed() -> None:
    chat_route.chat_service = StubRaiseChatService()
    with patch("app.routes.chat._chat_log") as mock_log:
        with TestClient(app, raise_server_exceptions=False) as exc_client:
            exc_client.post(
                "/agent_api/chat",
                json={"message": "hi", "session_id": "input-session-id"},
            )
        mock_log.error.assert_called_once()
        assert mock_log.error.call_args[0][0] == "chat_failed"


def test_chat_service_exception_observes_chat_completion_error() -> None:
    e0 = REGISTRY.get_sample_value(
        "lcp_chat_completions_total", {"outcome": "error"}
    )
    e0 = 0.0 if e0 is None else float(e0)
    chat_route.chat_service = StubRaiseChatService()
    with TestClient(app, raise_server_exceptions=False) as exc_client:
        response = exc_client.post(
            "/agent_api/chat",
            json={"message": "hi", "session_id": "input-session-id"},
        )
    assert response.status_code == 500
    e1 = REGISTRY.get_sample_value(
        "lcp_chat_completions_total", {"outcome": "error"}
    )
    assert float(e1 or 0.0) == e0 + 1.0
