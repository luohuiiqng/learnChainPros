from uuid import uuid4
from app.agent.chat_agent import ChatAgent
from app.models.openai_model import OpenAIModel
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
import os





def ensure_session_id(session_id: str | None) -> str:
    return session_id or str(uuid4())

def request_chat_agent(message:str)->AgentOutput:
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

    agent_input = AgentInput(message=message)
    return chat_agent.run(agent_input)
