# Day 14 (2026.06.26) — 项目 B（上）：Enterprise RAG 框架搭建

**主题**：异构数据摄入管道的设计与实现，把 8 篇研报文档（2 租户）灌入 ChromaDB，搭建带权限隔离的查询引擎，设计引用溯源方案，外加 Langfuse 全链路追踪。

## Part 1：异构数据摄入管道 — 统一索引层

### 问题
企业里的数据不是整齐摆在那里的。一个典型的研报系统需要同时对接 PDF 文档（分析师研报、财报）、数据库记录（基本面数据、持仓快照）和 API 返回的 JSON（行情数据、制裁名单）等多种数据源。当前阶段用硬编码的 `Document(text=...)` 构建文档库，实际企业场景中需要对接 PDF 解析、DB 连接和 API 调用等异构数据源。

### 设计
用一个统一的 `Document` 抽象层收口所有数据源。LlamaIndex 的 `Document` 就像 Spring Data 里的 `Entity`——不管你底层是 MySQL、MongoDB 还是 Elasticsearch，到了 Repository 层都是同一个对象模型。

8 篇文档按两个维度分布：
- **租户**：acme (5) / globex (3) — 类比 SaaS 系统的多租户 schema
- **访问级别**：public (5) / confidential (3) — 其中 2 篇 confidential 是 manager-only

元数据结构（所有字段均为标量类型 str / bool，适应 ChromaDB 的 metadata filter 限制）：
```python
{
    "text": str,
    "metadata": {
        "tenant": str,        # 租户标识
        "access_level": str,  # public / confidential
        "role_intern": bool,
        "role_engineer": bool,
        "role_manager": bool,
    }
}
```

### Java 类比
这个摄入管道本质上就是一个 ETL Pipeline：
- **Extract**：从数据源抽取原始数据（当前阶段为硬编码文档，生产需对接 PDF / DB / API 连接器）
- **Transform**：统一封装为 `Document` + metadata（字段映射、清洗、标准化）
- **Load**：embedding 后写入 ChromaDB（类比写入 Elasticsearch 索引）

跟数据中台的 CDC（Change Data Capture）管道的核心差异在于：这里 Load 的不是原始数据，而是 embedding 向量——结构数据变成了 384 维的语义向量。

## Part 2：多租户隔离 + 文档级 ACL — 权限前置到检索层

### 核心设计决策
传统 Java 后端的权限校验是后置的：Controller 层 `@PreAuthorize` 验证权限 → Service 层执行业务逻辑。但 RAG 系统不能这么干。

**为什么**：如果等 LLM 生成完答案再去过滤敏感内容，敏感文档已经进了 prompt。LLM「看过」的内容不可能用正则表达式事后擦除——token 已经消耗了，信息已经泄露了，合规风险已经产生了。

**所以权限必须在检索阶段前置**：

```
User Query → Session Resolver → ACL Where Builder → ChromaDB → LLM → Citation
```

具体做法：mock session 先解析出 `{tenant, role}`，再构建 ChromaDB 的 where clause：

```python
{"$and": [{"tenant": "acme"}, {"role_manager": True}]}
```

这个 where clause 在向量检索时直接过滤掉无权文档——既安全（敏感文档不进 context window），又省 token（不浪费在无权限文档的 LLM Prompt Token 上）。

### 权限矩阵
| 角色 | public | confidential(非manager-only) | confidential(manager-only) | 跨租户 |
|------|--------|---------------------------|--------------------------|------|
| intern | 可读 | 不可读 | 不可读 | 不可见 |
| engineer | 可读 | 可读 | 不可读 | 不可见 |
| manager | 可读 | 可读 | 可读 | 不可见 |

### Java 类比
这就像 Shiro/Spring Security 的权限模型，但验证点在「检索」层而非「API」层。传统 RBAC 是在 Controller 门槛把关，这里是直接在数据库查询层面加 where 条件——相当于把 `@PreAuthorize("hasRole('manager')")` 翻译成了 SQL 的 `WHERE role_manager = true`。

## Part 3：引用溯源（设计目标）+ 全链路追踪 — 可审计的生成链路

### 引用溯源（设计目标）
当前代码中尚未实现结构化 citation 输出，但这是企业 RAG 框架的设计目标之一。理想状态下，每一条 LLM 生成的答案都应带完整的 citation 列表：

```json
{"index": 1, "source_type": "pdf_report", "doc_id": "RES_PDF_001",
 "tenant": "acme", "access_level": "public"}
```

这个设计对应金融合规的基本要求：每一条投资建议必须能追溯到原始研报。不只是「AI 说涨」，而是要能说「基于 2026 年 Q3 财报（RES_PDF_001），营收增长 18%，所以看涨」。

实现思路：引用用 `[source_type:doc_id]` 格式标注在 context 中，让 LLM 在回答时自然引用。这比生成完后再做正则匹配去拼引用要可靠得多——结构化信息在 prompt 组装阶段就嵌入了，LLM 只是做格式化输出。当前阶段需要补充 citation 的 prompt 模板和输出解析逻辑。

### Langfuse 全链路追踪
Langfuse 接入做了三个关键工程决策：

1. **Graceful Degradation**：Langfuse 不可用时自动降级为 `_NoopSpan` + console fallback，不影响核心检索功能。类比 Java 里的 circuit breaker 模式——依赖挂了不拖垮主流程。
2. **Lazy Auth Check**：`auth_check()` 推迟到首次实例化时执行，不在模块 import 阶段触发网络请求。避免启动时因网络问题直接崩溃。
3. **Trace 结构标准化**：每条查询一个 Trace，内含 retrieval span （延迟/命中数/来源分布）+ generation span （model + tokens）+ score （retrieved_count）。

### Java 类比
Langfuse 的 Span 模型跟 Spring Cloud Sleuth 的 Trace/Span 概念几乎是 1:1 映射。区别在于 Sleuth 追踪的是 HTTP/RPC 调用链，Langfuse 追踪的是 RAG Pipeline 的知识流转链——从 query embedding 到 LLM generation 的每一步。

## 核心认知：企业 RAG 的三个差异化能力

经过 Day 11-14 的完整学习链（IR 基础 → 三级管道 → 权限检索 → 框架搭建），企业 RAG ≠ Demo RAG 的差异已经清晰：

1. **异构数据管道**：Demo RAG 读一个 txt 文件就能跑；企业 RAG 要对接 PDF/DB/API 三种以上数据源，每种有自己的 Schema、时延、容错策略。当前阶段用硬编码文档模拟异构数据摄入，真实场景需对接 PDF 解析、DB 连接器和 API 调用。这考验的不是「能不能跑 RAG」，而是「能不能设计数据中台级别的 ETL」。

2. **权限前置到检索层**：不是架构偏好，是被成本和安全逼出来的工程约束。检索回来的文档已经进了 prompt，LLM「看过」的内容不可能事后过滤。正确做法是 ChromaDB where clause 预过滤——跟数据库的 Row-Level Security 思路一致。

3. **引用溯源闭环**：每一条 AI 生成的结论必须能追溯到原始文档 + 具体段落。这不是 nice-to-have，是金融/医疗/法律等强监管行业的基本合规要求。实现方式：结构化 citation 在 prompt 组装阶段嵌入，LLM 只是格式化输出，不依赖 LLM 的记忆去「回忆」来源。

这三个能力，Demo RAG 一个都不需要——这才是 Day 14 用 6 个文件、约 1300 行代码搭建框架的真正原因。

## 产出
- `acl_retrieval.py` — 8 文档 / 2 租户 / 3 角色 / 4 场景，ACL where clause 预过滤权限感知检索
- `first_rag.py` — 第一个 RAG 系统实现，含文档摄入与问答流程
- `embedding_explorer.py` — Embedding 向量探索与可视化
- `langfuse_trace.py` — Langfuse 全链路追踪 + NoopSpan 优雅降级
- `ragas_evaluation.py` — RAGAS 评估框架集成
- `retrieval_eval.py` — 检索质量双维评估（RAGAS + NDCG）
