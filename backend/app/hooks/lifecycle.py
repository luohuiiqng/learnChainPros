"""ChatAgent 单轮 act 的前后钩子，用于审计、计费、实验策略等横切逻辑。"""

from typing import Protocol, runtime_checkable

from app.schemas.agent_input import AgentInput
from app.schemas.agent_output import AgentOutput


@runtime_checkable
class AgentLifecycleHook(Protocol):
    """在 ``ChatAgent.act`` 进入主链前、返回 ``AgentOutput`` 后各调用一次。"""

    def before_act(self, input_data: AgentInput) -> None:
        """只读观察；不应修改 ``input_data``。"""

    def after_act(self, input_data: AgentInput, output: AgentOutput) -> None:
        """只读观察；不应修改 ``output``（若需副作用请自行拷贝）。"""
