from typing import Any

class BasePrompt:
    def __init__(self,**kwargs) -> None:
        pass
    def format_history(self,messages:list[dict[str,Any]])->str:
        if not messages:
            return ""
        
        lines = []
        for message in messages:
            role = message.get("role","unknown")
            content = message.get("content","")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)
    
    def build_prompt(
            self,
            messages:list[dict[str,Any]],
            current_input:str|None = None,
    )->str:
        history_str = self.format_history(messages)
        if history_str and current_input:
            return f"这是与你的用户的对话历史:\n{history_str}\n用户的输入是:\n{current_input}\n你的任务是根据用户的输入生成合适的回复。"
        elif history_str:
            return f"这是与你的用户的对话历史:\n{history_str}\n你的任务是根据用户的输入生成合适的回复。"
        elif current_input:
            return f"用户的输入是:\n{current_input}\n你的任务是根据用户的输入生成合适的回复。"
        else:
            return "你的任务是根据用户的输入生成合适的回复。"