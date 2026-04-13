"""一个基础的agent类，提供标准的初始化agent和创建以及使用agent的接口"""
from abc import ABC,abstractmethod
from typing import Any
from app.models.base_model import BaseModel
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.schemas.error_codes import ErrorCode

class  BaseAgent(ABC):
    
    def __init__(self,model:BaseModel=None,**kwargs:Any)->None:
        """
        负责注入模型，工具，配置，记忆模块等依赖
        """
        self._config = kwargs
        self._state = {}
        if model is None:
            raise ValueError(f"error:model is {model}")
        self._model = model
    
    def validate_input(self,input_data:Any)->bool:
        """
        校验输入是否合法，避免子类各写各的
        """
        return input_data is not None and bool(input_data.message.strip())
    
    def plan(self,input_data:Any)->Any:
        """
        如果我们的agent需要先规划再执行，则实现该接口，简单agent返回空即可。
        """
        return None
    @abstractmethod
    def act(self, input_data: AgentInput) -> AgentOutput:
        """
        真正执行任务的核心接口，该方法必须实现
        """
        raise NotImplementedError
    
    def run(self,input_data:AgentInput)->AgentOutput:
        """
        统一编排入口，一般负责：
        先校验
        再规划
        再执行
        最后封装输出
        """
        if not self.validate_input(input_data):
            return AgentOutput(
                content="",
                success=False,
                error_message="输入不合法：message 为空或仅空白",
                error_code=ErrorCode.INVALID_INPUT,
                metadata={"failure_kind": "invalid_input"},
            )
        return self.act(input_data)
    
    def reset(self)->None:
        """
        清空上下文，临时状态，会话缓存，方便复用agent实例
        """
        self._state.clear()
    
    def get_status(self)->dict[str,Any]:
        """
        适合调试，监控，前端展示运行状态
        """
        return {
            "agent_name":self.__class__.__name__,
            "state":self._state,
            "model":self._model.__class__.__name__
        }
