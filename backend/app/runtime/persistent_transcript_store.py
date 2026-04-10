import sqlite3
import json
from app.runtime.runtime_session import RuntimeSession
from app.runtime.base_transcript_store import BaseTranscriptStore
from app.runtime.transcript_entry import TranscriptEntry


class PersistentTranscriptStore(BaseTranscriptStore):
    """把transcript记录持久保存下来的store"""

    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path)
        self._init_table()

    def _init_table(self) -> None:
        self._cursor = self._conn.cursor()
        self._cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS transcript (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            type TEXT NOT NULL,
            user_input TEXT NOT NULL,
            final_output TEXT,
            success BOOLEAN NOT NULL,
            timestamp TEXT NOT NULL,
            runtime_session_json TEXT
        )
        """
        )
        self._conn.commit()

    def append_entry(self, session_id: str, entry: TranscriptEntry) -> None:
        self._cursor.execute(
            """
            INSERT INTO transcript (session_id, type, user_input, final_output,success,timestamp,runtime_session_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                entry.type,
                entry.user_input,
                entry.final_output,
                entry.success,
                entry.timestamp,
                json.dumps(entry.runtime_session.to_dict()),
            ),
        )
        self._conn.commit()

    def get_entries(self, session_id: str) -> list[TranscriptEntry]:
        self._cursor.execute(
            """
        SELECT type, user_input, final_output, success, timestamp, runtime_session_json
        FROM transcript
        WHERE session_id = ?
        ORDER BY id ASC
        """,
            (session_id,),
        )
        rows = self._cursor.fetchall()
        entries: list[TranscriptEntry] = []
        for row in rows:
            runtime_session_data = json.loads(row[5])
            runtime_session = RuntimeSession(
                session_id=runtime_session_data["session_id"],
                user_input=runtime_session_data["user_input"],
            )
            runtime_session.planner_result = runtime_session_data["planner_result"]
            runtime_session.workflow_result = runtime_session_data["workflow_result"]
            runtime_session.tool_calls = runtime_session_data["tool_calls"]
            runtime_session.model_calls = runtime_session_data["model_calls"]
            runtime_session.workflow_trace = runtime_session_data["workflow_trace"]
            runtime_session.final_output = runtime_session_data["final_output"]
            runtime_session.errors = runtime_session_data["errors"]

            entries.append(
                TranscriptEntry(
                    type=row[0],
                    user_input=row[1],
                    final_output=row[2],
                    success=bool(row[3]),
                    timestamp=row[4],
                    runtime_session=runtime_session,
                )
            )

        return entries

    def clear(self, session_id: str) -> None:
        self._cursor.execute(
            "DELETE FROM transcript WHERE session_id = ?",
            (session_id,),
        )
        self._conn.commit()
