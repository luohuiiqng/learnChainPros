"""路由依赖：从请求上下文读取应用配置，并实现只读 HTTP 接口开关。"""

from __future__ import annotations

from fastapi import HTTPException, Request

from app.config.settings import Settings

__all__ = ["get_app_settings", "require_read_api"]


def get_app_settings(request: Request) -> Settings:
    """从 ``app.state.settings`` 读取启动时注入的配置（见 ``main.lifespan``）。

    若未注入（例如部分测试场景），则回退到 ``Settings.from_env()``。"""
    s = getattr(request.app.state, "settings", None)
    if s is not None:
        return s
    return Settings.from_env()


def require_read_api(request: Request) -> None:
    """若未启用只读 HTTP 接口，则拒绝会话、transcript、Markdown 等 GET（``POST /chat`` 不使用本依赖）。"""
    if not get_app_settings(request).agent_read_api_enabled:
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "只读接口已禁用",
                }
            },
        )
