from dataclasses import dataclass
from app.runtime.runtime_session import RuntimeSession


@dataclass
class TranscriptEntry:
    """会话运行记录"""
    type: str
    user_input: str
    final_output: str | None
    success: bool
    runtime_session: RuntimeSession
    timestamp: str
