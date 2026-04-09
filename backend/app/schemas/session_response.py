from pydantic import BaseModel
from typing import Any


class SessionResponse(BaseModel):
    """一条session元信息对外暴露时的标准响应结构"""

    session_id: str
    created_at: str
    updated_at: str
    metadata: dict[str, Any]

    @classmethod
    def from_session_dict(cls, data: dict[str, Any]) -> "SessionResponse":
        return cls(**data)
