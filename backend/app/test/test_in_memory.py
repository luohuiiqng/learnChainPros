from app.memory.in_memory_memory import InMemoryMemory


def test_in_memory_add_get_recent_and_clear() -> None:
    memory = InMemoryMemory()
    session_id = "pytest-in-memory-1"
    message1 = {"role": "user", "content": "你好"}
    message2 = {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}

    memory.add_message(session_id, message1)
    memory.add_message(session_id, message2)
    messages = memory.get_messages(session_id)
    assert len(messages) == 2
    assert messages[0] == message1
    assert messages[1] == message2

    messages_2 = memory.get_recent_messages(session_id, limit=1)
    assert len(messages_2) == 1
    assert messages_2[0] == message2

    memory.clear(session_id)
    assert memory.get_messages(session_id) == []
