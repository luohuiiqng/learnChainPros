from app.schemas.tool_input import ToolInput
from app.schemas.tool_output import ToolOutput
from app.tools.base_tool import BaseTool


class WeatherTool(BaseTool):
    """一个返回天气的工具"""

    def __init__(self, **kwargs):
        super().__init__(name="weather_tool", description="获取天气", **kwargs)

    def execute(self, tool_input: ToolInput) -> ToolOutput:
        now_weather = "天晴,24度,风力五级."
        return ToolOutput(
            content=now_weather,
            success=True,
            metadata={"name": self._name, "description": self._description},
        )
