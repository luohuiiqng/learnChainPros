"""FastAPI 应用入口：观测中间件、统一错误体、健康检查与 ``/agent_api`` 路由挂载。"""

from contextlib import asynccontextmanager
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

import logging
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.config.settings import Settings
from app.routes.chat import router as chat_router
from app.version import API_VERSION


@asynccontextmanager
async def lifespan(app: FastAPI):
    """进程启动时根据环境变量配置日志级别与格式，并记录 metrics 是否启用。"""
    from app.observability.json_logging import configure_logging_from_env

    configure_logging_from_env()
    settings = Settings.from_env()
    app.state.settings = settings
    app.state.metrics_enabled = settings.metrics_enabled
    log = logging.getLogger("app.main")
    if not settings.agent_read_api_enabled:
        log.warning(
            "AGENT_READ_API_ENABLED 为关闭：会话/transcript/Markdown 等只读 GET 将返回 403"
        )
    yield


app = FastAPI(
    title="LearnChainPros Chat API",
    version=API_VERSION,
    lifespan=lifespan,
    description=(
        "自研 Agent 后端：对话、会话与 transcript 查询（含按下标导出 Markdown）。"
        " OpenAPI 与 Try it out：`GET /docs`。"
        " 设计总纲见仓库 `docs/agent-framework-design.md`。"
    ),
)


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    from app.observability.metrics import observe_http_request

    log = logging.getLogger("app.http")
    raw = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
    if raw and str(raw).strip():
        rid = str(raw).strip()[:128]
    else:
        rid = str(uuid4())
    request.state.request_id = rid
    t0 = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        status_code = response.status_code
        return response
    finally:
        elapsed = time.perf_counter() - t0
        path = request.url.path or "/"
        observe_http_request(request.method, path, status_code, elapsed)
        log.info(
            "http_request",
            extra={
                "request_id": rid,
                "method": request.method,
                "path": path,
                "status_code": status_code,
                "duration_ms": int(elapsed * 1000),
            },
        )


# Development CORS config for local frontend. Tighten origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check(request: Request) -> dict[str, Any]:
    """存活探针；返回基础状态与关键特性开关（运维与编排可读）。"""
    settings = getattr(request.app.state, "settings", None)
    if settings is None:
        settings = Settings.from_env()
    return {
        "status": "ok",
        "api_version": API_VERSION,
        "metrics_enabled": bool(
            getattr(request.app.state, "metrics_enabled", True)
        ),
        "agent_read_api_enabled": settings.agent_read_api_enabled,
    }


@app.get("/metrics")
def prometheus_metrics(request: Request) -> Response:
    if not getattr(request.app.state, "metrics_enabled", True):
        raise HTTPException(status_code=404, detail="metrics disabled")
    from app.observability.metrics import metrics_response

    body, ctype = metrics_response()
    return Response(content=body, media_type=ctype)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, __: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "BAD_REQUEST",
                "message": "请求参数格式错误",
            }
        },
    )


@app.exception_handler(HTTPException)
# Preserve structured business errors; wrap unknown HTTPException detail into standard contract.
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail

    if isinstance(detail, dict) and "error" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(detail)}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log = logging.getLogger("app.main")
    rid = getattr(request.state, "request_id", None)
    log.error(
        "unhandled_exception",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={"request_id": rid} if rid else {},
    )
    # Keep error contract consistent for frontend handling.
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "服务暂不可用，请稍后再试",
            }
        },
    )


app.include_router(chat_router, prefix="/agent_api")
