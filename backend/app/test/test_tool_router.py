from app.tools.tool_router import ToolRouter
from app.agent.chat_agent import ChatAgent
from app.models.mock_model import MockModel
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry
from app.schemas.agent_input import AgentInput


model = MockModel()
tool_registry = ToolRegistry()
time_tool = TimeTool()
tool_registry.register_tool(time_tool)
tool_router = ToolRouter()
tool_router.add_rule(tool_name = "time_tool",keywords=["时间","现在时间","当前时间","日期","time now","time","几点","现在几点"])
tool_router.add_rule(tool_name = "test_not_exist_tool",keywords=["lala"])
chat_agent = ChatAgent(model=model,tool_registry=tool_registry,tool_router=tool_router)
agent_input = AgentInput(message="你好,现在几点了？")
chat_output = chat_agent.run(agent_input)
print(f"chat_output:{chat_output}")


agent_input = AgentInput(message="小鹿妹妹")
chat_output = chat_agent.run(agent_input)
print(f"chat_output:{chat_output}")

agent_input = AgentInput(message="lala")
chat_output = chat_agent.run(agent_input)
print(f"chat_output:{chat_output}")


