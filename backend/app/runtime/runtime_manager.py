from typing import Any
from app.runtime.base_session_store import BaseSessionStore
from app.runtime.base_transcript_store import BaseTranscriptStore
from app.runtime.runtime_session import RuntimeSession
from app.runtime.transcript_entry import TranscriptEntry
from datetime import datetime


class RuntimeManager:
    def __init__(
        self,
        session_store: BaseSessionStore,
        transcript_store: BaseTranscriptStore,
        **kwargs,
    ):
        self._config = kwargs
        self._session_store = session_store
        self._transcript_store = transcript_store

    def create_runtime_session(
        self,
        session_id: str,
        user_input: str,
    ) -> RuntimeSession:
        runtime_session = RuntimeSession(
            session_id=session_id,
            user_input=user_input,
        )
        return runtime_session

    def ensure_session_exists(self, session_id: str) -> None:
        if not session_id:
            return
        if self._session_store.get_session(session_id=session_id) is None:
            self._session_store.create_session(session_id=session_id, metadata={})
            return
        return

    def build_transcript_entry(
        self,
        type: str,
        user_input: str,
        final_output: str | None,
        success: bool,
        runtime_session: RuntimeSession,
    ) -> TranscriptEntry:
        return TranscriptEntry(
            type=type,
            user_input=user_input,
            final_output=final_output,
            success=success,
            runtime_session=runtime_session,
            timestamp=datetime.now().isoformat(),
        )

    def append_transcript_entry(
        self,
        session_id: str,
        transcript_entry: TranscriptEntry,
    ) -> None:
        if not session_id:
            return

        self._transcript_store.append_entry(
            session_id=session_id, entry=transcript_entry
        )
