from app.prompts.prompt_builder import PromptBuilder


builder = PromptBuilder()

empty_prompt = builder.build_prompt(messages=[], current_input="你好")
assert "用户的输入是" in empty_prompt
assert "你好" in empty_prompt

history_messages = [
    {"role": "user", "content": "我叫张三", "timestamp": "2026-04-01T10:00:00"},
    {"role": "assistant", "content": "你好，张三", "timestamp": "2026-04-01T10:00:01"},
]

history_text = builder.format_history(history_messages)
assert "user: 我叫张三" in history_text
assert "assistant: 你好，张三" in history_text

history_prompt = builder.build_prompt(
    messages=history_messages,
    current_input="你还记得我叫什么吗？",
)
assert "这是与你的用户的对话历史" in history_prompt
assert "user: 我叫张三" in history_prompt
assert "assistant: 你好，张三" in history_prompt
assert "你还记得我叫什么吗？" in history_prompt
assert "你的任务是根据用户的输入生成合适的回复。" in history_prompt

print("prompt builder tests passed")
