from app.agent.chat_agent import ChatAgent
from app.models.mock_model import MockModel
from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.runtime_manager import RuntimeManager
from app.runtime.runtime_session import RuntimeSession
from app.runtime.transcript_entry import TranscriptEntry
from app.schemas.agent_input import AgentInput


def test_chat_agent_persists_session_and_transcript_when_session_id_set() -> None:
    model = MockModel(response_text="mock session response")
    session_store = InMemorySessionStore()
    transcript_store = InMemoryTranscriptStore()
    runtime_manager = RuntimeManager(
        session_store=session_store,
        transcript_store=transcript_store,
    )
    chat_agent = ChatAgent(runtime_manager=runtime_manager, model=model)

    session_id = "pytest-chat-agent-session-store-1"
    agent_output = chat_agent.run(AgentInput(message="你好", session_id=session_id))

    session = session_store.get_session(session_id)
    assert session is not None
    assert session["session_id"] == session_id
    assert session["created_at"]
    assert session["updated_at"]
    assert session["metadata"] == {}

    entries = transcript_store.get_entries(session_id)
    assert len(entries) == 1
    entry = entries[0]
    assert isinstance(entry, TranscriptEntry)
    assert entry.type == "agent"
    assert entry.user_input == "你好"
    assert entry.final_output == agent_output.content
    assert entry.success == agent_output.success
    assert entry.timestamp
    assert isinstance(entry.runtime_session, RuntimeSession)
    assert entry.runtime_session.session_id == session_id


def test_chat_agent_no_session_row_when_session_id_none() -> None:
    model = MockModel(response_text="mock sessionless response")
    session_store = InMemorySessionStore()
    transcript_store = InMemoryTranscriptStore()
    runtime_manager = RuntimeManager(
        session_store=session_store,
        transcript_store=transcript_store,
    )
    agent = ChatAgent(runtime_manager=runtime_manager, model=model)

    sessionless_output = agent.run(AgentInput(message="你好", session_id=None))
    assert sessionless_output.success is True
    assert session_store.list_sessions() == []
