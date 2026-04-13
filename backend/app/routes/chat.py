"""HTTP 路由：聊天、会话与 transcript 只读接口（前缀由 ``main`` 挂载为 ``/agent_api``）。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import PlainTextResponse

from app.observability import metrics as prom_metrics
from app.routes.deps import require_read_api
from app.schemas.chat_input_output import ChatRequest, ChatResponse
from app.services.chat_service import chat_service
from app.schemas.transcript_response import TranscriptEntryResponse
from app.schemas.session_response import SessionResponse



router = APIRouter(tags=["chat"])
_chat_log = logging.getLogger("app.chat")  # 与结构化日志字段配合，便于按 request_id 检索


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="单轮对话",
    responses={
        400: {"description": "message 为空或超长"},
        500: {"description": "内部错误（如 Agent 链路未捕获异常）"},
    },
)
def chat(request: Request, payload: ChatRequest) -> ChatResponse:
    """单轮对话入口：校验消息长度与空串，并透传 ``request_id`` 至 Agent 元数据。"""
    # 与前端约定一致：先 strip 再判空，避免前后端校验行为不一致。
    message = payload.message.strip()
    if not message:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "BAD_REQUEST", "message": "message不能为空"}},
        )
    if len(message) > 2000:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "BAD_REQUEST", "message": "message长度不能超过2000"}},
        )
    rid = getattr(request.state, "request_id", None)
    try:
        agent_output, session_id = chat_service.chat(
            message=message, session_id=payload.session_id, request_id=rid
        )
    except Exception as exc:
        prom_metrics.observe_chat_completion(False)
        _chat_log.error(
            "chat_failed",
            exc_info=(type(exc), exc, exc.__traceback__),
            extra={
                "request_id": rid,
                "session_id": payload.session_id,
            },
        )
        raise
    prom_metrics.observe_chat_completion(agent_output.success)
    _chat_log.info(
        "chat_completed",
        extra={
            "request_id": rid,
            "session_id": session_id,
            "outcome": "success" if agent_output.success else "error",
        },
    )
    if not agent_output.success:
        return ChatResponse(
            reply=agent_output.error_message or "",
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
            request_id=rid,
            error_code=agent_output.error_code,
        )
    return ChatResponse(
        reply=agent_output.content,
        session_id=session_id,
        timestamp=datetime.now(timezone.utc),
        request_id=rid,
        error_code=None,
    )

@router.get(
    "/sessions",
    response_model=list[SessionResponse],
    summary="列出会话",
    dependencies=[Depends(require_read_api)],
    responses={403: {"description": "只读接口已禁用"}},
)
def list_sessions() -> list[SessionResponse]:
    """返回当前后端可见的会话元信息列表。"""
    return chat_service.list_sessions()


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="按 ID 获取会话元信息",
    dependencies=[Depends(require_read_api)],
    responses={
        403: {"description": "只读接口已禁用"},
        404: {"description": "session 不存在"},
    },
)
def read_session(session_id: str) -> SessionResponse:
    """按主键读取一条 session；不存在时 404。"""
    result = chat_service.get_session(session_id=session_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "session不存在",
                }
            },
        )
    return result


@router.get(
    "/sessions/{session_id}/transcript/latest/markdown",
    response_class=PlainTextResponse,
    summary="最新一轮 RuntimeSession 的 Markdown 导出",
    dependencies=[Depends(require_read_api)],
    responses={
        403: {"description": "只读接口已禁用"},
        404: {"description": "无 transcript 或无可导出记录"},
    },
)
def get_latest_runtime_markdown(session_id: str) -> PlainTextResponse:
    """调试：导出**最新一轮** ``RuntimeSession`` 的 Markdown（实现同内核 ``runtime_session_to_markdown``）。"""
    text = chat_service.get_latest_runtime_markdown(session_id=session_id)
    if text is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "无可导出的运行记录",
                }
            },
        )
    return PlainTextResponse(
        content=text, media_type="text/markdown; charset=utf-8"
    )


@router.get(
    "/sessions/{session_id}/transcript/{entry_index}/markdown",
    response_class=PlainTextResponse,
    summary="按 subscript 导出某一轮 RuntimeSession 的 Markdown",
    dependencies=[Depends(require_read_api)],
    responses={
        403: {"description": "只读接口已禁用"},
        404: {"description": "下标越界或无可导出记录"},
    },
)
def get_runtime_markdown_by_index(
    session_id: str,
    entry_index: Annotated[
        int,
        Path(ge=0, description="transcript 列表下标，从 0 开始，与 JSON transcript 顺序一致"),
    ],
) -> PlainTextResponse:
    """调试：按 transcript **0-based** 下标导出对应轮次的 Markdown。"""
    text = chat_service.get_runtime_markdown_at(session_id, entry_index)
    if text is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "无可导出的运行记录或下标越界",
                }
            },
        )
    return PlainTextResponse(
        content=text, media_type="text/markdown; charset=utf-8"
    )


@router.get(
    "/sessions/{session_id}/transcript",
    response_model=list[TranscriptEntryResponse],
    summary="获取会话 transcript（JSON）",
    dependencies=[Depends(require_read_api)],
    responses={403: {"description": "只读接口已禁用"}},
)
def get_session_transcript(session_id: str) -> list[TranscriptEntryResponse]:
    """返回该会话全部 transcript 条目（内含 ``RuntimeSessionSnapshot``）。"""
    return chat_service.get_transcript(session_id=session_id)

