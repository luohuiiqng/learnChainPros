from typing import Any

from app.agent.chat_agent import ChatAgent
from app.models.mock_model import MockModel
from app.planners.base_planner import BasePlanner
from app.runtime.runtime_session import RuntimeSession
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry


class WorkflowPlanner(BasePlanner):
    def plan(self, input_data: Any, context: Any = None) -> dict[str, Any]:
        return {
            "action": "workflow",
            "steps": [
                {
                    "action": "tool",
                    "tool_name": "time_tool",
                    "tool_input": {"content": input_data.message},
                    "step_name": "get_time",
                },
                {
                    "action": "model",
                    "prompt_template": "当前时间是 {step_output}，请生成一句话回复用户",
                    "use_step_result": "get_time",
                    "step_name": "generate_reply",
                },
            ],
            "context": {},
        }


tool_registry = ToolRegistry()
tool_registry.register_tool(TimeTool())

model = MockModel(response_text="mock workflow response")
planner = WorkflowPlanner()

chat_agent = ChatAgent(
    model=model,
    tool_registry=tool_registry,
    planner=planner,
)

agent_input = AgentInput(message="现在几点了？", session_id="workflow_session")
agent_output = chat_agent.run(agent_input)

assert isinstance(agent_output, AgentOutput)
assert agent_output.success is True
assert agent_output.content.startswith("mock workflow response:")

runtime_session = agent_output.metadata.get("runtime_session")
assert isinstance(runtime_session, RuntimeSession)
assert runtime_session.user_input == "现在几点了？"
assert runtime_session.planner_result["action"] == "workflow"
assert runtime_session.workflow_result is not None
assert runtime_session.workflow_result["success"] is True
assert len(runtime_session.workflow_result["results"]) == 2
assert runtime_session.workflow_result["results"][0]["step_name"] == "get_time"
assert runtime_session.workflow_result["results"][0]["success"] is True
assert runtime_session.workflow_result["results"][1]["step_name"] == "generate_reply"
assert runtime_session.workflow_result["results"][1]["success"] is True
assert len(runtime_session.workflow_trace) == 2
assert runtime_session.workflow_trace[0]["step_name"] == "get_time"
assert runtime_session.workflow_trace[0]["action"] == "tool"
assert runtime_session.workflow_trace[0]["success"] is True
assert runtime_session.workflow_trace[0]["output"] == runtime_session.workflow_result["results"][0]["output"]
assert runtime_session.workflow_trace[0]["error"] is None
assert runtime_session.workflow_trace[0]["timestamp"]
assert runtime_session.workflow_trace[1]["step_name"] == "generate_reply"
assert runtime_session.workflow_trace[1]["action"] == "model"
assert runtime_session.workflow_trace[1]["success"] is True
assert runtime_session.workflow_trace[1]["output"] == runtime_session.workflow_result["results"][1]["output"]
assert runtime_session.workflow_trace[1]["error"] is None
assert runtime_session.workflow_trace[1]["timestamp"]
assert runtime_session.tool_calls[0]["tool_name"] == "time_tool"
assert runtime_session.tool_calls[0]["output"] == runtime_session.workflow_result["results"][0]["output"]
assert len(runtime_session.model_calls) == 1
assert "当前时间是" in runtime_session.model_calls[0]["prompt"]
assert runtime_session.workflow_result["results"][0]["output"] in runtime_session.model_calls[0]["prompt"]
assert runtime_session.model_calls[0]["success"] is True
assert runtime_session.model_calls[0]["output"] == runtime_session.workflow_result["results"][1]["output"]
assert runtime_session.model_calls[0]["error"] is None
assert runtime_session.model_calls[0]["timestamp"]
assert runtime_session.final_output == agent_output.content
assert runtime_session.errors == []

mock_status = model.get_mock_status()
assert mock_status["call_count"] == 1
assert "当前时间是" in mock_status["last_input"].prompt
assert runtime_session.workflow_result["results"][0]["output"] in mock_status["last_input"].prompt

print("chat agent workflow tests passed")
