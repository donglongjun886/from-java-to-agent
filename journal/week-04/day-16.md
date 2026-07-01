# Day 16 (2026.06.29 一) — Agentic Retrieval + 多 Agent 模式 + Harness六层

## Part 1: Agentic Retrieval — Agent 驱动的检索决策 ✅

### 核心认知

**Agentic Retrieval 和静态 RAG Pipeline 的本质差别不在精度，在决策权归属。**

静态 RAG 的检索路径是开发者预设的：query -> embedding -> top-k -> LLM，一条直线，没有分叉。不管用户问的是什么类型的问题，都走同一条管道。这就像后端里硬编码 `if-else` 调不同 DAO——能跑，但每条分支都要你手动写死。

Agentic Retrieval 把这套决策权交给了 LLM。你只负责告诉它「你有哪些工具可用」，它自己根据问题类型选工具、决定调几次、什么时候停。四个 Tool 的设计：

| Tool | 解决场景 | 底层思路 |
|------|---------|---------|
| `vector_search` | 概念性/语义近似匹配 | Embedding + 余弦相似度 |
| `bm25_search` | 精确术语/数字/错误码 | 关键词频率 + 倒排索引 |
| `sql_query` | 聚合统计/时序/条件过滤 | Text-to-SQL（只读账号 + Schema 白名单 + Tool description 中声明仅 SELECT） |
| `graph_query` | 多跳关系/实体关联 | 知识图谱查询 |

路由决策不靠 `if-else`，靠 tool description 让 LLM 自主判断。比如用户问「HikariCP 配置」走 vector，「commit abc123 的 NPE」走 bm25，「Q2 SLA<99.9% 的天数」走 SQL——但更关键的是，遇到需要多源交叉验证的复杂问题时，Agent 会自主串行调用多个工具：先 vector 找相关文档，再 bm25 搜具体术语，最后融合结果。这不是四选一，是 Agent 自主编排一串工具调用。

**关键的认知升级**：Agentic 不是比 RAG 更准，而是更灵活。静态管道在明确查询场景下精度可能更高，Agentic 的价值在不确定性——用户意图不明确、需跨多数据源推理、中间结果不理想需换策略时，它能自己找到路。换的是适应性，不是精度。这个认知如果面试时说不清楚，会让人觉得你对 Agent 的理解停留在「用 LLM 替代规则」的浅层。

Java 类比：静态 RAG = 硬编码 DAO 调用链，Agentic Retrieval = 运行时动态路由决策。

### 代码产出

- `agentic_retrieval.py`：完整的 Agentic 检索演示，四个 Tool 注册 + LLM 自主路由决策 + 最多 5 轮迭代防死循环。三个测试查询覆盖单源/跨源/语义三类场景，运行输出清晰展示 Agent 每一步的 Tool 选择决策。末尾附 Agentic vs 静态 RAG 对比速查表，面试直接用。

### 笔记

- [multi-agent-patterns.md](../../notes/week-04/multi-agent-patterns.md) 第 1、5 节：Agentic Retrieval vs 静态 RAG 对比表 + 四 Tool 设计 + 路由决策原理

---

## Part 2: 多 Agent 协作模式 + 框架选型 ✅

### 核心认知

**多 Agent 协作的核心不是框架，是你如何组织 prompt + 控制流。三种模式对应三种控制流拓扑：**

1. **Manager-Worker（编排模式）**：Manager 拆解任务 -> 并行分派 Worker -> 汇总。控制流是中心化的，像微服务里的 API Gateway 并行调多个下游。适合多子任务独立场景（查报告+查财报+查新闻）。

2. **Pipeline（流水线模式）**：Agent1(检索) -> Agent2(过滤) -> Agent3(生成)，串行接力，前一阶段输出是后一阶段输入。控制流是线性的，像 Unix 管道或 Kafka topic 链。适合一个任务的多阶段处理（翻译 -> 润色 -> 校对）。

3. **Peer-to-Peer（对等协作模式）**：多个 Agent 从不同视角独立分析同一问题 -> 互相辩论 -> 融合输出。控制流是去中心化的，像多人 code review 同一 PR 后汇总意见。适合高风险决策需多角度验证（合规审查、安全审计）。

**关键洞察**：三种模式在代码层面都不是「魔法」——就是用不同的 system_prompt 给 LLM 戴上不同的「角色眼镜」，然后在代码里控制调用顺序（串行/并行/辩论）。框架的价值是省 boilerplate，但不理解三种模式的本质差异就盲目选框架，等于不知道 Spring 的 IOC 原理就直接用 `@Autowired`——面试一问就穿帮。

**框架选型认知**：第一问永远不是「哪个框架好」，而是「我需要多少控制力」：

| 维度 | LangGraph | OpenAI Agents SDK | CrewAI |
|------|-----------|-------------------|--------|
| 控制力 | 高（图结构完全可见） | 中（Handoff 透明） | 低（Task 拆解黑盒） |
| 学习曲线 | 高 | 低 | 中 |
| 适合场景 | 需精确控制的生产系统 | 快速原型+简单移交 | 探索性多 Agent 协作 |
| 模型绑定 | 无 | 绑 OpenAI | 无（最佳实践绑 GPT-4） |

Java 类比：LangGraph = 工作流引擎（Flowable/Camunda），你需要显式定义每一个节点和边，换来的是完全可审计可回放。CrewAI = 声明式编排，你告诉它目标，它自己拆解执行，但内部流程不透明。选哪个取决于你对「确定性」的要求有多高。

### 代码产出

- `multi_agent_collab.py`：三种模式全部用纯 OpenAI API 实现，零框架依赖。
  - **Manager-Worker 演示**：Manager 拆解任务 -> 三个 Worker 并行（org/finance/tech） -> ThreadPoolExecutor 并行执行 -> Manager 汇总报告
  - **Pipeline 演示**：Rewriter（口语改写） -> Retriever（精确检索） -> Reviewer（质量审核），三阶段链式传递
  - **Peer-to-Peer 演示**：CTO（技术视角） vs CFO（财务视角）独立分析 -> CEO 辩论融合，多视角权衡决策
- `four_agent_system.py`：Pipeline 模式的四 Agent 架构实战（Retrieval Planner -> Multi-Source Retriever -> Generator -> Evaluator），含独立评估（Evaluator 不是 Generator 自评，外部独立评估才能发现幻觉）、并行检索、LLM 容错（正则提取失败时关键词回退）。

### 笔记

- [multi-agent-patterns.md](../../notes/week-04/multi-agent-patterns.md) 第 2-7 节：三种模式详解 + 对比表 + 框架选型 + 面试要点（白板画法 + 必答关键句 + 常见陷阱）
- [production-agent.md](../../notes/week-04/production-agent.md)：Agent 生产化五维度（安全/容错/成本/可观测/SDD），用 Java 分布式系统经验类比 Agent 上生产的坑与解法

---

## Part 3: Harness 六层 — Agent 的工程骨架 ✅

### 核心认知

**Model 是大脑，Harness 是整个神经系统 + 骨骼系统。大脑决定「能不能想」，Harness 决定「想完之后能不能做事」。**

六层架构从底向上：

| 层 | 职责 | Java 类比 |
|----|------|----------|
| ① 文件系统层 | 大结果落盘只传引用，替代全塞 prompt | 数据库 + OSS 对象存储 |
| ② 工具系统层 | 注册/发现/调用/结果处理，渐进式注册 | SPI 机制（MCP 服务注册与发现） |
| ③ 记忆层 | 四种记忆独立存储（短期/长期/情节/事实） | Redis + MySQL + 向量库 |
| ④ 沙箱层 | 五层纵深防御，LLM 代码不可信 | SecurityManager + Docker + seccomp |
| ⑤ 上下文管理层 | 窗口预算分配 + 渐进式披露 + GC 策略 | JVM 堆管理（-Xmx, GC） |
| ⑥ 反馈环路 | LLM-as-a-Judge + 外部验证 + 自纠闭环 | CI/CD Pipeline |

**三个最深刻的洞察**：

1. **文件系统层的必要性**：全塞 prompt 看起来简单，但 Token 成本 O(n) 线性累积 + Lost-in-the-Middle 效应（中间信息被忽略概率 40-60%）+ 无法跨会话复用——三座大山。文件系统分流后按需读取 O(k)，注意力密度恒定。Token = Agent 的「现金」，浪费在 Java 叫 OOM，在这里叫账单。

2. **上下文管理的 GC 类比**：Context Reset（丢弃大部分历史重建上下文）类比 JVM Full GC——果断、便宜、有信息损失。Context Compaction（LLM 压缩历史为结构化摘要）类比日志压缩（Log Compaction）——保留核心信息、需额外交计算成本。选择策略跟 GC 调优一个思路：话题延续用 Compaction，话题切换用 Reset。

3. **Agent 生产化不是「调个 API 加个重试」**：五个核心挑战（非确定性/安全/成本/可观测/可靠性）在传统微服务里都有成熟方案，但 Agent 场景下都变了形。比如「重试」在微服务里是网络层的透明操作，在 Agent 里却要重试格式解析、JSON 提取、Tool 调用逻辑——失败模式远比微服务复杂。再比如「安全」从边界防御（网关/防火墙挡请求）转向纵深防御（输入 -> LLM -> Tool -> 输出每一层都要做校验），因为攻击面是自然语言，正则表达式根本封不住。

### 笔记

- [harness-engineering-deep.md](../../notes/week-04/harness-engineering-deep.md)：六层架构完整拆解 + Context Reset vs Compaction 深度对比 + 2026 行业最佳实践 + 生产级检查清单 + 面试必问五题

---

## 今日统计

- **笔记**：3 篇（多 Agent 协作模式 / Agent生产化 / Harness六层深度）
- **代码**：3 个 Python 文件（agentic_retrieval.py / four_agent_system.py / multi_agent_collab.py）
> **核心认知锚点**：
> - Agentic Retrieval != RAG Pipeline；前者是 Agent 决策检索策略，后者是固定流程
> - 多 Agent 的本质不是「把一个大模型切成多个小模型」，而是用不同的 system_prompt 给 LLM 戴上不同的「角色眼镜」。关键在交互结构（并行/串行/辩论）匹配业务场景
> - Harness = Agent 的 Spring Framework——提供全套基础设施，让 Model 这个「大脑」能真正做事
> - 静态管道够用时不引入 Agent；Agent 的价值在「不确定性和多步推理」
