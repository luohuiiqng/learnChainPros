import os

import pytest

from app.agent.chat_agent import ChatAgent
from app.models.mock_model import MockModel
from app.planners.rule_planner import RulePlanner
from app.schemas.agent_input import AgentInput
from app.schemas.tool_input import ToolInput
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_router import ToolRouter


def test_chat_agent_call_tool_directly_mock_model() -> None:
    model = MockModel(response_text="ignored")
    tool_registry = ToolRegistry()
    tool_registry.register_tool(TimeTool())
    tool_router = ToolRouter()
    tool_router.add_rule("time_tool", ["几点"])
    planner = RulePlanner(tool_router=tool_router)
    agent = ChatAgent(model=model, tool_registry=tool_registry, planner=planner)
    agent.run(AgentInput(message="现在几点？", session_id="pytest-registry-1"))
    tool_output = agent.call_tool("time_tool", ToolInput(params={"content": "现在几点了"}))
    assert tool_output.success is True
    assert tool_output.content


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_chat_agent_call_tool_openai_optional() -> None:
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
    agent = ChatAgent(model=model, tool_registry=tool_registry)
    out = agent.run(AgentInput(message="hi", session_id="pytest-registry-openai"))
    skip_if_openai_unreachable(out)
    assert out.success is True
    tool_output = agent.call_tool("time_tool", ToolInput(params={}))
    assert tool_output.success is True
