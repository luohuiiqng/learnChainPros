from pydantic import BaseModel
from app.schemas.runtime_snapshot import RuntimeSessionSnapshot
from app.runtime.transcript_entry import TranscriptEntry


class TranscriptEntryResponse(BaseModel):
    """一条transcript记录的对外响应结构"""

    type: str
    user_input: str
    final_output: str | None
    success: bool
    timestamp: str
    runtime_session: RuntimeSessionSnapshot

    @classmethod
    def from_transcript_entry(cls, entry: TranscriptEntry) -> "TranscriptEntryResponse":
        return cls(
            type=entry.type,
            user_input=entry.user_input,
            final_output=entry.final_output,
            success=entry.success,
            timestamp=entry.timestamp,
            runtime_session=RuntimeSessionSnapshot.from_runtime_session(
                entry.runtime_session
            ),
        )
