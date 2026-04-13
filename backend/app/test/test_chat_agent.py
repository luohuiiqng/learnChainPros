import os

import pytest
from dotenv import load_dotenv

from app.agent.chat_agent import ChatAgent
from app.models.mock_model import MockModel
from app.schemas.agent_input import AgentInput

load_dotenv()


def test_chat_agent_model_branch_with_mock_model() -> None:
    model = MockModel(response_text="mock reply body")
    agent = ChatAgent(model=model)
    out = agent.run(AgentInput(message="你好", session_id="pytest-chat-agent-1"))
    assert out.success is True
    assert "mock reply body" in (out.content or "")


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set; skip optional integration call",
)
def test_chat_agent_optional_openai_call() -> None:
    from app.models.openai_model import OpenAIModel

    model = OpenAIModel(
        model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY", ""),
        base_url=os.getenv("OPENAI_BASE_URL"),
        organization=os.getenv("OPENAI_ORGANIZATION"),
    )
    agent = ChatAgent(model=model)
    out = agent.run(
        AgentInput(message="用一句话回答：1+1等于几？", session_id="pytest-chat-agent-openai")
    )
    from app.test.support_helpers import skip_if_openai_unreachable

    skip_if_openai_unreachable(out)
    assert out.success is True
    assert len((out.content or "").strip()) > 0
