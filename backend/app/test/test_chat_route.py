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
from app.runtime.runtime_session import RuntimeSession
from app.runtime.transcript_entry import TranscriptEntry
from app.schemas.session_response import SessionResponse
from app.schemas.transcript_response import TranscriptEntryResponse


class StubChatService:
    def __init__(self) -> None:
        self.calls: list[dict[str, str | None]] = []
        self.session_queries = 0
        self.transcript_queries: list[str] = []

    def chat(self, message: str, session_id: str | None):
        self.calls.append({"message": message, "session_id": session_id})
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

    sessions_response = client.get("/agent_api/sessions")
    assert sessions_response.status_code == 200
    sessions_data = sessions_response.json()
    assert len(sessions_data) == 1
    assert sessions_data[0]["session_id"] == "route-session-id"
    assert sessions_data[0]["created_at"] == "2026-04-09T10:00:00"
    assert sessions_data[0]["updated_at"] == "2026-04-09T10:05:00"
    assert sessions_data[0]["metadata"] == {}
    assert stub_service.session_queries == 1

    transcript_response = client.get("/agent_api/sessions/route-session-id/transcript")
    assert transcript_response.status_code == 200
    transcript_data = transcript_response.json()
    assert len(transcript_data) == 1
    assert transcript_data[0]["type"] == "agent"
    assert transcript_data[0]["user_input"] == "你好"
    assert transcript_data[0]["final_output"] == "mock route reply"
    assert transcript_data[0]["runtime_session"]["session_id"] == "route-session-id"
    assert stub_service.transcript_queries == ["route-session-id"]

    missing_transcript_response = client.get("/agent_api/sessions/missing/transcript")
    assert missing_transcript_response.status_code == 200
    assert missing_transcript_response.json() == []
    assert stub_service.transcript_queries == ["route-session-id", "missing"]

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
