from app.runtime.runtime_session import RuntimeSession


def test_runtime_session_default_fields() -> None:
    runtime_session = RuntimeSession(session_id="session-1", user_input="你好")

    assert runtime_session.session_id == "session-1"
    assert runtime_session.user_input == "你好"
    assert runtime_session.planner_result is None
    assert runtime_session.workflow_result is None
    assert runtime_session.tool_calls == []
    assert runtime_session.model_calls == []
    assert runtime_session.final_output is None
    assert runtime_session.errors == []


def test_runtime_session_list_fields_not_shared_between_instances() -> None:
    runtime_session_a = RuntimeSession(session_id="session-a")
    runtime_session_b = RuntimeSession(session_id="session-b")

    runtime_session_a.tool_calls.append(
        {
            "tool_name": "time_tool",
            "success": True,
            "output": "2026-04-04 10:00:00",
            "error": None,
        }
    )
    runtime_session_a.model_calls.append(
        {
            "prompt": "你好",
            "success": True,
            "output": "mock response",
            "error": None,
        }
    )
    runtime_session_a.errors.append("mock error")

    assert len(runtime_session_a.tool_calls) == 1
    assert len(runtime_session_a.model_calls) == 1
    assert runtime_session_a.errors == ["mock error"]

    assert runtime_session_b.tool_calls == []
    assert runtime_session_b.model_calls == []
    assert runtime_session_b.errors == []
