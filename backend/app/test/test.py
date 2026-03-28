from app.models.mock_model import MockModel
from app.agent.chat_agent import ChatAgent
from app.schemas.agent_input import AgentInput

model = MockModel(prefix = "mock_model")
agent = ChatAgent(model)
response = agent.run(AgentInput(message = "你好,我是你哥哥！"))
print(f"response:{response}")