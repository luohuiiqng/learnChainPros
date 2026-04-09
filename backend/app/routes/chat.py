from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.schemas.chat_input_output import ChatRequest, ChatResponse
from app.services.chat_service import chat_service
from app.schemas.transcript_response import TranscriptEntryResponse
from app.schemas.session_response import SessionResponse



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
    agent_output, session_id = chat_service.chat(
        message=message, session_id=payload.session_id
    )
    if not agent_output.success:
        return ChatResponse(
            reply=agent_output.error_message,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
        )
    return ChatResponse(
        reply=agent_output.content,
        session_id=session_id,
        timestamp=datetime.now(timezone.utc),
    )

@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions() -> list[SessionResponse]:
    return chat_service.list_sessions()


@router.get(
    "/sessions/{session_id}/transcript", response_model=list[TranscriptEntryResponse]
)
def get_session_transcript(session_id: str) -> list[TranscriptEntryResponse]:
    return chat_service.get_transcript(session_id=session_id)

