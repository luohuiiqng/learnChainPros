import os
from concurrent.futures import ThreadPoolExecutor

from app.runtime.persistent_session_store import PersistentSessionStore
from app.runtime.persistent_transcript_store import PersistentTranscriptStore
from app.runtime.runtime_session import RuntimeSession
from app.runtime.transcript_entry import TranscriptEntry


def test_persistent_session_and_transcript_stores(tmp_path) -> None:
    session_db_path = str(tmp_path / "sessions.db")
    transcript_db_path = str(tmp_path / "transcript.db")
    nested_session_db_path = str(tmp_path / "data" / "runtime" / "nested-sessions.db")
    os.makedirs(os.path.dirname(nested_session_db_path), exist_ok=True)

    session_store = PersistentSessionStore(session_db_path)
    session_store.create_session("session-a", {"agent_type": "chat"})
    session = session_store.get_session("session-a")
    assert session is not None
    assert session["session_id"] == "session-a"
    assert session["metadata"] == {"agent_type": "chat"}
    assert session["created_at"]
    assert session["updated_at"]

    sessions = session_store.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == "session-a"

    with ThreadPoolExecutor(max_workers=1) as executor:
        threaded_sessions = executor.submit(session_store.list_sessions).result()
    assert len(threaded_sessions) == 1

    nested_session_store = PersistentSessionStore(nested_session_db_path)
    nested_session_store.create_session("session-b", {"source": "nested"})
    nested_session = nested_session_store.get_session("session-b")
    assert nested_session is not None
    assert nested_session["session_id"] == "session-b"
    assert os.path.exists(nested_session_db_path)

    transcript_store = PersistentTranscriptStore(transcript_db_path)
    runtime_session_1 = RuntimeSession(session_id="session-a", user_input="你好")
    runtime_session_1.final_output = "你好呀"
    entry_1 = TranscriptEntry(
        type="agent",
        user_input="你好",
        final_output="你好呀",
        success=True,
        runtime_session=runtime_session_1,
        timestamp="2026-04-09T10:00:00",
    )
    runtime_session_2 = RuntimeSession(session_id="session-a", user_input="再见")
    runtime_session_2.final_output = None
    entry_2 = TranscriptEntry(
        type="agent",
        user_input="再见",
        final_output=None,
        success=True,
        runtime_session=runtime_session_2,
        timestamp="2026-04-09T10:05:00",
    )
    transcript_store.append_entry("session-a", entry_1)
    transcript_store.append_entry("session-a", entry_2)
    entries = transcript_store.get_entries("session-a")
    assert len(entries) == 2
    assert entries[0].user_input == "你好"
    assert entries[1].user_input == "再见"

    with ThreadPoolExecutor(max_workers=1) as executor:
        threaded_entries = executor.submit(transcript_store.get_entries, "session-a").result()
    assert len(threaded_entries) == 2

    transcript_store.clear("session-a")
    assert transcript_store.get_entries("session-a") == []
