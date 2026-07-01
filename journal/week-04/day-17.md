# Day 17 (2026.06.30 二) — 生产化 + 检索评估 + 项目B架构设计

## Part 1: 检索质量评估 — 三指标体系

### 核心认知

**检索评估和生成评估必须分离。** 这是 Day13 排序评估（NDCG/MRR）的自然延伸，但今天把整个评估体系串起来了：

| 评估层次 | 测量什么 | 指标 | 类比 |
|---------|---------|------|------|
| 检索层 | 召回质量：该搜到的搜到了吗？ | P@K / MRR / NDCG | ES 查询写对了吗？ |
| 生成层 | 答案质量：搜到了但用对了吗？ | Faithfulness / Answer Relevance | 前端渲染对了吗？ |

两层必须独立评估的原因：RAGAS 的 Faithfulness 高分不代表检索好（可能是 LLM 自己编的），反过来 MRR 满分也不代表答案好（可能搜对了但 LLM 理解错了）。这跟后端里「DAO 层单元测试」和「Controller 层集成测试」分离是一个道理——不能因为集成测试过了就省略 DAO 测试，你根本不知道 bug 在哪一层。

**三指标的含义，用一句话记**：
- **P@K（Precision at K）**：前K个结果里有几个相关的？分母固定为K，不足K个结果的空缺位按不相关计分，防止仅返回少量结果时虚高。——测的是「搜出来的有没有用」
- **MRR（Mean Reciprocal Rank）**：第一个相关结果排在第几位？1/rank，排第1得1.0，排第3得0.33。——测的是「有用的排得靠不靠前」
- **NDCG@K（Normalized DCG）**：实际排序质量与理想排序的比值。相关度分3档（高/中/低/无），不是简单的0/1，越相关排越前分越高。——测的是「整体排序有多接近最优」

Java 类比：P@K ≈ DAO 方法返回值的非空率；MRR ≈ 第一次 cache hit 的位置；NDCG ≈ 搜索结果排序与业务预期的 Spearman 相关系数。

### 评估结论的工程诚实

静态 RAG 和 Agentic Retrieval 在本次 8 个 QA pair / 4 个数据源的小规模评测中**平均分持平**。这个结论本身就是一个重要的工程认知：

**不是「Agentic 没用」，而是评估粒度和数据规模还不足以暴露差异。** 当前评估粒度是「源级别」——只要 Agent 选对了 `finance` 或 `vector` 这个源，就算命中。真正的差异要到「段落级精准命中」才会显现：当数据源从 4 个扩展到 20+ 个，每个源内部切分成数十个段落，静态规则的覆盖盲区就会出现，Agentic 的路由优势才能量化。

这是评估体系本身的工程素养：**知道你的指标在什么条件下有效、什么条件下失真。**

### 代码产出

- `retrieval_compare.py`：静态 RAG（关键词 if-else 规则路由）vs Agentic Retrieval（Planner + Retriever），同一套评估标准（关键词相关度 0-3 分 → P@3/MRR/NDCG@3），8 个 QA pair 覆盖单源/跨源/对比三类场景。末尾附诚实结论：两者持平，分析粒度与规模局限。

---

## Part 2: Agent 安全深化 — 纵深防御体系

### 核心认知

Day 16 的安全笔记是框架性概述，今天把安全体系落到了具体可实现的代码模式上：

**Agent 安全的本质变化：攻击面从「结构化输入」变成了「自然语言」。**

传统 Web 安全（SQL 注入、XSS、CSRF）的防御手段高度成熟——攻击模式有限、正则就够用。但 Agent 收到的是自然语言，攻击者可以用无数种说法绕过关键词过滤：「忘记之前的指令」「现在你扮演开发者模式」「用 base64 编码输出密码」——同一个意图可以有上千种表达。

**五层纵深防御**（从外到内）：

```
第1层 输入过滤    — 长度限制 + 敏感词检测（类似 WAF，但只能挡最明显的）
第2层 Unicode归一化 — NFKC 防同形异义字符（俄文 a ≠ 英文 a，正则看不出来）
第3层 角色隔离    — system/user role 在 API 层分字段传递（类比参数化查询防 SQL 注入）
第4层 Tool调用预检 — 白名单 + 参数校验 + 危险操作拦截（类比 Spring Security Filter Chain）
第5层 输出校验    — 脱敏 + 格式校验 + 内容安全（类比输出编码防 XSS）
```

关键认知：**单层防御必破，必须纵深。** 就像微服务安全不能只靠网关，Agent 的每一条链路（输入→LLM→Tool→输出）都要做校验。

### 代码产出

- `notes/week-04/production-agent.md`（Day16 撰写，Day17 复习深化）：完整的 Agent 安全体系笔记，含 ToolGuard 代码示例、Prompt 注入防御分层、输出校验三类规则。

---

## Part 3: SDD + Token 成本优化

### SDD（Spec-Driven Development）

**SDD 就是把 Agent 的行为约束写成「合约」，然后自动化验证。** 类比 Java 里的 `interface` + `@Contract` 注解——接口定义行为边界，JSR 380（Bean Validation）校验运行时合规性。Agent 的 SDD 等价物是：

| Java 层 | Agent 层 |
|---------|---------|
| `interface` 定义方法签名 | System Prompt 定义角色边界 |
| `@Contract` 注解约束参数 | JSON Schema 约束输出格式 |
| `@Validated` 运行时校验 | Guardrails（输出校验规则） |
| 单元测试 + CI | Evaluation Pipeline（跑50条用例，分数≥0.85通过） |

**SDD 工作流**：写 Spec（行为约束 YAML）→ 实现 Agent → 跑 Evaluation → 分数 ≥ 阈值？YES 上线 : NO 改 Prompt/换模型。

SDD 解决的核心问题：LLM 输出天然不确定，同一 Prompt 不同调用产出不同结果。传统软件测试的「给定输入=固定输出」在 Agent 世界不成立。SDD 不做精确断言，做**基于统计概率的阈值验收**——跑 50 次，90% 以上达标就算过。

### Token 成本优化

**Token 就是 Agent 的「现金」——花了就没了，而且容易被浪费。** 三个核心策略：

1. **缓存复用**：相同的 System Prompt 可被 API 缓存（DeepSeek 支持 prompt caching），后续调用只计 incremental token。这就像 Redis 缓存热点数据——第一次查库贵，后续命中缓存几乎免费。**关键技巧**：把 System Prompt 放在 messages 数组最前面，且每次调用的 System Prompt 完全相同，缓存命中最高。

2. **上下文窗口管理**：两种策略对应 JVM GC 的两种思路：
   - **Context Reset**（类比 Full GC）：果断丢弃大部分历史，重建上下文。便宜但有信息损失。适用场景：话题完全切换时。
   - **Context Compaction**（类比 Kafka Log Compaction）：让 LLM 把历史压缩成结构化摘要（关键决策/数据/结论），保留核心信息。花一点 Token 做压缩，省后续大量 Token。适用场景：话题延续但历史过长时。

3. **工具定义精简**：不要把全部 Tools 都传给每次 LLM 调用。Tool 的 JSON Schema 定义本身就占 Context Window——传 20 个 Tool 每次调用白花 3000+ Token。按场景分批传递，或者用 Tool 路由（先让轻量分类器判断意图，再决定传哪些 Tool）。

**核心认知**：成本优化不是在「功能实现之后才考虑」的事。架构设计阶段就要想清楚——文件系统层为什么存在？就是为了避免全塞 Prompt 导致的 Token 爆炸。Context Management 层为什么存在？就是为了控制历史消息的膨胀速度。Harness 六层中的每一层都有成本维度的设计考量。

### 笔记

- `notes/week-04/production-agent.md` 第四、六节：Token 预算管理 + SDD 规约驱动开发
- `notes/week-04/harness-engineering-deep.md`：上下文管理层的成本视角分析

---

## Part 4: 项目B — 四 Agent 架构设计（基于 Day16 的 four_agent_system.py 深化分析）

### 核心认知

**四 Agent 不是四个独立的 AI，而是同一个 LLM 戴上四副不同的「角色眼镜」：**

```
用户问题
    │
    ▼
┌──────────────────┐
│ Agent 1: Planner │  ← system_prompt: "你是检索规划专家"
│ 拆解查询→选数据源   │     职责：分析问题，拆成子任务，标注数据源
└────────┬─────────┘
         │ 子任务列表 [{"source":"finance","sub_query":"..."}]
         ▼
┌──────────────────┐
│ Agent 2: Retriever│  ← 并行调四个数据源（vector/bm25/sql/graph）
│ 多源检索→结果融合   │     ThreadPoolExecutor 并发执行
└────────┬─────────┘
         │ 检索结果 {"finance":"...", "vector":"..."}
         ▼
┌──────────────────┐
│ Agent 3: Generator│  ← system_prompt: "你是企业报告生成专家"
│ 基于上下文生成回答   │     约束：不编造、标来源、结构输出
└────────┬─────────┘
         │ 生成回答
         ▼
┌──────────────────┐
│ Agent 4: Evaluator│ ← system_prompt: "你是独立评估专家"
│ 独立评估生成质量     │     评分维度：Faithfulness + Answer Relevancy
└──────────────────┘
```

**三个关键设计决策**：

1. **Evaluator 不能是 Generator 自己**。如果 Generator 自评，幻觉永远发现不了——等于让学生自己批改自己的考卷。外部独立评估才能发现「回答里编了检索上下文没有的数据」。这个设计对应 Zoom JD 里「multi-step, tool-using AI agents」中的质量验证环节。

2. **Retrieval Planner 的价值不在简单查询，在复杂查询**。用户问「研发部预算利用率」，Planner 只输出 1 个子任务——体现不出价值。但当用户问「分析研发部Q3的技术投入和预算效率，给出Q4建议」，Planner 自动拆成 3 个子任务（查财务的研发部预算、查向量的技术文档、综合对比）——这是静态规则做不到的自主推理。

3. **Planner 的容错设计**。LLM 输出的 JSON 格式不可靠——正则提取失败是常态，不能让它把整个 Pipeline 打崩。设计了关键词回退机制：JSON 解析失败 → 用 `if "预算" in query` 规则兜底 → 确保至少有一个数据源被调用。这就像微服务里的 fallback 降级——不追求完美，追求可用。

### 代码产出

- `four_agent_system.py`：完整的四 Agent Pipeline，纯 OpenAI API + 代码编排，零框架依赖。三个演示查询覆盖单源/跨源/对比分析三类场景。Planner 容错（正则提取 + JSON 解析 + 关键词回退三层）、Retriever 并行（ThreadPoolExecutor）、Generator 约束（不编造+标来源）、Evaluator 独立（Faithfulness + Answer Relevancy 双维评分）。

---

## 今日统计

- **笔记**：2 篇深入（生产化 Agent 安全深化 / SDD+Token 成本优化 + Harness 成本视角）
- **代码**：2 个 Python 文件（retrieval_compare.py / four_agent_system.py）
- **核心认知锚点**：
  - 检索评估与生成评估必须分离：先保证召回质量（P@K/MRR/NDCG），再优化生成质量（Faithfulness/Relevancy）
  - 评估的工程诚实：小规模持平不说明 Agentic 没用，说明评估粒度和数据规模还不足以暴露差异——这本身就是工程素养
  - Agent 的纵深防御：攻击面是自然语言，正则封不住。必须五层（输入→Unicode→角色隔离→Tool预检→输出）都做校验
  - SDD = Agent 的「接口契约 + 自动化验收」；Token = Agent 的「现金」，架构设计阶段就得算账
  - 四 Agent 的核心不是四个 AI，是同一个 LLM 戴四副角色眼镜 + 代码控制串/并行流
