# 多Agent协作模式

> 面向有多年后端经验的 Java 工程师。目标：能画出三种模式交互图，能讲清楚 Agentic 与静态管道的本质差别，面试中对答如流。

---

## 1. Agentic Retrieval vs 静态 RAG Pipeline

| 维度 | 静态 RAG Pipeline | Agentic Retrieval |
|------|-------------------|-------------------|
| **检索路径** | 固定：query → embedding → top-k → LLM | 动态：Agent 自主决定调哪些工具、调几次、何时停 |
| **决策权** | 开发者预设所有分叉 | Agent 运行时观察中间结果后自主路由 |
| **多数据源** | 需预设融合策略（RRF/加权） | Agent 根据中间结果决定是否跨源切换 |
| **异常处理** | 查不到就返回空/降级 | 改写 query 重试，或换工具 |
| **Java 类比** | 硬编码 `if-else` 分支调不同 DAO | 策略模式 + Ribbon 运行时动态路由 |

**本质**：静态管道拼「给定 query 下检索质量最优」，Agentic 拼「不确定信息需求下自主探索最优路径」。前者是精度，后者是灵活。

```
静态 RAG:   query → [embedding → top-k → LLM] → answer     直线
Agentic:    query → Agent思考 → 调工具A → 看结果 → 够吗？
                              ↑ 换个工具/改写query ← 不够
                              ↓ 够 → answer                  有环
```

> 关键句：「Agentic 不是比 RAG 更准，而是更灵活。需要多步推理、跨源关联、意图不明确时，它能自己找到路。」

---

## 2. 三种协作模式

### 2.1 Manager-Worker（编排模式）

```
Manager: 拆解任务 → 分派Worker → 汇总
  │           ┌─────────┬─────────┐
  ▼           ▼         ▼         ▼
Worker1    Worker2   Worker3    (可并行)
  │           │         │
  └───────────┴────┬────┘
                   ▼
              Manager: 综合生成最终回答
```

**Java 类比**：微服务编排（Orchestrator Pattern）。BFF 服务收请求 → 并行调多个下游 → 聚合返回。

**关键决策**：Manager 通过 prompt 拆解子任务粒度；Worker 间无依赖可并行（`CompletableFuture.allOf`）；前一个 Worker 输出裁剪后注入下一个 Worker prompt。

### 2.2 Pipeline（流水线模式）

```
Agent1(检索) → Agent2(过滤) → Agent3(生成) → 最终结果
   output = next input
```

**Java 类比**：Unix 管道 `cat | grep | sort | uniq`，或 Kafka topic 链。

**特征**：每 Agent 职责单一；输出即输入；顺序固定可预测；任一环节出错整条链中断。适合「一个任务的多阶段」，非「多子任务并行」。

### 2.3 Peer-to-Peer（对等协商模式）

```
AgentA(视角1) ←→ AgentB(视角2) ←→ AgentC(视角3)
       │              │              │
       └──────────────┼──────────────┘
                      ▼
              辩论/投票 → 共识结论
```

**Java 类比**：分布式共识（Raft），或多人 code review 同一 PR 后汇总意见。

**特征**：多 Agent 从不同视角分析同一问题；通过 Debate 或 Majority Vote 达成共识；适合高风险需求多角度验证（合规审查、安全审计）。

---

## 3. 三种模式对比

| 维度 | Manager-Worker | Pipeline | Peer-to-Peer |
|------|:---:|:---:|:---:|
| **控制流** | 中心化调度 | 线性串行 | 去中心化多轮 |
| **并行度** | 高 | 低 | 高 |
| **适用场景** | 多子任务独立（研究：查报告+财报+新闻） | 多阶段串行（检索→过滤→摘要→润色） | 多视角验证（审查/审计/诊断） |
| **错误容忍** | Worker 失败可降级 | 任一步出错全链断 | 多数覆盖单个错误 |
| **延迟** | = max(Worker) | = Σ(各阶段) | 取决于辩论轮数 |
| **实现复杂度** | 中 | 低 | 高（辩论+共识逻辑） |
| **可控性** | 高（显式控制） | 最高（易调试） | 低（涌现行为） |
| **代表框架** | CrewAI, AutoGen | LangGraph StateGraph | ChatDev, AgentVerse |

> 选型原则：能拆成独立子任务 → Manager-Worker；步骤确定 → Pipeline；需多角度交叉验证 → Peer-to-Peer。

---

## 4. 不依赖框架的实现思路

三种模式的核心不是框架，是你如何组织 prompt + 控制流。框架省 boilerplate。

### 4.1 用 system_prompt 区分角色

```python
ROLES = {
    "manager":  "你拆解用户需求为2-5个子任务，各指定worker类型。输出JSON: {subtasks: [{id, type, query}]}",
    "retriever": "信息检索专家。返回原文+来源标注，不要总结。",
    "analyst":  "数据分析专家。基于检索结果提取数据+趋势，只分析不下结论。",
    "writer":   "技术写作专家。基于分析生成结构化输出。",
}
```

### 4.2 三种模式核心骨架

```python
# Manager-Worker：拆解 → 并行执行 → 汇总
def manager_worker(query):
    plan = llm(ROLES["manager"], query)  # → JSON subtasks
    with ThreadPoolExecutor() as pool:
        futures = {pool.submit(llm, ROLES[t["type"]], t["query"]): t["id"] for t in plan["subtasks"]}
        results = {futures[f]: f.result() for f in as_completed(futures)}
    return llm(ROLES["manager"], f"结果: {results}\n综合生成回答。")

# Pipeline：链式传递
def pipeline(query):
    ctx = query
    for role in ["retriever", "ranker", "generator"]:
        ctx = llm(ROLES[role], ctx)  # 上一步输出 = 下一步输入
    return ctx

# Peer-to-Peer：独立分析 → 互评辩论 → 融合
def peer_debate(question, n=3, rounds=2):
    opinions = [llm(f"专家视角{i+1}，独立分析", question) for i in range(n)]
    for _ in range(1, rounds):
        opinions = [
            llm(f"审视他人观点后修正你的分析", f"你的: {opinions[i]}\n他人: {opinions[:i]+opinions[i+1:]}")
            for i in range(n)
        ]
    return llm("综合以下专家观点，给共识结论（标注一致点/分歧点）", str(opinions))
```

---

## 5. Agentic Retrieval 四 Tool 设计

给 Agent 配备四种检索工具，让它自己决定用哪个、用几次。

```
                 Agent（路由器）
              自主判断该调哪个工具
    ┌──────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼
vector     bm25        sql       graph
_search   _search    _query     _query
语义近似   关键词匹配  结构化查询  实体关系
```

| Tool | 解决场景 | 底层技术 | 典型 Query |
|------|---------|---------|-----------|
| `vector_search` | 「类似意思」的同义/模糊匹配 | Embedding + 余弦相似度 | 「如何优化数据库性能」 |
| `bm25_search` | 精确术语/数字/API名/错误码 | 稀疏向量 + 倒排索引 | 「NPE 在 commit abc123 的修复」 |
| `sql_query` | 聚合统计/时序/条件过滤 | Text-to-SQL | 「上月 DAU>10万的日期」 |
| `graph_query` | 多跳关系/实体关联 | KG (Cypher/SPARQL) | 「张三的直属领导是谁」 |

**路由决策不靠 if-else**，靠 tool description 让 LLM 自主判断：

```python
TOOLS = [
    {"name": "vector_search", "description": "语义相似度搜索。概念性/描述性查询。不适用精确匹配。"},
    {"name": "bm25_search",   "description": "关键词精确匹配。具体术语、错误码、数字时优先用。"},
    {"name": "sql_query",     "description": "结构化SQL查询。聚合/统计/时间范围过滤。先DESCRIBE看表结构。"},
    {"name": "graph_query",   "description": "知识图谱多跳关系查询。谁是谁的上级、依赖关系。"},
]
```

**路由示例**：

| 用户输入 | Agent 决策 | 可能的多步策略 |
|---------|-----------|--------------|
| 「HikariCP 连接池最佳配置」 | `vector_search` | 一步到位 |
| 「commit abc123 造成的 NPE」 | `bm25_search` | 一步到位 |
| 「Q2 SLA<99.9%的天数」 | `sql_query` | 一步到位 |
| 「王五领导管理的所有下属」 | `graph_query` | 一步到位 |
| 「HikariCP 配置 + 相关 issue」 | 先 `vector_search` → 再 `bm25_search` | 串行两工具 |

> 不是四选一，是 Agent 自主编排一串工具调用。这就是 Agentic：它自己编排检索策略，不需要你预设 RRF 融合公式。

---

## 6. 框架选型认知

| 维度 | LangGraph | OpenAI Agents SDK | CrewAI |
|------|-----------|-------------------|--------|
| **核心抽象** | StateGraph（有向图） | Agent + Handoff（移交） | Crew + Task + Agent |
| **协作模型** | 你定义图结构，Agent 是图节点 | Agent 间通过 Handoff 移交控制权 | Manager 自动拆解+分派 |
| **封装度** | 低（图结构完全可见） | 中（Handoff 透明） | 高（Task 拆解黑盒） |
| **学习曲线** | 高（图/状态/条件边） | 低（两个核心概念） | 中（概念多但 API 简洁） |
| **适合场景** | 需精确控制流程的生产系统 | 快速原型+简单多Agent移交 | 探索性多Agent协作 |
| **Java 类比** | 工作流引擎（Flowable/Camunda） | Spring AI ChatClient | 声明式编排（Temporal 高级封装） |
| **可观测性** | ✅ checkpointer + state回溯 | 通过 OpenAI tracing | ⚠️ 内部流程不透明 |
| **模型绑定** | 无（OpenAI 兼容均可） | 绑 OpenAI | 无（但最佳实践绑 GPT-4） |

**选型原则**：需要确定性/可回放/可审计 → LangGraph；Demo/原型验证 → OpenAI Agents SDK；探索性项目，任务拆解靠 LLM 智能 → CrewAI。

> 如同 Java 里你不会用工作流引擎写 CRUD，也不会用 MVC 编排审批流程——第一问永远是我需要多少控制力。

---

## 7. 面试要点

### 7.1 白板画法（三种模式 30 秒画完）

```
Manager-Worker:      Pipeline:           Peer-to-Peer:
    M                   A → B → C         A ←→ B ←→ C
   /|\                                      ↘  ↙
  W1 W2 W3                                   共识
   \|/
    M
```

画完图一句话概括：「Manager-Worker 是任务拆解派发，Pipeline 是阶段串行，Peer-to-Peer 是多方辩论。核心差异在控制流——中心化 vs 链式 vs 去中心化。」

### 7.2 必答关键句

**Q: Agentic Retrieval 比 RAG 更准吗？**

> 「不是更准，而是更灵活。静态 RAG 的检索路径固定，在明确查询场景下精度可能更高。Agentic 的价值在于：用户意图不明确、需跨多数据源推理、中间结果不理想需换策略时，它能自己找到路。换的是适应性，不是精度。」

**Q: 为什么不直接用框架的多 Agent 功能？**

> 「框架封装的是通用模式。我们用 system_prompt 区分角色 + 显式调度逻辑，牺牲了便利性，换来了流程的可调试性和确定性。跟后端里手写 SQL 替代全自动 ORM 优化复杂查询一个道理。」

**Q: Agent 间怎么共享上下文？**

> 「三种方式：1) 共享 State 对象（如 LangGraph 的 state，类似 ThreadLocal 传参）；2) 显式传递（上一步输出注入下一步 prompt）；3) 共享外部存储（Redis/向量库），适合跨会话。选哪种取决于同步还是异步。」

### 7.3 常见陷阱

| 陷阱 | 现象 | 解法 |
|------|------|------|
| Agent 循环调用 | A调B，B调A，死循环 | max_turns 上限 + 调用链环路检测 |
| 上下文膨胀 | 累积全部历史超出 token 限制 | 裁剪：只传摘要不传完整对话 |
| Manager 拆解过度 | 拆出 20+ 子任务，大量冗余 | prompt 约束上限 2-5 个 |
| Pipeline 级联失败 | 中间出错后续全垮 | 每步超时+降级；关键节点加 checkpoint |
