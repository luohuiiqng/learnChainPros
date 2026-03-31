


class ToolRouter:
    """工具的规则路由"""
    def __init__(self,**kwargs):
        self._routes = {}

    def route(self,input_text:str)->str|None:
        for tool_name in self._routes:
            for keyword in self._routes.get(tool_name):
                if keyword.lower() in input_text.lower():
                    return tool_name
        return None
    
    def add_rule(self,tool_name:str,keywords:list[str]):
        if len(keywords) == 0 or tool_name == "":
            return
        self._routes[tool_name] = keywords