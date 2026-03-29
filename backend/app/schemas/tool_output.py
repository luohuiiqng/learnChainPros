from dataclasses import dataclass,field
from typing import Any

@dataclass
class ToolOutput:
    """工具的统一输出"""
    content: Any
    success: bool = True
    error_message: str|None = None
    metadata: dict[str,Any] = field(default_factory = dict)