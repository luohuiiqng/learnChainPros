from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore


store = InMemoryTranscriptStore()

session_a = "session-a"
session_b = "session-b"

entry_a1 = {
    "type": "agent_run",
    "user_input": "你好",
    "final_output": "你好，有什么可以帮你？",
}
entry_a2 = {
    "type": "agent_run",
    "user_input": "现在几点了？",
    "final_output": "2026-04-07 21:00:00",
}
entry_b1 = {
    "type": "agent_run",
    "user_input": "测试另一个会话",
    "final_output": "另一个会话输出",
}

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

print("in-memory transcript store tests passed")
