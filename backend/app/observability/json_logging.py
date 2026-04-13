"""可选 JSON 行日志，便于日志平台解析；默认仍为可读文本格式。"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any


class JsonLogFormatter(logging.Formatter):
    """将 LogRecord 序列化为单行 JSON（含 extra 中的业务字段）。"""

    _SKIP_KEYS = frozenset(
        {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "exc_info",
            "exc_text",
            "thread",
            "threadName",
            "taskName",
            "message",
        }
    )

    def format(self, record: logging.LogRecord) -> str:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
        frac = int(record.msecs)
        payload: dict[str, Any] = {
            "@timestamp": f"{ts}.{frac:03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key in self._SKIP_KEYS or key.startswith("_"):
                continue
            if value is not None:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging_from_env() -> None:
    from app.config.settings import Settings

    s = Settings.from_env()
    level = getattr(logging, s.log_level.upper(), logging.INFO)
    configure_logging(level=level, use_json=s.log_json)


def configure_logging(*, level: int = logging.INFO, use_json: bool = False) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    for h in root.handlers[:]:
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    if use_json:
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    root.addHandler(handler)
