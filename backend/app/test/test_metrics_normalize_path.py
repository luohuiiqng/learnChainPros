"""HTTP 路径归一化（Prometheus 标签降基数）。"""

import pytest

from app.observability.metrics import normalize_http_path


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", "/"),
        ("/agent_api/sessions", "/agent_api/sessions"),
        (
            "/agent_api/sessions/550e8400-e29b-41d4-a716-446655440000",
            "/agent_api/sessions/{id}",
        ),
        (
            "/agent_api/sessions/abc/transcript",
            "/agent_api/sessions/{id}/transcript",
        ),
        (
            "/agent_api/sessions/x/transcript/3/markdown",
            "/agent_api/sessions/{id}/transcript/{index}/markdown",
        ),
        (
            "/agent_api/sessions/x/transcript/latest/markdown",
            "/agent_api/sessions/{id}/transcript/latest/markdown",
        ),
    ],
)
def test_normalize_http_path(raw: str, expected: str) -> None:
    assert normalize_http_path(raw) == expected
