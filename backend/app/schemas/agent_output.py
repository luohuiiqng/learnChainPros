from dataclasses import dataclass, field
from typing import Any

@dataclass
class AgentOutput:
    """agent统一输出对象"""

    content: str
    success: bool = True
    error_message: str | None = None
    error_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
