from app.planners.base_planner import BasePlanner
from typing import Any



class RulePlanner(BasePlanner):
    def __init__(self,**kwargs)->None:
        super().__init__(**kwargs)
        self._rules = [
            {"tool_name":"time_tool", "keywords": ["时间", "现在时间", "当前时间", "几点", "现在几点"]}
            ]

    def plan(self,input_data:Any,context:Any=None)->dict[str,Any]:
        """根据输入内容生成最小规则计划结果。"""
        if not self.validate_input(input_data):
            return {
                "action":"model",
                "reason":"输入数据不合法，无法规划工具调用"
            }
        message = input_data.message.strip()
        for rule in self._rules:
            if any(keyword in message for keyword in rule["keywords"]):
                return {"action":"tool","tool_name": rule["tool_name"]}
        return {"action": "model"}