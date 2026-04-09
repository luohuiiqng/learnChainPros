from dataclasses import dataclass
from app.runtime.runtime_session import RuntimeSession
from typing import Any


@dataclass
class TranscriptEntry:
    """会话运行记录"""
    type: str
    user_input: str
    final_output: str | None
    success: bool
    runtime_session: RuntimeSession
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "user_input": self.user_input,
            "final_output": self.final_output,
            "success": self.success,
            "runtime_session": self.runtime_session.to_dict(),
            "timestamp": self.timestamp,
        }
