from app.agent.chat_agent import ChatAgent
from app.models.openai_model import OpenAIModel
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_router import ToolRouter
from app.memory.in_memory_memory import InMemoryMemory
from app.prompts.prompt_builder import PromptBuilder
from app.workflows.sequential_workflow import SequentialWorkflow
from app.workflows.agent_executor import AgentExecutor
from app.schemas.agent_input import AgentInput
from app.planners.rule_planner import RulePlanner
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("OPENAI_MODEL", "gpt-5.4")
base_url = os.getenv("OPENAI_BASE_URL")
organization = os.getenv("OPENAI_ORGANIZATION")

model = OpenAIModel(
    model_name=model_name, api_key=api_key, base_url=base_url, organization=organization
)

tool_registry = ToolRegistry()
time_tool = TimeTool()
tool_registry.register_tool(time_tool)
tool_router = ToolRouter()
tool_router.add_rule(
    tool_name="time_tool",
    keywords=[
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
plan = RulePlanner()
prompt_builder = PromptBuilder()
chat_agent = ChatAgent(
    model=model,
    tool_registry=tool_registry,
    tool_router=tool_router,
    memory=memory,
    planner=plan,
    prompt_builder=prompt_builder,
)
agent_input = AgentInput(message="请回复我现在几点？", session_id="test_session_1")

agent_output = chat_agent.run(agent_input)
print("=========================agent_output==========================")
print(f"agent_output:{agent_output}")
