"""从 AgentInput.metadata 提取可进入 AgentOutput 的轻量观测字段。"""

from typing import Any

_TRACE_KEYS = ("request_id", "correlation_id")


def pick_client_trace(metadata: dict[str, Any] | None) -> dict[str, str]:
    if not metadata:
        return {}
    out: dict[str, str] = {}
    for key in _TRACE_KEYS:
        raw = metadata.get(key)
        if raw is None:
            continue
        text = str(raw).strip()
        if not text:
            continue
        out[key] = text[:128]
    return out
