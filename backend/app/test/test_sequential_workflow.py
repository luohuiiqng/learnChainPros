from app.workflows.sequential_workflow import SequentialWorkflow
from app.workflows.agent_executor import AgentExecutor
from app.models.mock_model import MockModel
from app.tools.tool_registry import ToolRegistry
from app.tools.time_tool import TimeTool


tool_registry = ToolRegistry()
time_tool = TimeTool()
tool_registry.register_tool(time_tool)
model = MockModel()





sequentialWorkflow = SequentialWorkflow()
agent_executor = AgentExecutor(model=model,tool_registry=tool_registry)
steps = [
    {"action":"tool","tool_name":"time_tool","tool_input":{"content":"现在几点了？"},"step_name":"get_time"},
    {
    "action": "model",
    "prompt_template": "当前时间是 {step_output}，请生成一句话回复用户",
    "use_step_result": "get_time",
    "step_name": "generate_reply",
}

]

context = {}
workflow_output = sequentialWorkflow.run(steps=steps, executor=agent_executor, context=context)
print(f"workflow_output:{workflow_output}")


