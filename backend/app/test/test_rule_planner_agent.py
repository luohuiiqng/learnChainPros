from app.agent.chat_agent import ChatAgent
from app.memory.in_memory_memory import InMemoryMemory
from app.models.mock_model import MockModel
from app.planners.rule_planner import RulePlanner
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry


model = MockModel(model_name="mock-rule-planner-model", response_text="mock response")
planner = RulePlanner()
memory = InMemoryMemory()

tool_registry = ToolRegistry()
tool_registry.register_tool(TimeTool())

chat_agent = ChatAgent(
    model=model,
    tool_registry=tool_registry,
    memory=memory,
    planner=planner,
)

session_id = "rule_planner_session"

tool_input = AgentInput(message="现在几点了？", session_id=session_id)
tool_output = chat_agent.run(tool_input)
assert isinstance(tool_output, AgentOutput)
assert tool_output.success is True
assert tool_output.metadata.get("name") == "time_tool"

mock_status = model.get_mock_status()
assert mock_status["call_count"] == 0
assert mock_status["last_input"] is None

model_input = AgentInput(message="你好", session_id=session_id)
model_output = chat_agent.run(model_input)
assert isinstance(model_output, AgentOutput)
assert model_output.success is True
assert "mock response" in (model_output.content or "")

mock_status = model.get_mock_status()
assert mock_status["call_count"] == 1
assert "现在几点了？" in mock_status["last_input"].prompt
assert tool_output.content in mock_status["last_input"].prompt
assert "你好" in mock_status["last_input"].prompt

memory_messages = memory.get_messages(session_id)
assert len(memory_messages) == 4
assert memory_messages[0]["role"] == "user"
assert memory_messages[1]["role"] == "assistant"
assert memory_messages[1]["content"] == tool_output.content
assert memory_messages[2]["role"] == "user"
assert memory_messages[3]["role"] == "assistant"
assert memory_messages[3]["content"] == model_output.content

print("rule planner agent tests passed")
