"""加载 workflow 触发规则（关键词组 JSON）：可选文件路径，否则使用包内默认。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WorkflowTriggerRule:
    workflow_name: str
    reason: str
    keyword_groups: tuple[tuple[str, ...], ...]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> WorkflowTriggerRule:
        name = str(raw.get("workflow_name", "")).strip()
        reason = str(raw.get("reason", "")).strip()
        groups_raw = raw.get("keyword_groups") or []
        groups: list[tuple[str, ...]] = []
        for g in groups_raw:
            if not isinstance(g, list):
                continue
            groups.append(tuple(str(x).strip() for x in g if str(x).strip()))
        if not name or not groups:
            raise ValueError("invalid workflow trigger: missing workflow_name or keyword_groups")
        return cls(
            workflow_name=name,
            reason=reason or name,
            keyword_groups=tuple(groups),
        )


@dataclass(frozen=True)
class PlannerTriggerSpec:
    version: int
    workflow_triggers: tuple[WorkflowTriggerRule, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlannerTriggerSpec:
        version = int(data.get("version", 1))
        rules_raw = data.get("workflow_triggers") or []
        rules = tuple(WorkflowTriggerRule.from_dict(r) for r in rules_raw if isinstance(r, dict))
        return cls(version=version, workflow_triggers=rules)


def _load_package_default() -> PlannerTriggerSpec:
    pkg = "app.planners.data"
    with resources.files(pkg).joinpath("default_workflow_triggers.json").open(
        "r", encoding="utf-8"
    ) as f:
        return PlannerTriggerSpec.from_dict(json.load(f))


def load_planner_trigger_spec(path: str | Path | None) -> PlannerTriggerSpec:
    """若 *path* 已设置则必须存在且为合法 JSON；未设置则用包内默认。"""
    if path:
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"planner rules file not found: {p}")
        with p.open("r", encoding="utf-8") as f:
            return PlannerTriggerSpec.from_dict(json.load(f))
    return _load_package_default()


def message_matches_trigger(message: str, rule: WorkflowTriggerRule) -> bool:
    """每组关键词至少命中一个子串即视为该组满足；所有组都满足则触发。"""
    text = str(message)
    for group in rule.keyword_groups:
        if not group:
            return False
        if not any(kw in text for kw in group):
            return False
    return True
