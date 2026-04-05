from app.workflows.base_workflow import BaseWorkflow
from typing import Any
from app.workflows.agent_executor import AgentExecutor


class SequentialWorkflow(BaseWorkflow):
    def __init__(self,**kwargs)->None:
        super().__init__(**kwargs)


    def run(self,steps:list[dict[str,Any]],executor:AgentExecutor=None,context:Any=None)->dict[str,Any]:
        results = []
        if context is None:
            context = {}
        if context.get("step_results") is None:
            context["step_results"] = {}
        for step in steps:
            step_result = executor.execute_step(step,context=context)
            step_name = step.get("step_name","unknown")
            results.append(step_result)
            context["step_results"][step_name] = step_result
            if not step_result.get("success",False):
                return {
                    "success": False,
                    "error": f"Step {step.get('step_name', 'unknown')} failed",
                    "results": results,
                }
        return {
            "success": True,
            "results": results
        }