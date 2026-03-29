from dotenv import load_dotenv
load_dotenv()
import os
from app.models.openai_model import OpenAIModel
from app.schemas.model_request import ModelRequest


api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("OPENAI_MODEL","gpt-5.4")
base_url = os.getenv("OPENAI_BASE_URL")
organization = os.getenv("OPENAI_ORGANIZATION")

model = OpenAIModel(
    model_name=model_name,
    api_key=api_key,
    base_url=base_url,
    organization= organization
    )
model_request = ModelRequest(prompt="你好!")
response = model.generate(input_data= model_request)
print(f"response:{response}")