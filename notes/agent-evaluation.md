# Agent 评估体系

> 核心认知：**Agent 输出非确定性来自 LLM 的生成特性 — 同一问题两次回答可能不同。评估体系就是把「主观感觉好不好」变成「可量化的数字」，让 Agent 像传统软件一样走 CI/CD。**

---

## 1. 为什么需要评估

| 维度 | 传统软件（Java 后端） | Agent（LLM 驱动） |
|------|----------------------|-------------------|
| 输出确定性 | 相同输入 → 相同输出 | 相同输入 → 不同输出（随机性） |
| 验证方式 | 断言：`assertEquals(expected, actual)` | 语义判断：回答「对」还是「错」 |
| 回归测试 | 单元测试 + 集成测试跑通即上线 | 反复抽样评估，确认分布没退化 |
| 故障模式 | 异常堆栈、错误码、超时 | 幻觉编造、遗漏关键信息、格式错乱 |

**不能用测 Spring Boot 的方式测 Agent。**

### 评估的三个层次

```
第一层：组件级（离线）— RAGAS / NDCG / MRR → 回答是否正确？检索是否覆盖？
第二层：链路级（在线）— Langfuse Trace → Token 消耗？延迟？哪个环节卡住？
第三层：用户体验（在线）— 反馈/打分 → 用户是否满意？任务完成率？
```

---

## 2. RAGAS 四维评估

> RAGAS（RAG Assessment）是目前最通用的 RAG 离线评估体系。核心思路：在 `ground_truth`（标准答案）之外，单独评估检索环节质量。

### 2.1 四维总览

| 维度 | 评估对象 | 核心问题 | 需要人工标注？ | 行业参考范围 |
|------|---------|---------|-------------|------------|
| **Faithfulness** | 生成 | 回答是否有据可查，有没有编造？ | 否（自动拆 statement 逐条验证） | 0.85-0.95 |
| **Answer Relevancy** | 生成 | 回答是否紧扣问题，有没有跑题？ | 否（反向生成问题比对相似度） | 0.80-0.90 |
| **Context Recall** | 检索 | 答案需要的信息，检索文档覆盖了吗？ | 是（需 standard_answer） | 0.70-0.85 |
| **Context Precision** | 检索 | 排在前面文档真的相关吗？ | 是（需 relevant 标记） | 0.80-0.90 |

> **本项目实测**（chunk_size=128 切分 / 不切分）：Faithfulness=0.50 / 0.67，Answer Relevancy=0.88，Context Recall=0.85，Context Precision=0.80。

### 2.2 Faithfulness（忠实度）

**公式**：`|能在文档中找到依据的 statement| / |回答中所有 statement|`

计算逻辑：拆回答为原子陈述 → 逐条去检索文档中验证 → 统计有依据的占比。

**关键认知**：Faithfulness 高 ≠ 回答好。如果检索文档本身就是错的，Agent 忠实复述错误信息，Faithfulness 仍然是 1.0。必须和 Answer Relevancy 联合使用。

**面试一句话**：「Faithfulness 衡量 Agent 有没有胡编乱造 — 相当于传统软件的『数据源校验』，只不过校验对象是 LLM 生成内容而非数据库返回值。」

### 2.3 Answer Relevancy（答案相关性）

**公式**：从回答反向生成 N 个问题 → 计算它们与原问题的 embedding 余弦相似度 → 取均值。

**与 Faithfulness 的联合诊断**：

| Faithfulness | Answer Relevancy | 诊断 |
|-------------|-----------------|------|
| 高 | 高 | ✅ 理想状态 |
| 高 | **低** | 说的都对但没回答问题 → 优化 Prompt |
| **低** | 高 | 紧扣问题但内容编造 → 换模型 / 优化检索 |
| 低 | 低 | 🔴 全面崩溃 → 查全链路 |

**面试一句话**：「Answer Relevancy 衡量 Agent 有没有跑题 — 类似 API 接口的后置校验，确认返回字段和请求意图匹配。」

### 2.4 Context Recall（上下文召回）

**公式**：`|标准答案中被检索文档覆盖的句子| / |标准答案所有句子|`

**Java 类比**：查全率（Recall）。搜索「Spring Boot 配置绑定」时，`@ConfigurationProperties` 和 `@Value` 的文档都检索出来才算满分。

### 2.5 Context Precision（上下文精确度）

**公式**：`CP@K = Σ(k=1..K) (precision@k × relevance_at_k) / total_relevant`，其中 `precision@k = (前k个中相关文档数) / k`。RAGAS 的 CP 衡量的是"相关文档是否集中排在前面"，而非简单的倒数加权。

**Java 类比**：查准率（Precision@K）。搜索「Spring 事务」时，排第一位是 `@Transactional` 文档而非 Spring Framework 概述。

---

## 3. NDCG / MRR 排序评估

> RAGAS 的检索维度关注「覆盖+精确」，但当应用场景是「返回排序列表」时，需要经典 IR 指标做更细粒度的衡量。

### 3.1 MRR（Mean Reciprocal Rank）

只看**第一个**相关文档的位置：`MRR = (1/|Q|) × Σ (1 / rank_i)`

| 第一个相关文档排位 | Reciprocal Rank |
|------------------|-----------------|
| 第 1 位 | 1.0 |
| 第 2 位 | 0.5 |
| 第 5 位 | 0.20 |
| 没找到 | 0 |

**适用场景**：用户只需要一个正确答案（FAQ、客服问答）。

### 3.2 NDCG（Normalized Discounted Cumulative Gain）

考虑**位置衰减 + 相关度分级**的排序指标，TREC 标准。

```
DCG@k = Σ (2^relevance_i - 1) / log₂(i + 1)      relevance_i ∈ {0,1,2,3}
NDCG@k = DCG@k / IDCG@k                           IDCG = 理想排序下的 DCG
```

| 概念 | 含义 | Java 类比 |
|------|------|----------|
| Gain | 每个文档相关度得分 | 单个结果的「价值」 |
| Discount | 位置越靠后权重越低 | 分页查询，第2页流量远小于第1页 |
| Normalized | 除以理想得分归一化到 [0,1] | 跨查询可比 |
| Cumulative | 累加前 k 个结果 | 分页 API 前 N 条整体质量 |

### 3.3 MRR vs NDCG vs RAGAS CP

| 维度 | MRR | NDCG | RAGAS Context Precision |
|------|-----|------|------------------------|
| 考察范围 | 只看第一个相关 | 看前 k 个 | 看前 k 个 |
| 相关度分级 | 二值 | 多级（0-3） | 二值 |
| 位置衰减 | 1/rank（线性） | 1/log₂(rank+1)（对数） | 1/rank（线性） |
| 标注成本 | 低 | 高（需 qrels） | **零**（自动计算） |
| 使用场景 | 快速 baseline | 上线前最终验证 | 开发迭代 |

**实践策略**：开发阶段用 RAGAS CP（快速迭代、零标注成本），上线前用 NDCG@10 做最终验证。

---

## 4. Langfuse 全链路追踪

> RAGAS 是「单元测试」，Langfuse 是「APM」— 在生产环境持续监控 Agent 运行质量。

### 4.1 四个核心概念

```
Trace（一次用户对话）
  ├── Span（LLM 调用）     → prompt tokens / latency / model name
  ├── Span（Tool 调用）    → tool name / params / execution time / result
  ├── Generation（生成）   → input / output / token usage
  └── Score（评分）        → 附着在 Trace/Span/Generation 上的评分元数据，source: "ragas"|"human"|"custom", value: 0.85
```

**Java APM 类比**：

| SkyWalking / Pinpoint | Langfuse |
|----------------------|----------|
| Trace（一次 HTTP 请求） | Trace（一次对话） |
| Span（一个 RPC 调用） | Span（一次 LLM 或 Tool 调用） |
| 慢查询分析 | Token 消耗 / 延迟分析 |
| 错误率监控 | Faithfulness 漂移检测 |
| 告警规则 | Score 阈值告警 |

### 4.2 接入示例

```python
from langfuse.decorators import observe, langfuse_context

@observe()
def generate_answer(query: str, context: list[str]) -> str:
    response = llm.chat(query, context)
    langfuse_context.score_current_trace(
        name="faithfulness",
        value=calculate_faithfulness(response, context),
    )
    return response
```

### 4.3 离线 vs 在线评估

| 维度 | 离线（RAGAS / NDCG） | 在线（Langfuse / Score） |
|------|---------------------|------------------------|
| 数据来源 | 构造的测试集 + 标注 | 真实用户流量 |
| 频率 | 发版前 / 定期批量 | 每次调用 / 抽样 |
| 目的 | 确定基线，对比版本 | 检测漂移，触发告警 |
| 典型发现 | 「新版 RAG recall 下降 5%」 | 「今天 faithfulness 从 0.9 掉到 0.7」 |

---

## 5. 三者分工

| 工具 | 管什么 | 怎么跑 | 核心产出 | 一句话定位 |
|------|-------|--------|---------|-----------|
| **RAGAS** | 生成质量（回答好不好） | 离线，发版前 | 四维度分数 + 诊断 | 回答好不好？ |
| **NDCG/MRR** | 检索排序（排序准不准） | 离线，发版前 | 归一化排序得分 | 排序准不准？ |
| **Langfuse** | 运维质量（系统稳不稳） | 在线，持续 | 延迟/Token/漂移告警 | 系统稳不稳？ |

```
编译态                                   运行态
  │                                        │
  ├── RAGAS ─── 回答质量                    ├── Langfuse ── 全链路追踪
  │                                        │
  └── NDCG/MRR ── 检索排序                  └── Score ───── 质量漂移告警
```

---

## 6. LLM-as-a-Judge 的风险

> RAGAS 的 Faithfulness / Answer Relevancy 都依赖 LLM 做判断，评估器本身可能编造。

### 6.1 五大风险

| 风险点 | 表现 | 缓解措施 |
|--------|------|---------|
| 评估器偏见 | 倾向给自家模型打高分 | 用不同模型交叉验证 |
| 评估器幻觉 | 错误判定 statement 有依据 | 多轮判断 + 人工抽样复核 |
| 温度敏感 | temperature > 0 时打分不稳定 | 评估器 temperature=0 |
| 位置偏见 | 倾向认为后面内容更重要 | 随机打乱 context 顺序 |
| 长文本退化 | 长文档时注意力分散漏判 | 切分后逐段验证 |

### 6.2 温度/一致性权衡

```
评估器 → temperature = 0（确定性，可复现）
Agent  → temperature = 0.3-0.7（保持创造性）
```

### 6.3 标注策略对比

| 方法 | 成本 | 一致性 | 适用环节 |
|------|------|--------|---------|
| LLM-as-a-Judge | 低（API 费） | 85-90% | 开发迭代，快速反馈 |
| 人工标注（qrels） | 高（人时） | 95%+ | 上线前最终验证 |
| 混合（LLM 初筛 + 人工复核） | 中 | 90-95% | **工业实践主流方案** |

---

## 7. 面试要点

### 7.1 一张图讲完评估体系

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ 离线质量  │    │ 离线排序  │    │ 在线监控  │
│  RAGAS   │    │ NDCG/MRR │    │ Langfuse │
└────┬─────┘    └────┬─────┘    └────┬─────┘
     ▼               ▼               ▼
 回答是不是编的   排序是不是对的   系统有没有退化
```

### 7.2 三个面试问题

**Q1：上线了一个 RAG Agent，怎么衡量质量？**

离线：构造 50-100 条测试问题 + 标准答案，RAGAS 四维评估拿 baseline，NDCG 验证排序。在线：Langfuse 持续监控 faithfulness 和 answer_relevancy，设 0.8 阈值告警。

**Q2：faithfulness 从 0.9 掉到 0.72，怎么排查？**

Langfuse Trace 定位具体请求 → 检查检索文档是否变质（数据源更新？embedding 模型换了？）→ 如果检索正常，可能是 LLM temperature 过高或 Prompt 被误改 → 回滚后重新评估确认。

**Q3：Context Precision 0.78、MRR 0.95 矛盾吗？**

不矛盾。MRR 高 = 第一个相关文档排得靠前（用户场景好）。CP 低 = 检索结果混入不少不相关文档（浪费 token、干扰生成）。需要优化 chunking 策略或加 reranker。

### 7.3 关键词速查

| 术语 | 一句话 |
|------|--------|
| RAGAS | RAG 系统四维离线评估体系 |
| Faithfulness | 回答是否有据可查（反幻觉） |
| Answer Relevancy | 回答是否紧扣问题（反跑题） |
| Context Recall | 检索是否覆盖了答案所需信息 |
| Context Precision | 检索排序是否合理 |
| NDCG | 考虑位置衰减+相关度分级的排序指标（TREC 标准） |
| MRR | 只看第一个相关文档排名的简化指标 |
| Langfuse | Agent 全链路追踪平台（开源 APM） |
| LLM-as-a-Judge | 用 LLM 评分替代人工标注 |
| qrels | Query Relevance Judgments，人工标注的查询-文档相关度 |
| Drift Detection | 检测模型输出质量是否随时间退化 |
