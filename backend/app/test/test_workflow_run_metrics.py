"""工作流执行指标 ``lcp_workflow_runs_total``。"""

from prometheus_client import REGISTRY

from app.observability.metrics import observe_workflow_duration, observe_workflow_run


def _wf_count(name: str, outcome: str) -> float:
    v = REGISTRY.get_sample_value(
        "lcp_workflow_runs_total",
        {"workflow_name": name, "outcome": outcome},
    )
    return 0.0 if v is None else float(v)


def test_observe_workflow_run_increments() -> None:
    n0 = _wf_count("time_reply_workflow", "success")
    observe_workflow_run("time_reply_workflow", True)
    assert _wf_count("time_reply_workflow", "success") == n0 + 1.0

    e0 = _wf_count("conditional_workflow", "error")
    observe_workflow_run("conditional_workflow", False)
    assert _wf_count("conditional_workflow", "error") == e0 + 1.0


def test_observe_workflow_run_none_name_uses_unknown() -> None:
    u0 = _wf_count("unknown", "success")
    observe_workflow_run(None, True)
    assert _wf_count("unknown", "success") == u0 + 1.0


def _wf_duration_sum(name: str, outcome: str) -> float:
    v = REGISTRY.get_sample_value(
        "lcp_workflow_duration_seconds_sum",
        {"workflow_name": name, "outcome": outcome},
    )
    return 0.0 if v is None else float(v)


def test_observe_workflow_duration_sum() -> None:
    s0 = _wf_duration_sum("time_reply_workflow", "success")
    observe_workflow_duration("time_reply_workflow", 0.05, True)
    assert _wf_duration_sum("time_reply_workflow", "success") == s0 + 0.05
    e0 = _wf_duration_sum("conditional_workflow", "error")
    observe_workflow_duration("conditional_workflow", 0.1, False)
    assert _wf_duration_sum("conditional_workflow", "error") == e0 + 0.1
