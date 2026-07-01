# Agent 状态持久化：Checkpoint vs Saga vs 事件溯源

> 三种模式解决不同层次的问题：Checkpoint 管"断了怎么续"，Saga 管"错了怎么退"，事件溯源管"发生了什么"。

## 关键对比 / 架构认知

| 维度 | Checkpoint（LangGraph） | Saga 模式 | 事件溯源 |
|------|------------------------|-----------|---------|
| 粒度 | 每个 super-step 快照（状态全量） | 每个步骤的补偿操作 | 每个事件（增量追加） |
| 回滚方式 | 重新加载 Checkpoint，从此处重试 | 逆序执行补偿（cancel→refund） | 重放事件流到目标版本 |
| 存储模型 | 快照（snapshot）+ 增量（pending writes） | 补偿链（compensation chain） | 事件日志（append-only log） |
| 典型场景 | Token 超限/服务中断→继续执行 | 跨系统 Tool 调用失败→回滚 | 审计追踪/调试/A/B 测试重放 |
| 实现复杂度 | 低（框架内置） | 中（需手动编写补偿逻辑） | 高（需事件版本管理） |

**核心问题：Agent 为什么需要持久化，不是无状态服务吗？**
Agent 的执行链路比传统微服务长得多（一次用户请求可能触发 5-10 次 LLM 调用 + 3-5 次 Tool 调用 + 多次推理循环），总耗时可能 30-60 秒。上下文窗口（200K tokens）是稀缺资源——如果中间断了，不能从头再来。

## Java 映射 + 面试话术

**Java 类比**：
- LangGraph Checkpoint ≈ **Seata Saga 的状态表**（`seata_state_machine_inst`）——Seata Saga 是一个状态机框架，同时提供状态持久化（每步落盘）和补偿回滚（undo log）两层能力，下面对应 Checkpoint 和补偿链的不同侧面
- Saga 补偿 ≈ **分布式事务回滚**（TC 协调 undo log）——正向操作 + 反向补偿成对定义
- 事件溯源 ≈ **Axon Framework / Eventuate**——领域事件追加写入，查询端投影状态

**面试这么说**：
> "Agent 状态持久化跟分布式事务有天然对应关系。LangGraph 的 Checkpoint 跟我之前用的 Seata Saga 很像——每个 super-step 自动快照，失败时从最近的 checkpoint 恢复，不需要从头重放。区别在于，Saga 的回滚逻辑（补偿）是手写的，Checkpoint 是框架自动的。如果跨系统的 Tool 调用需要补偿（比如发了邮件要撤回），就需要在 Checkpoint 基础上加 Saga 补偿层。事件溯源我目前认为在 Agent 领域的 ROI 不高——调试和审计用 Langfuse 做全链路追踪就够了，不需要引入事件流管理的复杂度。"
