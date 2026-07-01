# Day 13 (2026.06.25 三) — 权限感知检索 + 双维评估体系 + Langfuse

Week 3 产出最大的一天。四个文件 ~1100 行代码 + 两篇笔记，从权限模型一路写到评估体系再到全链路追踪，把 Enterprise RAG 最核心的三块拼图一次性补齐。

## Part 1: 权限感知检索 ✅

**权限过滤必须在检索阶段完成，不能等 LLM 生成后校验。** 三重约束的交集：

| 约束 | 失败的代价 | 为什么事后校验不行 |
|------|-----------|------------------|
| 安全 | 敏感文档进入 prompt 后无法擦除 | LLM 已经「看过」了，正则过滤回答是掩耳盗铃 |
| 成本 | 无关文档占用 context window，token 随文档量线性增长 | 钱已经花了，context 已经占用了 |
| 合规 | 多租户下数据隔离是基本要求 | 审计日志无法证明「生成时没有参考越权文档」 |

两层权限模型落地：租户级（`tenant_id`）+ 文档级（`access_level` + `allowed_roles`），全部通过 ChromaDB `collection.query()` 的 `where` clause 在向量检索前做 metadata 预过滤。没有走 LlamaIndex 的 `MetadataFilters`——它对布尔字段组合（`role_intern: True AND role_engineer: True`）支持有限，绕过抽象层直接操作 ChromaDB 反而更灵活。

**Java 类比**：MyBatis 多租户插件在 SQL 入口注入 `tenant_id`，这里是向量数据库的 metadata filter 做同样的事——在查询入口强制注入权限条件，业务代码不可能「忘记」带过滤。

用 8 篇文档（2 租户 × 2 级别 × 2 角色）跑了四个场景：无过滤（暴露跨租户泄露）→ 租户隔离 → 角色级 ACL → 访问级别过滤。这种「先演示不安全，再逐步加约束」的对比写法，比直接讲架构有说服力得多。

**坑点**：LlamaIndex `MetadataFilters` 对 ChromaDB 布尔字段的 `$and` 组合有限制，所以 `acl_retrieval.py` 里直接调了 `collection.query()`。如果只过滤字符串字段（如 tenant），用 `as_retriever` 是可以的。另外，ChromaDB Collection 在反复运行时不会自动清空旧数据，需要每次 `delete_collection` 再重建，否则文档会堆积导致检索结果失真——已通过 `2d554fa` 修复。

## Part 2: RAGAS + NDCG 双维评估 ✅

**评估 RAG 系统需要两把尺子，各测各的维度，不可互相替代：**

| 工具 | 测什么 | 怎么测 | Java 类比 |
|------|-------|--------|----------|
| RAGAS | 生成质量（回答好不好） | LLM-as-a-Judge 自动评分 | 业务逻辑的功能测试 |
| NDCG/MRR | 检索排序（排序准不准） | 人工 qrels + 数学公式 | 数据库索引的查询计划分析 |

RAGAS 四维实测：`Faithfulness=0.67`，`Answer Relevancy=0.88`，`Context Recall=0.85`，`Context Precision=0.80`。评估集是 5 组 QA 对——从单文档事实提取（Q2: HikariCP 公式）、跨文档综合推理（Q1: Virtual Threads + 连接池）、到概念类比理解（Q3: MCP ↔ Java SPI），覆盖了不同难度的检索场景。每组都包含人工写的 `ground_truth` 标准答案，作为 Context Recall 的评估基准。

**Chunking 实验的反直觉发现**：对这批 ~140 token 的文档，不切分效果最好（`Faithfulness=0.67`），`chunk_size=128` 时掉到 `0.50`——切太碎导致单个 chunk 丢失跨句上下文。`chunk_size=256` 时 token 超限直接失败。不是越小越好，也不是越大越好，必须实验数据说话。

实施中最头疼的是兼容性。RAGAS 0.4.x 在 `langchain-community >= 0.4` 下因导入已移除的 `vertexai` 模块而崩溃，需用 `MagicMock` 做 stub。自定义 LLM 注册要用 `llm_factory` 传入 `openai.OpenAI` client，不能走 `OpenAILike`——RAGAS 内部走的是 `langchain` 链路。

RAGAS 评估完还会输出逐题的诊断建议：Faithfulness 不足时提示强化 Prompt 模板禁止外部知识，Answer Relevancy 低时检查检索文档是否真的覆盖了问题域。这套「跑分 + 诊断」的闭环在 `ragas_evaluation.py` 最后 50 行全部落地。

**NDCG 比 MRR 更细粒度**。MRR 只看第一个相关文档排在哪（`1/rank`），NDCG 采用 TREC 标准公式 `DCG = sum((2^rel_i - 1) / log2(i+1))` 同时考虑位置对数衰减 + 相关度指数加权（relevance ∈ {0,1,2,3}）。同一个 query 里两个不同的检索排序 MRR 可能都是 1.0，但 NDCG 能通过高度相关(3)和边缘相关(2)的排位差异区分它们——这是粗粒度和细粒度指标的典型差异。

**小数据集陷阱**：8 docs + `top_k=3` → 每次检索返回 37.5% 语料库 → 所有指标接近满分（`NDCG=1.0`, `MRR=1.0`），完全没有区分度。生产环境 10 万+ chunks 下才有意义。代码里专门用 Dataset Size Trap 章节承认 Demo 局限，同时给出正确做法：离线用 NDCG@20 测排序 + RAGAS 测生成，在线用 Langfuse 做全量追踪。

## Part 3: Langfuse 全链路追踪 ✅

**RAGAS 是单元测试，Langfuse 是 APM。** Java 世界里你不会用单元测试替代 SkyWalking，同样，离线评估不能替代在线追踪。

四层模型：`Trace（一次查询）→ Span "retrieval"（检索细节+耗时）→ Generation "llm-gen"（token usage+latency）→ Score "faithfulness"（事后异步写入）`。

**实现亮点——优雅降级**：`_NoopSpan` 类在 Langfuse 未配置时接管所有 span 操作，Pipeline 正常跑但 trace 只打印到控制台。同一个代码在「本地开发」和「Docker 环境」下都能正常运行——类比 Spring Boot 的 `@ConditionalOnBean`。生产环境中评估分数不是每次查询都实时写入，而是采样（如 10%）或批量异步评估后回写到 Trace 上，避免评估 LLM 调用拖慢主链路延迟。

**离线 vs 在线分工**：离线（RAGAS/NDCG）定基线，发版前跑，回答「这个版本比上一个好还是差」；在线（Langfuse）做监控，持续追踪，回答「系统现在有没有退化」。最狠的一个场景：「Context Recall 从 0.85 掉到 0.6 → embedding 模型退化 → 没有 tracing 根本发现不了。」

## 笔记产出

- `notes/week-03/agent-evaluation.md` — RAGAS 四维 + NDCG/MRR + Langfuse 三者分工 + LLM-as-a-Judge 五大风险
- `notes/week-03/enterprise-rag-auth.md` — 三层权限模型 + 检索级 vs 生成级校验 + 与 Tool 级 RBAC 的区别

### 代码产出
- `projects/03-rag-system/acl_retrieval.py` — 权限感知检索（200 行）
- `projects/03-rag-system/ragas_evaluation.py` — RAGAS 四维评估 + Chunking 实验（369 行）
- `projects/03-rag-system/retrieval_eval.py` — NDCG/MRR 排序评估 + 交叉验证（257 行）
- `projects/03-rag-system/langfuse_trace.py` — Langfuse 全链路追踪（263 行）

## 核心收获

今天的主题是「怎么证明你的 RAG 系统不是玩具」。三者分工不同，缺一不可：

```
编译态                                    运行态
  ├── NDCG/MRR ── 检索排序质量               ├── Langfuse ── 全链路追踪 + 漂移告警
  └── RAGAS ──── 回答生成质量                └── Score ───── 质量漂移检测
```

这个分工跟 Java 后端「单元测试 + 集成测试 + APM 监控」是同一思路，只是评估对象从「确定性的代码逻辑」变成了「非确定性的 LLM 输出」。一旦建立这个类比，整个评估体系的心智模型就完整了。

## 关联提交

- `b8e6b4a` feat(rag): Day13 Part1+3 — 权限感知检索 + NDCG/MRR 排序评估
- `a272e90` feat(rag): RAGAS 四维评估体系
- `d0e2c25` feat(rag): Day13 Part4 — Langfuse 全链路追踪，优雅降级支持离线模式
- `3a9a87b` docs: Day13 Part1-3 全部完成
