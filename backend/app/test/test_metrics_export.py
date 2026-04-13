"""``/metrics`` 文本包含本仓库登记的核心指标名，防止重命名或漏注册破坏看板。"""

from app.observability.metrics import metrics_response

# 与 ``app/observability/metrics.py`` 中 Histogram/Counter 名一致（不含 ``_bucket`` 等后缀）
_EXPECTED_LCP_METRIC_NAMES = (
    "lcp_http_request_duration_seconds",
    "lcp_http_requests_total",
    "lcp_chat_completions_total",
    "lcp_tool_calls_total",
    "lcp_model_generations_total",
    "lcp_planner_route_total",
    "lcp_planner_plan_duration_seconds",
    "lcp_workflow_runs_total",
    "lcp_workflow_duration_seconds",
    "lcp_agent_act_duration_seconds",
    "lcp_agent_act_exceptions_total",
    "lcp_workflow_step_retry_attempts_total",
)


def test_generate_latest_contains_core_metric_names() -> None:
    body, ctype = metrics_response()
    assert ctype
    text = body.decode()
    for name in _EXPECTED_LCP_METRIC_NAMES:
        assert name in text, f"missing metric name in export: {name}"
