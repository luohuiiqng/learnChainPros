from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any

from app.models.base_model import BaseModel
from app.observability.metrics import observe_workflow_step_retry_attempt
from app.schemas.error_codes import DEFAULT_RETRYABLE_STEP_ERROR_CODES, ErrorCode
from app.schemas.model_request import ModelRequest
from app.schemas.model_response import ModelResponse
from app.schemas.tool_input import ToolInput
from app.schemas.tool_output import ToolOutput
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_runner import run_tool_with_timeout
from app.workflows.base_executor import BaseExecutor


def _run_model_with_timeout(
    model: BaseModel,
    model_request: ModelRequest,
    timeout_seconds: float | None,
) -> ModelResponse:
    if timeout_seconds is None or timeout_seconds <= 0:
        return model.generate(model_request)
    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(model.generate, model_request)
        try:
            return fut.result(timeout=timeout_seconds)
        except FuturesTimeoutError:
            return ModelResponse(
                content=None,
                success=False,
                error_message=f"模型调用超过 {timeout_seconds:g}s 上限",
                metadata={"error_code": ErrorCode.MODEL_TIMEOUT},
            )


class AgentExecutor(BaseExecutor):
    def __init__(
        self,
        model: BaseModel | None = None,
        tool_registry: ToolRegistry | None = None,
        *,
        tool_timeout_seconds: float | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._model = model
        self._tool_registry = tool_registry
        self._tool_timeout_seconds = tool_timeout_seconds

    def _parse_step_timeout(self, step: dict[str, Any]) -> float | None:
        raw = step.get("step_timeout_seconds")
        if raw is None:
            return None
        try:
            t = float(raw)
        except (TypeError, ValueError):
            return None
        if t <= 0:
            return None
        return t

    def _resolve_tool_timeout(self, step: dict[str, Any]) -> float | None:
        st = self._parse_step_timeout(step)
        if st is not None:
            return st
        return self._tool_timeout_seconds

    def _model_timeout_for_step(self, step: dict[str, Any]) -> float | None:
        return self._parse_step_timeout(step)

    def _parse_retry_max(self, step: dict[str, Any]) -> int:
        try:
            n = int(step.get("step_retry_max", 0) or 0)
        except (TypeError, ValueError):
            return 0
        return min(max(0, n), 5)

    def _build_step_result(
        self,
        step_name: str,
        action: str,
        success: bool,
        output: Any,
        error: str | None,
        input_summary: str,
        output_summary: str,
        *,
        error_code: str | None = None,
    ) -> dict[str, Any]:
        d: dict[str, Any] = {
            "step_name": step_name,
            "action": action,
            "success": success,
            "output": output,
            "error": error,
            "input_summary": input_summary,
            "output_summary": output_summary,
        }
        if error_code:
            d["error_code"] = error_code
        return d

    def _tool_error_code(self, tool_output: ToolOutput) -> str:
        mc = (tool_output.metadata or {}).get("error_code")
        if mc:
            return str(mc)
        return ErrorCode.TOOL_ERROR

    def _retryable_codes_for_step(self, step: dict[str, Any]) -> frozenset[str]:
        """默认见 ``DEFAULT_RETRYABLE_STEP_ERROR_CODES``；步骤可设 ``step_retryable_error_codes`` 覆盖。"""
        raw = step.get("step_retryable_error_codes")
        if isinstance(raw, list):
            return frozenset(str(x).strip() for x in raw if str(x).strip())
        return DEFAULT_RETRYABLE_STEP_ERROR_CODES

    def _step_failure_is_retryable(
        self, step: dict[str, Any], step_result: dict[str, Any]
    ) -> bool:
        """``TOOL_NOT_FOUND`` 等不在默认可重试集合内；勿默认重试 ``TOOL_ERROR``。"""
        if step_result.get("success"):
            return False
        ec = step_result.get("error_code")
        if not ec:
            return False
        return ec in self._retryable_codes_for_step(step)

    def execute_step(
        self,
        step: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        max_retries = self._parse_retry_max(step)
        attempt = 0
        last: dict[str, Any] | None = None
        while True:
            last = self._execute_step_once(step, context)
            if last.get("success"):
                if attempt > 0:
                    last["retry_count"] = attempt
                return last
            if not self._step_failure_is_retryable(step, last):
                return last
            if attempt >= max_retries:
                if attempt > 0:
                    last["retry_count"] = attempt
                return last
            observe_workflow_step_retry_attempt(step.get("action", "unknown"))
            attempt += 1

    def _execute_step_once(
        self,
        step: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        action = step.get("action", "unknown")
        step_name = step.get("step_name", "unknown")

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
                    error_code=ErrorCode.TOOL_ERROR,
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
                    error_code=ErrorCode.TOOL_NOT_FOUND,
                )
            tool_output = run_tool_with_timeout(
                tool,
                ToolInput(params=tool_input_params),
                self._resolve_tool_timeout(step),
            )
            ec = self._tool_error_code(tool_output) if not tool_output.success else None
            return self._build_step_result(
                step_name=step_name,
                action=action,
                success=tool_output.success,
                output=tool_output.content,
                error=tool_output.error_message,
                input_summary=input_summary,
                output_summary=f"tool returned: {tool_output.content}",
                error_code=ec,
            )
        if action == "model":
            if self._model is None:
                return self._build_step_result(
                    step_name=step_name,
                    action=action,
                    success=False,
                    output=None,
                    error="model is not configured",
                    input_summary="model execution requested",
                    output_summary="model missing",
                    error_code=ErrorCode.MODEL_NOT_CONFIGURED,
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
                        error_code=ErrorCode.WORKFLOW_STEP_FAILED,
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
                        error_code=ErrorCode.WORKFLOW_STEP_FAILED,
                    )

                step_output = previous_result.get("output")
                prompt = prompt_template.format(step_output=step_output)

            model_output = _run_model_with_timeout(
                self._model,
                ModelRequest(prompt=prompt),
                self._model_timeout_for_step(step),
            )
            ec = None
            if not model_output.success:
                ec = (model_output.metadata or {}).get("error_code")
                ec = str(ec) if ec else ErrorCode.MODEL_ERROR
            return self._build_step_result(
                step_name=step_name,
                action=action,
                success=model_output.success,
                output=model_output.content,
                error=model_output.error_message,
                input_summary=f"prompt={prompt}",
                output_summary=f"model returned: {model_output.content}",
                error_code=ec,
            )
        return self._build_step_result(
            step_name=step_name,
            action=action,
            success=False,
            output=None,
            error=f"unknown action: {action}",
            input_summary=f"unsupported action: {action}",
            output_summary="executor rejected step",
            error_code=ErrorCode.UNKNOWN_STEP_ACTION,
        )
