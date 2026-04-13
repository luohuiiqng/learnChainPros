"""planner_rules_loader：默认加载、自定义路径、关键词匹配。"""

import json
import tempfile
from pathlib import Path

import pytest

from app.planners.planner_rules_loader import (
    PlannerTriggerSpec,
    WorkflowTriggerRule,
    load_planner_trigger_spec,
    message_matches_trigger,
)


def test_load_default_when_path_none() -> None:
    spec = load_planner_trigger_spec(None)
    assert isinstance(spec, PlannerTriggerSpec)
    assert spec.version == 1
    assert len(spec.workflow_triggers) >= 2
    names = {r.workflow_name for r in spec.workflow_triggers}
    assert "time_reply_workflow" in names
    assert "conditional_workflow" in names


def test_load_missing_path_raises() -> None:
    missing = Path(tempfile.gettempdir()) / "planner_rules_nonexistent_xyz.json"
    with pytest.raises(FileNotFoundError, match="planner rules file not found"):
        load_planner_trigger_spec(missing)


def test_load_custom_json_file() -> None:
    data = {
        "version": 2,
        "workflow_triggers": [
            {
                "workflow_name": "time_reply_workflow",
                "reason": "custom",
                "keyword_groups": [["alpha"], ["beta"]],
            }
        ],
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f)
        path = Path(f.name)
    try:
        spec = load_planner_trigger_spec(path)
        assert spec.version == 2
        assert len(spec.workflow_triggers) == 1
        assert spec.workflow_triggers[0].reason == "custom"
    finally:
        path.unlink(missing_ok=True)


def test_message_matches_trigger_and_groups() -> None:
    rule = WorkflowTriggerRule(
        workflow_name="x",
        reason="r",
        keyword_groups=(("foo", "FOO"), ("bar",)),
    )
    assert message_matches_trigger("foo and bar", rule) is True
    assert message_matches_trigger("FOO bar", rule) is True
    assert message_matches_trigger("foo only", rule) is False
    assert message_matches_trigger("bar only", rule) is False


def test_empty_keyword_group_never_matches() -> None:
    rule = WorkflowTriggerRule(
        workflow_name="x",
        reason="r",
        keyword_groups=(("a",), ()),
    )
    assert message_matches_trigger("a", rule) is False
