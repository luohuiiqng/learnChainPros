from dataclasses import dataclass
import os


@dataclass
class Settings:
    openai_api_key: str | None
    openai_model: str
    openai_base_url: str | None
    openai_organization: str | None
    store_backend: str
    runtime_db_path: str | None
    openai_timeout_seconds: float = 120.0
    openai_max_retries: int = 2
    tool_timeout_seconds: float = 60.0
    metrics_enabled: bool = True
    log_level: str = "INFO"
    log_json: bool = False
    agent_lifecycle_logging: bool = False
    planner_rules_path: str | None = None
    #: 是否开放 ``GET /sessions``、transcript、Markdown 等只读接口；``POST /chat`` 不受此开关影响。
    agent_read_api_enabled: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        timeout_raw = os.getenv("OPENAI_TIMEOUT_SECONDS", "120")
        retries_raw = os.getenv("OPENAI_MAX_RETRIES", "2")
        try:
            timeout_sec = float(timeout_raw)
        except ValueError:
            timeout_sec = 120.0
        try:
            max_retries = int(retries_raw)
        except ValueError:
            max_retries = 2
        tool_timeout_raw = os.getenv("TOOL_TIMEOUT_SECONDS", "60")
        try:
            tool_timeout = float(tool_timeout_raw)
        except ValueError:
            tool_timeout = 60.0
        tool_timeout = max(1.0, min(tool_timeout, 600.0))
        metrics_enabled = os.getenv("METRICS_ENABLED", "true").lower() not in (
            "0",
            "false",
            "no",
        )
        log_level = os.getenv("LOG_LEVEL", "INFO")
        log_json = os.getenv("LOG_JSON", "").lower() in ("1", "true", "yes")
        agent_lifecycle_logging = os.getenv(
            "AGENT_LIFECYCLE_LOGGING", ""
        ).lower() in ("1", "true", "yes")
        planner_rules_path = os.getenv("PLANNER_RULES_PATH") or None
        if planner_rules_path is not None and not str(planner_rules_path).strip():
            planner_rules_path = None
        read_api_raw = os.getenv("AGENT_READ_API_ENABLED")
        if read_api_raw is None or str(read_api_raw).strip() == "":
            agent_read_api_enabled = True
        else:
            agent_read_api_enabled = str(read_api_raw).strip().lower() not in (
                "0",
                "false",
                "no",
            )
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
            openai_base_url=os.getenv("OPENAI_BASE_URL"),
            openai_organization=os.getenv("OPENAI_ORGANIZATION"),
            store_backend=os.getenv("STORE_BACKEND", "memory"),
            runtime_db_path=os.getenv("RUNTIME_DB_PATH"),
            openai_timeout_seconds=max(5.0, min(timeout_sec, 600.0)),
            openai_max_retries=max(0, min(max_retries, 10)),
            tool_timeout_seconds=tool_timeout,
            metrics_enabled=metrics_enabled,
            log_level=log_level,
            log_json=log_json,
            agent_lifecycle_logging=agent_lifecycle_logging,
            planner_rules_path=planner_rules_path,
            agent_read_api_enabled=agent_read_api_enabled,
        )

    @classmethod
    def for_tests(cls) -> "Settings":
        """单元测试 / 桩服务使用的固定配置，避免依赖真实环境变量。"""
        return cls(
            openai_api_key="test-api-key",
            openai_model="test-model",
            openai_base_url=None,
            openai_organization=None,
            store_backend="memory",
            runtime_db_path=None,
            openai_timeout_seconds=30.0,
            openai_max_retries=0,
            tool_timeout_seconds=30.0,
            metrics_enabled=True,
            log_level="WARNING",
            log_json=False,
            agent_lifecycle_logging=False,
            planner_rules_path=None,
            agent_read_api_enabled=True,
        )
