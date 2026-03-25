from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ensure_session_id, generate_reply

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

    return ChatResponse(
        reply=generate_reply(message),
        session_id=ensure_session_id(payload.session_id),
        timestamp=datetime.now(timezone.utc),
    )


