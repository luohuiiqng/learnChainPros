"""可选：在单轮 act 前后打结构化日志，便于与 request_id 等日志关联。"""

from __future__ import annotations

import logging

from app.hooks.lifecycle import AgentLifecycleHook
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput

_log = logging.getLogger("app.agent.lifecycle")


class LoggingLifecycleHook:
    """由 ``Settings.agent_lifecycle_logging`` 控制是否装配。"""

    def before_act(self, input_data: AgentInput) -> None:
        rid = (input_data.metadata or {}).get("request_id")
        _log.info(
            "agent_before_act",
            extra={
                "request_id": rid,
                "session_id": input_data.session_id,
                "message_len": len(input_data.message or ""),
            },
        )

    def after_act(self, input_data: AgentInput, output: AgentOutput) -> None:
        rid = (input_data.metadata or {}).get("request_id")
        reply_len = len(output.content or "")
        err_len = len(output.error_message or "")
        _log.info(
            "agent_after_act",
            extra={
                "request_id": rid,
                "session_id": input_data.session_id,
                "success": output.success,
                "reply_len": reply_len,
                "error_len": err_len,
                "error_code": output.error_code,
            },
        )
