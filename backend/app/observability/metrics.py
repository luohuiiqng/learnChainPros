"""Prometheus 指标；路径标签经归一化以降低基数。"""

from __future__ import annotations

import re

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

_PATH_SESSION = re.compile(r"/sessions/[^/]+")
# transcript 下标与具体 session id 一并归一，避免 Prometheus path 标签爆炸
_PATH_TRANSCRIPT_INDEX_MD = re.compile(r"/transcript/\d+/markdown")

http_request_duration_seconds = Histogram(
    "lcp_http_request_duration_seconds",
    "HTTP 请求耗时（秒）",
    ["method", "path"],
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
    ),
)

http_requests_total = Counter(
    "lcp_http_requests_total",
    "HTTP 请求计数",
    ["method", "path", "status"],
)

chat_completions_total = Counter(
    "lcp_chat_completions_total",
    "聊天完成次数",
    ["outcome"],
)

tool_calls_total = Counter(
    "lcp_tool_calls_total",
    "工具调用次数",
    ["tool_name", "outcome"],
)

model_generations_total = Counter(
    "lcp_model_generations_total",
    "模型 generate 调用次数",
    ["outcome"],
)

planner_route_total = Counter(
    "lcp_planner_route_total",
    "每轮规划路由：planner 给出的 action，或无 planner 时直走模型",
    ["kind"],
)

planner_plan_duration_seconds = Histogram(
    "lcp_planner_plan_duration_seconds",
    "``planner.plan`` 调用耗时（秒）；无 planner 时不记；异常时 ``outcome=error`` 后仍重抛",
    ["outcome"],
    buckets=(
        0.001,
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
    ),
)

workflow_runs_total = Counter(
    "lcp_workflow_runs_total",
    "Workflow 执行结束次数（一次 ``_run_workflow`` 对应一次；``success`` 与 ``AgentOutput`` 一致）",
    ["workflow_name", "outcome"],
)

workflow_duration_seconds = Histogram(
    "lcp_workflow_duration_seconds",
    "已注册 Workflow 从 ``run`` 开始到结束的耗时（秒）；未注册名称走错误分支时不记此项",
    ["workflow_name", "outcome"],
    buckets=(
        0.01,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
        120.0,
    ),
)

agent_act_duration_seconds = Histogram(
    "lcp_agent_act_duration_seconds",
    "单轮 ``ChatAgent.act`` 耗时（含 lifecycle hooks 与 ``_execute_act``）；``outcome`` 与 ``AgentOutput.success`` 一致，若异常逃逸则为 ``error``",
    ["outcome"],
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
        120.0,
    ),
)

agent_act_exceptions_total = Counter(
    "lcp_agent_act_exceptions_total",
    "``ChatAgent.act`` 内未捕获、继续向外抛出的异常次数（含 ``before_act`` / ``_execute_act`` / ``after_act``）",
)

workflow_step_retry_attempts_total = Counter(
    "lcp_workflow_step_retry_attempts_total",
    "Workflow 单步重试次数（不含首次执行；每次进入下一轮尝试前 +1）",
    ["action"],
)


def _normalize_workflow_metric_name(name: str | None) -> str:
    """限制标签长度，避免异常长字符串拉高基数。"""
    s = (name or "unknown").strip()
    if not s:
        s = "unknown"
    return s[:64]


def normalize_http_path(path: str) -> str:
    """将 ``/sessions/<uuid>/...`` 与 ``/transcript/<n>/markdown`` 归一成模板路径。"""
    if not path:
        return "/"
    p = _PATH_SESSION.sub("/sessions/{id}", path)[:200]
    p = _PATH_TRANSCRIPT_INDEX_MD.sub("/transcript/{index}/markdown", p)
    return p


def observe_http_request(
    method: str, path: str, status_code: int, duration_seconds: float
) -> None:
    p = normalize_http_path(path)
    m = (method or "GET").upper()
    status = str(status_code)
    http_requests_total.labels(method=m, path=p, status=status).inc()
    http_request_duration_seconds.labels(method=m, path=p).observe(duration_seconds)


def observe_chat_completion(success: bool) -> None:
    chat_completions_total.labels(
        outcome="success" if success else "error",
    ).inc()


def observe_tool_call(tool_name: str, success: bool) -> None:
    tool_calls_total.labels(
        tool_name=tool_name or "unknown",
        outcome="success" if success else "error",
    ).inc()


def observe_model_generation(success: bool) -> None:
    model_generations_total.labels(
        outcome="success" if success else "error",
    ).inc()


def observe_planner_route(kind: str) -> None:
    """记录单轮规划结果：``workflow`` / ``tool`` / ``model`` 来自 ``planner_result``；无 planner 时为 ``no_planner``。"""
    k = (kind or "unknown").strip().lower()
    if k not in ("workflow", "tool", "model", "no_planner"):
        k = "unknown"
    planner_route_total.labels(kind=k).inc()


def observe_planner_plan_duration(seconds: float, success: bool) -> None:
    """在 ``ChatAgent._execute_act`` 中包裹 ``planner.plan``；成功返回后 ``success=True``。"""
    planner_plan_duration_seconds.labels(
        outcome="success" if success else "error",
    ).observe(max(0.0, float(seconds)))


def observe_workflow_run(workflow_name: str | None, success: bool) -> None:
    """在 ``ChatAgent._run_workflow`` 结束时调用；未注册 workflow 时在返回错误前也会调用一次（``success=False``）。"""
    workflow_runs_total.labels(
        workflow_name=_normalize_workflow_metric_name(workflow_name),
        outcome="success" if success else "error",
    ).inc()


def observe_workflow_duration(
    workflow_name: str | None, seconds: float, success: bool
) -> None:
    """与 ``observe_workflow_run`` 配对，仅在真实执行 ``workflow.run`` 的路径上调用。"""
    workflow_duration_seconds.labels(
        workflow_name=_normalize_workflow_metric_name(workflow_name),
        outcome="success" if success else "error",
    ).observe(max(0.0, float(seconds)))


def observe_agent_act_duration(seconds: float, success: bool) -> None:
    """在 ``ChatAgent.act`` 的 ``finally`` 中调用；若 ``act`` 抛出异常则 ``success`` 应为 ``False``。"""
    agent_act_duration_seconds.labels(
        outcome="success" if success else "error",
    ).observe(max(0.0, float(seconds)))


def observe_agent_act_exception() -> None:
    """与 ``observe_agent_act_duration(..., False)`` 配对，在 ``finally`` 中检测到活跃异常时调用。"""
    agent_act_exceptions_total.inc()


def observe_workflow_step_retry_attempt(action: str) -> None:
    """单步失败后、再次执行前调用；``action`` 为 ``tool`` / ``model`` / ``unknown``。"""
    a = (action or "unknown").strip().lower()
    if a not in ("tool", "model"):
        a = "unknown"
    workflow_step_retry_attempts_total.labels(action=a).inc()


def metrics_response() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
