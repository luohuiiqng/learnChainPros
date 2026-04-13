from app.models.mock_model import MockModel
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry
from app.workflows.agent_executor import AgentExecutor
from app.workflows.sequential_workflow import SequentialWorkflow
from app.workflows.workflow_result import WorkflowResult


def test_sequential_workflow_tool_then_model_with_context() -> None:
    tool_registry = ToolRegistry()
    tool_registry.register_tool(TimeTool())
    model = MockModel()
    workflow = SequentialWorkflow()
    executor = AgentExecutor(model=model, tool_registry=tool_registry)
    steps = [
        {
            "action": "tool",
            "tool_name": "time_tool",
            "tool_input": {"content": "现在几点了？"},
            "step_name": "get_time",
        },
        {
            "action": "model",
            "prompt_template": "当前时间是 {step_output}，请生成一句话回复用户",
            "use_step_result": "get_time",
            "step_name": "generate_reply",
        },
    ]
    context: dict = {}
    workflow_output = workflow.run(steps=steps, executor=executor, context=context)

    assert isinstance(workflow_output, WorkflowResult)
    assert workflow_output.success is True
    assert workflow_output.workflow_name == "sequential_workflow"
    assert workflow_output.completed_steps == 2
    assert workflow_output.final_output == workflow_output.results[-1]["output"]
    assert len(workflow_output.results) == 2
    assert workflow_output.results[0]["step_name"] == "get_time"
    assert workflow_output.results[0]["success"] is True
    assert workflow_output.results[1]["step_name"] == "generate_reply"
    assert workflow_output.results[1]["success"] is True
    assert "step_results" in context
    assert context["step_results"]["get_time"]["output"] == workflow_output.results[0]["output"]
    assert (
        context["step_results"]["generate_reply"]["output"]
        == workflow_output.results[1]["output"]
    )
