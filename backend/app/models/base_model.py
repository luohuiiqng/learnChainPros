from abc import ABC,abstractmethod
from typing import Any
from app.schemas.model_request import ModelRequest
from app.schemas.model_response import ModelResponse


class BaseModel(ABC):
    def __init__(self,model_name:str,api_key:str = "",**kwargs:Any)->None:
        self._model_name = model_name
        self._api_key = api_key
        self._config = kwargs
        self.validate_config()

    def validate_config(self)->None:
        if not self._model_name:
            raise ValueError(f"model_name不能为空:{self._model_name}")

    @abstractmethod
    def generate(self,input_data:ModelRequest,**kwargs:Any)->ModelResponse:
        raise NotImplementedError
    
    def stream_generate(self,input_data:ModelRequest,**kwargs:Any)->ModelResponse:
        raise NotImplementedError("当前模型暂时不支持流式输出...")
    
    def get_model_info(self)->dict[str,Any]:
        return {
            "provider":self.__class__.__name__,
            "model_name":self._model_name,
            "config":self._config
        }