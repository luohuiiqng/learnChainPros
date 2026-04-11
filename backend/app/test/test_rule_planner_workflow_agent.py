from app.agent.chat_agent import ChatAgent
from app.models.mock_model import MockModel
from app.planners.rule_planner import RulePlanner
from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.runtime_manager import RuntimeManager
from app.runtime.runtime_session import RuntimeSession
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_router import ToolRouter


tool_router = ToolRouter()
tool_router.add_rule(
    tool_name="time_tool",
    keywords=["时间", "现在时间", "当前时间", "几点", "现在几点"],
)

planner = RulePlanner(tool_router=tool_router)

tool_registry = ToolRegistry()
tool_registry.register_tool(TimeTool())

model = MockModel(response_text="mock workflow response")
runtime_manager = RuntimeManager(
    session_store=InMemorySessionStore(),
    transcript_store=InMemoryTranscriptStore(),
)

chat_agent = ChatAgent(
    runtime_manager=runtime_manager,
    model=model,
    tool_registry=tool_registry,
    planner=planner,
)

agent_input = AgentInput(
    message="现在几点了，回复我一句",
    session_id="rule-planner-workflow-session",
)
agent_output = chat_agent.run(agent_input)

assert isinstance(agent_output, AgentOutput)
assert agent_output.success is True
assert agent_output.content.startswith("mock workflow response:")

runtime_session = agent_output.metadata.get("runtime_session")
assert isinstance(runtime_session, RuntimeSession)
assert runtime_session.user_input == "现在几点了，回复我一句"
assert runtime_session.planner_result["action"] == "workflow"
assert runtime_session.planner_result["reason"] == "同时命中时间意图和自然回复意图，选择workflow"
assert runtime_session.workflow_result is not None
assert runtime_session.workflow_result["success"] is True
assert len(runtime_session.workflow_result["results"]) == 2
assert runtime_session.workflow_result["results"][0]["step_name"] == "get_time"
assert runtime_session.workflow_result["results"][0]["success"] is True
assert runtime_session.workflow_result["results"][1]["step_name"] == "generate_reply"
assert runtime_session.workflow_result["results"][1]["success"] is True
assert len(runtime_session.workflow_trace) == 3
assert runtime_session.workflow_trace[0]["step_name"] == "planner"
assert runtime_session.workflow_trace[0]["action"] == "workflow"
assert runtime_session.workflow_trace[0]["success"] is True
assert runtime_session.workflow_trace[0]["output"] == runtime_session.planner_result
assert runtime_session.workflow_trace[0]["input_summary"] == "现在几点了，回复我一句"
assert runtime_session.workflow_trace[0]["output_summary"] == runtime_session.planner_result["reason"]
assert runtime_session.workflow_trace[0]["timestamp"]
assert runtime_session.workflow_trace[1]["step_name"] == "get_time"
assert runtime_session.workflow_trace[1]["action"] == "tool"
assert runtime_session.workflow_trace[1]["success"] is True
assert runtime_session.workflow_trace[1]["output"] == runtime_session.workflow_result["results"][0]["output"]
assert runtime_session.workflow_trace[1]["input_summary"] == "tool=time_tool,params={}"
assert runtime_session.workflow_trace[1]["output_summary"] == f"tool returned: {runtime_session.workflow_result['results'][0]['output']}"
assert runtime_session.workflow_trace[1]["error"] is None
assert runtime_session.workflow_trace[1]["timestamp"]
assert runtime_session.workflow_trace[2]["step_name"] == "generate_reply"
assert runtime_session.workflow_trace[2]["action"] == "model"
assert runtime_session.workflow_trace[2]["success"] is True
assert runtime_session.workflow_trace[2]["output"] == runtime_session.workflow_result["results"][1]["output"]
assert "当前时间是" in runtime_session.workflow_trace[2]["input_summary"]
assert runtime_session.workflow_trace[2]["output_summary"] == f"model returned: {runtime_session.workflow_result['results'][1]['output']}"
assert runtime_session.workflow_trace[2]["error"] is None
assert runtime_session.workflow_trace[2]["timestamp"]
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

print("rule planner workflow agent tests passed")
