
from app.schemas.tool_input import ToolInput
from app.schemas.tool_output import ToolOutput
from app.tools.base_tool import BaseTool
from datetime import datetime

class TimeTool(BaseTool):
    """一个返回当前时间的工具"""
    def __init__(self,**kwargs):
        super().__init__(name="time_tool",description="获取当前时间",**kwargs)

    def execute(self,tool_input:ToolInput)->ToolOutput:
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return ToolOutput(content=now_time,success=True,metadata={"name":self._name,"description":self._description})