import os

from app.agent.chat_agent import ChatAgent
from app.memory.in_memory_memory import InMemoryMemory
from app.models.openai_model import OpenAIModel
from app.planners.rule_planner import RulePlanner
from app.prompts.prompt_builder import PromptBuilder
from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.runtime_manager import RuntimeManager
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_router import ToolRouter
from app.runtime.base_session_store import BaseSessionStore
from app.runtime.base_transcript_store import BaseTranscriptStore
from app.runtime.persistent_session_store import PersistentSessionStore
from app.runtime.persistent_transcript_store import PersistentTranscriptStore


class AgentFactory:
    """应用层组装根，负责创建 ChatAgent 及其依赖。"""

    def __init__(
        self, store_backend: str = "memory", db_path: str | None = None
    ) -> None:
        if store_backend == "memory":
            self._session_store = InMemorySessionStore()
            self._transcript_store = InMemoryTranscriptStore()
        elif store_backend == "sqlite":
            if db_path is None:
                raise ValueError("sqlite backend requires db_path...")
            self._session_store = PersistentSessionStore(db_path=db_path)
            self._transcript_store = PersistentTranscriptStore(db_path=db_path)
        else:
            raise ValueError(f"unsupported store_backend: {store_backend}")
        self._memory = InMemoryMemory()
        self._prompt_builder = PromptBuilder()
        self._runtime_manager = RuntimeManager(
            session_store=self._session_store,
            transcript_store=self._transcript_store,
        )

    def create_chat_agent(self) -> ChatAgent:
        api_key = os.getenv("OPENAI_API_KEY")
        model_name = os.getenv("OPENAI_MODEL", "gpt-5.4")
        base_url = os.getenv("OPENAI_BASE_URL")
        organization = os.getenv("OPENAI_ORGANIZATION")

        model = OpenAIModel(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            organization=organization,
        )

        tool_registry = ToolRegistry()
        tool_router = ToolRouter()
        time_tool = TimeTool()
        tool_registry.register_tool(time_tool)
        tool_router.add_rule(
            time_tool.get_name(),
            ["现在时间", "当前时间", "现在日期", "当前日期", "now time", "now date"],
        )
        planner = RulePlanner(tool_router=tool_router)

        return ChatAgent(
            model=model,
            memory=self._memory,
            prompt_builder=self._prompt_builder,
            planner=planner,
            tool_registry=tool_registry,
            runtime_manager=self._runtime_manager,
        )

    def get_session_store(
        self,
    ) -> BaseSessionStore:
        return self._session_store

    def get_transcript_store(self) -> BaseTranscriptStore:
        return self._transcript_store
