from dataclasses import dataclass,field
from typing import Any

@dataclass
class ModelRequest:
    """模型统一输入对象"""
    prompt: str
    metadata: dict[str,Any] = field(default_factory=dict)