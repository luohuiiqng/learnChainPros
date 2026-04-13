# Claw-code-main、Everything-Claude-Code 与 LearnChainPros 对齐说明

> **范围**：`student/claw-code-main` 与 `student/everything-claude-code` 为本地参考树；本文把「学到了什么」与「主仓库已落在哪里 / 下一步可落哪里」写在一起，便于评审与排期。  
> **主线**：主工程仍以 [`agent-framework-design.md`](agent-framework-design.md) 与根目录 `README.md` 为准。

---

## 1. 两个参考项目各自是什么

### 1.1 `claw-code-main`（Harness / Runtime 研究向）

- **形态**：Python `src/` 以 **CLI** 为总入口（`main.py` 暴露大量子命令），另有 `rust/` 推进正式 CLI/runtime。
- **重心**：**镜像式**命令/工具清单、`PortRuntime`、**`RuntimeSession`** 聚合报告（上下文、setup、路由命中、turn 结果、执行消息、持久化路径等）、`QueryEngine`、`permissions`、`session_store`、parity/manifest。
- **与商业产品的距离**：更像 **可观测 harness 原型 + 结构学习**，不是完整多租户 SaaS；但 **「一次运行 = 一份报告」** 对 B 端排障极有价值。

### 1.2 `everything-claude-code`（ECC，插件与工作流资产向）

- **形态**：**Claude Code 插件**——`agents/`、`skills/`（**规范工作流表面**）、`commands/`（兼容壳）、`hooks/`、`rules/`、`mcp-configs/`、`scripts/`。
- **重心**：**规模化工作流资产** + **默认编排策略**（`AGENTS.md`：何时 planner / code-reviewer / tdd-guide 等）、安全与 TDD 纪律、跨 harness 安装与兼容。
- **与商业产品的距离**：强在 **资产与规范**；内核 HTTP 服务、统一存储、计费多租户等仍需宿主应用承载。

---

## 2. 与 LearnChainPros 主链的映射（简表）

| 概念 | claw-code-main | everything-claude-code | LearnChainPros（当前） |
|------|----------------|------------------------|-------------------------|
| 入口 | CLI 多命令 | 编辑器 / 斜杠命令 | FastAPI `ChatService` → `ChatAgent` |
| 运行快照 | `RuntimeSession`（报告型） | 依赖 harness 会话 | `RuntimeSession` + transcript |
| 工具与路由 | 镜像 inventory + route | skills/commands 分流 | `ToolRouter` + `RulePlanner` + `WorkflowRegistry` |
| 横切扩展 | permissions、registry | **hooks**、rules | **见 §3 已实现钩子** |
| 编排策略 | runtime 内流程 | **AGENTS 级 playbook** | 规则 planner；可演进为策略表 |

---

## 3. 主仓库已吸收的最小实现：生命周期钩子

对标 ECC 的 **hooks 思想**与 claw 的 **横切观测**，在不引入插件文件树的前提下，增加内核级扩展点：

- **协议**：[`backend/app/hooks/lifecycle.py`](../backend/app/hooks/lifecycle.py) 中的 **`AgentLifecycleHook`**（`before_act` / `after_act`）。
- **挂载点**：[`ChatAgent`](../backend/app/agent/chat_agent.py) 构造函数参数 **`hooks`**；`act()` 在进入 `_execute_act` 前后调用（**约定：只读，不修改入参/出参**）。
- **用途**：审计日志、计费埋点、实验开关、采样 trace；复杂副作用建议异步队列，避免拖慢主链。

**已补充**：`AGENT_LIFECYCLE_LOGGING` 打开时由 **`AgentFactory`** 装配 **`LoggingLifecycleHook`**；**`runtime_session_to_markdown`** 用于单轮快照可读导出。

**未做（留作后续）**：YAML/DB 策略表、hook 优先级与短路、插件类路径发现等。

---

## 4. 建议的后续落点（按性价比）

1. **策略表**：将 `RulePlanner` 中硬编码关键词逐步迁到可配置表（仍由同一接口 `plan` 消费）。
2. **Hook 装配**：`Settings` / 环境变量选择启用哪些 hook 类（反射或注册表），由 `AgentFactory` 注入。
3. **Runtime 报告导出**：借鉴 claw `RuntimeSession.as_markdown()`，增加 **只读导出**（JSON/Markdown）供工单与客服系统。
4. **Manifest 轻量版**：模块与工具版本清单接口（不必一步做到 parity-audit）。

---

## 5. 相关文档

- 更细的 claw 模块对照：[`claw-code-main-architecture-notes.md`](claw-code-main-architecture-notes.md)、[`claw-code-main-vs-learnchainpros.md`](claw-code-main-vs-learnchainpros.md)
- ECC 与 runtime 路线：[`everything-claude-code-architecture-notes.md`](everything-claude-code-architecture-notes.md)、[`everything-claude-code-vs-runtime-roadmap.md`](everything-claude-code-vs-runtime-roadmap.md)
- 总纲：[`agent-framework-design.md`](agent-framework-design.md)
