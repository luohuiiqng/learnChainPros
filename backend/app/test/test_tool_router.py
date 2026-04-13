from app.tools.tool_router import ToolRouter


def test_tool_router_route_matches_first_keyword_hit() -> None:
    router = ToolRouter()
    router.add_rule(
        "time_tool",
        ["时间", "现在时间", "当前时间", "日期", "time now", "time", "几点", "现在几点"],
    )
    router.add_rule("test_not_exist_tool", ["lala"])
    assert router.route("你好,现在几点了？") == "time_tool"
    assert router.route("小鹿妹妹") is None
    assert router.route("lala") == "test_not_exist_tool"
