# LangGraph StateGraph vs BPMN 工作流引擎

> 核心差异：BPMN 编排的是"已知路径"，LangGraph 编排的是"LLM 决策的不确定路径"——前者是流程图，后者是决策图。

## 关键对比 / 架构认知

| 维度 | BPMN（Flowable/Camunda） | LangGraph StateGraph |
|------|--------------------------|----------------------|
| 路由决策 | 预定义网关（排他/并行/包容） | 条件边函数（`(state) → str`），可作为规则函数也可作为 LLM 推理输出——后者是 Agent 区别于 BPMN 的核心 |
| 状态模型 | 流程变量（KV pairs） | 强类型 State（TypedDict/Pydantic，不可变更新） |
| 持久化 | 数据库（ACT_RU_* 表） | Checkpoint（SQLite/Postgres，每个 super-step 快照） |
| 人机交互 | 用户任务（UserTask） | Human-in-the-Loop（interrupt + Command 恢复） |
| 版本演进 | 流程定义版本号（BPMN XML） | 代码即流程（Python 函数，Git 管理） |
| 并行策略 | BPMN 并行网关 | Send API（Map-Reduce 风格动态 fan-out） |

**为什么 BPMN 不适合 Agent 编排**：
BPMN 的每一个分支条件必须在设计时定义清楚（`amount > 10000`）。Agent 场景的分支条件往往是"这个查询需要拆成几个子问题？每个子问题走哪个工具？"——这些只能由 LLM 在运行时决定，无法提前枚举。

## Java 映射 + 面试话术

**Java 类比**：
- BPMN ≈ Flowable 工作流——流程图画好，引擎照图执行
- LangGraph 的图里不只有排他网关，还有 LLM 推理节点——路由决策可以从大模型的推理能力中派生，而不是提前写死
- Checkpoint ≈ **Seata Saga 模式的状态快照**——每个步骤落盘，失败时回滚到上一个稳定状态

**面试这么说**：
> "我之前用 Flowable 做审批流，本质是预定义路径的编排。Agent 场景的核心变化是：路由条件无法在设计时穷举。比如用户问'对比宁德时代和比亚迪的储能业务'，Agent 需要自主决策先搜谁、用什么数据源、搜完要不要交叉验证。LangGraph 用 LLM 驱动的条件边替代 BPMN 的硬编码网关，用 Checkpoint 替代流程变量做状态持久化。这跟 Saga 模式的断点续传是一个道理——只是决策者从规则引擎变成了大模型。"
