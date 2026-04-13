from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.runtime_session import RuntimeSession
from app.runtime.transcript_entry import TranscriptEntry


def test_in_memory_transcript_store_append_get_clear() -> None:
    store = InMemoryTranscriptStore()
    session_a = "pytest-transcript-a"
    session_b = "pytest-transcript-b"

    entry_a1 = TranscriptEntry(
        type="agent_run",
        user_input="你好",
        final_output="你好，有什么可以帮你？",
        success=True,
        runtime_session=RuntimeSession(session_id=session_a, user_input="你好"),
        timestamp="2026-04-07T21:00:00",
    )
    entry_a2 = TranscriptEntry(
        type="agent_run",
        user_input="现在几点了？",
        final_output="2026-04-07 21:00:00",
        success=True,
        runtime_session=RuntimeSession(session_id=session_a, user_input="现在几点了？"),
        timestamp="2026-04-07T21:01:00",
    )
    entry_b1 = TranscriptEntry(
        type="agent_run",
        user_input="测试另一个会话",
        final_output="另一个会话输出",
        success=True,
        runtime_session=RuntimeSession(session_id=session_b, user_input="测试另一个会话"),
        timestamp="2026-04-07T21:02:00",
    )

    store.append_entry(session_a, entry_a1)
    store.append_entry(session_a, entry_a2)
    store.append_entry(session_b, entry_b1)

    entries_a = store.get_entries(session_a)
    entries_b = store.get_entries(session_b)
    assert len(entries_a) == 2
    assert entries_a[0] == entry_a1
    assert entries_a[1] == entry_a2
    assert len(entries_b) == 1
    assert entries_b[0] == entry_b1
    assert store.get_entries("missing-session") == []

    store.clear(session_a)
    assert store.get_entries(session_a) == []
    assert store.get_entries(session_b) == [entry_b1]
