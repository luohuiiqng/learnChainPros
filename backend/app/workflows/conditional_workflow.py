from app.workflows.base_workflow import BaseWorkflow
from app.workflows.base_executor import BaseExecutor
from app.workflows.workflow_result import WorkflowResult
from typing import Any


class ConditionalWorkflow(BaseWorkflow):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def _should_execute_step(
        self, step: dict[str, Any], context: dict[str, Any]
    ) -> bool:
        condition = step.get("condition")
        if condition is None:
            return True
        depends_on = condition.get("depends_on")
        field = condition.get("field")
        expected_value = condition.get("equals")

        step_results = context.get("step_results", {})
        dependency_result = step_results.get(depends_on)

        if dependency_result is None:
            return False

        actual_value = dependency_result.get(field)
        return actual_value == expected_value

    def _build_skipped_result(self, step: dict[str, Any]) -> dict[str, Any]:
        return {
            "step_name": step.get("step_name", "unknown"),
            "action": step.get("action", "unknown"),
            "success": True,
            "output": None,
            "error": None,
            "input_summary": "condition not matched",
            "output_summary": "step skipped",
            "skipped": True,
        }

    def run(
        self,
        steps: list[dict[str, Any]],
        executor: BaseExecutor,
        context: dict[str, Any] | None = None,
    ) -> WorkflowResult:
        results: list[dict[str, Any]] = []
        if context is None:
            context = {}
        if context.get("step_results") is None:
            context["step_results"] = {}
        for step in steps:
            step_name = step.get("step_name", "unknown")
            if not self._should_execute_step(step=step, context=context):
                skipped_result = self._build_skipped_result(step)
                results.append(skipped_result)
                context["step_results"][step_name] = skipped_result
                continue

            step_result = executor.execute_step(step, context=context)
            results.append(step_result)
            context["step_results"][step_name] = step_result
            # 不因单步失败提前结束：后续步骤可通过 condition 消费失败态（如兜底模型回复）
        executed_results = [item for item in results if not item.get("skipped")]
        if not executed_results:
            return WorkflowResult(
                workflow_name="conditional_workflow",
                success=True,
                results=results,
                final_output=None,
                completed_steps=0,
                error=None,
                error_code=None,
                metadata={},
            )
        final = executed_results[-1]
        final_ok = final.get("success", False)
        return WorkflowResult(
            workflow_name="conditional_workflow",
            success=final_ok,
            results=results,
            final_output=final.get("output"),
            completed_steps=len(executed_results),
            error=None if final_ok else (final.get("error") or "workflow final step failed"),
            error_code=None if final_ok else final.get("error_code"),
            metadata={},
        )
