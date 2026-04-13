"""规划路由指标 ``lcp_planner_route_total`` 的单元测试。"""

from prometheus_client import REGISTRY

from app.observability.metrics import observe_planner_route


def _route_count(kind: str) -> float:
    v = REGISTRY.get_sample_value("lcp_planner_route_total", {"kind": kind})
    return 0.0 if v is None else float(v)


def test_observe_planner_route_increments_known_kinds() -> None:
    w0 = _route_count("workflow")
    observe_planner_route("workflow")
    assert _route_count("workflow") == w0 + 1.0

    observe_planner_route("tool")
    observe_planner_route("model")
    observe_planner_route("no_planner")


def test_observe_planner_route_maps_unknown_action() -> None:
    u0 = _route_count("unknown")
    observe_planner_route("not_valid_action_xyz")
    assert _route_count("unknown") == u0 + 1.0
