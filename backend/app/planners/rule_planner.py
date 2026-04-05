from app.planners.base_planner import BasePlanner
from typing import Any
from app.tools.tool_router import ToolRouter



class RulePlanner(BasePlanner):
    def __init__(self,tool_router:ToolRouter=None,**kwargs)->None:
        super().__init__(**kwargs)
        self._tool_router = tool_router

    def _should_use_workflow(self, message: Any) -> bool:
        """根据输入内容判断是否需要使用workflow进行规划，默认根据message内容是否包含特定关键词进行判断，可以在子类中重写实现更复杂的逻辑"""
        rule_time_tool_str = ["时间", "几点", "现在几点", "当前时间"]
        has_time_intent = False
        for rule in rule_time_tool_str:
            if rule in str(message):
                has_time_intent = True
                break
        rule_workflow_str = ["回复", "说一句", "生成一句", "告诉我一句"]
        has_workflow_intent = False
        for rule in rule_workflow_str:
            if rule in str(message):
                has_workflow_intent = True
                break
        return has_time_intent and has_workflow_intent

    def plan(self,input_data:Any,context:Any=None)->dict[str,Any]:
        """根据输入内容生成最小规则计划结果。"""
        if not self.validate_input(input_data):
            return {
                "action":"model",
                "reason":"输入数据不合法，无法规划工具调用"
            }
        if self._should_use_workflow(input_data.message):
            return {
                "action": "workflow",
                "steps": [
                    {
                        "step_name": "get_time",
                        "action": "tool",
                        "tool_name": "time_tool",
                        "tool_input": {},
                    },
                    {
                        "step_name": "generate_reply",
                        "action": "model",
                        "prompt_template": "当前时间是{step_output},请生成一句自然回复给用户",
                        "use_step_result": "get_time",
                    },
                ],
                "context": {},
            }
        tool_name = self._tool_router.route(input_data.message) if self._tool_router else None
        if tool_name is not None:
            return {"action":"tool","tool_name": tool_name}

        return {"action": "model"}