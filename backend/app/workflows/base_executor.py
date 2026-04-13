from abc import ABC,abstractmethod
from typing import Any


class BaseExecutor(ABC):
    """执行器的统一抽象接口"""
    def __init__(self,**kwargs:Any)->None:
        self._config = kwargs

    @abstractmethod
    def execute_step(
        self,
        step: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError
    
    def get_executor_info(self)->dict[str,Any]:
        return {
            "name": self.__class__.__name__,
            "description": self._config.get("description","No description provided")
        }