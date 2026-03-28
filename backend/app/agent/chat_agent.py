from app.agent.base_agent import BaseAgent
from typing import Any
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.schemas.model_request import ModelRequest


class ChatAgent(BaseAgent):
    #子类暂时没有要额外初始化的逻辑
    # def __init__(self,model:BaseModel=None,**kwargs)->None:
        # if  model is None:
        #     raise ValueError("model is None...")
        # super().__init__(model = model,**kwargs)

    def act(self,input_data:AgentInput,plan:Any = None)->AgentOutput:
        model_request = ModelRequest(prompt = input_data.message)
        model_response = self._model.generate(model_request)
        return AgentOutput(content = model_response.content or "",
                           success=model_response.success,
                           error_message=model_response.error_message,
                           metadata=model_response.metadata
                           ) 
        