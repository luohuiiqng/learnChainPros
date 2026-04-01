from app.memory.in_memory_memory import InMemoryMemory


memory = InMemoryMemory()
session_id = "test_session"
message1 = {"role":"user","content":"你好"}
message2 = {"role":"assistant","content":"你好！有什么可以帮助你的吗？"}

memory.add_message(session_id,message1)
memory.add_message(session_id,message2)
messages = memory.get_messages(session_id)
print(f"messages:{messages}")

messages_2 = memory.get_recent_messages(session_id,limit=1)
print(f"messages_2:{messages_2}")

memory.clear(session_id)
messages_after_clear = memory.get_messages(session_id)
print(f"messages_after_clear:{messages_after_clear}")