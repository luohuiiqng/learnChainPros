from app.agent.base_agent import BaseAgent
from typing import Any
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.schemas.model_request import ModelRequest
from app.tools.tool_registry import ToolRegistry
from app.models.base_model import BaseModel
from app.schemas.tool_input import ToolInput
from app.schemas.tool_output import ToolOutput
from app.memory.base_memory import BaseMemory
from datetime import datetime
from app.prompts.prompt_builder import PromptBuilder
from app.prompts.base_prompt import BasePrompt
from app.planners.base_planner import BasePlanner
from app.runtime.runtime_session import RuntimeSession

class ChatAgent(BaseAgent):
    def __init__(self,model:BaseModel=None,tool_registry:ToolRegistry=None,
                 memory:BaseMemory|None=None,prompt_builder:BasePrompt|None=None,
                 planner:BasePlanner|None=None,**kwargs)->None:
        super().__init__(model = model,**kwargs)
        self._tool_registry = tool_registry
        self._memory = memory
        self._prompt_builder = prompt_builder if prompt_builder is not None else PromptBuilder()
        self._planner = planner

    def _build_output_metadata(
        self,
        metadata: dict[str, Any] | None,
        runtime_session: RuntimeSession,
    ) -> dict[str, Any]:
        merged_metadata = dict(metadata or {})
        merged_metadata["runtime_session"] = runtime_session
        return merged_metadata

    def call_tool(self,tool_name:str,tool_input:ToolInput)->ToolOutput:
        if self._tool_registry is None:
            return ToolOutput(content= None,error_message="tool registry is not configured",success=False)
        tool = self._tool_registry.get_tool(tool_name)
        if tool is not None:
            return tool.run(tool_input)
        return ToolOutput(content= None,error_message=f"tool not found: {tool_name}",success=False)

    def call_model(self, input_data: AgentInput) -> tuple[AgentOutput, str | None]:
        if self._memory is not None and input_data.session_id is not None:
            prompt_text = self._prompt_builder.build_prompt(messages=self._memory.get_messages(input_data.session_id))
            model_request = ModelRequest(prompt = prompt_text)
            model_response = self._model.generate(model_request)
            self._memory.add_message(input_data.session_id,{"role":"assistant","content":model_response.content or "","timestamp": datetime.now().isoformat()})
            return AgentOutput(
                content=model_response.content or "",
                success=model_response.success,
                error_message=model_response.error_message,
                metadata=model_response.metadata,
            ), prompt_text
        else:
            prompt_text = self._prompt_builder.build_prompt(messages=[], current_input=input_data.message)
            model_request = ModelRequest(prompt = prompt_text)
            model_response = self._model.generate(model_request)
            return AgentOutput(
                content=model_response.content or "",
                success=model_response.success,
                error_message=model_response.error_message,
                metadata=model_response.metadata,
            ), prompt_text

    def act(self,input_data:AgentInput,plan:Any = None)->AgentOutput:
        runtime_session = RuntimeSession(
            session_id=input_data.session_id, user_input=input_data.message
        )
        if self._memory is not None and input_data.session_id is not None:
            self._memory.add_message(input_data.session_id,{"role":"user","content":input_data.message,"timestamp": datetime.now().isoformat()})        
        if self._planner is not None:
            plan = self._planner.plan(input_data)
            runtime_session.planner_result = plan
            if plan is not None:
                if plan.get("action")=="tool":
                    tool_name = plan.get("tool_name")
                    if tool_name is not None:
                        tool_output = self.call_tool(tool_name,ToolInput(params={}))
                        runtime_session.add_tool_call(
                            tool_name=tool_name,
                            success=tool_output.success,
                            output=tool_output.content,
                            error=tool_output.error_message,
                        )
                        if self._memory is not None and input_data.session_id is not None:
                            self._memory.add_message(input_data.session_id,{"role":"assistant","content":tool_output.content or "","timestamp": datetime.now().isoformat()})
                        runtime_session.final_output = tool_output.content or ""
                        if not tool_output.success:
                            runtime_session.add_error(
                                f"tool call error: {tool_output.error_message}"
                            )
                        return AgentOutput(
                            content=tool_output.content or "",
                            success=tool_output.success,
                            error_message=tool_output.error_message,
                            metadata=self._build_output_metadata(
                                tool_output.metadata,
                                runtime_session,
                            ),
                        )
                    else:
                        model_output, prompt_text = self.call_model(input_data)
                        runtime_session.add_model_call(
                            prompt=prompt_text or "",
                            success=model_output.success,
                            output=model_output.content,
                            error=model_output.error_message,
                        )
                        if not model_output.success:
                            runtime_session.add_error(
                                f"model call error: {model_output.error_message}"
                            )
                        runtime_session.final_output = model_output.content or ""
                        model_output.metadata = self._build_output_metadata(
                            model_output.metadata,
                            runtime_session,
                        )
                        return model_output
                else:
                    model_output, prompt_text = self.call_model(input_data)
                    runtime_session.add_model_call(
                        prompt=prompt_text or "",
                        success=model_output.success,
                        output=model_output.content,
                        error=model_output.error_message,
                    )
                    if not model_output.success:
                        runtime_session.add_error(
                            f"model call error: {model_output.error_message}"
                        )
                    runtime_session.final_output = model_output.content or ""
                    model_output.metadata = self._build_output_metadata(
                        model_output.metadata,
                        runtime_session,
                    )
                    return model_output
            else:
                model_output, prompt_text = self.call_model(input_data)
                runtime_session.add_model_call(
                    prompt=prompt_text or "",
                    success=model_output.success,
                    output=model_output.content,
                    error=model_output.error_message,
                )
                if not model_output.success:
                    runtime_session.add_error(
                        f"model call error: {model_output.error_message}"
                    )
                runtime_session.final_output = model_output.content or ""
                model_output.metadata = self._build_output_metadata(
                    model_output.metadata,
                    runtime_session,
                )
                return model_output
                    
        else:
            model_output, prompt_text = self.call_model(input_data)
            runtime_session.add_model_call(
                prompt=prompt_text or "",
                success=model_output.success,
                output=model_output.content,
                error=model_output.error_message,
            )
            if not model_output.success:
                runtime_session.add_error(
                    f"model call error: {model_output.error_message}"
                )
            runtime_session.final_output = model_output.content or ""
            model_output.metadata = self._build_output_metadata(
                model_output.metadata,
                runtime_session,
            )
            return model_output
