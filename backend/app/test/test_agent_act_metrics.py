"""``lcp_agent_act_duration_seconds`` / ``lcp_agent_act_exceptions_total``。"""

import pytest
from prometheus_client import REGISTRY

from app.agent.chat_agent import ChatAgent
from app.models.mock_model import MockModel
from app.observability.metrics import observe_agent_act_duration, observe_agent_act_exception
from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.runtime_manager import RuntimeManager
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput


def _act_sum(outcome: str) -> float:
    v = REGISTRY.get_sample_value(
        "lcp_agent_act_duration_seconds_sum",
        {"outcome": outcome},
    )
    return 0.0 if v is None else float(v)


def test_observe_agent_act_duration_sum() -> None:
    s0 = _act_sum("success")
    observe_agent_act_duration(0.02, True)
    assert _act_sum("success") == s0 + 0.02
    e0 = _act_sum("error")
    observe_agent_act_duration(0.03, False)
    assert _act_sum("error") == e0 + 0.03


def _exc_count() -> float:
    v = REGISTRY.get_sample_value("lcp_agent_act_exceptions_total")
    return 0.0 if v is None else float(v)


def test_observe_agent_act_exception_increments() -> None:
    n0 = _exc_count()
    observe_agent_act_exception()
    assert _exc_count() == n0 + 1.0


class _BoomAfterHook:
    def before_act(self, input_data: AgentInput) -> None:
        pass

    def after_act(self, input_data: AgentInput, output: AgentOutput) -> None:
        raise RuntimeError("hook boom")


def test_chat_agent_after_act_raises_metrics() -> None:
    e0 = _act_sum("error")
    x0 = _exc_count()
    agent = ChatAgent(
        runtime_manager=RuntimeManager(
            session_store=InMemorySessionStore(),
            transcript_store=InMemoryTranscriptStore(),
        ),
        model=MockModel(response_text="ok"),
        planner=None,
        hooks=(_BoomAfterHook(),),
    )
    with pytest.raises(RuntimeError, match="hook boom"):
        agent.run(AgentInput(message="hi", session_id="s-hook-boom"))
    assert _exc_count() == x0 + 1.0
    assert _act_sum("error") > e0
