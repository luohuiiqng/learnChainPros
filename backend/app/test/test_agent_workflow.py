from app.agent.chat_agent import ChatAgent
from app.memory.in_memory_memory import InMemoryMemory
from app.models.mock_model import MockModel
from app.planners.rule_planner import RulePlanner
from app.prompts.prompt_builder import PromptBuilder
from app.schemas.agent_input import AgentInput
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_router import ToolRouter


def test_chat_agent_rule_planner_time_question_mock() -> None:
    model = MockModel(response_text="mock workflow line reply")
    tool_registry = ToolRegistry()
    tool_registry.register_tool(TimeTool())
    tool_router = ToolRouter()
    tool_router.add_rule(
        "time_tool",
        [
            "时间",
            "现在时间",
            "现在几点",
            "当前时间",
            "日期",
            "time now",
            "time",
            "几点",
        ],
    )
    memory = InMemoryMemory()
    planner = RulePlanner(tool_router=tool_router)
    chat_agent = ChatAgent(
        model=model,
        tool_registry=tool_registry,
        memory=memory,
        planner=planner,
        prompt_builder=PromptBuilder(),
    )
    agent_output = chat_agent.run(
        AgentInput(message="请回复我现在几点？", session_id="pytest-agent-workflow-1")
    )
    assert agent_output.success is True
    assert agent_output.content
