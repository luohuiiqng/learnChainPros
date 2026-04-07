from abc import ABC, abstractmethod
from typing import Any


class BaseSessionStore(ABC):
    def __init__(self, **kwargs: Any):
        """管理会话元信息的抽象存储接口"""
        self._config = kwargs

    @abstractmethod
    def create_session(self, session_id: str, metadata: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_session(self, session_id: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def list_sessions(self) -> list[dict[str, Any]]:
        raise NotImplementedError
