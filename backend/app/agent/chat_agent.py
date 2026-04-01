from app.agent.base_agent import BaseAgent
from typing import Any
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.schemas.model_request import ModelRequest
from app.tools.tool_registry import ToolRegistry
from app.models.base_model import BaseModel
from app.schemas.tool_input import ToolInput
from app.schemas.tool_output import ToolOutput
from app.tools.tool_router import ToolRouter
from app.memory.base_memory import BaseMemory
from datetime import datetime
from app.prompts.base_prompt import BasePrompt


class ChatAgent(BaseAgent):
    def __init__(self,model:BaseModel=None,tool_registry:ToolRegistry=None,tool_router:ToolRouter=None,memory:BaseMemory|None=None,**kwargs)->None:
        super().__init__(model = model,**kwargs)
        self._tool_registry = tool_registry
        self._tool_router = tool_router
        self._memory = memory
        self._base_prompt = BasePrompt()

    def call_tool(self,tool_name:str,tool_input:ToolInput)->ToolOutput:
        if self._tool_registry is None:
            return ToolOutput(content= None,error_message="tool registry is not configured",success=False)
        tool = self._tool_registry.get_tool(tool_name)
        if tool is not None:
            return tool.run(tool_input)
        return ToolOutput(content= None,error_message=f"tool not found: {tool_name}",success=False)
    def act(self,input_data:AgentInput,plan:Any = None)->AgentOutput:
        if self._memory is not None and input_data.session_id is not None:
            self._memory.add_message(input_data.session_id,{"role":"user","content":input_data.message,"timestamp": datetime.now().isoformat()})
        if self._tool_router is not None:
            tool_name = self._tool_router.route(input_data.message)
            if tool_name is not None:
                tool_output = self.call_tool(tool_name,ToolInput(params={}))
                if self._memory is not None and input_data.session_id is not None:
                    self._memory.add_message(input_data.session_id,{"role":"assistant","content":tool_output.content or "","timestamp": datetime.now().isoformat()})
                return AgentOutput(content = tool_output.content or "",
                            success=tool_output.success,
                            error_message=tool_output.error_message,
                            metadata=tool_output.metadata
                            )
        if self._memory is not None and input_data.session_id is not None:
            build_prompt = self._base_prompt.build_prompt(messages=self._memory.get_messages(input_data.session_id))
            model_request = ModelRequest(prompt = build_prompt)
        else:
            build_prompt = self._base_prompt.build_prompt(messages=[], current_input=input_data.message)
            model_request = ModelRequest(prompt = build_prompt)
        model_response = self._model.generate(model_request)
        if self._memory is not None and input_data.session_id is not None:
            self._memory.add_message(input_data.session_id,{"role":"assistant","content":model_response.content or "","timestamp": datetime.now().isoformat()})
        return AgentOutput(content = model_response.content or "",
                           success=model_response.success,
                           error_message=model_response.error_message,
                           metadata=model_response.metadata
                           ) 
        