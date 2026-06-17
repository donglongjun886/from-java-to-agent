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
