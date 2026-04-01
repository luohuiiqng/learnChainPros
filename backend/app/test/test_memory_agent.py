from dotenv import load_dotenv
load_dotenv()
import os
from app.agent.chat_agent import ChatAgent
from app.tools.tool_registry import ToolRegistry
from app.schemas.agent_input import AgentInput
from app.tools.time_tool import TimeTool
from app.models.openai_model import OpenAIModel
from app.memory.in_memory_memory import InMemoryMemory
from app.tools.tool_router import ToolRouter



api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("OPENAI_MODEL","gpt-5.4")
base_url = os.getenv("OPENAI_BASE_URL")
organization = os.getenv("OPENAI_ORGANIZATION")



session_id = "test_session_1"
time_tool = TimeTool()
tool_registry = ToolRegistry()
tool_registry.register_tool(time_tool)

model = OpenAIModel(
    model_name=model_name,
    api_key=api_key,
    base_url=base_url,
    organization= organization
    )
model_request = AgentInput(message="你好,现在几点了？",session_id=session_id)
tool_router = ToolRouter()
tool_router.add_rule(tool_name = "time_tool",keywords=["时间","现在时间","当前时间","日期","time now","time","几点","现在几点"])
tool_router.add_rule(tool_name = "test_not_exist_tool",keywords=["lala"])
memory = InMemoryMemory()
chat_agent = ChatAgent(model = model,tool_registry=tool_registry,tool_router=tool_router,memory=memory)

agent_output = chat_agent.run(model_request)
print(f"agent_output:{agent_output}")

model_request = AgentInput(message="你好!",session_id=session_id)
agent_output = chat_agent.run(model_request)
print(f"agent_output:{agent_output}")

print(f"memory content:{memory.get_messages(session_id)}")