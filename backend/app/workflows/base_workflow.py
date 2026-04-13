from abc import ABC,abstractmethod
from typing import Any
from app.workflows.workflow_result import WorkflowResult
from app.workflows.base_executor import BaseExecutor



class BaseWorkflow(ABC):
    """工作流的基础抽象类。"""

    def __init__(self, **kwargs) -> None:
        self._config = kwargs

    @abstractmethod
    def run(
        self,
        steps: list[dict[str, Any]],
        executor: BaseExecutor,
        context: dict[str, Any] | None = None,
    ) -> WorkflowResult:
        """工作流的核心接口，返回 WorkflowResult 标准结果对象"""
        raise NotImplementedError
    
    def get_workflow_info(self)->dict[str,Any]:
        """返回工作流的基本信息，默认返回类名，可以在子类中重写进行具体的信息描述"""
        return {"workflow_class": self.__class__.__name__,"config": self._config }