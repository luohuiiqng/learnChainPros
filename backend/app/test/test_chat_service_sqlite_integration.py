import os
import sys
import types

import pytest

from app.config.settings import Settings
from app.schemas.session_response import SessionResponse
from app.schemas.transcript_response import TranscriptEntryResponse


@pytest.fixture(scope="module", autouse=True)
def fake_openai_for_sqlite_chat():
    os.environ.setdefault("OPENAI_API_KEY", "test-api-key")
    fake = types.ModuleType("openai")

    class FakeOpenAI:
        def __init__(self, *args, **kwargs) -> None:
            pass

    fake.OpenAI = FakeOpenAI
    sys.modules.setdefault("openai", fake)
    yield


def test_chat_service_sqlite_session_and_transcript(tmp_path) -> None:
    from app.services.chat_service import ChatService

    db_path = str(tmp_path / "runtime.db")
    settings = Settings(
        openai_api_key="test-api-key",
        openai_model="test-model",
        openai_base_url="https://example.com/v1",
        openai_organization=None,
        store_backend="sqlite",
        runtime_db_path=db_path,
    )
    service = ChatService(settings=settings)
    agent_output, session_id = service.chat("当前时间", None)
    assert agent_output.success is True
    assert session_id
    assert agent_output.content

    sessions = service.list_sessions()
    assert len(sessions) == 1
    assert isinstance(sessions[0], SessionResponse)
    assert sessions[0].session_id == session_id

    transcript = service.get_transcript(session_id)
    assert len(transcript) == 1
    assert isinstance(transcript[0], TranscriptEntryResponse)
    assert transcript[0].type == "agent"
    assert transcript[0].user_input == "当前时间"
    assert transcript[0].success is True
