from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowResult:
    workflow_name: str
    success: bool
    results: list[dict[str, Any]]
    final_output: Any
    completed_steps: int
    error: str | None
    error_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_name": self.workflow_name,
            "success": self.success,
            "results": self.results,
            "final_output": self.final_output,
            "completed_steps": self.completed_steps,
            "error": self.error,
            "error_code": self.error_code,
            "metadata": self.metadata,
        }
