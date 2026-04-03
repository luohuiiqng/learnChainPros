from  abc import ABC,abstractmethod
from typing import Any


class BasePlanner(ABC):
    def __init__(self,**kwargs)->None:
        self._config = kwargs

    @abstractmethod
    def plan(self,input_data:Any,context:Any=None)->dict[str,Any]:
        """根据输入内容生成最小规则计划结果。"""
        raise NotImplementedError
 
    def validate_input(self,input_data:Any)->bool:
        """根据输入生成最小计划结果"""
        if input_data is None:
            return False

        message = getattr(input_data, "message", None)
        if message is None:
            return False

        return bool(str(message).strip())

    def get_planner_info(self)->dict[str,Any]:
        """返回规划器的基本信息，默认返回类名，可以在子类中重写进行具体的信息描述"""
        return {"planner_class": self.__class__.__name__,"config": self._config }