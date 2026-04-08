from abc import ABC,abstractmethod
from typing import Any
from app.schemas.tool_input import ToolInput
from app.schemas.tool_output import ToolOutput

class BaseTool(ABC):
    def __init__(self,name:str,description:str="",**kwargs:Any)->None:
        self._name = name
        self._description = description
        self._config = kwargs
    
    def validate_input(self,tool_input:ToolInput)->bool:
        return tool_input is not None

    def get_name(self) -> str:
        tool_name = self._name
        return tool_name

    def run(self,tool_input:ToolInput)->ToolOutput:
        if not self.validate_input(tool_input=tool_input):
            return ToolOutput(success=False,content="",error_message="tool input validate_input failed..")
        try:
            return self.execute(tool_input=tool_input)
        except Exception as e:
            return ToolOutput(success=False,error_message=f"ToolOutput error:{e}",metadata={"name":self._name})


    @abstractmethod
    def execute(self,tool_input:ToolInput)->ToolOutput:
        raise NotImplementedError

    def get_tool_info(self)->dict[str,Any]:
        return {
            "name":self._name,
            "description":self._description,
            "config":self._config
        }