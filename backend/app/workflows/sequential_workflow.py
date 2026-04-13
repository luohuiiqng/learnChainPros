from app.workflows.base_workflow import BaseWorkflow
from typing import Any
from app.workflows.base_executor import BaseExecutor
from app.workflows.workflow_result import WorkflowResult


class SequentialWorkflow(BaseWorkflow):
    def __init__(self,**kwargs)->None:
        super().__init__(**kwargs)

    def run(
        self,
        steps: list[dict[str, Any]],
        executor: BaseExecutor,
        context: dict[str, Any] | None = None,
    ) -> WorkflowResult:
        results = []
        if context is None:
            context = {}
        if context.get("step_results") is None:
            context["step_results"] = {}
        for step in steps:
            step_result = executor.execute_step(step,context=context)
            step_name = step.get("step_name","unknown")
            results.append(step_result)
            context["step_results"][step_name] = step_result
            if not step_result.get("success", False):
                return WorkflowResult(
                    workflow_name="sequential_workflow",
                    success=False,
                    results=results,
                    final_output=step_result.get("output"),
                    completed_steps=len(results),
                    error=step_result.get("error")
                    or f"Step {step.get('step_name', 'unknown')} failed",
                    error_code=step_result.get("error_code"),
                    metadata={},
                )
        return WorkflowResult(
            workflow_name="sequential_workflow",
            success=True,
            results=results,
            final_output=results[-1].get("output") if results else None,
            completed_steps=len(results),
            error=None,
            error_code=None,
            metadata={},
        )