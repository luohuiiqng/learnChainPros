import importlib
import os
import sys
import types

from app.agent.chat_agent import ChatAgent
from app.planners.rule_planner import RulePlanner
from app.runtime.runtime_manager import RuntimeManager


os.environ.setdefault("OPENAI_API_KEY", "test-api-key")

fake_openai_module = types.ModuleType("openai")


class FakeOpenAI:
    def __init__(self, *args, **kwargs) -> None:
        pass


fake_openai_module.OpenAI = FakeOpenAI
sys.modules.setdefault("openai", fake_openai_module)

agent_factory_module = importlib.import_module("app.services.agent_factory")
agent_factory_module = importlib.reload(agent_factory_module)

AgentFactory = agent_factory_module.AgentFactory

factory = AgentFactory()
agent = factory.create_chat_agent()

assert isinstance(agent, ChatAgent)
assert agent._runtime_manager is not None
assert isinstance(agent._runtime_manager, RuntimeManager)
assert agent._planner is not None
assert isinstance(agent._planner, RulePlanner)
assert agent._tool_registry is not None
assert agent._memory is not None

print("agent factory tests passed")
