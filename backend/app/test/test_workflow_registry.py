from typing import Any

from prometheus_client import REGISTRY

from app.agent.chat_agent import ChatAgent
from app.models.mock_model import MockModel
from app.planners.base_planner import BasePlanner
from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.runtime_manager import RuntimeManager
from app.schemas.agent_input import AgentInput
from app.workflows.workflow_registry import WorkflowRegistry, build_default_workflow_registry


def test_build_default_registry_has_core_workflows() -> None:
    reg = build_default_workflow_registry()
    assert reg.get("time_reply_workflow") is not None
    assert reg.get("conditional_workflow") is not None
    assert reg.get("nonexistent") is None


def test_unknown_workflow_returns_graceful_agent_output() -> None:
    class UnknownWorkflowPlanner(BasePlanner):
        def plan(self, input_data: Any, context: Any = None) -> dict[str, Any]:
            return {
                "action": "workflow",
                "workflow_name": "not_registered_xyz",
                "steps": [],
                "context": {},
            }

    rm = RuntimeManager(
        session_store=InMemorySessionStore(),
        transcript_store=InMemoryTranscriptStore(),
    )
    agent = ChatAgent(
        runtime_manager=rm,
        model=MockModel(response_text="x"),
        planner=UnknownWorkflowPlanner(),
        workflow_registry=WorkflowRegistry(),
    )
    wf_err_before = REGISTRY.get_sample_value(
        "lcp_workflow_runs_total",
        {"workflow_name": "not_registered_xyz", "outcome": "error"},
    )
    wf_err_before = 0.0 if wf_err_before is None else float(wf_err_before)
    out = agent.run(AgentInput(message="hi", session_id="wf-unknown"))
    assert out.success is False
    assert "未注册的工作流" in (out.content or "")
    wf_err_after = REGISTRY.get_sample_value(
        "lcp_workflow_runs_total",
        {"workflow_name": "not_registered_xyz", "outcome": "error"},
    )
    assert float(wf_err_after or 0.0) == wf_err_before + 1.0

