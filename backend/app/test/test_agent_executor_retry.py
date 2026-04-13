"""Workflow 单步重试与 Prometheus 计数。"""

from prometheus_client import REGISTRY

from app.models.mock_model import MockModel
from app.schemas.error_codes import ErrorCode
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry
from app.workflows.agent_executor import AgentExecutor


def _retry_metric(action: str) -> float:
    v = REGISTRY.get_sample_value(
        "lcp_workflow_step_retry_attempts_total",
        {"action": action},
    )
    return 0.0 if v is None else float(v)


def test_step_retry_max_eventually_calls_real_step(monkeypatch) -> None:
    reg = ToolRegistry()
    reg.register_tool(TimeTool())
    ex = AgentExecutor(
        model=MockModel(response_text="x"),
        tool_registry=reg,
        tool_timeout_seconds=30.0,
    )
    step = {
        "step_name": "s1",
        "action": "tool",
        "tool_name": "time_tool",
        "tool_input": {},
        "step_retry_max": 2,
    }
    calls = {"n": 0}
    real_once = AgentExecutor._execute_step_once

    def _patched_once(self, step, context):
        calls["n"] += 1
        if calls["n"] < 3:
            return {
                "step_name": step["step_name"],
                "action": "tool",
                "success": False,
                "output": None,
                "error": "transient",
                "input_summary": "",
                "output_summary": "",
                "error_code": ErrorCode.TOOL_TIMEOUT,
            }
        return real_once(self, step, context)

    monkeypatch.setattr(AgentExecutor, "_execute_step_once", _patched_once)
    out = ex.execute_step(step, context={})
    assert out["success"] is True
    assert out.get("retry_count") == 2


def test_tool_not_found_does_not_retry_or_increment_metric() -> None:
    t0 = _retry_metric("tool")
    reg = ToolRegistry()
    reg.register_tool(TimeTool())
    ex = AgentExecutor(
        model=MockModel(response_text="x"),
        tool_registry=reg,
        tool_timeout_seconds=30.0,
    )
    step = {
        "step_name": "s1",
        "action": "tool",
        "tool_name": "missing_tool_xyz",
        "tool_input": {},
        "step_retry_max": 3,
    }
    out = ex.execute_step(step, context={})
    assert out["success"] is False
    assert out.get("error_code") == ErrorCode.TOOL_NOT_FOUND
    assert _retry_metric("tool") == t0


def test_tool_timeout_retries_increment_prometheus(monkeypatch) -> None:
    t0 = _retry_metric("tool")
    reg = ToolRegistry()
    reg.register_tool(TimeTool())
    ex = AgentExecutor(
        model=MockModel(response_text="x"),
        tool_registry=reg,
        tool_timeout_seconds=30.0,
    )
    step = {
        "step_name": "s1",
        "action": "tool",
        "tool_name": "time_tool",
        "tool_input": {},
        "step_retry_max": 1,
    }
    real_once = AgentExecutor._execute_step_once
    calls = {"n": 0}

    def _fail_once_then_ok(self, st, ctx):
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "step_name": st["step_name"],
                "action": "tool",
                "success": False,
                "output": None,
                "error": "timeout",
                "input_summary": "",
                "output_summary": "",
                "error_code": ErrorCode.TOOL_TIMEOUT,
            }
        return real_once(self, st, ctx)

    monkeypatch.setattr(AgentExecutor, "_execute_step_once", _fail_once_then_ok)
    out = ex.execute_step(step, context={})
    assert out["success"] is True
    assert _retry_metric("tool") == t0 + 1.0


def test_step_retryable_error_codes_can_include_tool_error(monkeypatch) -> None:
    t0 = _retry_metric("tool")
    reg = ToolRegistry()
    reg.register_tool(TimeTool())
    ex = AgentExecutor(
        model=MockModel(response_text="x"),
        tool_registry=reg,
        tool_timeout_seconds=30.0,
    )
    step = {
        "step_name": "s1",
        "action": "tool",
        "tool_name": "time_tool",
        "tool_input": {},
        "step_retry_max": 1,
        "step_retryable_error_codes": [ErrorCode.TOOL_ERROR],
    }
    real_once = AgentExecutor._execute_step_once
    calls = {"n": 0}

    def _fail_tool_error_then_ok(self, st, ctx):
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "step_name": st["step_name"],
                "action": "tool",
                "success": False,
                "output": None,
                "error": "transient",
                "input_summary": "",
                "output_summary": "",
                "error_code": ErrorCode.TOOL_ERROR,
            }
        return real_once(self, st, ctx)

    monkeypatch.setattr(AgentExecutor, "_execute_step_once", _fail_tool_error_then_ok)
    out = ex.execute_step(step, context={})
    assert out["success"] is True
    assert _retry_metric("tool") == t0 + 1.0


def test_empty_step_retryable_error_codes_disables_all_retries(monkeypatch) -> None:
    t0 = _retry_metric("tool")
    reg = ToolRegistry()
    reg.register_tool(TimeTool())
    ex = AgentExecutor(
        model=MockModel(response_text="x"),
        tool_registry=reg,
        tool_timeout_seconds=30.0,
    )
    calls = {"n": 0}

    def _always_timeout(self, st, ctx):
        calls["n"] += 1
        return {
            "step_name": st["step_name"],
            "action": "tool",
            "success": False,
            "output": None,
            "error": "t",
            "input_summary": "",
            "output_summary": "",
            "error_code": ErrorCode.TOOL_TIMEOUT,
        }

    monkeypatch.setattr(AgentExecutor, "_execute_step_once", _always_timeout)
    step = {
        "step_name": "s1",
        "action": "tool",
        "tool_name": "time_tool",
        "tool_input": {},
        "step_retry_max": 3,
        "step_retryable_error_codes": [],
    }
    out = ex.execute_step(step, context={})
    assert out["success"] is False
    assert calls["n"] == 1
    assert _retry_metric("tool") == t0
