from app.runtime.base_transcript_store import BaseTranscriptStore
from typing import Any


class InMemoryTranscriptStore(BaseTranscriptStore):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._store: dict[str, list[dict[str, Any]]] = {}

    def append_entry(self, session_id: str, entry: dict[str, Any]) -> None:
        self._store.setdefault(session_id, []).append(entry)

    def get_entries(self, session_id: str) -> list[dict[str, Any]]:
        return self._store.get(session_id, [])

    def clear(self, session_id: str) -> None:
        """清除指定会话的所有运行记录"""
        self._store.pop(session_id, None)
