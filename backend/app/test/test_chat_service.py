import importlib
import os
import sys
import types

from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.runtime.runtime_session import RuntimeSession
from app.runtime.transcript_entry import TranscriptEntry
from app.schemas.session_response import SessionResponse
from app.schemas.transcript_response import TranscriptEntryResponse


os.environ.setdefault("OPENAI_API_KEY", "test-api-key")

fake_openai_module = types.ModuleType("openai")


class FakeOpenAI:
    def __init__(self, *args, **kwargs) -> None:
        pass


fake_openai_module.OpenAI = FakeOpenAI
sys.modules.setdefault("openai", fake_openai_module)

chat_service_module = importlib.import_module("app.services.chat_service")
chat_service_module = importlib.reload(chat_service_module)

ChatService = chat_service_module.ChatService
ensure_session_id = chat_service_module.ensure_session_id


class StubAgent:
    def __init__(self, response_text: str) -> None:
        self._response_text = response_text
        self.last_input = None

    def run(self, agent_input):
        self.last_input = agent_input
        return AgentOutput(content=self._response_text, success=True)


class StubAgentFactory:
    def __init__(self, agent: StubAgent) -> None:
        self._agent = agent
        self.create_count = 0
        self._session_store = StubSessionStore()
        self._transcript_store = StubTranscriptStore()

    def create_chat_agent(self):
        self.create_count += 1
        return self._agent

    def get_session_store(self):
        return self._session_store

    def get_transcript_store(self):
        return self._transcript_store


class StubSessionStore:
    def list_sessions(self):
        return [
            {
                "session_id": "session-a",
                "created_at": "2026-04-09T09:00:00",
                "updated_at": "2026-04-09T09:05:00",
                "metadata": {},
            }
        ]


class StubTranscriptStore:
    def __init__(self) -> None:
        self._entries = [
            TranscriptEntry(
                type="agent",
                user_input="你好",
                final_output="你好呀",
                success=True,
                runtime_session=RuntimeSession(
                    session_id="session-a",
                    user_input="你好",
                ),
                timestamp="2026-04-09T09:10:00",
            )
        ]

    def get_entries(self, session_id: str):
        if session_id == "session-a":
            return self._entries
        return []


generated_session_id = ensure_session_id(None)
assert generated_session_id
assert isinstance(generated_session_id, str)

existing_session_id = ensure_session_id("existing-session")
assert existing_session_id == "existing-session"


stub_agent = StubAgent(response_text="mock service response")
stub_factory = StubAgentFactory(agent=stub_agent)
service = ChatService(agent_factory=stub_factory)
assert stub_factory.create_count == 1

agent_output, resolved_session_id = service.chat("你好", None)

assert agent_output.content == "mock service response"
assert resolved_session_id
assert stub_agent.last_input is not None
assert stub_agent.last_input.message == "你好"
assert stub_agent.last_input.session_id == resolved_session_id
assert isinstance(stub_agent.last_input, AgentInput)


fixed_session_id = "fixed-session-id"
agent_output_fixed, resolved_fixed_session_id = service.chat("再来一次", fixed_session_id)

assert agent_output_fixed.content == "mock service response"
assert resolved_fixed_session_id == fixed_session_id
assert stub_agent.last_input is not None
assert stub_agent.last_input.message == "再来一次"
assert stub_agent.last_input.session_id == fixed_session_id

sessions = service.list_sessions()
assert len(sessions) == 1
assert isinstance(sessions[0], SessionResponse)
assert sessions[0].session_id == "session-a"
assert sessions[0].created_at == "2026-04-09T09:00:00"
assert sessions[0].updated_at == "2026-04-09T09:05:00"
assert sessions[0].metadata == {}

transcript_entries = service.get_transcript("session-a")
assert len(transcript_entries) == 1
assert isinstance(transcript_entries[0], TranscriptEntryResponse)
assert transcript_entries[0].user_input == "你好"
assert transcript_entries[0].final_output == "你好呀"
assert transcript_entries[0].runtime_session.session_id == "session-a"

assert service.get_transcript("") == []
assert service.get_transcript("missing-session") == []

print("chat service tests passed")
