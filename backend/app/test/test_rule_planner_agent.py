from app.agent.chat_agent import ChatAgent
from app.memory.in_memory_memory import InMemoryMemory
from app.models.mock_model import MockModel
from app.planners.rule_planner import RulePlanner
from app.runtime.in_memory_session_store import InMemorySessionStore
from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore
from app.runtime.runtime_manager import RuntimeManager
from app.runtime.runtime_session import RuntimeSession
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.tools.time_tool import TimeTool
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_router import ToolRouter


def _make_rule_planner_chat_agent(session_suffix: str) -> tuple[ChatAgent, InMemoryMemory, str]:
    model = MockModel(
        model_name="mock-rule-planner-model", response_text="mock response"
    )
    tool_router = ToolRouter()
    tool_router.add_rule(
        tool_name="time_tool",
        keywords=["时间", "现在时间", "当前时间", "几点", "现在几点"],
    )
    planner = RulePlanner(tool_router=tool_router)
    memory = InMemoryMemory()
    tool_registry = ToolRegistry()
    tool_registry.register_tool(TimeTool())
    runtime_manager = RuntimeManager(
        session_store=InMemorySessionStore(),
        transcript_store=InMemoryTranscriptStore(),
    )
    chat_agent = ChatAgent(
        runtime_manager=runtime_manager,
        model=model,
        tool_registry=tool_registry,
        memory=memory,
        planner=planner,
    )
    session_id = f"rule_planner_session_{session_suffix}"
    return chat_agent, memory, session_id


def test_rule_planner_agent_tool_branch() -> None:
    chat_agent, _memory, session_id = _make_rule_planner_chat_agent("tool")
    tool_input = AgentInput(message="现在几点了？", session_id=session_id)
    tool_output = chat_agent.run(tool_input)
    assert isinstance(tool_output, AgentOutput)
    assert tool_output.success is True
    tool_runtime_session = tool_output.metadata.get("runtime_session")
    assert isinstance(tool_runtime_session, RuntimeSession)
    assert tool_runtime_session.user_input == "现在几点了？"
    assert tool_runtime_session.planner_result["action"] == "tool"
    assert tool_runtime_session.planner_result["tool_name"] == "time_tool"
    assert tool_runtime_session.planner_result["reason"] == "命中工具路由规则"
    assert tool_runtime_session.workflow_trace[0]["step_name"] == "planner"
    assert (
        tool_runtime_session.workflow_trace[0]["output"]
        == tool_runtime_session.planner_result
    )
    assert tool_runtime_session.workflow_trace[0]["input_summary"] == "现在几点了？"
    assert (
        tool_runtime_session.workflow_trace[0]["output_summary"]
        == "命中工具路由规则"
    )
    assert len(tool_runtime_session.tool_calls) == 1
    assert tool_runtime_session.tool_calls[0]["tool_name"] == "time_tool"
    assert tool_runtime_session.tool_calls[0]["success"] is True
    assert tool_runtime_session.tool_calls[0]["output"] == tool_output.content
    assert tool_runtime_session.tool_calls[0]["error"] is None
    assert tool_runtime_session.tool_calls[0]["timestamp"]
    assert tool_runtime_session.model_calls == []
    assert tool_runtime_session.final_output == tool_output.content
    assert tool_runtime_session.errors == []
    assert tool_output.metadata.get("name") == "time_tool"
    assert tool_output.metadata.get("description") == "获取当前时间"


def test_rule_planner_agent_model_branch_and_memory() -> None:
    chat_agent, memory, session_id = _make_rule_planner_chat_agent("model")

    tool_input = AgentInput(message="现在几点了？", session_id=session_id)
    tool_output = chat_agent.run(tool_input)
    assert tool_output.success is True

    model = chat_agent._model
    mock_status = model.get_mock_status()
    assert mock_status["call_count"] == 0
    assert mock_status["last_input"] is None

    model_input = AgentInput(message="你好", session_id=session_id)
    model_output = chat_agent.run(model_input)
    assert isinstance(model_output, AgentOutput)
    assert model_output.success is True
    assert "mock response" in (model_output.content or "")
    model_runtime_session = model_output.metadata.get("runtime_session")
    assert isinstance(model_runtime_session, RuntimeSession)
    assert model_runtime_session.user_input == "你好"
    assert model_runtime_session.planner_result["action"] == "model"
    assert (
        model_runtime_session.planner_result["reason"]
        == "未命中workflow或tool规则，回退到模型"
    )
    assert model_runtime_session.workflow_trace[0]["step_name"] == "planner"
    assert (
        model_runtime_session.workflow_trace[0]["output"]
        == model_runtime_session.planner_result
    )
    assert model_runtime_session.workflow_trace[0]["input_summary"] == "你好"
    assert (
        model_runtime_session.workflow_trace[0]["output_summary"]
        == "未命中workflow或tool规则，回退到模型"
    )
    assert model_runtime_session.tool_calls == []
    assert len(model_runtime_session.model_calls) == 1
    assert "你好" in model_runtime_session.model_calls[0]["prompt"]
    assert model_runtime_session.model_calls[0]["success"] is True
    assert model_runtime_session.model_calls[0]["output"] == model_output.content
    assert model_runtime_session.model_calls[0]["error"] is None
    assert model_runtime_session.model_calls[0]["timestamp"]
    assert model_runtime_session.final_output == model_output.content
    assert model_runtime_session.errors == []

    mock_status = model.get_mock_status()
    assert mock_status["call_count"] == 1
    assert "现在几点了？" in mock_status["last_input"].prompt
    assert tool_output.content in mock_status["last_input"].prompt
    assert "你好" in mock_status["last_input"].prompt

    memory_messages = memory.get_messages(session_id)
    assert len(memory_messages) == 4
    assert memory_messages[0]["role"] == "user"
    assert memory_messages[1]["role"] == "assistant"
    assert memory_messages[1]["content"] == tool_output.content
    assert memory_messages[2]["role"] == "user"
    assert memory_messages[3]["role"] == "assistant"
    assert memory_messages[3]["content"] == model_output.content
