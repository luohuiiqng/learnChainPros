from dataclasses import dataclass, field
from typing import Any

@dataclass
class AgentContext:
    """
    AgentContext:agent运行时上下文对象
    session_id:标识当前会话
    user_id:标识当前用户
    state:保存agent运行过程中的临时状态信息
    metadata:保存额外上下文参数，为后续扩展预留接口
    """
    session_id: str = ""
    user_id: str | None = None
    state: dict[str,Any] = field(default_factory = dict)
    metadata: dict[str,Any] = field(default_factory = dict)
