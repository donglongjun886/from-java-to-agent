# A2A 协议：概念、核心抽象与 MCP 的分工

> MCP 连接 Agent 和工具（Agent ↔ Tool），A2A 连接 Agent 和 Agent（Agent ↔ Agent）——两者不是替代关系，是解决不同层次的问题。

## 关键认知

**为什么需要 A2A**：
一个 Agent 能做的事有上限（上下文窗口 + 工具数量）。当任务需要多 Agent 协作时（比如 Research Agent 搜集资料 → Writer Agent 生成报告 → Reviewer Agent 质量审核），需要 Agent 之间的标准通信协议。

**MCP vs A2A 分工**

| 维度 | MCP | A2A |
|------|-----|-----|
| 连接对象 | Agent ↔ 外部工具/数据源 | Agent ↔ Agent |
| 通信内容 | Tool 定义 + 调用 + 结果 | 任务卡片（Task Card）+ 消息 + 工件（Artifact） |
| 发现机制 | `tools/list` | Agent Card（能力声明 + 端点 + 认证方式） |
| 交互模式 | 请求→响应 | 任务生命周期（提交→执行→状态更新→完成） |
| 成熟度 | 生产可用 | 演进中（v0.3→v1.0），生产案例少 |

**A2A 的核心抽象**：
- **Agent Card**：声明"我是谁，我能做什么，怎么联系我"（≈ 服务注册中心的元数据）
- **Task**：工作单元，有状态机（submitted → working → completed/failed/canceled）
- **Artifact**：任务产出（文档/报告/代码），与消息分离存储

## Java 映射 + 面试话术

**Java 类比**：
- MCP ≈ **JDBC**——应用通过标准接口连接外部资源（数据库）
- A2A ≈ **RESTful 微服务间 HTTP 通信 + 服务注册（类比 Spring Cloud Feign + Nacos）**——Agent Card 声明能力/端点/认证方式，类似 Nacos 的服务元数据
- Task 状态机 ≈ **工作流引擎的任务生命周期**（待处理→处理中→完成/失败/取消），是 Flowable 任务生命周期的极简版本——保留了最核心的主路径状态，去掉了边界事件和多实例等复杂语义

**面试这么说**：
> "MCP 和 A2A 的分工很清晰——MCP 是纵向连接，Agent 到工具；A2A 是横向连接，Agent 到 Agent。类比 Java 生态，MCP 像 JDBC，定义了工具访问的标准协议；A2A 像 gRPC，定义了服务间通信的标准协议。A2A 的 Agent Card 就是 Nacos 的服务注册——声明能力、端点、认证方式。Task 状态机跟 Flowable 的任务生命周期一个模型。但说实话，A2A 目前还在早期，我用 LangGraph 的多 Agent 编排也能达到同样效果，只是缺少标准化的 Agent 发现机制。"
