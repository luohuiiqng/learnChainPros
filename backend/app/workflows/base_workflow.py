from abc import ABC,abstractmethod
from typing import Any



class BaseWorkflow(ABC):
    """"工作流的基础抽象类"""
    def __init__(self,**kwargs)->None:
        self._config = kwargs

    @abstractmethod
    def run(self,steps:list[dict[str,Any]],executor:Any,context:Any=None)->dict[str,Any]:
        """工作流的核心接口，输入输出都是字典格式，方便适配不同的场景和需求"""
        raise NotImplementedError
    
    def get_workflow_info(self)->dict[str,Any]:
        """返回工作流的基本信息，默认返回类名，可以在子类中重写进行具体的信息描述"""
        return {"workflow_class": self.__class__.__name__,"config": self._config }