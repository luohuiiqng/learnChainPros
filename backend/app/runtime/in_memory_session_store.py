from app.runtime.base_session_store import BaseSessionStore
from typing import Any
from datetime import datetime


class InMemorySessionStore(BaseSessionStore):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._store = dict[str, dict[str, Any]]()

    def create_session(self, session_id: str, metadata: Any) -> None:
        session = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self._store[session_id] = session

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self._store.get(session_id)

    def list_sessions(self) -> list[dict[str, Any]]:
        sessions = []
        for session_id in self._store:
            sessions.append(
                {
                    "session_id": session_id,
                    "metadata": self._store.get(session_id).get("metadata"),
                    "created_at": self._store.get(session_id).get("created_at"),
                    "updated_at": self._store.get(session_id).get("updated_at"),
                }
            )

        return sessions
