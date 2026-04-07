from abc import ABC, abstractmethod
from typing import Any


class BaseTranscriptStore(ABC):
    def __init__(self, **kwargs: Any):
        self._config = kwargs

    @abstractmethod
    def append_entry(self, session_id: str, entry: dict[str, Any]) -> None:
        """将新的运行记录追加到指定会话的记录中"""
        raise NotImplementedError("append_entry方法需要在子类中实现")

    @abstractmethod
    def get_entries(self, session_id: str) -> list[dict[str, Any]]:
        """获取指定会话的所有运行记录，返回一个列表，每个元素是一个字典，包含角色和内容等信息"""
        raise NotImplementedError("get_entries方法需要在子类中实现")

    @abstractmethod
    def clear(self, session_id: str) -> None:
        """清除指定会话的所有运行记录"""
        raise NotImplementedError("clear方法需要在子类中实现")
