from app.workflows.conditional_workflow import ConditionalWorkflow
from app.workflows.workflow_result import WorkflowResult


class FakeExecutor:
    def __init__(self) -> None:
        self.executed_steps: list[str] = []

    def execute_step(self, step, context=None):
        self.executed_steps.append(step.get("step_name"))
        return step.get("mock_result", {"success": True})


def test_conditional_workflow_success_branch_skips_false_path() -> None:
    workflow = ConditionalWorkflow()
    success_executor = FakeExecutor()
    success_steps = [
        {
            "step_name": "step_1",
            "action": "tool",
            "mock_result": {
                "step_name": "step_1",
                "action": "tool",
                "success": True,
                "output": "ok-1",
            },
        },
        {
            "step_name": "step_if_success",
            "action": "model",
            "condition": {
                "depends_on": "step_1",
                "field": "success",
                "equals": True,
            },
            "mock_result": {
                "step_name": "step_if_success",
                "action": "model",
                "success": True,
                "output": "ok-2",
            },
        },
        {
            "step_name": "step_if_failed",
            "action": "model",
            "condition": {
                "depends_on": "step_1",
                "field": "success",
                "equals": False,
            },
            "mock_result": {
                "step_name": "step_if_failed",
                "action": "model",
                "success": True,
                "output": "should-not-run",
            },
        },
    ]
    success_context: dict = {}
    success_result = workflow.run(
        success_steps, executor=success_executor, context=success_context
    )
    assert isinstance(success_result, WorkflowResult)
    assert success_result.workflow_name == "conditional_workflow"
    assert success_result.success is True
    assert success_result.completed_steps == 2
    assert success_result.final_output == "ok-2"
    assert len(success_result.results) == 3
    assert success_executor.executed_steps == ["step_1", "step_if_success"]
    assert success_result.results[2]["step_name"] == "step_if_failed"
    assert success_result.results[2]["skipped"] is True
    assert success_result.results[2]["output_summary"] == "step skipped"
    assert success_context["step_results"]["step_if_failed"]["skipped"] is True


def test_conditional_workflow_tool_fail_then_fallback_model() -> None:
    workflow = ConditionalWorkflow()
    fallback_executor = FakeExecutor()
    fallback_steps = [
        {
            "step_name": "step_1",
            "action": "tool",
            "mock_result": {
                "step_name": "step_1",
                "action": "tool",
                "success": False,
                "output": "tool-failed",
                "error": "tool failed",
            },
        },
        {
            "step_name": "step_if_success",
            "action": "model",
            "condition": {
                "depends_on": "step_1",
                "field": "success",
                "equals": True,
            },
            "mock_result": {
                "step_name": "step_if_success",
                "action": "model",
                "success": True,
                "output": "should-not-run",
            },
        },
        {
            "step_name": "step_if_failed",
            "action": "model",
            "condition": {
                "depends_on": "step_1",
                "field": "success",
                "equals": False,
            },
            "mock_result": {
                "step_name": "step_if_failed",
                "action": "model",
                "success": True,
                "output": "fallback-output",
            },
        },
    ]
    fallback_result = workflow.run(
        fallback_steps, executor=fallback_executor, context={}
    )
    assert isinstance(fallback_result, WorkflowResult)
    assert fallback_result.workflow_name == "conditional_workflow"
    assert fallback_result.success is True
    assert fallback_result.completed_steps == 2
    assert fallback_result.final_output == "fallback-output"
    assert fallback_result.error is None
    assert len(fallback_result.results) == 3
    assert fallback_executor.executed_steps == ["step_1", "step_if_failed"]


def test_conditional_workflow_condition_not_met_step_skipped() -> None:
    workflow = ConditionalWorkflow()
    skip_executor = FakeExecutor()
    skip_steps = [
        {
            "step_name": "step_1",
            "action": "tool",
            "mock_result": {
                "step_name": "step_1",
                "action": "tool",
                "success": True,
                "output": "ok-1",
            },
        },
        {
            "step_name": "step_2",
            "action": "model",
            "condition": {
                "depends_on": "step_1",
                "field": "output",
                "equals": "different-output",
            },
            "mock_result": {
                "step_name": "step_2",
                "action": "model",
                "success": True,
                "output": "should-not-run",
            },
        },
    ]
    skip_result = workflow.run(skip_steps, executor=skip_executor, context={})
    assert isinstance(skip_result, WorkflowResult)
    assert skip_result.success is True
    assert skip_result.completed_steps == 1
    assert skip_result.final_output == "ok-1"
    assert len(skip_result.results) == 2
    assert skip_executor.executed_steps == ["step_1"]
    assert skip_result.results[1]["skipped"] is True
    assert skip_result.results[1]["output"] is None
