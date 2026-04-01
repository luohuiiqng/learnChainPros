from abc import ABC,abstractmethod
from typing import Any


class BaseMemory(ABC):
    """会话记忆组件的统一抽象接口"""
    def __init__(self,**kwargs:Any)->None:
        self._config = kwargs

    @abstractmethod
    def add_message(self,session_id:str,message:dict[str,Any]):
        raise NotImplementedError   

    @abstractmethod
    def get_messages(self,session_id:str)->list[dict[str,Any]]:
        raise NotImplementedError

    @abstractmethod
    def clear(self,session_id:str)->None:
        raise NotImplementedError

    def get_recent_messages(self,session_id:str,limit:int=10)->list[dict[str,Any]]:
        messages = self.get_messages(session_id=session_id)
        return messages[-limit:]

    def has_memory(self,session_id:str)->bool:
        return bool(self.get_messages(session_id=session_id))