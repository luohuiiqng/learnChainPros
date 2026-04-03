from app.workflows.sequential_workflow import SequentialWorkflow


class FakeExecutor:
    def __init__(self):
        self.executed_steps = []

    def execute_step(self, step, context=None):
        self.executed_steps.append(step.get("step_name"))
        return step.get("mock_result", {"success": True})


workflow = SequentialWorkflow()

# 成功场景
success_executor = FakeExecutor()
success_steps = [
    {
        "step_name": "step_1",
        "action": "tool",
        "mock_result": {
            "step_name": "step_1",
            "success": True,
            "output": "ok-1",
        },
    },
    {
        "step_name": "step_2",
        "action": "model",
        "mock_result": {
            "step_name": "step_2",
            "success": True,
            "output": "ok-2",
        },
    },
]

success_result = workflow.run(success_steps, executor=success_executor)

assert success_result["success"] is True
assert len(success_result["results"]) == 2
assert success_executor.executed_steps == ["step_1", "step_2"]

# 失败场景
fail_executor = FakeExecutor()
fail_steps = [
    {
        "step_name": "step_1",
        "action": "tool",
        "mock_result": {
            "step_name": "step_1",
            "success": True,
            "output": "ok-1",
        },
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
        "mock_result": {
            "step_name": "step_3",
            "success": True,
            "output": "ok-3",
        },
    },
]

fail_result = workflow.run(fail_steps, executor=fail_executor)

assert fail_result["success"] is False
assert len(fail_result["results"]) == 2
assert fail_executor.executed_steps == ["step_1", "step_2"]
assert fail_result["results"][-1]["success"] is False

print("workflow tests passed")
