"""与 HTTP / AgentOutput / 日志共用的稳定错误码字符串。"""

from typing import Final


class ErrorCode:
    """逻辑失败与可观测性对齐；未列出的场景可用 ``INTERNAL_ERROR`` 或具体子码。"""

    INVALID_INPUT = "INVALID_INPUT"
    WORKFLOW_NOT_REGISTERED = "WORKFLOW_NOT_REGISTERED"
    WORKFLOW_STEP_FAILED = "WORKFLOW_STEP_FAILED"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    TOOL_ERROR = "TOOL_ERROR"
    MODEL_ERROR = "MODEL_ERROR"
    MODEL_TIMEOUT = "MODEL_TIMEOUT"
    MODEL_NOT_CONFIGURED = "MODEL_NOT_CONFIGURED"
    UNKNOWN_STEP_ACTION = "UNKNOWN_STEP_ACTION"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# Workflow 单步默认「可重试」集合（``AgentExecutor``）；不含 ``TOOL_ERROR`` / ``MODEL_ERROR``，
# 避免把确定性失败当瞬时故障重试。若需重试 ``MODEL_ERROR`` 等，在步骤 JSON 中设置
# ``step_retryable_error_codes`` 白名单覆盖默认值。
DEFAULT_RETRYABLE_STEP_ERROR_CODES: Final[frozenset[str]] = frozenset(
    {
        ErrorCode.TOOL_TIMEOUT,
        ErrorCode.MODEL_TIMEOUT,
    }
)
