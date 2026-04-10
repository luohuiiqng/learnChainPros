import os
from uuid import uuid4
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.services.agent_factory import AgentFactory
from app.schemas.transcript_response import TranscriptEntryResponse
from app.schemas.session_response import SessionResponse


def ensure_session_id(session_id: str | None) -> str:
    return session_id or str(uuid4())


class ChatService:
    def __init__(
        self,
        agent_factory: AgentFactory | None = None,
        store_backend: str = "memory",
        db_path: str | None = None,
    ) -> None:
        self._agent_factory = agent_factory or AgentFactory(
            store_backend=store_backend, db_path=db_path
        )
        self._agent = self._agent_factory.create_chat_agent()
        self._session_store = self._agent_factory.get_session_store()
        self._transcript_store = self._agent_factory.get_transcript_store()

    def chat(
        self, message: str, session_id: str | None = None
    ) -> tuple[AgentOutput, str]:
        resolved_session_id = ensure_session_id(session_id=session_id)
        agent_input = AgentInput(message=message, session_id=resolved_session_id)
        agent_output = self._agent.run(agent_input)
        return agent_output, resolved_session_id

    def list_sessions(self) -> list[SessionResponse]:
        sessions = self._session_store.list_sessions()
        return [SessionResponse.from_session_dict(session) for session in sessions]

    def get_transcript(self, session_id: str) -> list[TranscriptEntryResponse]:
        if not session_id:
            return []
        entries = self._transcript_store.get_entries(session_id)
        return [
            TranscriptEntryResponse.from_transcript_entry(entry) for entry in entries
        ]

store_backend = os.getenv("STORE_BACKEND", "memory")
runtime_db_path = os.getenv("RUNTIME_DB_PATH", "/tmp/runtime.db")
chat_service = ChatService(store_backend=store_backend, db_path=runtime_db_path)
