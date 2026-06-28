# Harness 工程基础

> Day 4-5 学习笔记（2026-06-10/11）。核心认知：**Agent 的核心竞争力不在模型，在 Harness 工程能力。模型是引擎，Harness 是整辆车。**

---

## 1. 公式与类比

```
Agent = Model（大脑） + Harness（编排框架） + Feedback Loop（反馈环）
```

| Java 概念 | Harness 概念 | 为什么 |
|-----------|-------------|--------|
| Spring Framework | Harness 框架 | 提供 DI/AOP/配置管理等基础设施 |
| Bean 生命周期 | Agent 生命周期 | 初始化 → 运行 → 销毁，有状态管理 |
| @Scheduled 定时任务 | Feedback Loop | 周期性检查 → 触发动作 → 修正 |
| Prometheus + Grafana | 可观测性 | Token 统计 / 延迟 / 链路追踪 |
| Docker Container | 沙箱 | 隔离执行环境 |

**关键认知**：2026 年模型能力趋于同质化，差异化竞争在于谁能把 Agent 工程化做好。就像 Java 生态里 Spring 的成功不在于 JDK，在于框架层。

---

## 2. Harness 六层架构

```
┌─────────────────────────────────────┐
│           应用层（Agent 业务逻辑）     │
├─────────────────────────────────────┤
│ ① 上下文管理  │ 窗口管理 / 重置 / 分片 │
│ ② 工具系统    │ Tool 注册 / 绑定 / 调用│
│ ③ 记忆系统    │ 短期 / 长期 / 情节 / KV│
│ ④ 沙箱        │ 代码隔离执行           │
│ ⑤ 文件系统    │ 状态持久化 / 审计 / 回滚│
│ ⑥ 可观测性    │ Token / 延迟 / 链路追踪 │
└─────────────────────────────────────┘
```

---

## 3. 文件系统作为状态

### 3.1 为什么不用 Context Window 存状态

Context Window 是两个稀缺资源：
- **容量有限**（DeepSeek 128K，Claude 200K，但越大越贵越慢）
- **按 token 计费**（input 也花钱）

把历史对话全塞窗口 ≈ 把数据库数据全加载到 JVM 堆内存。

### 3.2 正确做法：文件系统是 Agent 的数据库

```python
# ❌ 反模式：把所有状态放窗口里
messages = [system_prompt] + all_history + new_question  # 窗口炸了

# ✅ 正确：关键状态落盘，窗口只放当前上下文
state_file = Path(f"agent_state/{session_id}.json")
state = json.loads(state_file.read_text())  # 从文件恢复
context = state["summary"][-500:]  # 只取近期摘要
```

类比：
- 文件系统 ≈ MySQL/PostgreSQL（持久化、可审计、可回滚）
- Context Window ≈ Redis Cache（热数据，有容量限制和驱逐策略）

### 3.3 实际代码中的体现

`agent_with_feedback.py` 的 `history` 列表就是文件状态的原型——每次重试的 QA 对都记录下来，窗口里只放当前重试需要的反馈信息。

---

## 4. 工具系统（Tool System）

### 4.1 Function Calling 流程

```
User: "杭州天气怎么样？"
  → LLM（决策）：需要调用 get_weather(city="杭州")
    → Client 执行：查数据库 → "晴，28°C"
      → LLM（总结）："杭州今天晴，28°C，适合出门"
        → User 看到最终回复
```

### 4.2 工具注册与绑定

```python
# langgraph_agent.py 中的实际代码结构
TOOLS = [
    {"name": "get_weather", "description": "...", "parameters": {...}},
    {"name": "calculate", "description": "...", "parameters": {...}},
]

model_with_tools = model.bind_tools(TOOLS)  # 一次性绑定

def router(state) -> Literal["tool", "eval"]:
    last = state["messages"][-1]
    return "tool" if last.tool_calls else "eval"
```

| Java 类比 | Tool 概念 |
|-----------|----------|
| `@Service` 注解 | `@tool` 装饰器 |
| ApplicationContext.getBean() | Tool 路由分发（按 name 查找） |
| REST API endpoint | Tool 的 `name + parameters` |
| API Gateway 路由 | `router()` 条件分支 |

### 4.3 关键认知

Tool Calling 是 Agent 从「聊天机器人」到「干活的系统」的质变点。没有 Tool 的 LLM 只能说话，有了 Tool 的 Agent 能做事。

---

## 5. 记忆系统（Memory）

### 5.1 四种记忆类型

| 类型 | 存储 | 类比 | 生命周期 | 适用场景 |
|------|------|------|---------|---------|
| **短期窗口** | messages 数组 | HTTP Session | 单次会话 | 当前对话上下文 |
| **长期语义** | 向量数据库（ChromaDB） | Elasticsearch | 跨会话持久 | 「之前聊过的类似话题」 |
| **情节摘要** | KV 存储（Redis） | 用户行为日志 | 按时间衰减 | 「上个月做过什么」 |
| **事实 KV** | 关系型数据库 | 配置中心 | 永久（手动更新） | 「公司政策」「我的偏好」 |

### 5.2 使用决策

```
新消息进来
  → 是事实？（公司政策、个人信息）→ 事实 KV
  → 是事件？（上次做了什么）      → 情节摘要
  → 是知识？（概念、原理）         → 长期语义（向量化后存入）
  → 是上下文？（当前对话）         → 短期窗口（会话结束可能丢弃）
```

---

## 6. 上下文管理

### 6.1 核心原则

> Context Reset > Compaction（重置上下文优于压缩上下文）

压缩上下文（Compaction）≈ 把 100KB 日志 gzip 到 10KB——信息必然丢失。
重置上下文（Context Reset）≈ 把关键状态存文件，开新会话时只加载摘要——信息结构化保留。

### 6.2 渐进式披露

不一次性把所有信息塞给 LLM，而是：
1. 先给概要（任务描述 + 当前状态摘要）
2. LLM 需要时再查询详情（通过 Tool 调用文件/数据库）
3. 类比：懒加载（Lazy Loading）——只加载当前需要的

### 6.3 工程约束

- DeepSeek: 128K 窗口，但超过 64K 后注意力衰减明显
- 速算：1K token ≈ 700 汉字。100K 对话 ≈ 7 万汉字 ≈ 一篇中篇小说
- 经验值：日常对话控制在 4-8K token，复杂任务控制在 16-32K

---

## 7. 反馈环（Feedback Loop）

### 7.1 基本流程

```
生成 → 评估 → 不合格？→ 带反馈重试 → 再评估 → ... → 达标输出
```

### 7.2 实际代码（agent_with_feedback.py）

```python
class AgentWithFeedback:
    def chat_with_feedback(self, user_input, expected_format):
        for attempt in range(self.max_retries + 1):
            answer = self.chat_raw(user_input, hint)   # 生成
            eval_result = evaluate(question, answer)     # 评估
            if eval_result["overall"]["score"] >= threshold:
                return answer                            # 通过
            hint = build_feedback(eval_result)           # 未通过→构造反馈
```

### 7.3 关键设计决策

- **传递反馈，不是盲目重试**：重试时告诉 Agent 上次哪里不好（accuracy/relevance/completeness/format_quality 各维度 reason），Agent 才能针对性改进
- **设置上限**：max_retries=2，避免死循环烧 token
- **记录历史**：每次评估结果保存到 history，可回溯分析

类比：Feedback Loop ≈ CI/CD Pipeline 的 test → fix → retest 循环。

---

## 8. 可观测性

### 8.1 Agent 需要观测什么

| 指标 | 含义 | Java 类比 |
|------|------|-----------|
| Token 消耗 | input/output token 数量 | 数据库 QPS |
| 延迟 | 首 token 时间 / 总耗时 | P99 响应时间 |
| 重试率 | Feedback Loop 触发比例 | 异常率 |
| 工具调用次数 | 每次对话调了几次 Tool | 下游依赖调用量 |
| 评估分数 | LLM-as-a-Judge overall 分布 | 业务指标 |

### 8.2 实际代码中的 token 统计

`agent_with_feedback.py` 的 `stats()` 方法已经在做了：
```python
self.total_input_tokens += response.usage.prompt_tokens
self.total_output_tokens += response.usage.completion_tokens
```

生产环境需要接 Langfuse / LangSmith 做全链路追踪。

---

## 核心 Takeaway

1. **模型是引擎，Harness 是整辆车** — 只关注模型选型就像只关注发动机马力，不管底盘和变速箱
2. **文件系统是 Agent 的数据库** — 状态落盘，不要塞窗口
3. **Feedback Loop 是 Agent 的 CI/CD** — 自动化质量门禁，不是可有可无
4. **Tool 注册 ≈ Bean 注册** — Spring 的 DI 思想在 Agent 世界完全适用
5. **可观测性从一开始就要做** — 不要等到生产环境出问题才加监控

---

## 延伸

- [Modern Agent Harness Blueprint 2026](https://gist.github.com/amazingvince/52158d00fb8b3ba1b8476bc62bb562e3)
- [Harness Engineering: The 2026 Guide](https://techiegigs.com/harness-engineering-complete-guide/)
- Langfuse 文档：https://langfuse.com/