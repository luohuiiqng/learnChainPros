from dataclasses import dataclass,field
from typing import Any

@dataclass
class ToolInput:
    """工具的统一输入对象"""
    params: dict[str,Any]
    metadata: dict[str,Any] = field(default_factory = dict)