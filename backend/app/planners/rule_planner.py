import logging
from typing import Any

from app.planners.base_planner import BasePlanner
from app.planners.planner_rules_loader import (
    PlannerTriggerSpec,
    WorkflowTriggerRule,
    load_planner_trigger_spec,
    message_matches_trigger,
)
from app.planners.workflow_plan_builders import get_workflow_plan_builder
from app.tools.tool_router import ToolRouter

_log = logging.getLogger("app.planner.rule")


class RulePlanner(BasePlanner):
    def __init__(
        self,
        tool_router: ToolRouter | None = None,
        *,
        trigger_spec: PlannerTriggerSpec | None = None,
        rules_path: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._tool_router = tool_router
        if trigger_spec is not None:
            self._trigger_spec = trigger_spec
        else:
            self._trigger_spec = load_planner_trigger_spec(rules_path)
        self._workflow_rules = self._build_resolved_workflow_rules(self._trigger_spec)

    @staticmethod
    def _build_resolved_workflow_rules(
        spec: PlannerTriggerSpec,
    ) -> tuple[tuple[WorkflowTriggerRule, Any], ...]:
        """仅保留已在 ``workflow_plan_builders`` 注册的规则；缺失名称打一次 WARNING。"""
        resolved: list[tuple[WorkflowTriggerRule, Any]] = []
        missing: set[str] = set()
        for rule in spec.workflow_triggers:
            try:
                builder = get_workflow_plan_builder(rule.workflow_name)
            except KeyError:
                missing.add(rule.workflow_name)
                continue
            resolved.append((rule, builder))
        if missing:
            _log.warning(
                "planner trigger rules skip workflow_name(s) with no registered plan builder: %s",
                sorted(missing),
            )
        return tuple(resolved)

    def plan(self, input_data: Any, context: Any = None) -> dict[str, Any]:
        """根据输入内容生成最小规则计划结果。"""
        if not self.validate_input(input_data):
            return {
                "action": "model",
                "reason": "输入数据不合法，无法规划工具调用",
                "tool_name": None,
                "workflow_name": None,
                "steps": [],
                "context": {},
            }
        message = input_data.message
        for rule, builder in self._workflow_rules:
            if not message_matches_trigger(message, rule):
                continue
            return builder(input_data, reason=rule.reason)

        tool_name = (
            self._tool_router.route(input_data.message) if self._tool_router else None
        )
        if tool_name is not None:
            return {
                "action": "tool",
                "reason": "命中工具路由规则",
                "tool_name": tool_name,
                "workflow_name": None,
                "steps": [],
                "context": {},
            }

        return {
            "action": "model",
            "reason": "未命中workflow或tool规则，回退到模型",
            "tool_name": None,
            "workflow_name": None,
            "steps": [],
            "context": {},
        }
