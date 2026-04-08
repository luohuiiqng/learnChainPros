from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.schemas.chat_input_output import ChatRequest, ChatResponse
from app.services.chat_service import ensure_session_id, request_chat_agent



router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    # Strip once and reuse to keep backend/frontend validation behavior aligned.
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
    agent_output = request_chat_agent(message=message, session_id=payload.session_id)
    if not agent_output.success:
        return ChatResponse(
        reply=agent_output.error_message,
        session_id=ensure_session_id(payload.session_id),
        timestamp=datetime.now(timezone.utc),
    )
    return ChatResponse(
        reply=agent_output.content,
        session_id=ensure_session_id(payload.session_id),
        timestamp=datetime.now(timezone.utc),
    )


