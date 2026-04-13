"""测试辅助函数（可被普通模块 import）。"""

from __future__ import annotations

import pytest


def skip_if_openai_unreachable(out) -> None:
    """可选 OpenAI 用例：网络失败或环境中被 stub 替换导致 API 不完整时 skip。"""
    if getattr(out, "success", False):
        return
    err = (getattr(out, "error_message", None) or "") + (getattr(out, "content", None) or "")
    lowered = err.lower()
    network_markers = (
        "connection",
        "timeout",
        "resolve",
        "network",
        "unreachable",
    )
    stub_markers = (
        "fakeopenai",
        "has no attribute 'responses'",
        "has no attribute \"responses\"",
        "no attribute 'responses'",
    )
    if any(x in lowered for x in network_markers):
        pytest.skip("OpenAI 端点当前不可达，跳过可选集成用例")
    if any(x in lowered for x in stub_markers):
        pytest.skip("当前进程内 OpenAI 客户端已被测试 stub 替换，跳过可选集成用例")
