# Agent 基础类面经题

> 目标 15 道，每道包含：参考答案 + 考点分析 + Java 视角加分项

---

## 题 1：什么是 Agent？和 ChatBot 的本质区别？

### 参考答案

**Agent** = LLM（大脑）+ 自主决策（规划）+ 工具调用（执行）+ 记忆（状态）+ 反馈环（纠错）。接收目标后能自己拆解步骤、选择工具、根据中间结果调整策略。

**ChatBot** = LLM + 对话界面。接收输入 → 生成回复，每轮都是"一锤子买卖"，没有自主规划能力。

核心区别：**ChatBot 答问题，Agent 干事情。**

举例——用户说"帮我订明天去上海的机票"：

- ChatBot：回复"建议您查一下携程，价格大概 500-1500 元"
- Agent：查天气 → 搜航班 → 比对时间价格 → 检查日历冲突 → "推荐 G1234，850 元，已下单"

### 考点分析

| 层级 | 考察什么 | 发挥点 |
|------|---------|--------|
| 知道"是什么" | ChatBot vs Agent 的概念边界 | 订机票的例子直观可感知 |
| 知道"为什么难" | Agent 多了哪些工程挑战 | 工具容错、上下文管理、幻觉放大、成本失控 |
| 知道"怎么设计" | 如果让你做，架构如何分层 | 感知层→决策层→执行层→反馈层 |

### Java 视角加分

> "从工程角度，ChatBot 是无状态的请求-响应模型，跟传统 Controller→Service→DAO 一样。Agent 相当于自带任务调度器的微服务集群——LLM 是调度器，Tool 是下游微服务，Memory 是分布式会话状态，Feedback Loop 是熔断+重试+降级。难度不在调 API，在于这个调度器的可靠性。"

### 延伸关键词

Tool Calling、Planning、Memory、ReAct、Checkpoint、Human-in-the-Loop

---

## 题 2：Function Calling 的原理？模型怎么知道该调用哪个函数？

### 参考答案

**原理**：不是模型"知道"该调哪个函数，而是模型**输出了一种特殊格式的决策信号**，由客户端（你的代码）识别信号 → 执行业务逻辑 → 结果塞回对话 → 再调模型。

完整流程：

```
用户输入 → 客户端拼接 [System Prompt + 工具 JSON Schema + 对话历史] → 发 LLM
       → LLM 返回时选择一个：直接回复文本 OR 输出 tool_call（包含 tool_name + 参数 JSON）
       → 如果返回 tool_call：客户端匹配对应函数 → 反射调用 → 结果拼回 messages
       → 再次发 LLM → 模型基于工具结果生成最终回复
```

**模型怎么选的**：

1. 训练时见过大量"用户提问 + 可用工具 + 是否调用"的对话样本
2. 推理时将工具签名（name/description/parameters）注入上下文，模型基于语义匹配判断意图
3. 关键技术点：模型是通过 instruct tuning 学会"需要时输出 tool_call 指令"，不是规则匹配，所以描述写得好不好直接影响调用准确率

### 考点分析

| 层级 | 考察什么 |
|------|---------|
| 表面 | 知道 tool_call 是一种特殊的 response 格式，不是魔法 |
| 中层 | 理解工具注册→注入 schema→LLM 决策→客户端执行的完整链路 |
| 深层 | 知道为什么"工具描述质量"比"代码实现质量"更重要——LLM 只能看到描述，看不到你的代码 |

### Java 视角加分

> "JSON Schema 自动生成是 Java 的天然优势。Python 要手写 JSON 或靠 Pydantic 转，Java 的 @Tool 方法签名本身就是强类型约束，框架反射读取参数名+类型+注解，编译期就锁定了 schema 的正确性。这就是 Spring AI 和 LangChain4j 比 Python 生态省代码的地方。"

### 延伸关键词

ReAct Pattern、Tool Choice（auto/none/required）、Parallel Tool Calling、Tool Spec Schema、幻觉调用（Hallucinated Tool Call）

---

## 题 3：MCP 协议是什么？为什么不用代码里直接写工具？

### 参考答案

**MCP（Model Context Protocol）** 是 Agent 调用外部工具的标准协议。Server 声明能力（list_tools），Client 动态发现并调用（call_tool），两者通过 stdio 或 HTTP+SSE 通信，与语言无关。

**为什么不在代码里直接写工具？**

| 直接写 | 通过 MCP |
|--------|---------|
| 工具和 Agent 代码耦合，加/改工具要改 Agent | Agent 代码不变，运行时动态发现新工具 |
| 一种语言（Python 的工具 JS 的 Agent 调不了） | 跨语言：Python Server → Java Client 无缝 |
| 工具代码跟 Agent 跑在同一个进程里 | 工具独立进程，隔离执行，崩了不影响 Agent |

**核心认知**：Function Calling 定义了「模型怎么表达要调工具」，MCP 定义了「工具怎么暴露给模型」。两者互补——Function Calling 是语言，MCP 是运输管道。

### 考点分析

| 层级 | 考察什么 |
|------|---------|
| 知道"是什么" | MCP = 工具标准协议，Server/Client 架构 |
| 知道"为什么需要" | 解耦、跨语言、独立进程、统一标准 |
| 知道"怎么实现的" | list_tools 声明能力 → call_tool 执行分发 → stdio/HTTP 传输 |

### Java 视角加分

> "MCP 本质上就是 SPI 机制——定义标准接口，实现方按协议注册，调用方运行时动态发现。不用改一行 Agent 代码，换个 MCP Server 就能换一套工具。我实际做过跨语言场景：Python MCP Server 暴露工具，Java LangChain4j MCP Client 通过 stdio 子进程连上去，工具定义和 Agent 代码完全解耦。"

### 延伸关键词

SPI 机制、跨语言、动态发现、Server/Client 架构、stdio/HTTP+SSE、工具隔离

---

## 题 4：LangGraph 的 StateGraph 解决什么问题？和手写 if-else 有什么区别？

### 参考答案

**StateGraph** 是把 Agent 的决策流程建模为有向图：节点（Node）做具体逻辑，边（Edge）定义流转方向，State 自动在节点间传递和合并。

**和手写 if-else 的三个核心区别：**

**① State 自动合并（而非手动拼接）**

手写 if-else：每步产出要自己 `messages.append()`，历史拼接逻辑散落在各处。

```python
# 手写：每步都要手动管理历史
messages.append(HumanMessage(content=input))
response = llm.invoke(messages)
messages.append(response)
if response.tool_calls:
    result = execute_tool(response)
    messages.append(result)  # 容易漏、容易乱
    messages.append(llm.invoke(messages))
```

StateGraph：每个节点只输出自己的部分，框架通过 reducer（如 `operator.add`）自动合并到 State。

```python
# LangGraph：每个节点只关心自己的产出
def chatbot(state): return {"messages": [llm.invoke(state["messages"])]}
def tool_node(state): return {"messages": [execute_tool(state["messages"][-1])]}
```

**② 条件路由和节点隔离（而非代码耦合）**

if-else 的所有分支写在一个函数里，加一个分支要通读全部代码。StateGraph 的节点是独立函数，加节点改路由不改已有代码：

```python
graph.add_conditional_edges("agent", router, {"tools": "tool_node", "end": END})
```

**③ 内建 Checkpoint（断点续传）**

if-else 要实现"某步失败后从断点重试"，需要自己写状态快照和恢复逻辑。LangGraph 的 Checkpointer 一行 `graph.compile(checkpointer=...)` 就解决了。

### 考点分析

| 层级 | 考察什么 |
|------|---------|
| 知道"是什么" | 有向图：Node=处理逻辑，Edge=流转规则，State=共享数据 |
| 知道"和 if-else 的差异" | State 自动合并、节点隔离、内建 Checkpoint |
| 知道"怎么选" | 简单流程 if-else 够用，多工具/多轮/条件复杂时用 LangGraph |

### Java 视角加分

> "LangGraph 本质就是 Flowable 的工作流引擎——你把业务流程定义成节点和连线，引擎负责调度节点、传递上下文、持久化快照。只是 Flowable 用于审批流，LangGraph 用于 LLM 决策流。用 if-else 写 Agent 相当于用 main 方法写微服务编排——能跑，但没法维护。"

### 延伸关键词

StateGraph、Node/Edge、Conditional Edge、Checkpointer、Reducer、operator.add
