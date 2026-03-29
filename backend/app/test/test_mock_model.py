from app.models.mock_model import MockModel
from app.schemas.model_request import ModelRequest

model = MockModel()
response = model.generate(ModelRequest(prompt="你好"))
print(response.content)