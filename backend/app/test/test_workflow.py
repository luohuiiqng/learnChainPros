from app.workflows.sequential_workflow import SequentialWorkflow
from app.workflows.workflow_result import WorkflowResult


class FakeExecutor:
    def __init__(self) -> None:
        self.executed_steps: list[str] = []

    def execute_step(self, step, context=None):
        self.executed_steps.append(step.get("step_name"))
        return step.get("mock_result", {"success": True})


def test_sequential_workflow_success_path() -> None:
    workflow = SequentialWorkflow()
    success_executor = FakeExecutor()
    success_steps = [
        {
            "step_name": "step_1",
            "action": "tool",
            "mock_result": {"step_name": "step_1", "success": True, "output": "ok-1"},
        },
        {
            "step_name": "step_2",
            "action": "model",
            "mock_result": {"step_name": "step_2", "success": True, "output": "ok-2"},
        },
    ]
    success_result = workflow.run(success_steps, executor=success_executor)
    assert isinstance(success_result, WorkflowResult)
    assert success_result.success is True
    assert success_result.workflow_name == "sequential_workflow"
    assert success_result.completed_steps == 2
    assert success_result.final_output == "ok-2"
    assert len(success_result.results) == 2
    assert success_executor.executed_steps == ["step_1", "step_2"]


def test_sequential_workflow_stops_on_step_failure() -> None:
    workflow = SequentialWorkflow()
    fail_executor = FakeExecutor()
    fail_steps = [
        {
            "step_name": "step_1",
            "action": "tool",
            "mock_result": {"step_name": "step_1", "success": True, "output": "ok-1"},
        },
        {
            "step_name": "step_2",
            "action": "model",
            "mock_result": {
                "step_name": "step_2",
                "success": False,
                "output": "failed",
            },
        },
        {
            "step_name": "step_3",
            "action": "tool",
            "mock_result": {"step_name": "step_3", "success": True, "output": "ok-3"},
        },
    ]
    fail_result = workflow.run(fail_steps, executor=fail_executor)
    assert isinstance(fail_result, WorkflowResult)
    assert fail_result.success is False
    assert fail_result.workflow_name == "sequential_workflow"
    assert fail_result.completed_steps == 2
    assert fail_result.final_output == "failed"
    assert len(fail_result.results) == 2
    assert fail_executor.executed_steps == ["step_1", "step_2"]
    assert fail_result.results[-1]["success"] is False
