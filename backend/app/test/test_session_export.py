from app.runtime.runtime_session import RuntimeSession
from app.runtime.session_export import runtime_session_to_markdown


def test_runtime_session_to_markdown_contains_core_sections() -> None:
    rs = RuntimeSession(
        session_id="s1",
        user_input="你好",
        planner_result={"action": "model", "reason": "test"},
        final_output="ok",
        errors=["soft warn"],
    )
    rs.add_tool_call("time_tool", True, "12:00", None)
    md = runtime_session_to_markdown(rs)
    assert "# RuntimeSession" in md
    assert "s1" in md
    assert "你好" in md
    assert "planner_result" in md
    assert "time_tool" in md
    assert "soft warn" in md
    assert "final_output" in md
