from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户输入文本（服务端会 strip；空串返回 400）")
    session_id: Optional[str] = Field(
        default=None,
        description="会话 ID；省略时服务端生成新 UUID",
    )


class ChatResponse(BaseModel):
    """单轮对话响应：HTTP 多为 200；Agent 逻辑失败时仍为 200，见 ``error_code`` 与 ``reply``。"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "reply": "你好，很高兴见到你。",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2026-04-13T10:00:00Z",
                    "request_id": "req-abc",
                    "error_code": None,
                },
                {
                    "reply": "未注册的工作流: demo_wf",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2026-04-13T10:00:00Z",
                    "request_id": "req-abc",
                    "error_code": "WORKFLOW_NOT_REGISTERED",
                },
            ]
        }
    )

    reply: str = Field(
        ...,
        description="助手回复正文；逻辑失败时多为错误说明文案，稳定分支请用 error_code",
    )
    session_id: str = Field(..., description="本条对话归属的会话 ID")
    timestamp: datetime = Field(..., description="服务端生成响应时间（UTC）")
    request_id: Optional[str] = Field(
        default=None,
        description="与请求/响应头 X-Request-ID 一致，便于日志对账与客服排障",
    )
    error_code: Optional[str] = Field(
        default=None,
        description=(
            "逻辑失败时的稳定码，与 ``AgentOutput.error_code`` / ``ErrorCode`` 一致（如 "
            "WORKFLOW_NOT_REGISTERED、WORKFLOW_STEP_FAILED、MODEL_ERROR）；"
            "成功时为 null"
        ),
    )


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
