import logging

import pytest

from app.planners.planner_rules_loader import PlannerTriggerSpec, WorkflowTriggerRule
from app.planners.rule_planner import RulePlanner
from app.schemas.agent_input import AgentInput
from app.tools.tool_router import ToolRouter


@pytest.fixture
def planner_with_time_router() -> RulePlanner:
    tool_router = ToolRouter()
    tool_router.add_rule(
        tool_name="time_tool",
        keywords=["时间", "现在时间", "当前时间", "几点", "现在几点"],
    )
    return RulePlanner(tool_router=tool_router)


def test_rule_planner_workflow_when_time_and_reply_intent(
    planner_with_time_router: RulePlanner,
) -> None:
    workflow_plan = planner_with_time_router.plan(
        AgentInput(message="现在几点了，回复我一句", session_id="planner-session")
    )
    assert workflow_plan["action"] == "workflow"
    assert len(workflow_plan["steps"]) == 2
    assert workflow_plan["steps"][0]["step_name"] == "get_time"
    assert workflow_plan["steps"][0]["action"] == "tool"
    assert workflow_plan["steps"][0]["tool_name"] == "time_tool"
    assert workflow_plan["steps"][1]["step_name"] == "generate_reply"
    assert workflow_plan["steps"][1]["action"] == "model"
    assert workflow_plan["steps"][1]["use_step_result"] == "get_time"
    assert workflow_plan["context"] == {}


def test_rule_planner_tool_only_when_time_intent(
    planner_with_time_router: RulePlanner,
) -> None:
    tool_plan = planner_with_time_router.plan(
        AgentInput(message="现在几点了？", session_id="planner-session")
    )
    assert tool_plan["action"] == "tool"
    assert tool_plan["tool_name"] == "time_tool"


def test_rule_planner_model_fallback(planner_with_time_router: RulePlanner) -> None:
    model_plan = planner_with_time_router.plan(
        AgentInput(message="你好", session_id="planner-session")
    )
    assert model_plan["action"] == "model"
    assert model_plan.get("tool_name") is None


def test_rule_planner_invalid_input(planner_with_time_router: RulePlanner) -> None:
    invalid_plan = planner_with_time_router.plan(
        AgentInput(message="   ", session_id="planner-session")
    )
    assert invalid_plan["action"] == "model"
    assert invalid_plan["reason"] == "输入数据不合法，无法规划工具调用"


def test_rule_planner_info(planner_with_time_router: RulePlanner) -> None:
    planner_info = planner_with_time_router.get_planner_info()
    assert planner_info["planner_class"] == "RulePlanner"


def test_rule_planner_unknown_workflow_logs_and_falls_back(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING, logger="app.planner.rule")
    spec = PlannerTriggerSpec(
        version=1,
        workflow_triggers=(
            WorkflowTriggerRule(
                workflow_name="nonexistent_workflow_xyz",
                reason="test",
                keyword_groups=(("hello",),),
            ),
        ),
    )
    planner = RulePlanner(tool_router=None, trigger_spec=spec)
    result = planner.plan(AgentInput(message="hello world", session_id="s"))
    assert result["action"] == "model"
    assert any(
        "nonexistent_workflow_xyz" in r.message
        and "plan builder" in r.message
        for r in caplog.records
    )
