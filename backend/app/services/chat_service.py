from uuid import uuid4
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.services.agent_factory import AgentFactory
from app.schemas.transcript_response import TranscriptEntryResponse
from app.schemas.session_response import SessionResponse
from app.config.settings import Settings


def ensure_session_id(session_id: str | None) -> str:
    return session_id or str(uuid4())


class ChatService:
    def __init__(
        self,
        settings: Settings,
        agent_factory: AgentFactory | None = None,
    ) -> None:
        self._settings = settings or Settings.from_env()
        self._agent_factory = agent_factory or AgentFactory(
            store_backend=self._settings.store_backend,
            db_path=self._settings.runtime_db_path,
        )
        self._agent = self._agent_factory.create_chat_agent(settings=self._settings)
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

settings = Settings.from_env()
chat_service = ChatService(settings=settings)
