"""对话智能体：单轮 ``act`` 串联 Planner、工具、模型与工作流执行器。"""

from app.agent.base_agent import BaseAgent
from app.hooks.lifecycle import AgentLifecycleHook
from collections.abc import Sequence
import sys
import time
from typing import Any
from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput
from app.schemas.error_codes import ErrorCode
from app.schemas.model_request import ModelRequest
from app.tools.tool_registry import ToolRegistry
from app.models.base_model import BaseModel
from app.schemas.tool_input import ToolInput
from app.schemas.tool_output import ToolOutput
from app.memory.base_memory import BaseMemory
from datetime import datetime
from app.prompts.prompt_builder import PromptBuilder
from app.prompts.base_prompt import BasePrompt
from app.planners.base_planner import BasePlanner
from app.runtime.client_trace import pick_client_trace
from app.runtime.runtime_session import RuntimeSession
from app.workflows.agent_executor import AgentExecutor
from app.runtime.runtime_manager import RuntimeManager
from app.workflows.base_workflow import BaseWorkflow
from app.tools.tool_runner import run_tool_with_timeout
from app.workflows.workflow_registry import WorkflowRegistry, build_default_workflow_registry
from app.observability.metrics import (
    observe_agent_act_duration,
    observe_agent_act_exception,
    observe_planner_plan_duration,
    observe_planner_route,
    observe_workflow_duration,
    observe_workflow_run,
)


class ChatAgent(BaseAgent):
    """默认 Agent 实现：Runtime、Memory、Planner、WorkflowRegistry、生命周期钩子。"""

    def __init__(
        self,
        runtime_manager: RuntimeManager | None = None,
        *,
        model: BaseModel,
        tool_registry: ToolRegistry | None = None,
        memory: BaseMemory | None = None,
        prompt_builder: BasePrompt | None = None,
        planner: BasePlanner | None = None,
        workflow_registry: WorkflowRegistry | None = None,
        tool_timeout_seconds: float | None = 60.0,
        hooks: Sequence[AgentLifecycleHook] | None = None,
        **kwargs,
    ) -> None:
        if runtime_manager is None:
            from app.runtime.in_memory_session_store import InMemorySessionStore
            from app.runtime.in_memory_transcript_store import InMemoryTranscriptStore

            runtime_manager = RuntimeManager(
                session_store=InMemorySessionStore(),
                transcript_store=InMemoryTranscriptStore(),
            )
        super().__init__(model=model, **kwargs)
        self._tool_registry = tool_registry
        self._memory = memory
        self._prompt_builder = prompt_builder if prompt_builder is not None else PromptBuilder()
        self._planner = planner
        self._runtime_manager = runtime_manager
        self._workflow_registry = workflow_registry or build_default_workflow_registry()
        self._tool_timeout_seconds = tool_timeout_seconds
        self._hooks: tuple[AgentLifecycleHook, ...] = tuple(hooks or ())

    def _add_memory_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        if self._memory is None or not session_id:
            return
        self._memory.add_message(
            session_id,
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def _finalize_model_output(
        self,
        model_output: AgentOutput,
        prompt_text: str | None,
        runtime_session: RuntimeSession,
        *,
        client_trace: dict[str, str] | None = None,
    ) -> AgentOutput:
        runtime_session.add_model_call(
            prompt=prompt_text or "",
            success=model_output.success,
            output=model_output.content,
            error=model_output.error_message,
        )
        if not model_output.success:
            runtime_session.add_error(
                f"model call error: {model_output.error_message}"
            )
        runtime_session.final_output = model_output.content or ""
        model_output.metadata = self._build_output_metadata(
            model_output.metadata,
            runtime_session,
            client_trace=client_trace,
        )
        if not model_output.success:
            ec = (model_output.metadata or {}).get("error_code")
            model_output.error_code = str(ec) if ec else ErrorCode.MODEL_ERROR
        else:
            model_output.error_code = None
        return model_output

    def _run_workflow(
        self,
        plan: dict[str, Any],
        runtime_session: RuntimeSession,
        workflow: BaseWorkflow,
        *,
        client_trace: dict[str, str] | None = None,
    ) -> AgentOutput:
        _wf_t0 = time.monotonic()
        workflow = workflow
        agent_executor = AgentExecutor(
            model=self._model,
            tool_registry=self._tool_registry,
            tool_timeout_seconds=self._tool_timeout_seconds,
        )
        workflow_output = workflow.run(
            steps=plan.get("steps", []),
            executor=agent_executor,
            context=plan.get("context", {}),
        )

        runtime_session.workflow_result = workflow_output.to_dict()
        results = workflow_output.results
        for result in results:
            step_name = result.get("step_name", "unknown")
            for step in plan.get("steps", []):
                if step.get("step_name", "unknown") == step_name:
                    action = result.get("action", step.get("action", "unknown"))
                    runtime_session.add_workflow_step_trace(
                        step_name=result.get("step_name", "unknown"),
                        action=action,
                        success=result.get("success", False),
                        output=result.get("output", ""),
                        error=result.get("error", None),
                        input_summary=result.get("input_summary", ""),
                        output_summary=result.get("output_summary", ""),
                    )
                    if action == "tool":
                        runtime_session.add_tool_call(
                            tool_name=step.get("tool_name", "unknown"),
                            success=result.get("success", False),
                            output=result.get("output", ""),
                            error=result.get("error", None),
                        )
                    elif action == "model":
                        prompt_template = step.get("prompt_template", "")
                        use_step_result = step.get("use_step_result")
                        finally_prompt = step.get("prompt", "")
                        if not finally_prompt and use_step_result:
                            dependency_output = ""
                            for previous_result in results:
                                if previous_result.get("step_name") == use_step_result:
                                    dependency_output = previous_result.get(
                                        "output", ""
                                    )
                                    finally_prompt = prompt_template.replace(
                                        "{step_output}", str(dependency_output)
                                    )
                                    break

                        runtime_session.add_model_call(
                            prompt=finally_prompt or "",
                            success=result.get("success", False),
                            output=result.get("output", ""),
                            error=result.get("error", None),
                        )

        final_result = results[-1] if results else {}
        runtime_session.final_output = final_result.get("output", "")
        self._add_memory_message(
            runtime_session.session_id,
            "assistant",
            runtime_session.final_output,
        )
        if not workflow_output.success:
            runtime_session.add_error(workflow_output.error)
        if not final_result.get("success", False):
            runtime_session.add_error(final_result.get("error", ""))
        _elapsed = time.monotonic() - _wf_t0
        observe_workflow_duration(
            plan.get("workflow_name"),
            _elapsed,
            workflow_output.success,
        )
        observe_workflow_run(
            plan.get("workflow_name"),
            workflow_output.success,
        )
        wec: str | None = workflow_output.error_code
        if not workflow_output.success and not wec:
            wec = (final_result or {}).get("error_code") or ErrorCode.WORKFLOW_STEP_FAILED
        return AgentOutput(
            content=runtime_session.final_output,
            success=workflow_output.success,
            error_message=workflow_output.error or final_result.get("error", ""),
            error_code=None if workflow_output.success else wec,
            metadata=self._build_output_metadata(
                workflow_output.metadata,
                runtime_session,
                client_trace=client_trace,
            ),
        )

    def _build_output_metadata(
        self,
        metadata: dict[str, Any] | None,
        runtime_session: RuntimeSession,
        *,
        client_trace: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        merged_metadata = dict(metadata or {})
        if client_trace:
            merged_metadata.update(client_trace)
        merged_metadata["runtime_session"] = runtime_session
        return merged_metadata

    def call_tool(self, tool_name: str, tool_input: ToolInput) -> ToolOutput:
        from app.observability import metrics as prom_metrics

        if self._tool_registry is None:
            prom_metrics.observe_tool_call(tool_name or "unknown", False)
            return ToolOutput(
                content=None,
                error_message="tool registry is not configured",
                success=False,
                metadata={"error_code": ErrorCode.TOOL_ERROR},
            )
        tool = self._tool_registry.get_tool(tool_name)
        if tool is not None:
            out = run_tool_with_timeout(
                tool, tool_input, self._tool_timeout_seconds
            )
            prom_metrics.observe_tool_call(tool.get_name(), out.success)
            return out
        prom_metrics.observe_tool_call(tool_name or "unknown", False)
        return ToolOutput(
            content=None,
            error_message=f"tool not found: {tool_name}",
            success=False,
            metadata={"error_code": ErrorCode.TOOL_NOT_FOUND},
        )

    def call_model(self, input_data: AgentInput) -> tuple[AgentOutput, str | None]:
        if self._memory is not None and input_data.session_id:
            prompt_text = self._prompt_builder.build_prompt(messages=self._memory.get_messages(input_data.session_id))
            model_request = ModelRequest(prompt = prompt_text)
            model_response = self._model.generate(model_request)
            self._add_memory_message(
                input_data.session_id,
                "assistant",
                model_response.content or "",
            )
            return AgentOutput(
                content=model_response.content or "",
                success=model_response.success,
                error_message=model_response.error_message,
                metadata=model_response.metadata,
            ), prompt_text
        else:
            prompt_text = self._prompt_builder.build_prompt(messages=[], current_input=input_data.message)
            model_request = ModelRequest(prompt = prompt_text)
            model_response = self._model.generate(model_request)
            return AgentOutput(
                content=model_response.content or "",
                success=model_response.success,
                error_message=model_response.error_message,
                metadata=model_response.metadata,
            ), prompt_text

    def _record_turn(
        self,
        session_id: str,
        entry_type: str,
        runtime_session: RuntimeSession,
        user_input: str,
        final_output: str,
        success: bool,
    ) -> None:
        self._runtime_manager.ensure_session_exists(session_id)
        self._runtime_manager.append_transcript_entry(
            session_id=session_id,
            transcript_entry=self._runtime_manager.build_transcript_entry(
                type=entry_type,
                runtime_session=runtime_session,
                user_input=user_input,
                final_output=final_output,
                success=success,
            ),
        )

    def _run_plan(
        self,
        runtime_session: RuntimeSession,
        plan: dict[str, Any],
        input_data: AgentInput,
        workflow: BaseWorkflow,
        *,
        client_trace: dict[str, str] | None = None,
    ) -> AgentOutput:
        runtime_session.planner_result = plan
        runtime_session.add_workflow_step_trace(
            step_name="planner",
            action=plan.get("action", "unknown"),
            success=True,
            output=plan,
            error=None,
            input_summary=input_data.message,
            output_summary=plan.get("reason", ""),
        )
        if plan.get("action") == "workflow":
            agent_output = self._run_workflow(
                plan,
                runtime_session,
                workflow=workflow,
                client_trace=client_trace,
            )
            self._record_turn(
                input_data.session_id,
                entry_type="agent",
                runtime_session=runtime_session,
                user_input=input_data.message,
                final_output=agent_output.content,
                success=agent_output.success,
            )
            return agent_output
        elif plan.get("action") == "tool":
            tool_name = plan.get("tool_name")
            if tool_name is not None:
                tool_output = self.call_tool(tool_name, ToolInput(params={}))
                runtime_session.add_tool_call(
                    tool_name=tool_name,
                    success=tool_output.success,
                    output=tool_output.content,
                    error=tool_output.error_message,
                )
                self._add_memory_message(
                    input_data.session_id,
                    "assistant",
                    tool_output.content or "",
                )
                runtime_session.final_output = tool_output.content or ""
                if not tool_output.success:
                    runtime_session.add_error(
                        f"tool call error: {tool_output.error_message}"
                    )

                tec: str | None = None
                if not tool_output.success:
                    tec = (tool_output.metadata or {}).get("error_code")
                    tec = str(tec) if tec else ErrorCode.TOOL_ERROR
                agent_output = AgentOutput(
                    content=tool_output.content or "",
                    success=tool_output.success,
                    error_message=tool_output.error_message,
                    error_code=tec,
                    metadata=self._build_output_metadata(
                        tool_output.metadata,
                        runtime_session,
                        client_trace=client_trace,
                    ),
                )
                self._record_turn(
                    input_data.session_id,
                    entry_type="agent",
                    runtime_session=runtime_session,
                    user_input=input_data.message,
                    final_output=agent_output.content,
                    success=agent_output.success,
                )
                return agent_output
            else:
                model_output, prompt_text = self.call_model(input_data)
                agent_output = self._finalize_model_output(
                    model_output,
                    prompt_text,
                    runtime_session,
                    client_trace=client_trace,
                )
                self._record_turn(
                    input_data.session_id,
                    entry_type="agent",
                    runtime_session=runtime_session,
                    user_input=input_data.message,
                    final_output=agent_output.content,
                    success=agent_output.success,
                )
                return agent_output

        else:
            model_output, prompt_text = self.call_model(input_data)
            agent_output = self._finalize_model_output(
                model_output,
                prompt_text,
                runtime_session,
                client_trace=client_trace,
            )
            self._record_turn(
                input_data.session_id,
                entry_type="agent",
                runtime_session=runtime_session,
                user_input=input_data.message,
                final_output=agent_output.content,
                success=agent_output.success,
            )
            return agent_output

    def _resolve_workflow(self, plan: dict[str, Any]) -> BaseWorkflow | None:
        """根据 plan[\"workflow_name\"] 从注册表解析工作流实例。"""
        return self._workflow_registry.get(plan.get("workflow_name"))

    def act(self, input_data: AgentInput) -> AgentOutput:
        _act_t0 = time.monotonic()
        outcome_ok = False
        try:
            for hook in self._hooks:
                hook.before_act(input_data)
            result = self._execute_act(input_data)
            outcome_ok = result.success
            for hook in self._hooks:
                hook.after_act(input_data, result)
            return result
        finally:
            _elapsed = time.monotonic() - _act_t0
            if sys.exc_info()[0] is not None:
                observe_agent_act_exception()
                observe_agent_act_duration(_elapsed, False)
            else:
                observe_agent_act_duration(_elapsed, outcome_ok)

    def _execute_act(self, input_data: AgentInput) -> AgentOutput:
        client_trace = pick_client_trace(input_data.metadata)
        runtime_session = self._runtime_manager.create_runtime_session(
            session_id=input_data.session_id, user_input=input_data.message
        )
        self._add_memory_message(
            input_data.session_id,
            "user",
            input_data.message,
        )
        if self._planner is not None:
            _pp_t0 = time.monotonic()
            try:
                plan = self._planner.plan(input_data)
            except Exception:
                observe_planner_plan_duration(time.monotonic() - _pp_t0, False)
                raise
            observe_planner_plan_duration(time.monotonic() - _pp_t0, True)
            observe_planner_route(str(plan.get("action", "unknown")))
            workflow = None
            if plan.get("action", "") == "workflow":
                workflow = self._resolve_workflow(plan=plan)
                if workflow is None:
                    unknown = plan.get("workflow_name")
                    runtime_session.planner_result = plan
                    runtime_session.add_error(
                        f"unknown or missing workflow_name: {unknown!r}"
                    )
                    msg = (
                        f"未注册的工作流: {unknown}"
                        if unknown
                        else "缺少 workflow_name"
                    )
                    runtime_session.final_output = msg
                    agent_output = AgentOutput(
                        content=msg,
                        success=False,
                        error_message=msg,
                        error_code=ErrorCode.WORKFLOW_NOT_REGISTERED,
                        metadata=self._build_output_metadata(
                            {},
                            runtime_session,
                            client_trace=client_trace,
                        ),
                    )
                    observe_workflow_run(unknown, False)
                    self._record_turn(
                        input_data.session_id,
                        entry_type="agent",
                        runtime_session=runtime_session,
                        user_input=input_data.message,
                        final_output=agent_output.content,
                        success=False,
                    )
                    return agent_output
            return self._run_plan(
                runtime_session=runtime_session,
                plan=plan,
                input_data=input_data,
                workflow=workflow,
                client_trace=client_trace,
            )
        else:
            observe_planner_route("no_planner")
            model_output, prompt_text = self.call_model(input_data)
            agent_output = self._finalize_model_output(
                model_output,
                prompt_text,
                runtime_session,
                client_trace=client_trace,
            )
            self._record_turn(
                input_data.session_id,
                entry_type="agent",
                runtime_session=runtime_session,
                user_input=input_data.message,
                final_output=agent_output.content,
                success=agent_output.success,
            )
            return agent_output
