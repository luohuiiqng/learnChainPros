from app.agent.chat_agent import ChatAgent
from app.tools.tool_registry import ToolRegistry
from app.schemas.agent_input import AgentInput
from app.tools.time_tool import TimeTool
from app.models.openai_model import OpenAIModel
from app.memory.in_memory_memory import InMemoryMemory
from dotenv import load_dotenv
import os
from app.tools.tool_router import ToolRouter

load_dotenv()

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
session_id = "test_session_1"
time_tool = TimeTool()
tool_registry = ToolRegistry()
tool_registry.register_tool(time_tool)
tool_router = ToolRouter()
tool_router.add_rule(tool_name = "time_tool",keywords=["时间","现在时间","当前时间","日期","time now","time","几点","现在几点"])
tool_router.add_rule(tool_name = "test_not_exist_tool",keywords=["lala"])
memory = InMemoryMemory()
chat_agent = ChatAgent(model = model,tool_registry=tool_registry,tool_router=tool_router,memory=memory)

agent_input_1 = AgentInput(message="你好，请记住我叫张三!",session_id=session_id)
agent_output = chat_agent.run(agent_input_1)
print(f"agent_output:{agent_output}")
agent_input_2 = AgentInput(message="你能告诉我现在几点了么？",session_id=session_id)
agent_output = chat_agent.run(agent_input_2)
print(f"agent_output:{agent_output}")
agent_input_3 = AgentInput(message="你还记得我叫什么名字吗？",session_id=session_id)
agent_output = chat_agent.run(agent_input_3)
print(f"agent_output:{agent_output}")