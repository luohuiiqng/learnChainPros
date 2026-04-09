from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentInput:
    """agent的统一输入对象"""
    message: str
    session_id: str = ""
    user_id: str | None = None
    metadata: dict[str,Any] = field(default_factory=dict)
