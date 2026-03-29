from app.tools.time_tool import TimeTool
from app.schemas.tool_input import ToolInput

time_tool = TimeTool()
out_put = time_tool.run(ToolInput(params={}))
print(f"now time is:{out_put}")