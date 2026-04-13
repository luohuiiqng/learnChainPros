from unittest.mock import patch

from app.agent.chat_agent import ChatAgent
from app.hooks.lifecycle import AgentLifecycleHook
from app.models.mock_model import MockModel
from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.runtime_manager import RuntimeManager
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput


class _SpyHook:
    def __init__(self) -> None:
        self.before: list[str] = []
        self.after: list[tuple[str, bool]] = []

    def before_act(self, input_data: AgentInput) -> None:
        self.before.append(input_data.message)

    def after_act(self, input_data: AgentInput, output: AgentOutput) -> None:
        self.after.append((input_data.message, output.success))


def test_chat_agent_invokes_lifecycle_hooks() -> None:
    spy = _SpyHook()
    rm = RuntimeManager(
        session_store=InMemorySessionStore(),
        transcript_store=InMemoryTranscriptStore(),
    )
    agent = ChatAgent(
        runtime_manager=rm,
        model=MockModel(response_text="hooked"),
        hooks=(spy,),
    )
    out = agent.run(AgentInput(message="ping", session_id="pytest-hooks-1"))
    assert out.success is True
    assert spy.before == ["ping"]
    assert len(spy.after) == 1
    assert spy.after[0] == ("ping", True)


def test_agent_lifecycle_hook_protocol_runtime_check() -> None:
    assert isinstance(_SpyHook(), AgentLifecycleHook)


def test_logging_lifecycle_hook_after_act_includes_len_fields() -> None:
    from app.hooks.logging_hook import LoggingLifecycleHook

    hook = LoggingLifecycleHook()
    inp = AgentInput(
        message="m", session_id="s", metadata={"request_id": "r1"}
    )
    with patch("app.hooks.logging_hook._log") as mock_log:
        hook.after_act(
            inp,
            AgentOutput(content="hello", success=True, error_message=None),
        )
    extra = mock_log.info.call_args[1]["extra"]
    assert extra["reply_len"] == 5
    assert extra["error_len"] == 0
    assert extra["success"] is True
    assert extra.get("error_code") is None

    with patch("app.hooks.logging_hook._log") as mock_log:
        hook.after_act(
            inp,
            AgentOutput(
                content="",
                success=False,
                error_message="bad",
                error_code="MODEL_ERROR",
            ),
        )
    extra2 = mock_log.info.call_args[1]["extra"]
    assert extra2["reply_len"] == 0
    assert extra2["error_len"] == 3
    assert extra2["error_code"] == "MODEL_ERROR"
