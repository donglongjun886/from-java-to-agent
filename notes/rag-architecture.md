# Enterprise RAG 架构笔记

> 面向有多年后端经验的 Java 工程师。目标：能画出完整架构图，能讲清楚每层设计决策，面试对答如流。

---

## 1. RAG 三级管道

```
INDEXING  ──▶  RETRIEVAL  ──▶  GENERATION
(索引构建)     (查询检索)     (答案生成)
```

> 注：文档摄入（Ingestion，含加载/解析/切分）并入 Indexing 阶段，与业界主流三级管道表述一致。

| 阶段 | 做什么 | Java 类比 | 关键组件 |
|------|--------|-----------|----------|
| **Indexing** | 文档加载/解析（PDF/Markdown/DB）→ 切分成 chunk → embedding 向量 → 存入向量库 | ETL Extract+Transform + 写入 Elasticsearch 索引 | LlamaParse, UnstructuredIO, Embedding Model (all-MiniLM-L6-v2 等), ChromaDB/PGVector/Milvus |
| **Retrieval** | 用户 query → embedding → 向量检索 top-k | ES 的查询阶段 (`match` + `knn`) | 向量相似度 (cosine), BM25 关键词, Reranker |
| **Generation** | 拼接 prompt = system + context + query → LLM 生成 | Service 层调用下游 API 并组装响应 | Prompt Template, LLM (DeepSeek/GPT/Claude) |

**核心公式**: `answer = LLM(prompt_template + retrieved_chunks + user_query)`

---

## 2. 文档切分策略

### 2.1 核心参数

| 参数 | 含义 | 典型值 |
|------|------|--------|
| `chunk_size` | 每个分块的最大 token 数 | 256-1024 |
| `chunk_overlap` | 相邻分块的重叠 token 数 | chunk_size 的 10%-20% |

overlap 的意义：避免关键信息刚好落在两个 chunk 的边界上被割裂。类似数据库页分裂时保留溢出页的逻辑。

### 2.2 短文档 vs 长文档策略

| 场景 | 文档特征 | 切分策略 | 原因 |
|------|----------|----------|------|
| **短文档** (FAQ/API 文档) | 每篇 <200 tokens | **不切分**，整篇作一个 chunk | 自带完整语义，再切反而丢失上下文 |
| **中等文档** (技术博客) | 500-2000 tokens | chunk_size=512, overlap=64 | 保持段落完整性 |
| **长文档** (合同/论文) | 5000+ tokens | chunk_size=1024, overlap=128 + 层级切分 | 按章节/标题树切分，保留结构信息 |
| **代码仓库** | 按文件/函数边界 | AST 感知切分 (tree-sitter) | 不能把函数拦腰截断 |

### 2.3 我们的 3 轮 Chunking 实验结果（2026.06.26）

数据集：6 篇技术文档（~140 tokens/篇），对比实验在 Q1（跨文档综合题）上完成，Q2-Q5 为单文档查询不受切分影响。评估指标：RAGAS Faithfulness

| 实验 | chunk_size | 结果 (节点数) | Q1 Faithfulness | 诊断 |
|------|-----------|-------------|-----------------|------|
| 第1轮 | 128 | 6 docs → 11 nodes | **0.50** (↓) | 过度切分，碎片化，单个 chunk 缺乏完整语义 |
| 第2轮 | 256 | 6 docs → 6 nodes | **N/A** (max_tokens exceeded) | N/A：prompt 拼接后总 token 数超过模型上下文窗口，非 chunk 质量问题 |
| 第3轮 | 不切分 | 6 docs → 6 nodes | **0.67** (↑) | 最佳。140-token 文档本身已是合适粒度 |

**结论**：chunk_size 不是越小越好，也不是越大越好。关键是「语义完整性」——每个 chunk 必须能独立回答问题。当文档本身已接近最优 chunk 大小时，不切分就是最好的切分。（注：此结论适用于当前 6 文档短文本数据集。生产环境文档长度分布不均时，需基于自身数据重新评估切分策略。详见 7.3 节数据集规模陷阱讨论。）

**面试讲法**：「我们的 3 轮实验验证了一个直觉：chunk_size 的最优解取决于文档源的粒度分布。短文档不切分，长文档按段落结构切。优化方向不是调 chunk 参数本身，而是引入 reranker + hybrid search 做检索侧补偿。」

---

## 3. 混合检索：BM25 + 稠密向量 + Reranker 三级管道

```
Query → BM25关键词(精确匹配) ──▶ 候选集A ──▶ RRF融合 ──▶ Reranker精排 ──▶ Top-K → LLM
      → 稠密向量  (语义近似)  ──▶ 候选集B ──▶  (RRF)      (Cross-Encoder)
```

| 检索级 | 技术 | 解决什么问题 | 局限 |
|--------|------|-------------|------|
| **BM25 关键词** | TF-IDF 稀疏向量 + 倒排索引 | 精确匹配：数字、API 名、错误码、专有名词。向量检索找不到 `NullPointerException` 的变体写法 | 不会同义匹配，查「连接池」找不到「HikariCP」 |
| **稠密向量** | Embedding → cosine 相似度 | 语义近似：同义改写、跨语言、概念匹配。「线程池调优」能找到「HikariCP pool sizing」 | 对专有名词/数字不敏感，容易召回「相关但不精确」的内容 |
| **Reranker** | Cross-Encoder (Cohere Rerank / bge-reranker) | 精排：对融合后的候选集做 pair-wise 相关度打分。纠正第一阶段粗排的排序错误 | 计算量大，不能对全库做，只能对 top-N 候选集做 |

**融合算法 RRF**（Reciprocal Rank Fusion）：

```
RRF_score(d) = Σ 1 / (k + rank_i(d))
```

令 k=60，文档在 BM25 排第1、向量检索排第3 → `1/(60+1) + 1/(60+3) = 0.0164 + 0.0159 = 0.0323`。简单、无需调权、鲁棒性强，Elasticsearch 8.x 内置支持。

**Java 类比**：BM25 ≈ 数据库 B+Tree 索引（精确查找），稠密向量 ≈ 全文索引（模糊匹配），Reranker ≈ 应用层二次排序（`ORDER BY` 之后再用 Java `Comparator` 精排）。

---

## 4. 知识图谱认知（GraphRAG 架构级别）

### 4.1 图 vs 向量：什么时候用图

| 维度 | Vector RAG | GraphRAG |
|------|-----------|----------|
| **处理的问题** | 「这个概念是什么？」 | 「A 和 B 有什么关系？」「这件事的上下游是什么？」 |
| **数据形态** | 非结构化文本 | 实体 + 关系三元组 (subject, predicate, object) |
| **检索方式** | 语义相似度 | 图遍历 (1-hop, 2-hop, 最短路径) |
| **典型场景** | 客服 FAQ、技术文档问答 | 供应链溯源、反洗钱、知识推理 |
| **Java 类比** | Elasticsearch full-text search | Neo4j Cypher 图查询 / 关系型数据库 JOIN |

### 4.2 GraphRAG 构建流程

```
构建: 原始文档 → 实体抽取(LLM/NER) → 关系构建 → 知识图谱(Neo4j)
查询: 用户Query → 实体识别 → 图遍历(Cypher) → 子图上下文 → LLM生成
```

| 阶段 | 做什么 | 工具 |
|------|--------|------|
| 实体抽取 | 从文本中识别 Person/Org/Product 等实体 | LLM Few-shot prompt / spaCy NER |
| 关系构建 | 判断实体之间的关系类型 (持股/供应/依赖) | LLM + 关系 schema 约束 |
| 图存储 | 持久化三元组 + 图索引 | Neo4j, ArangoDB, Amazon Neptune |
| 图检索 | query → 实体链接 → 1-hop/2-hop 邻居遍历 | Cypher / Gremlin / SPARQL |

### 4.3 图 + 向量的协同

GraphRAG 不是替代 Vector RAG，而是互补：

- **图检索**出「HikariCP 依赖哪些 Spring Boot auto-configuration 条件注解」的关系链
- **向量检索**出「HikariCP 连接池怎么配置」的原文段落
- LLM 将两者拼接成完整答案

生产上通常是 **混合架构**：「图检索做结构化知识导航，向量检索做非结构化证据补充」。

---

## 5. 结构化 + 非结构化混合查询

```
用户Query: "上个月销售额最高的5个产品？"
  ├── Text-to-SQL ──▶ 结构化数据 (MySQL/PG) ──┐
  └── 向量检索   ──▶ 非结构化数据 (Vector DB) ─┤
                                              ▼
                                    结果融合 (LLM拼装回答)
```

| 环节 | 技术方案 | Java 类比 | 关键点 |
|------|----------|-----------|--------|
| **Text-to-SQL** | LLM 根据表 schema + 问题生成 SQL | MyBatis XML 的 SQL 模板，但 SQL 由 LLM 动态生成 | 需要提供 table DDL + sample rows 作为 prompt；必须做 SQL 安全校验（禁 DROP/DELETE） |
| **向量检索** | 同上文混合检索管道 | Spring Data Elasticsearch `@Query` | 产品名称需要做实体对齐（alias 映射） |
| **结果融合** | LLM 同时拿到 SQL 结果 + 文档片段，生成自然语言 | 微服务编排层的聚合 | prompt 模板需要明确：「数值来自数据库」「描述来自文档」 |

**多跳查询示例**：
> Q: 「对比 HikariCP 和 Druid 的线程模型差异」

1. 向量检索 → 找到两篇文档各自的线程模型描述
2. Text-to-SQL（若有 benchmark 表）→ 查出两者的 P99 延迟数据
3. LLM 融合 → 生成对比分析

---

## 6. LlamaIndex 在架构中的定位

| LlamaIndex 概念 | Java 类比 | 说明 |
|-----------------|-----------|------|
| `Document` | POJO / Entity | 统一文档数据模型 |
| `Node` (chunk) | DTO (数据传输对象) | 切分后的最小检索单元 |
| `VectorStoreIndex` | Spring Data Repository | 抽象索引构建 + 查询接口 |
| `StorageContext` | DataSource / ConnectionFactory | 管理向量库连接 |
| `QueryEngine` | Service 层的 `findByXxx()` | 封装检索 + 生成逻辑 |
| `IngestionPipeline` | Spring Batch Job | 文档摄入 + 转换的批处理管道 |
| `Settings` | `@Configuration` / application.yml | 全局配置 (LLM/Embedding/Chunking) |

**一句话定位**：**LlamaIndex ≈ 面向 LLM 应用的 Spring Data**。它提供数据层统一抽象，让你在不同向量库 (ChromaDB/PGVector/Milvus) 和 LLM (DeepSeek/GPT/Claude) 之间切换而不改上层代码。

**框架选型对比**：

| 维度 | LlamaIndex | LangChain | 自己手写 |
|------|-----------|-----------|----------|
| 数据摄入 | 一流（IngestionPipeline, LlamaParse） | 中等（Document Loaders 丰富但管道抽象弱） | 维护成本高 |
| 索引构建 | 一流（内置多种 index 类型） | 需手动拼装 | 灵活但需重复造轮子 |
| 检索评估 | 集成 RAGAS 等评估框架 | 同样支持 | 需自己写 |
| 学习曲线 | 中等（封装度高，概念多） | 较高（抽象层次多） | 低（但功能不完整） |
| 适合场景 | **RAG 为核心的项目** | 复杂 Agent 编排 | 简单原型/Demo |

---

## 7. 面试要点

### 7.1 完整架构图（必须能徒手画出）

```
┌──────────────────────────────────────────────────────┐
│                    用户 Query                          │
└──────────────────────┬───────────────────────────────┘
                       │
     ┌─────────────────┼─────────────────┐
     ▼                 ▼                  ▼
┌─────────┐    ┌─────────────┐    ┌──────────────┐
│Text2SQL │    │  BM25 关键词 │    │  稠密向量检索  │
│(结构化)  │    │  (精确匹配)  │    │  (语义近似)   │
└────┬─────┘    └──────┬──────┘    └──────┬───────┘
     │                 │                  │
     │          ┌──────▼──────┐           │
     │          │   RRF 融合   │◀──────────┘
     │          └──────┬──────┘
     │                 ▼
     │          ┌────────────┐
     │          │  Reranker   │  ← Cross-Encoder 精排
     │          │  精排 Top-K │
     │          └──────┬─────┘
     │                 │
     └─────────┬───────┘
               ▼
     ┌──────────────────┐
     │  Prompt 模板拼接   │
     │  system + context │
     │  + user_query     │
     └────────┬─────────┘
              ▼
     ┌──────────────────┐
     │  LLM 生成答案      │
     └──────────────────┘
```

### 7.2 每层设计决策（必须能讲清楚）

| 面试问题 | 回答要点 |
|----------|----------|
| 「为什么不用纯向量检索？」 | BM25 对专有名词/数字/错误码的召回率远高于向量检索，两者互补 |
| 「chunk_size 设多大？」 | 取决于文档粒度。我们的实验：短文档不切分最好；长文档按段落 + overlap 切。没有万能值，要基于数据集做评估 |
| 「Reranker 为什么不做全量？」 | Cross-Encoder 需要对 query-doc pair 做完整前向计算，全库做太贵。只能对粗排 Top-N (N≈50-100) 做精排 |
| 「怎么评估检索质量？」 | 双轨验证：离线用 NDCG@20 + MRR（人工 qrels，白盒可复现）；在线用 RAGAS Faithfulness（LLM 判断，可规模化）+ Langfuse 全量追踪 |
| 「什么时候上 GraphRAG？」 | 当领域知识以「关系」为核心时（供应链/金融风控/法律），图比向量更能表达多跳推理 |
| 「LlamaIndex vs LangChain 怎么选？」 | RAG 为主的项目选 LlamaIndex（数据层抽象强）；复杂 Agent 编排选 LangChain/LangGraph。企业项目两者可以混用 |

### 7.3 面试坑点预警

| 坑 | 面试官追问 | 你的回应 |
|----|----------|---------|
| 小数据集所有指标满分 | 「NDCG=1.0 是不是说明检索器很好？」 | 不是，6 个 doc 检索 top-3 覆盖了 50% 语料库，高命中是必然的。生产环境 10 万+ chunks 检索 top-20 才见真章 |
| 只用 RAGAS 评估 | 「为什么不用传统的 IR 评估？」 | 我做了交叉验证：NDCG/MRR（传统 IR 排序指标，白盒）+ RAGAS（LLM 生成评估，黑盒），两者结果互相校验 |
| 没考虑 chunk overlap | 「两个 chunk 之间信息断了怎么办？」 | 设置 overlap 保证关键句跨 chunk 可检索；另外引入 parent-document retriever（检小子块，返回父文档全文） |
| 用 ChromaDB 做生产 | 「ChromaDB 能上生产吗？」 | 当前是 demo。生产换 PGVector（团队已有 PostgreSQL 运维经验，零额外运维成本）或 Milvus（十亿级向量） |

### 7.4 关联阅读（同仓库）

- `projects/03-rag-system/first_rag.py` — 首个 RAG Pipeline 实现（LlamaIndex + ChromaDB）
- `projects/03-rag-system/ragas_evaluation.py` — RAGAS 四维评估 + 3 轮 chunking 实验记录
- `projects/03-rag-system/retrieval_eval.py` — NDCG/MRR 排序质量评估 + 与 RAGAS 的交叉验证
- `projects/03-rag-system/embedding_explorer.py` — Embedding 相似度直觉验证（Java ↔ AI 领域分离度）
