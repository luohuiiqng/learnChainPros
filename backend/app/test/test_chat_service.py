import importlib
import os
import sys
import types

from app.schemas.agent_output import AgentOutput


os.environ.setdefault("OPENAI_API_KEY", "test-api-key")

fake_openai_module = types.ModuleType("openai")


class FakeOpenAI:
    def __init__(self, *args, **kwargs) -> None:
        pass


fake_openai_module.OpenAI = FakeOpenAI
sys.modules.setdefault("openai", fake_openai_module)

chat_service_module = importlib.import_module("app.services.chat_service")
chat_service_module = importlib.reload(chat_service_module)

ChatService = chat_service_module.ChatService
ensure_session_id = chat_service_module.ensure_session_id


class StubAgent:
    def __init__(self, response_text: str) -> None:
        self._response_text = response_text
        self.last_input = None

    def run(self, agent_input):
        self.last_input = agent_input
        return AgentOutput(content=self._response_text, success=True)


generated_session_id = ensure_session_id(None)
assert generated_session_id
assert isinstance(generated_session_id, str)

existing_session_id = ensure_session_id("existing-session")
assert existing_session_id == "existing-session"


service = ChatService()
stub_agent = StubAgent(response_text="mock service response")
service._agent = stub_agent

agent_output, resolved_session_id = service.chat("你好", None)

assert agent_output.content == "mock service response"
assert resolved_session_id
assert stub_agent.last_input is not None
assert stub_agent.last_input.message == "你好"
assert stub_agent.last_input.session_id == resolved_session_id


fixed_session_id = "fixed-session-id"
agent_output_fixed, resolved_fixed_session_id = service.chat("再来一次", fixed_session_id)

assert agent_output_fixed.content == "mock service response"
assert resolved_fixed_session_id == fixed_session_id
assert stub_agent.last_input is not None
assert stub_agent.last_input.message == "再来一次"
assert stub_agent.last_input.session_id == fixed_session_id

print("chat service tests passed")
