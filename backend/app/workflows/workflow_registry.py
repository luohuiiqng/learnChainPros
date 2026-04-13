"""按名称注册工作流实现，便于扩展而无需修改 ChatAgent 分支逻辑。"""

from __future__ import annotations

from collections.abc import Callable

from app.workflows.base_workflow import BaseWorkflow

WorkflowFactory = Callable[[], BaseWorkflow]


class WorkflowRegistry:
    """维护 ``workflow_name`` → 可调用工厂，供 ``ChatAgent`` 按名实例化 ``BaseWorkflow``。"""

    def __init__(self) -> None:
        self._factories: dict[str, WorkflowFactory] = {}

    def register(self, name: str, factory: WorkflowFactory) -> None:
        if not name:
            raise ValueError("workflow name must be non-empty")
        self._factories[name] = factory

    def get(self, name: str | None) -> BaseWorkflow | None:
        if not name:
            return None
        factory = self._factories.get(name)
        return factory() if factory else None

    def has(self, name: str) -> bool:
        return name in self._factories


def build_default_workflow_registry() -> WorkflowRegistry:
    from app.workflows.conditional_workflow import ConditionalWorkflow
    from app.workflows.sequential_workflow import SequentialWorkflow

    reg = WorkflowRegistry()
    reg.register("time_reply_workflow", lambda: SequentialWorkflow())
    reg.register("conditional_workflow", lambda: ConditionalWorkflow())
    return reg
