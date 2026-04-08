from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.runtime_manager import RuntimeManager
from app.runtime.runtime_session import RuntimeSession
from app.runtime.transcript_entry import TranscriptEntry


session_store = InMemorySessionStore()
transcript_store = InMemoryTranscriptStore()
runtime_manager = RuntimeManager(
    session_store=session_store,
    transcript_store=transcript_store,
)


runtime_session = runtime_manager.create_runtime_session(
    session_id="runtime-manager-session",
    user_input="现在几点了？",
)

assert isinstance(runtime_session, RuntimeSession)
assert runtime_session.session_id == "runtime-manager-session"
assert runtime_session.user_input == "现在几点了？"


runtime_manager.ensure_session_exists("runtime-manager-session")
session = session_store.get_session("runtime-manager-session")
assert session is not None
assert session["session_id"] == "runtime-manager-session"
assert session["created_at"]
assert session["updated_at"]

runtime_manager.ensure_session_exists(None)
assert len(session_store.list_sessions()) == 1


runtime_session.final_output = "现在是 10:00"
entry = runtime_manager.build_transcript_entry(
    type="agent_run",
    user_input="现在几点了？",
    final_output=runtime_session.final_output,
    success=True,
    runtime_session=runtime_session,
)

assert isinstance(entry, TranscriptEntry)
assert entry.type == "agent_run"
assert entry.user_input == "现在几点了？"
assert entry.final_output == "现在是 10:00"
assert entry.success is True
assert entry.runtime_session is runtime_session
assert entry.timestamp


runtime_manager.append_transcript_entry(
    session_id="runtime-manager-session",
    transcript_entry=entry,
)

entries = transcript_store.get_entries("runtime-manager-session")
assert len(entries) == 1
assert entries[0] is entry
assert entries[0].runtime_session is runtime_session


runtime_manager.append_transcript_entry(
    session_id=None,
    transcript_entry=entry,
)
assert transcript_store.get_entries("runtime-manager-session") == [entry]

print("runtime manager tests passed")
