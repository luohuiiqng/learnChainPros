from app.agent.chat_agent import ChatAgent
from app.models.mock_model import MockModel
from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.runtime_session import RuntimeSession
from app.schemas.agent_input import AgentInput


model = MockModel(response_text="mock session response")
session_store = InMemorySessionStore()
transcript_store = InMemoryTranscriptStore()

chat_agent = ChatAgent(
    model=model,
    session_store=session_store,
    transcript_store=transcript_store,
)

session_id = "chat-agent-session-store"
agent_output = chat_agent.run(AgentInput(message="你好", session_id=session_id))

session = session_store.get_session(session_id)
assert session is not None
assert session["session_id"] == session_id
assert session["created_at"]
assert session["updated_at"]
assert session["metadata"]["agent_type"] == "chat"

entries = transcript_store.get_entries(session_id)
assert len(entries) == 1
entry = entries[0]
assert entry["type"] == "agent_run"
assert entry["user_input"] == "你好"
assert entry["final_output"] == agent_output.content
assert entry["success"] == agent_output.success
assert entry["timestamp"]
assert isinstance(entry["runtime_session"], RuntimeSession)
assert entry["runtime_session"].session_id == session_id

sessionless_model = MockModel(response_text="mock sessionless response")
sessionless_store = InMemorySessionStore()
sessionless_transcript_store = InMemoryTranscriptStore()

sessionless_agent = ChatAgent(
    model=sessionless_model,
    session_store=sessionless_store,
    transcript_store=sessionless_transcript_store,
)

sessionless_output = sessionless_agent.run(AgentInput(message="你好", session_id=None))
assert sessionless_output.success is True
assert sessionless_store.list_sessions() == []

print("chat agent session store tests passed")
