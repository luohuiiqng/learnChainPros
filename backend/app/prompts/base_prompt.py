from typing import Any
from abc import ABC,abstractmethod

class BasePrompt(ABC):
    def __init__(self, **kwargs) -> None:
        self._config = kwargs
    @abstractmethod
    def format_history(self,messages:list[dict[str,Any]])->str:
        raise NotImplementedError
    @abstractmethod
    def build_prompt(
            self,
            messages:list[dict[str,Any]],
            current_input:str|None = None,
    )->str:
        raise NotImplementedError
    
    