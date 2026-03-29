from dotenv import load_dotenv
load_dotenv()
import os
from app.agent.chat_agent import ChatAgent
from app.schemas.agent_input import AgentInput
from app.models.mock_model import MockModel
from app.agent.chat_agent import ChatAgent
from app.models.openai_model import OpenAIModel

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

chat_agent = ChatAgent(model = model)

input = AgentInput(message="今天是几号呢？")
out_put = chat_agent.run(input_data=input)

print(f"out_put:{out_put}")