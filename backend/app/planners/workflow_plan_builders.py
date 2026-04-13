"""由 workflow_name 生成完整 planner_result 片段（步骤与动态字段）。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.schemas.agent_input import AgentInput


def build_time_reply_workflow_plan(input_data: AgentInput, *, reason: str) -> dict[str, Any]:
    return {
        "action": "workflow",
        "reason": reason,
        "tool_name": None,
        "workflow_name": "time_reply_workflow",
        "steps": [
            {
                "step_name": "get_time",
                "action": "tool",
                "tool_name": "time_tool",
                "tool_input": {},
            },
            {
                "step_name": "generate_reply",
                "action": "model",
                "prompt_template": "当前时间是{step_output},请生成一句自然回复给用户",
                "use_step_result": "get_time",
            },
        ],
        "context": {},
    }


def build_conditional_workflow_plan(
    input_data: AgentInput, *, reason: str
) -> dict[str, Any]:
    return {
        "action": "workflow",
        "reason": reason,
        "tool_name": None,
        "workflow_name": "conditional_workflow",
        "steps": [
            {
                "step_name": "get_weather",
                "action": "tool",
                "tool_name": "weather_tool",
                "tool_input": {
                    "content": input_data.message,
                },
            },
            {
                "step_name": "generate_reply_if_success",
                "action": "model",
                "prompt_template": "当前天气状况是 {step_output}，请生成一句自然回复给用户",
                "use_step_result": "get_weather",
                "condition": {
                    "depends_on": "get_weather",
                    "field": "success",
                    "equals": True,
                },
            },
            {
                "step_name": "generate_reply_if_failed",
                "action": "model",
                "prompt": "天气工具调用失败了，请给用户一个简短、自然的兜底回复。",
                "condition": {
                    "depends_on": "get_weather",
                    "field": "success",
                    "equals": False,
                },
            },
        ],
        "context": {},
    }


_WORKFLOW_PLAN_BUILDERS: dict[str, Any] = {
    "time_reply_workflow": build_time_reply_workflow_plan,
    "conditional_workflow": build_conditional_workflow_plan,
}


def get_workflow_plan_builder(workflow_name: str):
    builder = _WORKFLOW_PLAN_BUILDERS.get(workflow_name)
    if builder is None:
        raise KeyError(f"no plan builder registered for workflow_name={workflow_name!r}")
    return builder


def register_workflow_plan_builder(
    workflow_name: str, builder: Callable[..., dict[str, Any]]
) -> None:
    """扩展点：注册自定义 workflow 的 plan 构建器（与 WorkflowRegistry 名称一致）。"""
    _WORKFLOW_PLAN_BUILDERS[workflow_name] = builder
