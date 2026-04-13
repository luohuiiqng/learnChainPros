from app.agent.chat_agent import ChatAgent
from app.memory.in_memory_memory import InMemoryMemory
from app.models.mock_model import MockModel
from app.planners.rule_planner import RulePlanner
from app.prompts.prompt_builder import PromptBuilder
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_router import ToolRouter


def test_memory_history_multi_turn_tool_and_model() -> None:
    model = MockModel(model_name="mock-memory-model", response_text="mock response")
    session_id = "pytest-memory-history-1"
    tool_registry = ToolRegistry()
    tool_registry.register_tool(TimeTool())
    tool_router = ToolRouter()
    tool_router.add_rule(
        "time_tool",
        ["时间", "现在时间", "当前时间", "日期", "time now", "time", "几点", "现在几点"],
    )
    tool_router.add_rule("test_not_exist_tool", ["lala"])
    memory = InMemoryMemory()
    planner = RulePlanner(tool_router=tool_router)
    chat_agent = ChatAgent(
        model=model,
        tool_registry=tool_registry,
        memory=memory,
        prompt_builder=PromptBuilder(),
        planner=planner,
    )

    agent_output_1 = chat_agent.run(
        AgentInput(message="你好，请记住我叫王老五!", session_id=session_id)
    )
    assert isinstance(agent_output_1, AgentOutput)
    assert agent_output_1.success is True
    assert "mock response" in (agent_output_1.content or "")
    mock_status = model.get_mock_status()
    assert mock_status["call_count"] == 1

    agent_output_2 = chat_agent.run(
        AgentInput(message="你能告诉我现在几点了么？", session_id=session_id)
    )
    assert isinstance(agent_output_2, AgentOutput)
    assert agent_output_2.success is True
    assert agent_output_2.metadata.get("name") == "time_tool"

    agent_output_3 = chat_agent.run(
        AgentInput(message="你还记得我叫什么名字吗？", session_id=session_id)
    )
    assert isinstance(agent_output_3, AgentOutput)
    assert agent_output_3.success is True
    assert "mock response" in (agent_output_3.content or "")

    memory_messages = memory.get_messages(session_id)
    assert len(memory_messages) == 6
    assert memory_messages[0]["role"] == "user"
    assert "王老五" in memory_messages[0]["content"]
    assert memory_messages[3]["content"] == agent_output_2.content
    assert memory_messages[5]["content"] == agent_output_3.content
    assert memory.has_memory(session_id) is True

    mock_status = model.get_mock_status()
    assert mock_status["call_count"] == 2
    assert "王老五" in mock_status["last_input"].prompt
    assert "你还记得我叫什么名字吗？" in mock_status["last_input"].prompt
    assert "2026-" in mock_status["last_input"].prompt or "assistant:" in mock_status["last_input"].prompt
