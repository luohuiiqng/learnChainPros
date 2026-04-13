from app.workflows.workflow_result import WorkflowResult


def test_workflow_result_to_dict() -> None:
    workflow_result = WorkflowResult(
        workflow_name="sequential_workflow",
        success=True,
        results=[
            {
                "step_name": "step_1",
                "success": True,
                "output": "ok-1",
            }
        ],
        final_output="ok-1",
        completed_steps=1,
        error=None,
        metadata={"source": "unit-test"},
    )
    workflow_result_dict = workflow_result.to_dict()
    assert workflow_result_dict == {
        "workflow_name": "sequential_workflow",
        "success": True,
        "results": [
            {
                "step_name": "step_1",
                "success": True,
                "output": "ok-1",
            }
        ],
        "final_output": "ok-1",
        "completed_steps": 1,
        "error": None,
        "error_code": None,
        "metadata": {"source": "unit-test"},
    }
