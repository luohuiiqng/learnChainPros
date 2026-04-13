"""将 RuntimeSession 导出为可读 Markdown，便于工单、调试与对账（claw RuntimeSession 报告思路的轻量版）。"""

from __future__ import annotations

import json
from typing import Any

from app.runtime.runtime_session import RuntimeSession


def _fence_json(label: str, data: Any, *, max_chars: int) -> list[str]:
    lines = [f"## {label}", ""]
    if data is None:
        lines.append("_（无）_")
        lines.append("")
        return lines
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    if len(text) > max_chars:
        text = text[: max_chars - 20] + "\n… _（已截断）_"
    lines.append("```json")
    lines.extend(text.splitlines())
    lines.append("```")
    lines.append("")
    return lines


def _truncate_prompt(prompt: str, max_chars: int) -> str:
    if len(prompt) <= max_chars:
        return prompt
    return prompt[: max_chars - 12] + "\n… _（截断）_"


def runtime_session_to_markdown(
    session: RuntimeSession,
    *,
    max_json_chars: int = 8000,
    max_prompt_chars: int = 1200,
) -> str:
    """生成单轮运行快照的 Markdown 文本（不含密钥；长 JSON / prompt 会截断）。"""
    parts: list[str] = [
        "# RuntimeSession 导出",
        "",
        f"- **session_id**: `{session.session_id}`",
        f"- **user_input**: {session.user_input[:500]}{'…' if len(session.user_input) > 500 else ''}",
        "",
    ]
    parts.extend(_fence_json("planner_result", session.planner_result, max_chars=max_json_chars))
    parts.extend(_fence_json("workflow_result", session.workflow_result, max_chars=max_json_chars))

    parts.append("## workflow_trace")
    parts.append("")
    if not session.workflow_trace:
        parts.append("_（无）_")
    else:
        parts.append("```json")
        raw = json.dumps(session.workflow_trace, ensure_ascii=False, indent=2, default=str)
        if len(raw) > max_json_chars:
            raw = raw[: max_json_chars - 20] + "\n…"
        parts.extend(raw.splitlines())
        parts.append("```")
    parts.append("")

    parts.append("## tool_calls")
    parts.append("")
    if not session.tool_calls:
        parts.append("_（无）_")
    else:
        for i, call in enumerate(session.tool_calls, 1):
            parts.append(f"### tool_call {i}")
            parts.append("")
            parts.append(f"- tool: `{call.get('tool_name')}` success={call.get('success')}")
            out = call.get("output")
            parts.append(f"- output: `{str(out)[:400]}{'…' if len(str(out)) > 400 else ''}`")
            if call.get("error"):
                parts.append(f"- error: `{call.get('error')}`")
            parts.append("")

    parts.append("## model_calls")
    parts.append("")
    if not session.model_calls:
        parts.append("_（无）_")
    else:
        for i, mc in enumerate(session.model_calls, 1):
            parts.append(f"### model_call {i}")
            parts.append("")
            prompt = str(mc.get("prompt", ""))
            parts.append("**prompt（截断）**")
            parts.append("")
            parts.append("```text")
            parts.append(_truncate_prompt(prompt, max_prompt_chars))
            parts.append("```")
            parts.append("")
            parts.append(f"- success: {mc.get('success')}")
            if mc.get("error"):
                parts.append(f"- error: `{mc.get('error')}`")
            parts.append("")

    parts.append("## final_output")
    parts.append("")
    fo = session.final_output or ""
    parts.append("```text")
    parts.append(fo[: max_prompt_chars * 2] + ("…" if len(fo) > max_prompt_chars * 2 else ""))
    parts.append("```")
    parts.append("")

    parts.append("## errors")
    parts.append("")
    if not session.errors:
        parts.append("_（无）_")
    else:
        for e in session.errors:
            parts.append(f"- {e}")
    parts.append("")

    return "\n".join(parts).rstrip() + "\n"
