"""``lcp_planner_plan_duration_seconds``。"""

from typing import Any

import pytest
from prometheus_client import REGISTRY

from app.agent.chat_agent import ChatAgent
from app.models.mock_model import MockModel
from app.observability.metrics import observe_planner_plan_duration
from app.planners.base_planner import BasePlanner
from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.runtime_manager import RuntimeManager
from app.schemas.agent_input import AgentInput


def _pp_sum(outcome: str) -> float:
    v = REGISTRY.get_sample_value(
        "lcp_planner_plan_duration_seconds_sum",
        {"outcome": outcome},
    )
    return 0.0 if v is None else float(v)


def test_observe_planner_plan_duration_sum() -> None:
    s0 = _pp_sum("success")
    observe_planner_plan_duration(0.001, True)
    assert _pp_sum("success") == s0 + 0.001
    e0 = _pp_sum("error")
    observe_planner_plan_duration(0.002, False)
    assert _pp_sum("error") == e0 + 0.002


class _ModelPlanner(BasePlanner):
    def plan(self, input_data: Any, context: Any = None) -> dict[str, Any]:
        return {"action": "model", "reason": "test"}


class _BoomPlanner(BasePlanner):
    def plan(self, input_data: Any, context: Any = None) -> dict[str, Any]:
        raise ValueError("planner boom")


def test_chat_agent_planner_plan_records_success_duration() -> None:
    s0 = _pp_sum("success")
    agent = ChatAgent(
        runtime_manager=RuntimeManager(
            session_store=InMemorySessionStore(),
            transcript_store=InMemoryTranscriptStore(),
        ),
        model=MockModel(response_text="ok"),
        planner=_ModelPlanner(),
    )
    out = agent.run(AgentInput(message="hi", session_id="s-pp-ok"))
    assert out.success is True
    assert _pp_sum("success") > s0


def test_chat_agent_planner_plan_exception_records_error_duration() -> None:
    e0 = _pp_sum("error")
    agent = ChatAgent(
        runtime_manager=RuntimeManager(
            session_store=InMemorySessionStore(),
            transcript_store=InMemoryTranscriptStore(),
        ),
        model=MockModel(response_text="ok"),
        planner=_BoomPlanner(),
    )
    with pytest.raises(ValueError, match="planner boom"):
        agent.run(AgentInput(message="hi", session_id="s-pp-boom"))
    assert _pp_sum("error") > e0
