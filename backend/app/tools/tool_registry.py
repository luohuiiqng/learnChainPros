from app.tools.base_tool import BaseTool
from typing import Any

class ToolRegistry:
    def __init__(self):
        self._tools:dict[str,BaseTool] = {}
    def register_tool(self,tool: BaseTool)->None:
        """注册一个工具到工具仓库里"""
        if tool._name in self._tools:
            raise ValueError(f"tool:{tool._name} is already exist...")
        self._tools[tool._name] = tool

    def get_tool(self,name: str)->BaseTool|None:
        return self._tools.get(name)
    
    def list_tools(self)->list[str]:
        """获取所有的工具名"""
        return list(self._tools.keys())

    def get_tool_infos(self)->list[dict[str,Any]]:
        """获取所有的工具信息"""
        return [tool.get_tool_info() for tool in self._tools.values()]
    