"""规划器抽象：将用户输入映射为可执行的 ``planner_result``（tool / model / workflow 等）。"""

from abc import ABC, abstractmethod
from typing import Any


class BasePlanner(ABC):
    """所有 Planner 实现的基类，约定 ``plan`` / ``validate_input`` 等行为。"""

    def __init__(self, **kwargs) -> None:
        self._config = kwargs

    @abstractmethod
    def plan(self, input_data: Any, context: Any = None) -> dict[str, Any]:
        """根据输入内容生成最小规则计划结果。"""
        raise NotImplementedError
 
    def validate_input(self, input_data: Any) -> bool:
        """校验输入是否可用于生成计划（非空 message）。"""
        if input_data is None:
            return False

        message = getattr(input_data, "message", None)
        if message is None:
            return False

        return bool(str(message).strip())

    def get_planner_info(self) -> dict[str, Any]:
        """返回规划器的基本信息，默认返回类名，可以在子类中重写进行具体的信息描述"""
        return {"planner_class": self.__class__.__name__, "config": self._config}