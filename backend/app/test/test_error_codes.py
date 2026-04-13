from app.schemas.error_codes import DEFAULT_RETRYABLE_STEP_ERROR_CODES, ErrorCode


def test_default_retryable_step_codes_exclude_tool_and_model_error() -> None:
    assert ErrorCode.TOOL_TIMEOUT in DEFAULT_RETRYABLE_STEP_ERROR_CODES
    assert ErrorCode.MODEL_TIMEOUT in DEFAULT_RETRYABLE_STEP_ERROR_CODES
    assert ErrorCode.TOOL_ERROR not in DEFAULT_RETRYABLE_STEP_ERROR_CODES
    assert ErrorCode.MODEL_ERROR not in DEFAULT_RETRYABLE_STEP_ERROR_CODES
