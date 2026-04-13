from app.models.mock_model import MockModel
from app.schemas.model_request import ModelRequest


def test_mock_model_generate_returns_prefixed_content() -> None:
    model = MockModel()
    response = model.generate(ModelRequest(prompt="你好"))
    assert response.success is True
    assert response.content == "mock response:你好"
