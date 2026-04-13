import importlib
import os
import sys
import types

import pytest

from app.config.settings import Settings
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.runtime.runtime_session import RuntimeSession
from app.runtime.transcript_entry import TranscriptEntry
from app.schemas.session_response import SessionResponse
from app.schemas.transcript_response import TranscriptEntryResponse


@pytest.fixture(scope="module")
def chat_service_module():
    os.environ.setdefault("OPENAI_API_KEY", "test-api-key")
    fake_openai_module = types.ModuleType("openai")

    class FakeOpenAI:
        def __init__(self, *args, **kwargs) -> None:
            pass

    fake_openai_module.OpenAI = FakeOpenAI
    sys.modules.setdefault("openai", fake_openai_module)
    mod = importlib.import_module("app.services.chat_service")
    mod = importlib.reload(mod)
    return mod


def test_ensure_session_id(chat_service_module) -> None:
    ensure_session_id = chat_service_module.ensure_session_id
    generated_session_id = ensure_session_id(None)
    assert generated_session_id
    assert isinstance(generated_session_id, str)
    assert ensure_session_id("existing-session") == "existing-session"


def test_chat_service_roundtrip(chat_service_module) -> None:
    ChatService = chat_service_module.ChatService

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

        def create_chat_agent(self, settings=None, **kwargs):
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

        def get_session(self, session_id: str):
            if session_id == "session-a":
                return {
                    "session_id": "session-a",
                    "created_at": "2026-04-09T09:00:00",
                    "updated_at": "2026-04-09T09:05:00",
                    "metadata": {},
                }
            return None

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
                ),
                TranscriptEntry(
                    type="agent",
                    user_input="第二条",
                    final_output="回二",
                    success=True,
                    runtime_session=RuntimeSession(
                        session_id="session-a",
                        user_input="第二条",
                    ),
                    timestamp="2026-04-09T09:11:00",
                ),
            ]

        def get_entries(self, session_id: str):
            if session_id == "session-a":
                return self._entries
            return []

    stub_agent = StubAgent(response_text="mock service response")
    stub_factory = StubAgentFactory(agent=stub_agent)
    service = ChatService(settings=Settings.for_tests(), agent_factory=stub_factory)
    assert stub_factory.create_count == 1

    agent_output, resolved_session_id = service.chat("你好", None)
    assert agent_output.content == "mock service response"
    assert resolved_session_id
    assert stub_agent.last_input is not None
    assert stub_agent.last_input.message == "你好"
    assert stub_agent.last_input.session_id == resolved_session_id
    assert isinstance(stub_agent.last_input, AgentInput)

    agent_output_fixed, resolved_fixed_session_id = service.chat("再来一次", "fixed-session-id")
    assert agent_output_fixed.content == "mock service response"
    assert resolved_fixed_session_id == "fixed-session-id"
    assert stub_agent.last_input.message == "再来一次"

    sessions = service.list_sessions()
    assert len(sessions) == 1
    assert isinstance(sessions[0], SessionResponse)
    assert sessions[0].session_id == "session-a"
    assert sessions[0].created_at == "2026-04-09T09:00:00"
    assert sessions[0].updated_at == "2026-04-09T09:05:00"
    assert sessions[0].metadata == {}

    one = service.get_session("session-a")
    assert one is not None
    assert one.session_id == "session-a"
    assert service.get_session("missing") is None
    assert service.get_session("") is None
    assert service.get_session("   ") is None

    transcript_entries = service.get_transcript("session-a")
    assert len(transcript_entries) == 2
    assert isinstance(transcript_entries[0], TranscriptEntryResponse)
    assert transcript_entries[0].user_input == "你好"
    assert transcript_entries[0].final_output == "你好呀"
    assert transcript_entries[0].runtime_session.session_id == "session-a"
    assert transcript_entries[1].user_input == "第二条"

    assert service.get_transcript("") == []
    assert service.get_transcript("missing-session") == []

    md = service.get_latest_runtime_markdown("session-a")
    assert md is not None
    assert "RuntimeSession" in md
    md0 = service.get_runtime_markdown_at("session-a", 0)
    md1 = service.get_runtime_markdown_at("session-a", 1)
    assert md0 is not None and md1 is not None
    assert "你好" in md0 and "第二条" in md1
    assert service.get_runtime_markdown_at("session-a", 2) is None
    assert service.get_runtime_markdown_at("session-a", -1) is None
    assert service.get_latest_runtime_markdown("missing-session") is None
    assert service.get_latest_runtime_markdown("") is None
