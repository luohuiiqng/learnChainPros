import sys
import types

from fastapi.testclient import TestClient

fake_openai_module = types.ModuleType("openai")


class FakeOpenAI:
    def __init__(self, *args, **kwargs) -> None:
        pass


fake_openai_module.OpenAI = FakeOpenAI
sys.modules.setdefault("openai", fake_openai_module)

from app.main import app
from app.routes import chat as chat_route
from app.schemas.agent_output import AgentOutput


class StubChatService:
    def __init__(self) -> None:
        self.calls: list[dict[str, str | None]] = []

    def chat(self, message: str, session_id: str | None):
        self.calls.append({"message": message, "session_id": session_id})
        return AgentOutput(content="mock route reply", success=True), "route-session-id"


class StubErrorChatService:
    def chat(self, message: str, session_id: str | None):
        return AgentOutput(
            content="",
            success=False,
            error_message="mock route error",
        ), "route-error-session-id"


client = TestClient(app)

original_chat_service = chat_route.chat_service

try:
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
    assert stub_service.calls == [
        {"message": "你好", "session_id": "input-session-id"}
    ]

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
finally:
    chat_route.chat_service = original_chat_service


print("chat route tests passed")
