from typing import Any

from openai import OpenAI

from app.models.base_model import BaseModel
from app.observability import metrics as prom_metrics
from app.schemas.model_request import ModelRequest
from app.schemas.model_response import ModelResponse


class OpenAIModel(BaseModel):
    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: str | None = None,
        organization: str | None = None,
        *,
        timeout: float = 120.0,
        max_retries: int = 2,
        **kwargs: Any,
    ) -> None:
        super().__init__(model_name=model_name, api_key=api_key, **kwargs)
        self._base_url = base_url
        self._organization = organization
        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            organization=self._organization,
            timeout=timeout,
            max_retries=max_retries,
        )
    def validate_config(self)->None:
        super().validate_config()
        if not self._api_key:
            raise ValueError("api_key is empty")
    def generate(self,input_data:ModelRequest,**kwargs:Any)->ModelResponse:
        if not input_data.prompt.strip():
            return ModelResponse(
                content=None,
                success=False,
                error_message="prompt 不能为空",
                metadata={"model_name": self._model_name},
            )
        try:
            response = self._client.responses.create(
                model=self._model_name, input=input_data.prompt
            )
            try:
                content = response.output[0].content[0].text.strip().strip('"')
            except Exception:
                content = "模型返回格式异常，无法解析回答"
            prom_metrics.observe_model_generation(True)
            return ModelResponse(
                content=content,
                success=True,
                metadata={"model_name": self._model_name},
            )
        except Exception as e:
            prom_metrics.observe_model_generation(False)
            meta: dict[str, Any] = {"model_name": self._model_name}
            err_name = type(e).__name__
            if err_name.endswith("TimeoutError") or err_name == "TimeoutError":
                meta["error_code"] = "MODEL_TIMEOUT"
            elif err_name in ("APIConnectionError", "ConnectError", "ReadTimeout"):
                meta["error_code"] = "MODEL_NETWORK"
            return ModelResponse(
                content=f"调用模型失败：{str(e)}",
                success=False,
                error_message=str(e),
                metadata=meta,
            )

        
