from app.models.mock_model import MockModel
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry
from app.workflows.agent_executor import AgentExecutor


def test_agent_executor_tool_step_success() -> None:
    tool_registry = ToolRegistry()
    tool_registry.register_tool(TimeTool())
    tool_executor = AgentExecutor(tool_registry=tool_registry)
    tool_step = {
        "step_name": "get_time",
        "action": "tool",
        "tool_name": "time_tool",
        "tool_input": {},
    }
    tool_result = tool_executor.execute_step(tool_step)
    assert tool_result["step_name"] == "get_time"
    assert tool_result["success"] is True
    assert tool_result["output"] is not None
    assert tool_result["error"] is None


def test_agent_executor_model_step_success() -> None:
    model = MockModel(model_name="mock-executor-model", response_text="mock response")
    model_executor = AgentExecutor(model=model)
    model_step = {
        "step_name": "reply",
        "action": "model",
        "prompt": "你好，请做一个简短回复",
    }
    model_result = model_executor.execute_step(model_step)
    assert model_result["step_name"] == "reply"
    assert model_result["success"] is True
    assert "mock response" in (model_result["output"] or "")
    assert model_result["error"] is None
    mock_status = model.get_mock_status()
    assert mock_status["call_count"] == 1
    assert "你好，请做一个简短回复" in mock_status["last_input"].prompt


def test_agent_executor_tool_step_fails_without_registry() -> None:
    missing_registry_executor = AgentExecutor()
    tool_step = {
        "step_name": "get_time",
        "action": "tool",
        "tool_name": "time_tool",
        "tool_input": {},
    }
    missing_registry_result = missing_registry_executor.execute_step(tool_step)
    assert missing_registry_result["step_name"] == "get_time"
    assert missing_registry_result["success"] is False
    assert missing_registry_result["output"] is None
    assert missing_registry_result["error"] == "tool registry is not configured"


def test_agent_executor_unknown_action() -> None:
    model = MockModel(response_text="x")
    model_executor = AgentExecutor(model=model)
    unknown_step = {"step_name": "unknown_step", "action": "unknown"}
    unknown_result = model_executor.execute_step(unknown_step)
    assert unknown_result["step_name"] == "unknown_step"
    assert unknown_result["success"] is False
    assert unknown_result["output"] is None
    assert unknown_result["error"] == "unknown action: unknown"
