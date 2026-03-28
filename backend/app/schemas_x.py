from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="User input text")
    session_id: Optional[str] = Field(default=None, description="Conversation session id")


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    timestamp: datetime


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
