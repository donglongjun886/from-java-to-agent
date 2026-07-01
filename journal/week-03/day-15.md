# Day 15 (2026.06.27 周五) —— 项目 B（下）+ Week 3 周复盘

## Part 1: 评估跑分 + 上下文工程落地

### 双维评估交叉验证

**核心认知：RAG 项目的完整交付标准 = 架构图 + 评估数据 + 设计权衡**。只写代码不跑评估的 RAG 项目，跟只写 CRUD 不做压测的后端系统一样，交付给面试官的是一个「表面能跑」的 demo，不是一套能证明工程判断力的体系。

今天跑通了 `evaluate.py` 的 RAGAS + NDCG 双维评估。5 个 QA pair（单源 x2、跨源 x2、跨部门 x1），12 篇文档，覆盖 research / trading / compliance 三租户。

**维度 A -- RAGAS 四维（生成质量，LLM-as-a-Judge 黑盒）**：
- faithfulness：LLM 生成是否与 context 一致（测幻觉）
- answer_relevancy：回答是否切题
- context_recall：相关文档是否被检索到（测漏检）
- context_precision：检索出的文档是否相关（测误检）

**维度 B -- NDCG@5 + MRR（排序质量，人工 qrels 白盒）**：
- 12 个 doc_id 按顺序标注 0-3 级相关性打分（3=高度相关，0=无关）
- NDCG 衡量「相关文档排在前面」的程度，MRR 衡量「第一个相关文档的排名」
- 这两指标不依赖 LLM 判断，纯公式计算，可解释、可复现

**双维交叉验证的逻辑**（这是我写进代码注释里的面试一句话）：

> Context Precision（RAGAS 黑盒）与 NDCG（白盒）呈高度正相关时 → 评估体系自身可信。两者分歧大 → 要么 qrels 标注有问题，要么 LLM 评估器有 bias。

这跟传统后端测试是两回事。传统软件的输入输出是确定的，评估是「跑通 / 不跑通」的二元判断。RAG 的评估是概率性的、多维度的，评估体系本身也有可信度问题——你需要用白盒指标去验证黑盒指标，再反过来校准——这是一个循环验证的过程。

> **Java 类比**：传统后端测试 = JUnit 的 assertEqual（确定）。RAG 评估 = 灰度发布的多维度监控面板（概率，需要趋势分析 + 告警阈值）。

### 静态 RAG vs Agentic Retrieval 对比评估

`retrieval_compare.py` 用 8 个 QA pair（单源 x3、跨源 x3、对比 x2），同一套 P@3 / MRR / NDCG@3 指标，对比两种检索模式：

- **静态 RAG（baseline）**：if/else 关键词匹配 → 固定规则路由 → 数据源检索。类似传统 Nacos 里的「条件路由规则」，命中哪个规则走哪个实例。
- **Agentic Retrieval**：Planner（LLM 拆解问题 → 路由决策）→ Retriever（按计划并行/串行调数据源）→ 融合。Agent 自主判断是查财务表还是查组织架构还是向量检索。

**诚实结论**：8 个 QA 对在 4 数据源规模下，两者平均分持平。这个结论本身就有工程认知价值——不是因为 Agentic 没用，而是因为：

1. 数据源太少（4 个），每个源是一整块，MRR 几乎必为 1.0
2. 评估粒度是「源级别」——调对源就算命中，未下沉到段落级
3. Agentic 的优势在「子查询拆解后的精准命中」和「多步迭代推理」，当前评测设计未覆盖

这个结果暴露了一个重要认知：**评估的粒度决定了结论的局限**。就像后端系统做 QPS 压测，只测单接口跟测全链路压测得到的是完全不同的瓶颈数据。知道自己的评估局限在哪里，比得到一个漂亮的数字更有价值。

### 上下文工程策略落地

回顾本周 Day 12 学习的渐进式披露、上下文重置、分片策略，在项目 B 中落地的具体形式：

- **租户隔离 as 上下文作用域**：ChromaDB 的 `$and` where clause 在索引层限定了「哪些文档能进 context」——这是最硬的上下文边界控制，类比 Java 里 ThreadLocal 的租户上下文传递机制
- **ACL 过滤 as 上下文安全策略**：role_intern / role_engineer / role_manager 三字段在 ChromaDB where 层前置过滤，确保敏感文档永远不进入 context window。即使 LLM 被 prompt 注入攻击，跨租户文档也不在可见范围内
- **引用链路 as 上下文可审计性**：每个回答附带 `[{source_type}:{doc_id}]` 格式的引用列表，让生成物可追溯——类比分布式系统的链路追踪 ID

## Part 2: 可观测 + 成本分析

### Langfuse 全链路追踪 + 延迟实测

`trace_pipeline.py` 落地了「查询 → retrieval span（延迟/命中数/来源分布）→ generation span（模型/tokens）→ score 回写」的完整 Trace 结构。工程考量：**优雅降级**（Langfuse 不可用时 console fallback，类比 Sentinel 熔断）、**延迟认证**（auth_check 推迟到首次实例化，类比 lazy-init bean）。

延迟实测（from trace_pipeline 输出）：

| 组件 | 典型耗时 | 占比 |
|------|---------|------|
| Embedding + ChromaDB 检索 | 20-50ms | 15-25% |
| LLM 生成首字延迟 TTFT（DeepSeek） | 150-300ms | 70-80% |
| ACL Filter + Session 解析 | <1ms | 可忽略 |

> 注：上表 LLM 延迟为**首字延迟（TTFT, Time To First Token）**，非完整生成延迟。完整生成延迟取决于输出 token 数量，典型值在 500-2000ms 区间。

LLM 生成是绝对瓶颈且延迟不可控。跟 MySQL 慢查询不同（能优化索引），LLM 延迟只能靠超时 + 重试 + 降级策略。

**租户隔离的检索性能影响**：纯向量检索 10-20ms，带 where clause 过滤 20-50ms。主要开销不在 ChromaDB（in-memory 标量过滤很快），而在 LlamaIndex 胶水层——这也是 `query_engine.py` 的 `acl_query()` 绕过 MetadataFilters 直接调 ChromaDB 的原因。

**成本参考**（DeepSeek V4 Pro，单次 RAG 查询 < $0.002）：日活 1000 用户、人均 10 次查询 ≈ $15-20/天 ≈ $450-600/月。起步阶段 API 调用 ROI 远高于自建 GPU 集群。

## Part 3: Week 3 周复盘

详细复盘见 `journal/week-03/retrospective.md`。Day 15 视角下补充几点：

### 本周的个人突破

Week 3 从 Day 11 的 IR 基础速通到 Day 15 跑通一套完整的企业级 RAG 系统（摄入 → 索引 → 权限检索 → 生成 → 评估 → 追踪），五天内跨越了「搭 RAG demo」到「能讲清楚企业级 RAG 架构」的鸿沟。

**关键认知跃迁**：

1. **RAG 不只是 vector search + LLM**。企业级的核心三差异——异构数据摄入、权限隔离、可审计引用——每一条都是传统 RAG demo 的盲区。IR 基础（BM25 的两大改进、混合检索的权重融合）给了「为什么这么做」的理论支撑。

2. **评估不是事后验证，而是开发过程的驱动轮**。Day 13 的三轮 chunking 实验就是典型案例——Faithfulness 从 0.50 跑到 0.67 再到结论「短文档不切分最优」，每一步都由数据说话。这跟传统后端「先写代码再写测试」的顺序是反的。

3. **Agent 驱动的检索 vs 静态管道，当前阶段量力而行**。`retrieval_compare.py` 的结果是「两者持平」——这不是泄气，而是做工程的人应该有的诚实。数据源 4 个时 Agentic 无优势，扩展到 40+ 个时静态规则的覆盖率一定会崩。知道「什么时候该用 Agent」，比盲目加 Agent 更体现工程判断力。

### 代码产出统计

项目 B 共 9 个文件（ingest / query_engine / evaluate / trace_pipeline / retrieval_compare / agentic_retrieval / four_agent_system / multi_agent_collab / ARCHITECTURE），总计 ~2200 行。Week 3 总收入 ~2400 行代码（Day 11-13 约 1100 行 + 项目 B），笔记 6 篇，12 个 commit。

> **Java 视角终极类比**：这套系统和传统后端的架构层次完全对得上——数据层（ChromaDB ≈ DB）、权限层（ACL ≈ Spring Security）、编排层（Planner→Generator ≈ Flowable）、评估层（RAGAS+NDCG ≈ 单元+集成测试）、可观测层（Langfuse ≈ Prometheus+Grafana）。本质一样：**把一个不确定的东西（LLM 生成）装进一个确定的工程框架，让系统稳定、可度量地运行**。

---

**Day 15 收官感言**：本周最大的收获不是学了 RAGAS 的四个指标或跑了 NDCG 计算公式——而是建立了一套「RAG 项目怎么算做好」的判断标准。评估数据 + 架构图 + 设计权衡，三者缺一不可。没有数据的架构图是 PPT 工程，没有权衡的架构图是不懂取舍。Week 4 进入 Agentic Retrieval 深度 + 多 Agent 协同 + 综合复盘，把这套标准继续贯彻下去。
