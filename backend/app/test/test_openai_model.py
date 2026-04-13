import os

import pytest

from app.schemas.model_request import ModelRequest


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_openai_model_generate_optional() -> None:
    from app.models.openai_model import OpenAIModel

    model = OpenAIModel(
        model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY", ""),
        base_url=os.getenv("OPENAI_BASE_URL"),
        organization=os.getenv("OPENAI_ORGANIZATION"),
    )
    response = model.generate(ModelRequest(prompt="仅回复：OK"))
    from app.test.support_helpers import skip_if_openai_unreachable

    skip_if_openai_unreachable(response)
    assert response.success is True
    assert len((response.content or "").strip()) > 0
