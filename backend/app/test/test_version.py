"""``app.version`` 单点维护语义。"""

from app.version import API_VERSION


def test_api_version_is_non_empty_semver_like() -> None:
    assert isinstance(API_VERSION, str)
    assert API_VERSION.strip()
    assert "." in API_VERSION
