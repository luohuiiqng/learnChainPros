from app.agent.chat_agent import ChatAgent
from app.memory.in_memory_memory import InMemoryMemory
from app.models.mock_model import MockModel
from app.planners.rule_planner import RulePlanner
from app.schemas.agent_input import AgentInput
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_router import ToolRouter


def test_memory_agent_tool_then_model_with_history() -> None:
    session_id = "pytest-memory-agent-1"
    time_tool = TimeTool()
    tool_registry = ToolRegistry()
    tool_registry.register_tool(time_tool)
    model = MockModel(response_text="mock memory reply")
    tool_router = ToolRouter()
    tool_router.add_rule(
        "time_tool",
        ["时间", "现在时间", "当前时间", "日期", "time now", "time", "几点", "现在几点"],
    )
    memory = InMemoryMemory()
    planner = RulePlanner(tool_router=tool_router)
    chat_agent = ChatAgent(
        model=model,
        tool_registry=tool_registry,
        memory=memory,
        planner=planner,
    )
    out1 = chat_agent.run(
        AgentInput(message="你好,现在几点了？", session_id=session_id)
    )
    assert out1.success is True
    out2 = chat_agent.run(AgentInput(message="你好!", session_id=session_id))
    assert out2.success is True
    msgs = memory.get_messages(session_id)
    assert len(msgs) >= 4
