from typing import Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RuntimeSession:
    """一次运行过程中的核心聚合快照"""

    session_id: str | None = None
    user_input: str = ""
    planner_result: dict[str, Any] | None = None
    workflow_result: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    model_calls: list[dict[str, Any]] = field(default_factory=list)
    final_output: str | None = None
    errors: list[str] = field(default_factory=list)

    def add_tool_call(
        self, tool_name: str, success: bool, output: Any, error: str | None
    ) -> None:
        timestamp = datetime.now().isoformat()
        self.tool_calls.append(
            {
                "tool_name": tool_name,
                "success": success,
                "output": output,
                "error": error,
                "timestamp": timestamp,
            }
        )

    def add_model_call(
        self, prompt: str, success: bool, output: Any, error: str | None
    ) -> None:
        timestamp = datetime.now().isoformat()
        self.model_calls.append(
            {
                "prompt": prompt,
                "success": success,
                "output": output,
                "error": error,
                "timestamp": timestamp,
            }
        )

    def add_error(self, error_message: str) -> None:
        self.errors.append(error_message)
