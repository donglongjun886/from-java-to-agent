# OpenAI Agents SDK vs LangGraph：Handoff/Guardrail vs StateGraph 范式

> OpenAI SDK 是"一个聪明 Agent 的护栏"，LangGraph 是"一群 Agent 的状态机"——选型取决于你是在增强单个 Agent，还是在编排多个 Agent。

## 关键对比

| 维度 | OpenAI Agents SDK | LangGraph |
|------|-------------------|-----------|
| 设计哲学 | 强化单个 Agent（Guardrail + Handoff） | 编排多个 Agent（图 + 状态 + 检查点） |
| 核心抽象 | Agent（instructions + tools）+ Handoff + Guardrail | StateGraph（节点 + 条件边 + Checkpoint） |
| 多Agent协作 | Handoff（Agent A 把对话转给 Agent B） | 显式图编排（并行/串行/条件/循环） |
| 人机交互 | 有限支持（Tool 调用审批级别，粒度较粗） | Human-in-the-Loop（interrupt/Command，任意节点暂停 + 状态修改） |
| 状态管理 | 会话级（Conversation） | 图级（TypedDict，不可变更新，持久化） |
| 模型绑定 | OpenAI 优先（设计上深度绑定） | 模型无关（任何 OpenAI 兼容 API） |

**Handoff vs LangGraph 的条件路由**：

- **Handoff**：Agent A 作为"控制器"，根据用户输入决定把工作转给 Agent B/C/D。类似**责任链模式**——每个 Agent 判断自己能不能处理，能就接，不能就传下一个。
- **LangGraph 条件边**：不依赖 Agent 的自我判断，而是在图中定义显式的路由逻辑（函数返回下一个节点名）。更可控，更适合复杂编排。

## 什么时候用哪个

| 场景 | 推荐 | 原因 |
|------|------|------|
| 单Agent + 复杂护栏 | OpenAI SDK | Guardrail 是 SDK 的核心优势 |
| 多Agent 固定协作流程 | LangGraph | 显式编排，可测试，可追溯 |
| 需要 Checkpoint/人机交互 | LangGraph | SDK 无此能力 |
| 快速原型 | OpenAI SDK | 代码量少，概念简单 |
| 需要模型无关 | LangGraph | SDK 绑定 OpenAI 生态 |
| 客服路由系统 | OpenAI SDK | Handoff 天然适合"根据问题类型转接" |

## Java 映射 + 面试话术

**Java 类比**：
- OpenAI SDK 的 Handoff ≈ **责任链模式（Chain of Responsibility）**——Handler 判断自己能否处理，不能则 handoff 给下一个
- OpenAI SDK 的 Guardrail ≈ **AOP 切面（`@Before`/`@After`/`@Around`）**——输入/输出校验，与业务逻辑解耦
- LangGraph StateGraph ≈ **Flowable BPMN**——显式图编排，节点+连线，每步可追踪

**面试这么说**：
> "OpenAI Agents SDK 和 LangGraph 不是竞品关系，是互补关系。SDK 的 Handoff 本质是责任链模式——Agent A 判断自己搞不定转给 Agent B，适合客服路由这种'按问题类型分工'的场景。LangGraph 是状态机编排，适合'多步骤固定流程'的场景。实际项目中我会混用——对外接口用 LangGraph 编排主流程（可观测、可回滚），内部单个 Agent 可以用 OpenAI SDK 的 Guardrail 做输入输出校验。技术上 LangGraph 更成熟——模型无关、有 Checkpoint、支持人机交互，这三点目前 SDK 做不到。"
