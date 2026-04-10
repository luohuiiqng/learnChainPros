import importlib
import os
import sys
import tempfile
import types

from app.agent.chat_agent import ChatAgent
from app.config.settings import Settings
from app.planners.rule_planner import RulePlanner
from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.persistent_session_store import PersistentSessionStore
from app.runtime.persistent_transcript_store import PersistentTranscriptStore
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

settings = Settings(
    openai_api_key="test-api-key",
    openai_model="test-model",
    openai_base_url="https://example.com/v1",
    openai_organization=None,
    store_backend="memory",
    runtime_db_path=None,
)

factory = AgentFactory()
agent = factory.create_chat_agent(settings=settings)

assert isinstance(agent, ChatAgent)
assert agent._runtime_manager is not None
assert isinstance(agent._runtime_manager, RuntimeManager)
assert agent._planner is not None
assert isinstance(agent._planner, RulePlanner)
assert agent._tool_registry is not None
assert agent._memory is not None

memory_factory = AgentFactory(store_backend="memory")
assert isinstance(memory_factory.get_session_store(), InMemorySessionStore)
assert isinstance(memory_factory.get_transcript_store(), InMemoryTranscriptStore)

with tempfile.TemporaryDirectory() as tmp_dir:
    db_path = os.path.join(tmp_dir, "runtime.db")
    sqlite_factory = AgentFactory(store_backend="sqlite", db_path=db_path)
    assert isinstance(sqlite_factory.get_session_store(), PersistentSessionStore)
    assert isinstance(sqlite_factory.get_transcript_store(), PersistentTranscriptStore)

try:
    AgentFactory(store_backend="sqlite")
    raise AssertionError("sqlite backend should require db_path")
except ValueError:
    pass

try:
    AgentFactory(store_backend="unknown")
    raise AssertionError("unsupported backend should raise ValueError")
except ValueError:
    pass

print("agent factory tests passed")
