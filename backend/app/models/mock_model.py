from typing import Any

from app.models.base_model import BaseModel
from app.schemas.model_request import ModelRequest
from app.schemas.model_response import ModelResponse


class MockModel(BaseModel):
    def __init__(
            self,
            model_name:str = "mock-model",
            response_text:str = "mock response",
            prefix:str = "",
            **kwargs:Any
    )->None:
        super().__init__(model_name,api_key="",**kwargs)
        self._response_text = response_text
        self._prefix = prefix
        self._call_count = 0
        self._last_input = None

    def generate(self,input_data:ModelRequest,**kwargs:Any)->ModelResponse:
        self._call_count += 1
        self._last_input = input_data

        if self._prefix:
            return ModelResponse(content=f"{self._prefix}:{input_data.prompt}")
        
        return ModelResponse(content=f"{self._response_text}:{input_data.prompt}")
    
    def get_mock_status(self)->dict[str,Any]:
        return {
            "call_count":self._call_count,
            "last_input":self._last_input
        }