from app.schemas.tool_input import ToolInput
from app.tools.time_tool import TimeTool


def test_time_tool_run_returns_success_and_content() -> None:
    time_tool = TimeTool()
    out_put = time_tool.run(ToolInput(params={}))
    assert out_put.success is True
    assert out_put.content
    assert len(out_put.content) >= 8
