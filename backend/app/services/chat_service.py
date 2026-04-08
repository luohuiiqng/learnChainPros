from uuid import uuid4
from app.agent.chat_agent import ChatAgent
from app.models.openai_model import OpenAIModel
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.memory.in_memory_memory import InMemoryMemory
from app.prompts.prompt_builder import PromptBuilder
from app.planners.rule_planner import RulePlanner
from app.tools.tool_router import ToolRouter
from app.tools.tool_registry import ToolRegistry
from app.tools.time_tool import TimeTool
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.runtime_manager import RuntimeManager
import os


def ensure_session_id(session_id: str | None) -> str:
    return session_id or str(uuid4())


class ChatService:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        model_name = os.getenv("OPENAI_MODEL", "gpt-5.4")
        base_url = os.getenv("OPENAI_BASE_URL")
        organization = os.getenv("OPENAI_ORGANIZATION")
        self._model = OpenAIModel(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            organization=organization,
        )
        self._inmemory_memory = InMemoryMemory()
        self._prompt_builder = PromptBuilder()
        time_tool = TimeTool()
        self._tool_registry = ToolRegistry()
        self._tool_router = ToolRouter()
        self._ruleplanner = RulePlanner(tool_router=self._tool_router)
        self._tool_registry.register_tool(time_tool)
        self._tool_router.add_rule(
            time_tool.get_name(),
            ["现在时间", "当前时间", "现在日期", "当前日期", "now time", "now date"],
        )
        self._in_memory_transcriptStore = InMemoryTranscriptStore()
        self._in_memory_sessionStore = InMemorySessionStore()
        self._runtime_manager = RuntimeManager(
            session_store=self._in_memory_sessionStore,
            transcript_store=self._in_memory_transcriptStore,
        )
        self._agent = ChatAgent(
            model=self._model,
            memory=self._inmemory_memory,
            prompt_builder=self._prompt_builder,
            planner=self._ruleplanner,
            tool_registry=self._tool_registry,
            runtime_manager=self._runtime_manager,
        )

    def chat(
        self, message: str, session_id: str | None = None
    ) -> tuple[AgentOutput, str]:
        resolved_session_id = ensure_session_id(session_id=session_id)
        agent_input = AgentInput(message=message, session_id=resolved_session_id)
        agent_output = self._agent.run(agent_input)
        return agent_output, resolved_session_id

chat_service = ChatService()