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
import os





def ensure_session_id(session_id: str | None) -> str:
    return session_id or str(uuid4())

def request_chat_agent(message: str, session_id: str = None) -> AgentOutput:
    api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("OPENAI_MODEL","gpt-5.4")
    base_url = os.getenv("OPENAI_BASE_URL")
    organization = os.getenv("OPENAI_ORGANIZATION")
    model = OpenAIModel(
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        organization= organization
    )
    inmemoryMemory = InMemoryMemory()
    promptBuilder = PromptBuilder()
    ruleplanner = RulePlanner()
    time_tool = TimeTool()
    tool_registry = ToolRegistry()
    tool_router = ToolRouter()
    tool_registry.register_tool(time_tool)
    tool_router.add_rule(
        time_tool.get_name(),
        ["现在时间", "当前时间", "现在日期", "当前日期", "now time", "now date"],
    )
    inMemoryTranscriptStore = InMemoryTranscriptStore()
    inMemorySessionStore = InMemorySessionStore()
    chat_agent = ChatAgent(
        model=model,
        memory=inmemoryMemory,
        prompt_builder=promptBuilder,
        planner=ruleplanner,
        tool_registry=tool_registry,
        transcript_store=inMemoryTranscriptStore,
        session_store=inMemorySessionStore,
    )
    print("888888888")
    agent_input = AgentInput(message=message, session_id=session_id)
    return chat_agent.run(agent_input)
