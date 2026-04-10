import os
import sys
import tempfile
import types


os.environ.setdefault("OPENAI_API_KEY", "test-api-key")

fake_openai_module = types.ModuleType("openai")


class FakeOpenAI:
    def __init__(self, *args, **kwargs) -> None:
        pass


fake_openai_module.OpenAI = FakeOpenAI
sys.modules.setdefault("openai", fake_openai_module)

from app.schemas.session_response import SessionResponse
from app.schemas.transcript_response import TranscriptEntryResponse
from app.services.chat_service import ChatService


with tempfile.TemporaryDirectory() as tmp_dir:
    db_path = os.path.join(tmp_dir, "runtime.db")
    service = ChatService(store_backend="sqlite", db_path=db_path)

    agent_output, session_id = service.chat("当前时间", None)

    assert agent_output.success is True
    assert session_id
    assert agent_output.content

    sessions = service.list_sessions()
    assert len(sessions) == 1
    assert isinstance(sessions[0], SessionResponse)
    assert sessions[0].session_id == session_id
    assert sessions[0].created_at
    assert sessions[0].updated_at

    transcript = service.get_transcript(session_id)
    assert len(transcript) == 1
    assert isinstance(transcript[0], TranscriptEntryResponse)
    assert transcript[0].type == "agent"
    assert transcript[0].user_input == "当前时间"
    assert transcript[0].success is True
    assert transcript[0].runtime_session.session_id == session_id
    assert transcript[0].runtime_session.user_input == "当前时间"

print("chat service sqlite integration tests passed")
