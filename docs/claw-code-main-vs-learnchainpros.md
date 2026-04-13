# `claw-code-main` 与 `learnChainPros` 模块对照表

> **主线说明**：`learnChainPros` 主代码库当前为 **快速开发迭代** 节奏；本文档用于与 `student/claw-code-main` 的模块级对照与借鉴，阅读语境偏参考归档，不等同于主仓库的日常开发清单。

## 1. 文档目的

这份文档用于把 [`student/claw-code-main`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main) 与我们当前的 [`learnChainPros`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros) 做一个“模块级对照”。

目标不是判断谁更好，而是帮助后续学习时快速分清：

1. 对方项目的模块在我们这里大概对应什么。
2. 哪些能力我们已经有了。
3. 哪些能力对方更强、值得我们借鉴。
4. 哪些能力是对方项目的特殊语境，不适合直接照搬。

## 2. 先给结论

如果只用一句话概括：

- `claw-code-main` 当前 Python `src/` 更偏 **runtime / harness / CLI orchestration**
- `learnChainPros` 当前更偏 **Agent framework 主链抽象与最小可运行能力**

也就是说：

### 对方更擅长的地方

- CLI runtime surface
- session / transcript / history / usage
- mirrored command/tool inventory
- runtime orchestration report

### 我们更早落地的地方

- `BaseAgent`
- `BaseTool`
- `BaseMemory`
- `BasePrompt`
- `BasePlanner`
- `BaseWorkflow`
- `BaseExecutor`

## 3. 总体映射图

```text
claw-code-main
  CLI / Runtime / QueryEngine / Session / Registry / Permissions

learnChainPros
  Agent / Prompt / Tool / Memory / Planner / Workflow / Executor
```

一句更直白的话：

- 对方更像“运行时外壳和执行环境研究”
- 我们更像“Agent 内核和执行主链搭建”

## 4. 模块级对照

### 4.1 入口层

#### `claw-code-main`

- [`src/main.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/main.py)

职责：

- 统一 CLI 入口
- 暴露多种运行模式
- 作为整个 runtime 的外部入口面

#### `learnChainPros`

- [`backend/app/main.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/main.py)
- [`backend/app/routes/chat.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/routes/chat.py)
- [`backend/app/services/chat_service.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/services/chat_service.py)

职责：

- HTTP API 入口
- 把前端请求接到 Agent 主流程

#### 对照结论

- 对方入口是 **CLI-first**
- 我们入口是 **HTTP/API-first**

这意味着后续如果我们要学习对方的 runtime 能力，最值得借鉴的是：

- “入口后的运行时组织”

而不是简单照搬 CLI 形式。

---

### 4.2 运行时总控层

#### `claw-code-main`

- [`src/runtime.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/runtime.py)

职责：

- 组装 context / setup / system init
- 路由 prompt
- 建立 execution registry
- 调 query engine
- 汇总成 `RuntimeSession`

#### `learnChainPros`

主链仍以 `ChatAgent` 为编排核心，但已抽出 **`RuntimeManager`** 作为记录与协调层，并与 **`RuntimeSession`**（单轮运行快照：规划、workflow trace、工具/模型调用、错误与 `workflow_result`）配合使用：

- [`backend/app/runtime/runtime_manager.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/runtime/runtime_manager.py)
- [`backend/app/runtime/runtime_session.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/runtime/runtime_session.py)
- [`backend/app/agent/chat_agent.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/agent/chat_agent.py)（规划、工具/模型/工作流分支与 trace 写入）
- [`backend/app/planners/rule_planner.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/planners/rule_planner.py)
- [`backend/app/workflows/sequential_workflow.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/workflows/sequential_workflow.py)、[`conditional_workflow.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/workflows/conditional_workflow.py)、[`agent_executor.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/workflows/agent_executor.py)

尚未引入对方那种「大而全」的独立 **`Runtime` façade**（例如 CLI 总控 + turn loop 一体），但 **`RuntimeManager + RuntimeSession`** 已承担「一次请求内聚合观测」的职责，方向与对方 `bootstrap_session` 汇总报告类似、范围更小。

#### 对照结论

执行主链与**可观测快照**已对齐到同一套对象上；后续若借鉴对方，重点仍是：**显式 Query/Turn 引擎、usage、stop_reason、结构化重试** 等，而不是重复造一个与 `RuntimeManager` 重叠的壳。

---

### 4.3 Query / Turn Engine

#### `claw-code-main`

- [`src/query_engine.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/query_engine.py)

职责：

- turn loop
- usage 统计
- structured output retry
- transcript compact
- stop reason 管理

#### `learnChainPros`

当前没有显式独立的 `QueryEngine` 层。  
类似职责主要分布在：

- `ChatAgent`（单轮编排、规划分支、转写协调）
- `Memory` / `PromptBuilder`（上下文与 prompt）

#### 对照结论

对方这里更强。  
尤其是这些点很值得后续借鉴：

1. `max_turns`
2. `max_budget_tokens`
3. `structured_output`
4. `structured_retry_limit`
5. `stop_reason`

这说明：

## 我们后续如果做 Runtime/Observability，Query/Turn Engine 会是很自然的一层

---

### 4.4 Agent 主体

#### `claw-code-main`

当前 Python `src/` 没有像我们这样清晰落地一个：

- `BaseAgent`
- `ChatAgent`

它更像 runtime orchestrator + mirrored inventories 的组合。

#### `learnChainPros`

- [`backend/app/agent/base_agent.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/agent/base_agent.py)
- [`backend/app/agent/chat_agent.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/agent/chat_agent.py)

职责：

- 统一接收 `AgentInput`
- 规划 / 工具 / 模型 / memory 编排
- 返回 `AgentOutput`

#### 对照结论

这里是我们比对方当前 Python 版更清晰的一层。  
这也是我们当前项目的主优势。

---

### 4.5 Prompt / 上下文构建

#### `claw-code-main`

没有像我们这样显式落地：

- `BasePrompt`
- `PromptBuilder`

更多是把输出组织、summary lines、structured output 放在 `QueryEnginePort` 里。

#### `learnChainPros`

- [`backend/app/prompts/base_prompt.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/prompts/base_prompt.py)
- [`backend/app/prompts/prompt_builder.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/prompts/prompt_builder.py)

职责：

- 组织历史消息
- 构建最终 prompt
- 让模型分支真正利用 memory

#### 对照结论

这层我们现在已经更像一个“可复用 Agent Prompt 模块”。  
对方当前 Python 版在这方面不是重点。

---

### 4.6 Tool 层

#### `claw-code-main`

- [`src/tools.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/tools.py)
- [`src/execution_registry.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/execution_registry.py)

特点：

- 工具以“镜像 inventory”方式存在
- 当前更偏 registry/index/surface
- `execute_tool(...)` 返回“哪个工具会处理该 payload”的 message

#### `learnChainPros`

- [`backend/app/tools/base_tool.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/tools/base_tool.py)
- [`backend/app/tools/time_tool.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/tools/time_tool.py)、[`weather_tool.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/tools/weather_tool.py)（示例工具，由 `AgentFactory` 注册）
- [`backend/app/tools/tool_registry.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/tools/tool_registry.py)
- [`backend/app/tools/tool_router.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/tools/tool_router.py)

特点：

- 工具是真执行的
- 注册中心清楚
- 有真实输入输出协议

#### 对照结论

对方更强的是：
- mirrored inventory / registry 思维

我们更强的是：
- 最小真实执行链

---

### 4.7 Planner

#### `claw-code-main`

当前 Python 版没有像我们这样显式落地：

- `BasePlanner`
- `RulePlanner`

但它的 runtime routing 和 query engine 已经体现了一些“执行前先分流”的思想。

#### `learnChainPros`

- [`backend/app/planners/base_planner.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/planners/base_planner.py)
- [`backend/app/planners/rule_planner.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/planners/rule_planner.py)

职责：

- 通过规则与 `ToolRouter` 决定 `planner_result.action`：
  - `tool`：单工具直调
  - `model`：直调模型
  - `workflow`：下发 `workflow_name` 与 `steps`，由 `ChatAgent` 经 **`WorkflowRegistry`** 解析为 `SequentialWorkflow`、`ConditionalWorkflow` 等实现并执行

#### 对照结论

这层目前是我们自己框架更清楚。  
后续如果学习对方，更适合学的是：

- 更高层 runtime routing / policy

而不是拿对方当前 Python 版来替代我们已有的 Planner 抽象。

---

### 4.8 Workflow / Executor

#### `claw-code-main`

当前 Python 版没有像我们这样显式落地：

- `BaseWorkflow`
- `SequentialWorkflow`
- `BaseExecutor`
- `AgentExecutor`

#### `learnChainPros`

- [`backend/app/workflows/base_workflow.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/workflows/base_workflow.py)
- [`backend/app/workflows/sequential_workflow.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/workflows/sequential_workflow.py)（顺序执行，**单步失败即结束**并返回失败汇总）
- [`backend/app/workflows/conditional_workflow.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/workflows/conditional_workflow.py)（按步骤 `condition` 选择后继，支持失败后的兜底模型步骤等）
- [`backend/app/workflows/workflow_registry.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/workflows/workflow_registry.py)、[`workflow_result.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/workflows/workflow_result.py)
- [`backend/app/workflows/base_executor.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/workflows/base_executor.py)
- [`backend/app/workflows/agent_executor.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/workflows/agent_executor.py)

职责：

- 由 `AgentExecutor` 执行 `tool` / `model` 步骤并产出统一 step result
- 支持步骤结果传递（后一步消费前一步输出）
- 顺序与条件两种控制流并存，由规划层命名工作流

#### 对照结论

这层目前是我们明显走得更深。  
因此对方在 Workflow 层不是直接借鉴对象，而更像提醒我们：

## 后面 Runtime 层要怎么把 Workflow 执行过程纳入统一观测

---

### 4.9 会话 / 转录 / 持久化

#### `claw-code-main`

- [`src/transcript.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/transcript.py)
- [`src/session_store.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/session_store.py)
- [`src/history.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/history.py)

职责分得很清楚：

- `TranscriptStore`：会话文本轨迹
- `SessionStore`：持久化 session
- `HistoryLog`：运行历史事件

#### `learnChainPros`

已拆出与主链衔接的存储与协调层（与 `Memory` 解耦）：

- [`backend/app/runtime/base_transcript_store.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/runtime/base_transcript_store.py) / 内存与 SQLite 实现
- [`backend/app/runtime/base_session_store.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/runtime/base_session_store.py) / 内存与 SQLite 实现
- [`backend/app/runtime/transcript_entry.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/runtime/transcript_entry.py)
- [`backend/app/runtime/runtime_manager.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/runtime/runtime_manager.py)（确保 session、构建并追加 transcript）
- HTTP 查询：[`backend/app/routes/chat.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/backend/app/routes/chat.py) 中 `list_sessions`、`get_session_transcript`

#### 对照结论

在「会话元信息 / 多轮转写 / 运行快照入条」方向上，主仓已与对方分层思路对齐；后续仍可借鉴 **`HistoryLog` 式事件流**、更细的 usage 与 compact 策略。

---

### 4.10 权限与策略

#### `claw-code-main`

- [`src/permissions.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/permissions.py)

通过 `ToolPermissionContext` 管理：

- deny names
- deny prefixes

#### `learnChainPros`

目前还没有正式独立的 permission/policy 层。

#### 对照结论

这是我们后续很值得补的一块。  
尤其是在：

- Tool gating
- Executor policy
- Workflow 节点权限

这些方向上，对方给了一个很好的切入思路。

---

### 4.11 清单 / 元数据 / 可描述性

#### `claw-code-main`

- [`src/port_manifest.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/port_manifest.py)
- [`src/models.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/models.py)

它非常强调：

- workspace manifest
- subsystem summary
- mirrored backlog

#### `learnChainPros`

目前我们还没有一个统一的：

- workspace manifest
- module inventory
- runtime report

#### 对照结论

这也是 Runtime/Observability 下一阶段很值得补的方向。

## 5. 最值得借鉴的模块优先级

如果接下来要从 `claw-code-main` 学东西，我建议按下面优先级来：

### 第一优先级：`RuntimeSession` / 运行总报告
对应来源：

- [`src/runtime.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/runtime.py)

主仓现状：`RuntimeSession` + `workflow_trace` / `workflow_result` 等已承载单轮总览。借鉴方向侧重 **usage、耗时、token 级汇总** 等与对方报告粒度对齐。

### 第二优先级：`TranscriptStore / SessionStore / HistoryLog`
对应来源：

- [`src/transcript.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/transcript.py)
- [`src/session_store.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/session_store.py)
- [`src/history.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/history.py)

主仓现状：Transcript / Session 抽象与 SQLite 实现、查询 API 已具备。借鉴方向侧重 **独立 History 事件流**、compact 与跨 harness 对齐（若未来需要）。

### 第三优先级：`ExecutionRegistry`
对应来源：

- [`src/execution_registry.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/execution_registry.py)

我们可以借鉴的方向：

- 在 ToolRegistry 之外，进一步思考统一的执行对象注册层

### 第四优先级：`ToolPermissionContext`
对应来源：

- [`src/permissions.py`](/Users/hqluo/Dev/AgentWorkSpace/learnChainPros/student/claw-code-main/src/permissions.py)

我们可以借鉴的方向：

- 工具权限
- 执行策略
- policy gating

## 6. 当前最不建议直接照搬的部分

1. 不要把对方 Python 版当前的 CLI surface 全盘搬进来
   原因：我们当前项目的入口不是 CLI-first。

2. 不要把 mirrored command/tool inventory 当作我们当前优先级最高的主线
   原因：我们当前更重要的是 Agent runtime 主链与 observability。

3. 不要因为对方有 query engine，就立刻做一个过重的大 Runtime
   原因：我们现在刚把 Planner / Workflow / Executor 立住，应该先在自己的主链上继续长。

## 7. 对我们后续学习的建议顺序

建议按照这个顺序继续推进：

1. 先把这份对照表和架构说明读透
2. 再从 `claw-code-main` 里挑一个最值得借鉴的点
3. 在已有 **`RuntimeSession` + `RuntimeManager` + Store** 的基础上，优先补 **Query/Turn 语义**（步数上限、stop_reason、usage）与 **History 式观测**
4. 持续打磨 **workflow 注册与条件/并行** 与 runtime trace 的一致性
5. 需要工具治理时再引入 **permissions / execution registry** 等策略层

## 8. 一句话总结

`claw-code-main` 当前最值得我们学的，不是“它怎么做一个聊天 Agent”，而是：

## 它怎么把 runtime、session、registry、history、permissions 这些外围骨架组织得更像一个真正的 harness。

而我们当前最值得坚持的，是继续保持自己的主线：

## Agent -> Prompt -> Tool -> Memory -> Planner -> Workflow -> Executor

在这个主链稳定的基础上，再有选择地吸收对方的 runtime / observability 设计。
