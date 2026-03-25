from uuid import uuid4


def generate_reply(user_message: str) -> str:
    """Stage 1 uses a deterministic echo strategy as placeholder behavior."""
    normalized = user_message.strip()

    if "你好" in normalized:
        return "你好，很高兴见到你。你可以继续告诉我你的需求。"

    return f"我收到了：{normalized}"


def ensure_session_id(session_id: str | None) -> str:
    return session_id or str(uuid4())
