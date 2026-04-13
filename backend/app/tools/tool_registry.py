"""工具注册表：按名称解析 ``BaseTool``，供 Planner / ChatAgent 调度。"""

from __future__ import annotations

from typing import Any

from app.tools.base_tool import BaseTool


class ToolRegistry:
    """内存中的 ``tool_name -> BaseTool`` 映射；同名重复注册会抛错。"""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """注册一个工具；若名称已存在则抛出 ``ValueError``。"""
        if tool._name in self._tools:
            raise ValueError(f"tool:{tool._name} is already exist...")
        self._tools[tool._name] = tool

    def get_tool(self, name: str) -> BaseTool | None:
        """按名称返回工具实例，不存在时 ``None``。"""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """返回已注册的全部工具名。"""
        return list(self._tools.keys())

    def get_tool_infos(self) -> list[dict[str, Any]]:
        """返回各工具的 ``get_tool_info()`` 字典列表。"""
        return [tool.get_tool_info() for tool in self._tools.values()]
