from app.workflows.base_executor import BaseExecutor
from typing import Any
from app.schemas.tool_input import ToolInput
from app.models.base_model import BaseModel
from app.tools.tool_registry import ToolRegistry
from app.schemas.model_request import ModelRequest


class AgentExecutor(BaseExecutor):
    def __init__(self,model:BaseModel=None,tool_registry:ToolRegistry=None,**kwargs)->None:
        super().__init__(**kwargs)
        self._model = model
        self._tool_registry = tool_registry

    def execute_step(self,step:Any,context:Any=None)->dict[str,Any]:
        action = step.get("action","unknown")
        step_name = step.get("step_name","unknown")

        if action == "tool":
            tool_name = step.get("tool_name")
            tool_input = ToolInput(params=step.get("tool_input",{}))
            if self._tool_registry is None:
                return {
                    "step_name": step_name,
                    "success": False,
                    "output": None,
                    "error": "tool registry is not configured"
                }
            tool = self._tool_registry.get_tool(tool_name)
            if tool is not None:
                tool_output = tool.run(tool_input)
                return {
                    "step_name": step_name,
                    "success": tool_output.success,
                    "output":tool_output.content,
                    "error":tool_output.error_message
                }
            else:
                return {
                    "step_name": step_name,
                    "success": False,
                    "output": None,
                    "error": f"tool not found: {tool_name}"
                }
        elif action == "model":
            if self._model is None:
                return {
                    "step_name": step_name,
                    "success": False,
                    "output": None,
                    "error": "model is not configured"
                }
            else:
                prompt = step.get("prompt","")
                prompt_template = step.get("prompt_template")
                use_step_result = step.get("use_step_result",False)
                if prompt_template and use_step_result:
                    if context is None:
                        return {
                            "step_name": step_name,
                            "success": False,
                            "output": None,
                            "error": "context is not provided for using prompt template with step result"
                        }
                    step_results = context.get("step_results",{})
                    previous_result = step_results.get(use_step_result)

                    if previous_result is None:
                        return {
                            "step_name": step_name,
                            "success": False,
                            "output": None,
                            "error": f"no step result found in context for key: {use_step_result}"
                        }
                    step_output = previous_result.get("output")
                    prompt = prompt_template.format(step_output=step_output)
                model_output = self._model.generate(ModelRequest(prompt=prompt))
                return {
                    "step_name": step_name,
                    "success": model_output.success,
                    "output":model_output.content,
                    "error":model_output.error_message
                }
        else:
            return {
                "step_name": step_name,
                "success": False,
                "output": None,
                "error": f"unknown action: {action}"
            }