from app.planners.rule_planner import RulePlanner
from app.schemas.agent_input import AgentInput
from app.tools.tool_router import ToolRouter


tool_router = ToolRouter()
tool_router.add_rule(
    tool_name="time_tool",
    keywords=["时间", "现在时间", "当前时间", "几点", "现在几点"],
)

planner = RulePlanner(tool_router=tool_router)

workflow_plan = planner.plan(
    AgentInput(message="现在几点了，回复我一句", session_id="planner-session")
)
assert workflow_plan["action"] == "workflow"
assert len(workflow_plan["steps"]) == 2
assert workflow_plan["steps"][0]["step_name"] == "get_time"
assert workflow_plan["steps"][0]["action"] == "tool"
assert workflow_plan["steps"][0]["tool_name"] == "time_tool"
assert workflow_plan["steps"][1]["step_name"] == "generate_reply"
assert workflow_plan["steps"][1]["action"] == "model"
assert workflow_plan["steps"][1]["use_step_result"] == "get_time"
assert workflow_plan["context"] == {}

tool_plan = planner.plan(AgentInput(message="现在几点了？", session_id="planner-session"))
assert tool_plan["action"] == "tool"
assert tool_plan["tool_name"] == "time_tool"

model_plan = planner.plan(AgentInput(message="你好", session_id="planner-session"))
assert model_plan["action"] == "model"
assert "tool_name" not in model_plan

invalid_plan = planner.plan(AgentInput(message="   ", session_id="planner-session"))
assert invalid_plan["action"] == "model"
assert invalid_plan["reason"] == "输入数据不合法，无法规划工具调用"

planner_info = planner.get_planner_info()
assert planner_info["planner_class"] == "RulePlanner"

print("rule planner tests passed")
