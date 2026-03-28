from dataclasses import dataclass,field
from typing import Any

@dataclass
class ModelResponse:
    """模型统一回复对象"""
    content: str| None = None
    success: bool = True
    error_message: str | None = None
    metadata: dict[str,Any] = field(default_factory=dict)