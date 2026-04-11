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

    def _build_step_result(
        self,
        step_name: str,
        action: str,
        success: bool,
        output: Any,
        error: str | None,
        input_summary: str,
        output_summary: str,
    ) -> dict[str, Any]:
        """构建执行结果"""
        return {
            "step_name": step_name,
            "action": action,
            "success": success,
            "output": output,
            "error": error,
            "input_summary": input_summary,
            "output_summary": output_summary,
        }
    def execute_step(self,step:Any,context:Any=None)->dict[str,Any]:
        action = step.get("action","unknown")
        step_name = step.get("step_name","unknown")

        if action == "tool":
            tool_name = step.get("tool_name")
            tool_input_params = step.get("tool_input", {})
            input_summary = f"tool={tool_name},params={tool_input_params}"
            if self._tool_registry is None:
                return self._build_step_result(
                    step_name=step_name,
                    action=action,
                    success=False,
                    output=None,
                    error="tool registry is not configured",
                    input_summary=input_summary,
                    output_summary="tool registry missing",
                )
            tool = self._tool_registry.get_tool(tool_name)
            if tool is None:
                return self._build_step_result(
                    step_name=step_name,
                    action=action,
                    success=False,
                    output=None,
                    error=f"tool not found: {tool_name}",
                    input_summary=input_summary,
                    output_summary="tool lookup failed",
                )
            else:
                tool_output = tool.run(ToolInput(params=tool_input_params))
                return self._build_step_result(
                    step_name=step_name,
                    action=action,
                    success=tool_output.success,
                    output=tool_output.content,
                    error=tool_output.error_message,
                    input_summary=input_summary,
                    output_summary=f"tool returned: {tool_output.content}",
                )
        elif action == "model":
            if self._model is None:
                return self._build_step_result(
                    step_name=step_name,
                    action=action,
                    success=False,
                    output=None,
                    error="model is not configured",
                    input_summary="model execution requested",
                    output_summary="model missing",
                )
            prompt = step.get("prompt", "")
            prompt_template = step.get("prompt_template")
            use_step_result = step.get("use_step_result")

            if prompt_template and use_step_result:
                if context is None:
                    return self._build_step_result(
                        step_name=step_name,
                        action=action,
                        success=False,
                        output=None,
                        error="context is not provided for prompt template",
                        input_summary=f"prompt_template={prompt_template}",
                        output_summary="missing context",
                    )

                step_results = context.get("step_results", {})
                previous_result = step_results.get(use_step_result)
                if previous_result is None:
                    return self._build_step_result(
                        step_name=step_name,
                        action=action,
                        success=False,
                        output=None,
                        error=f"no step result found for key: {use_step_result}",
                        input_summary=f"depends_on={use_step_result}",
                        output_summary="dependency missing",
                    )

                step_output = previous_result.get("output")
                prompt = prompt_template.format(step_output=step_output)

            model_output = self._model.generate(ModelRequest(prompt=prompt))
            return self._build_step_result(
                step_name=step_name,
                action=action,
                success=model_output.success,
                output=model_output.content,
                error=model_output.error_message,
                input_summary=f"prompt={prompt}",
                output_summary=f"model returned: {model_output.content}",
            )
        return self._build_step_result(
            step_name=step_name,
            action=action,
            success=False,
            output=None,
            error=f"unknown action: {action}",
            input_summary=f"unsupported action: {action}",
            output_summary="executor rejected step",
        )