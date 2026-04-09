import sqlite3
import json
from typing import Any
from datetime import datetime
from app.runtime.base_session_store import BaseSessionStore


class PersistentSessionStore(BaseSessionStore):
    """把session元信息持久保持现在的store"""

    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path)
        self._init_table()

    def _init_table(self) -> None:
        self._cursor = self._conn.cursor()
        self._cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata_json TEXT NOT NULL
        )
        """
        )
        self._conn.commit()

    def create_session(
        self,
        session_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        now = datetime.now().isoformat()
        self._cursor.execute(
            """
            INSERT INTO sessions (session_id, created_at, updated_at, metadata_json)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, now, now, json.dumps(metadata or {})),
        )
        self._conn.commit()

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        self._cursor.execute(
            "SELECT session_id, created_at, updated_at, metadata_json FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        row = self._cursor.fetchone()
        if row is None:
            return None
        return {
            "session_id": row[0],
            "created_at": row[1],
            "updated_at": row[2],
            "metadata": json.loads(row[3]),
        }

    def list_sessions(self) -> list[dict[str, Any]]:
        self._cursor.execute(
            "SELECT session_id, created_at, updated_at, metadata_json FROM sessions"
        )
        rows = self._cursor.fetchall()
        return [
            {
                "session_id": row[0],
                "created_at": row[1],
                "updated_at": row[2],
                "metadata": json.loads(row[3]),
            }
            for row in rows
        ]
