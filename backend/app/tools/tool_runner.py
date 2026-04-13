"""在独立线程中执行工具并支持超时（超时后原线程仍可能运行直至结束，适合 IO 型短工具）。"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from app.schemas.error_codes import ErrorCode
from app.schemas.tool_input import ToolInput
from app.schemas.tool_output import ToolOutput
from app.tools.base_tool import BaseTool


def run_tool_with_timeout(
    tool: BaseTool,
    tool_input: ToolInput,
    timeout_seconds: float | None,
) -> ToolOutput:
    if timeout_seconds is None or timeout_seconds <= 0:
        return tool.run(tool_input)
    name = tool.get_name()
    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(tool.run, tool_input)
        try:
            return fut.result(timeout=timeout_seconds)
        except FuturesTimeoutError:
            return ToolOutput(
                content="",
                success=False,
                error_message=f"工具执行超过 {timeout_seconds:g}s 上限",
                metadata={
                    "error_code": ErrorCode.TOOL_TIMEOUT,
                    "tool_name": name,
                },
            )
