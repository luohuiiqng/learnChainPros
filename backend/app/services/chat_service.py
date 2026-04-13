"""聊天应用层服务：封装 ``ChatAgent``、会话与 transcript 的对外能力。"""

from uuid import uuid4

from app.config.settings import Settings
from app.runtime.session_export import runtime_session_to_markdown
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.schemas.session_response import SessionResponse
from app.schemas.transcript_response import TranscriptEntryResponse
from app.services.agent_factory import AgentFactory


def ensure_session_id(session_id: str | None) -> str:
    """若调用方未传 ``session_id``，则生成新的 UUID 字符串。"""
    return session_id or str(uuid4())


class ChatService:
    """通过 ``AgentFactory`` 组装智能体与存储，对外提供对话与只读查询接口。"""

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
        self,
        message: str,
        session_id: str | None = None,
        *,
        request_id: str | None = None,
    ) -> tuple[AgentOutput, str]:
        """执行单轮对话，返回 ``AgentOutput`` 与解析后的 ``session_id``。"""
        resolved_session_id = ensure_session_id(session_id=session_id)
        meta: dict = {}
        if request_id:
            meta["request_id"] = request_id
        agent_input = AgentInput(
            message=message, session_id=resolved_session_id, metadata=meta
        )
        agent_output = self._agent.run(agent_input)
        return agent_output, resolved_session_id

    def list_sessions(self) -> list[SessionResponse]:
        """列出当前存储后端中可见的全部会话元信息。"""
        sessions = self._session_store.list_sessions()
        return [SessionResponse.from_session_dict(session) for session in sessions]

    def get_session(self, session_id: str) -> SessionResponse | None:
        """按 session_id 读取单条元信息；不存在或空 id 时返回 ``None``。"""
        if not session_id or not str(session_id).strip():
            return None
        sid = str(session_id).strip()
        raw = self._session_store.get_session(sid)
        if raw is None:
            return None
        return SessionResponse.from_session_dict(raw)

    def get_transcript(self, session_id: str) -> list[TranscriptEntryResponse]:
        """返回某会话下的全部 transcript 条目（JSON 协议，含 ``RuntimeSessionSnapshot``）。"""
        if not session_id:
            return []
        entries = self._transcript_store.get_entries(session_id)
        return [
            TranscriptEntryResponse.from_transcript_entry(entry) for entry in entries
        ]

    def _transcript_entries_for_session(self, session_id: str) -> list | None:
        """内部：规范化 ``session_id`` 后拉取 transcript 列表。
        返回 ``None`` 表示 id 非法；``[]`` 表示尚无记录。"""
        if not session_id or not str(session_id).strip():
            return None
        return self._transcript_store.get_entries(str(session_id).strip())

    def get_runtime_markdown_at(self, session_id: str, entry_index: int) -> str | None:
        """按 **0-based** 下标导出某一 transcript 条目的 ``RuntimeSession`` Markdown。

        下标与 :meth:`get_transcript` 返回列表顺序一致；越界或无可导出内容时返回 ``None``。"""
        entries = self._transcript_entries_for_session(session_id)
        if entries is None:
            return None
        if entry_index < 0 or entry_index >= len(entries):
            return None
        return runtime_session_to_markdown(entries[entry_index].runtime_session)

    def get_latest_runtime_markdown(self, session_id: str) -> str | None:
        """返回该 session **最后一条** transcript 对应 ``RuntimeSession`` 的 Markdown；无记录时 ``None``。"""
        entries = self._transcript_entries_for_session(session_id)
        if entries is None or not entries:
            return None
        return runtime_session_to_markdown(entries[-1].runtime_session)


# 进程级默认实例，供 FastAPI 路由等直接依赖（与既有 ``from_env`` 行为一致）。
settings = Settings.from_env()
chat_service = ChatService(settings=settings)
