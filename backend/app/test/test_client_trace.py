from app.agent.chat_agent import ChatAgent
from app.models.mock_model import MockModel
from app.runtime.client_trace import pick_client_trace
from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.runtime_manager import RuntimeManager
from app.schemas.agent_input import AgentInput


def test_pick_client_trace_truncates_and_skips_empty() -> None:
    meta = {
        "request_id": "  abc  ",
        "correlation_id": "",
        "noise": "x",
    }
    assert pick_client_trace(meta) == {"request_id": "abc"}


def test_chat_agent_output_metadata_includes_request_id() -> None:
    rm = RuntimeManager(
        session_store=InMemorySessionStore(),
        transcript_store=InMemoryTranscriptStore(),
    )
    agent = ChatAgent(runtime_manager=rm, model=MockModel(response_text="ok"))
    out = agent.run(
        AgentInput(
            message="你好",
            session_id="pytest-client-trace-1",
            metadata={"request_id": "rid-99"},
        )
    )
    assert out.success is True
    assert out.metadata.get("request_id") == "rid-99"
