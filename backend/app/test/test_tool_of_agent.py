import os

import pytest

from app.agent.chat_agent import ChatAgent
from app.models.mock_model import MockModel
from app.planners.rule_planner import RulePlanner
from app.schemas.agent_input import AgentInput
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_router import ToolRouter


def test_chat_agent_tool_then_model_with_rule_planner_mock() -> None:
    model = MockModel(response_text="mock reply")
    tool_registry = ToolRegistry()
    tool_registry.register_tool(TimeTool())
    tool_router = ToolRouter()
    tool_router.add_rule(
        "time_tool",
        ["时间", "现在时间", "当前时间", "日期", "time now", "time", "几点", "现在几点"],
    )
    planner = RulePlanner(tool_router=tool_router)
    agent = ChatAgent(
        model=model,
        tool_registry=tool_registry,
        planner=planner,
    )
    out1 = agent.run(
        AgentInput(message="你好,现在几点了？", session_id="pytest-tool-of-agent-1")
    )
    assert out1.success is True
    out2 = agent.run(AgentInput(message="你好!", session_id="pytest-tool-of-agent-1"))
    assert out2.success is True


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_chat_agent_optional_openai_tool_path() -> None:
    from app.models.openai_model import OpenAIModel
    from app.test.support_helpers import skip_if_openai_unreachable

    model = OpenAIModel(
        model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY", ""),
        base_url=os.getenv("OPENAI_BASE_URL"),
        organization=os.getenv("OPENAI_ORGANIZATION"),
    )
    tool_registry = ToolRegistry()
    tool_registry.register_tool(TimeTool())
    tool_router = ToolRouter()
    tool_router.add_rule(
        "time_tool",
        ["时间", "现在时间", "当前时间", "日期", "time now", "time", "几点", "现在几点"],
    )
    planner = RulePlanner(tool_router=tool_router)
    agent = ChatAgent(model=model, tool_registry=tool_registry, planner=planner)
    out = agent.run(
        AgentInput(message="你好,现在几点了？", session_id="pytest-tool-of-agent-openai")
    )
    skip_if_openai_unreachable(out)
    assert out.success is True
