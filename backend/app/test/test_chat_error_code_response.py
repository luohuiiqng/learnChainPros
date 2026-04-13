"""POST /agent_api/chat 响应体携带 ``error_code``（契约回归）。"""

import sys
import types

import pytest
from fastapi.testclient import TestClient

fake_openai_module = types.ModuleType("openai")


class FakeOpenAI:
    def __init__(self, *args, **kwargs) -> None:
        pass


fake_openai_module.OpenAI = FakeOpenAI
sys.modules.setdefault("openai", fake_openai_module)

from app.main import app  # noqa: E402
from app.routes import chat as chat_route
from app.schemas.agent_output import AgentOutput
from app.schemas.error_codes import ErrorCode


@pytest.fixture(autouse=True)
def restore_chat_service():
    original = chat_route.chat_service
    yield
    chat_route.chat_service = original


class _StubWorkflowNotRegistered:
    def chat(self, message: str, session_id: str | None = None, **kwargs):
        msg = "未注册的工作流: demo"
        return (
            AgentOutput(
                content=msg,
                success=False,
                error_message=msg,
                error_code=ErrorCode.WORKFLOW_NOT_REGISTERED,
            ),
            "session-contract-1",
        )


def test_chat_response_includes_error_code_on_logical_failure() -> None:
    chat_route.chat_service = _StubWorkflowNotRegistered()
    with TestClient(app, raise_server_exceptions=False) as client:
        r = client.post(
            "/agent_api/chat",
            json={"message": "hi", "session_id": None},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["error_code"] == ErrorCode.WORKFLOW_NOT_REGISTERED
    assert "未注册" in (data.get("reply") or "")
