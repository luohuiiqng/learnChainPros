import time

import pytest
from fastapi.testclient import TestClient

from app.schemas.tool_input import ToolInput
from app.schemas.tool_output import ToolOutput
from app.tools.base_tool import BaseTool
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_runner import run_tool_with_timeout
from app.workflows.agent_executor import AgentExecutor


@pytest.fixture
def client() -> TestClient:
    import sys
    import types

    if "openai" not in sys.modules:
        fake = types.ModuleType("openai")

        class FakeOpenAI:
            def __init__(self, *args, **kwargs) -> None:
                pass

        fake.OpenAI = FakeOpenAI
        sys.modules["openai"] = fake

    from app.main import app

    return TestClient(app)


class _SlowTool(BaseTool):
    def execute(self, tool_input: ToolInput) -> ToolOutput:
        time.sleep(0.8)
        return ToolOutput(content="done")


def test_run_tool_with_timeout_returns_tool_timeout() -> None:
    tool = _SlowTool(name="slow", description="")
    out = run_tool_with_timeout(tool, ToolInput(params={}), 0.15)
    assert out.success is False
    assert out.metadata.get("error_code") == "TOOL_TIMEOUT"


def test_agent_executor_applies_tool_timeout() -> None:
    reg = ToolRegistry()
    reg.register_tool(_SlowTool(name="slow", description=""))
    executor = AgentExecutor(tool_registry=reg, tool_timeout_seconds=0.2)
    step = {
        "step_name": "s1",
        "action": "tool",
        "tool_name": "slow",
        "tool_input": {},
    }
    result = executor.execute_step(step, context={})
    assert result["success"] is False
    assert result["error"]


def test_metrics_endpoint_returns_prometheus(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "lcp_http_requests_total" in response.text
