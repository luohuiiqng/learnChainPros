from app.memory.base_memory import BaseMemory
from typing import Any


class InMemoryMemory(BaseMemory):
    def __init__(self,**kwargs:Any):
        super().__init__(**kwargs)
        self._messages:dict[str,list[dict[str,Any]]] = {}

    def add_message(self, session_id:str, message:dict[str,Any]):
        if session_id not in self._messages:
            self._messages[session_id] = []
        self._messages[session_id].append(message)

    def get_messages(self, session_id:str)->list[dict[str,Any]]:
        return self._messages.get(session_id,[])
    
    def clear(self,session_id:str)->None:
        self._messages.pop(session_id,None)
        