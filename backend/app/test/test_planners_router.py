from dotenv import load_dotenv
load_dotenv()
import os
from app.models.openai_model import OpenAIModel
from app.agent.chat_agent import ChatAgent
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_router import ToolRouter
from app.memory.in_memory_memory import InMemoryMemory
from app.prompts.prompt_builder import PromptBuilder
from app.planners.rule_planner import RulePlanner
from app.tools.time_tool import TimeTool
from app.schemas.agent_input import AgentInput


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


tool_registry = ToolRegistry()
memory = InMemoryMemory()
prompt_builder = PromptBuilder()
tool_router = ToolRouter()

tool_registry.register_tool(TimeTool())
tool_router.add_rule(tool_name = "time_tool",keywords=["时间","现在时间","当前时间","日期","time now","time","几点","现在几点"])
rule_planner = RulePlanner(tool_router=tool_router)

chat_agent = ChatAgent(model=model,tool_registry=tool_registry,
                       memory=memory,prompt_builder=prompt_builder,
                       planner=rule_planner)

agent_input = AgentInput(message="你好,现在几点了？",session_id="test_session_1")
agent_output = chat_agent.run(agent_input)
print(f"agent_output:{agent_output}")


agent_input = AgentInput(message="你叫啥名？",session_id="test_session_1")
agent_output = chat_agent.run(agent_input)
print(f"agent_output:{agent_output}")
                       