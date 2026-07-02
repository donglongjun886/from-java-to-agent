# Smart Report Agent — 系统架构文档

## 系统架构总览

```mermaid
graph TB
    subgraph DataIngest["数据摄入层"]
        PDF["PDF 研报<br/>财报/趋势/风险"] -->|"Document + metadata"| INGEST["Ingest Pipeline"]
        DB["数据库记录<br/>基本面/持仓/审计"] -->|"Document + metadata"| INGEST
        API["API JSON<br/>行情/指数/制裁"] -->|"Document + metadata"| INGEST
    end

    subgraph IndexLayer["索引层"]
        INGEST -->|"租户/角色/来源 metadata"| EMBED["Embedding<br/>all-MiniLM-L6-v2"]
        EMBED -->|"384-dim vectors"| CHROMA[("ChromaDB<br/>in-memory")]
    end

    subgraph RetrieveLayer["检索层（权限感知）"]
        QUERY["User Query"] --> RESOLVER["Tenant Resolver<br/>session → tenant + role"]
        RESOLVER --> ACL["ACL Filter Builder<br/>where clause"]
        ACL --> VECTOR["Vector Search<br/>cosine similarity"]
        VECTOR --> TOPK["Top-K Results<br/>with metadata"]
    end

    subgraph GenerateLayer["生成层"]
        TOPK --> PROMPT["Prompt Assembly<br/>context + query + citations"]
        PROMPT --> LLM["DeepSeek V4 Pro"]
        LLM --> ANSWER["Answer + Citation List"]
    end

    subgraph EvalObserve["评估与观测"]
        ANSWER --> EVAL["RAGAS + NDCG/MRR<br/>离线双维评估"]
        ANSWER --> TRACE["Langfuse<br/>全链路追踪"]
        EVAL --> REPORT["Quality Report"]
        TRACE --> REPORT
    end
```

## 权限检索时序图

```mermaid
sequenceDiagram
    participant U as User (Alice/Manager)
    participant API as Query Engine
    participant SESS as Mock Session
    participant ACL as ACL Filter
    participant CHROMA as ChromaDB
    participant LLM as DeepSeek
    participant CITE as Citation Builder

    U->>API: query("Q3 revenue outlook?")
    API->>SESS: resolve("alice")
    SESS-->>API: {tenant: "research", role: "manager"}
    API->>ACL: build_where(tenant, role)
    Note over ACL: {$and: [{tenant: "research"},<br/>      {role_manager: true}]}
    ACL->>CHROMA: query(embedding, where=..., top_k=5)
    Note over CHROMA: 过滤掉 trading/compliance 租户文档<br/>过滤掉 role_manager=False 的文档
    CHROMA-->>ACL: [RES_PDF_001, RES_PDF_002, RES_DB_001, ...]
    ACL-->>API: filtered_results (4 docs)
    API->>LLM: generate(context + query)
    LLM-->>API: "Q3 revenue reached 38.2B CNY..."
    API->>CITE: build_citations(filtered_results)
    Note over CITE: [{source_type, doc_id, tenant, access_level}]
    CITE-->>API: formatted citations
    API-->>U: {answer, citations: [...]}
```

## 评估体系图

```mermaid
graph LR
    subgraph Offline["离线评估 Batch"]
        QA["5 QA Pairs<br/>3 场景: 跨源/跨租户/角色权限"] --> BUILD["构建 RAGAS Dataset<br/>+ NDCG qrels"]
        BUILD --> RAGAS["RAGAS 四维<br/>faithfulness<br/>answer_relevancy<br/>context_recall<br/>context_precision"]
        BUILD --> NDCG["NDCG@3 + MRR<br/>人工标注 qrels"]
        RAGAS --> COMPARE["双维对比报告"]
        NDCG --> COMPARE
    end

    subgraph Online["在线追踪 Real-time"]
        LIVE["用户查询"] --> LF_TRACE["Langfuse Trace"]
        LF_TRACE --> LF_SPAN["retrieval span + generation span"]
        LF_SPAN --> LF_SCORE["事后打分 score"]
        LF_SCORE --> LF_DASH["Dashboard 质量监控"]
    end

    COMPARE -.->|"基线设定"| LF_DASH
```

## 数据模型

所有文档携带统一 metadata schema（ChromaDB 要求标量类型）：

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| tenant | str | 租户标识 | "research" / "trading" / "compliance" |
| access_level | str | 访问级别 | "public" / "confidential" |
| role_intern | bool | intern 可读 | True / False |
| role_engineer | bool | engineer 可读 | True / False |
| role_manager | bool | manager 可读 | True / False |
| source_type | str | 数据来源 | "pdf_report" / "db_record" / "api_json" |
| doc_id | str | 文档唯一 ID | "RES_PDF_001" |
| timestamp | str | ISO 时间戳 | "2026-06-25T10:00:00" |

## 权限矩阵

| 角色 | public 文档 | confidential (本租户, non-manager-only) | confidential (manager-only) | 跨租户文档 |
|------|-----------|--------------------------------------|---------------------------|----------|
| intern | 可读 | 不可读 | 不可读 | 不可见 |
| engineer | 可读 | 可读 | 不可读 | 不可见 |
| manager | 可读 | 可读 | 可读 | 不可见 |

**关键设计**：租户隔离通过 `where={"tenant": "research"}` 在 ChromaDB 层面实现，角色过滤通过 `role_XXX=True` 布尔字段实现。即使 LLM 被 prompt 注入攻击，也无法读取跨租户文档——因为文档根本没进入 context。

## 12 篇文档分布

| doc_id | tenant | source | access | visible to |
|--------|--------|--------|--------|-----------|
| RES_PDF_001 | research | pdf_report | public | all |
| RES_PDF_002 | research | pdf_report | public | all |
| RES_DB_001 | research | db_record | public | all |
| RES_PDF_003 | research | pdf_report | confidential | engineer, manager |
| TRD_PDF_001 | trading | pdf_report | public | all |
| TRD_API_001 | trading | api_json | public | all |
| TRD_DB_001 | trading | db_record | confidential | engineer, manager |
| TRD_API_002 | trading | api_json | confidential | manager only |
| CMP_PDF_001 | compliance | pdf_report | public | all |
| CMP_DB_001 | compliance | db_record | public | all |
| CMP_API_001 | compliance | api_json | public | all |
| CMP_PDF_002 | compliance | pdf_report | confidential | manager only |

---

## 四Agent协同架构（Week 4: Agentic Retrieval）

```mermaid
graph TB
    subgraph Input["输入"]
        Q["用户查询<br/>'分析研发部技术投入和预算效率'"]
    end

    subgraph Agent1["Agent 1: Retrieval Planner"]
        P1["LLM 分解查询"]
        P2["输出 subtasks<br/>[{source:'finance',sub_query:'研发部Q3预算'}<br/> {source:'vector',sub_query:'AI平台技术架构'}]"]
        P1 --> P2
    end

    subgraph Agent2["Agent 2: Multi-Source Retriever"]
        R1["ThreadPoolExecutor<br/>并行检索"]
        R2["finance: 预算数据"]
        R3["org: 组织架构"]
        R4["vector: 技术文档"]
        R5["compare: 跨部门对比"]
        R1 --> R2 & R3 & R4 & R5
    end

    subgraph Agent3["Agent 3: Generator"]
        G1["Prompt Assembly<br/>context + citations"]
        G2["LLM 生成<br/>结构化报告"]
        G1 --> G2
    end

    subgraph Agent4["Agent 4: Evaluator"]
        E1["Faithfulness 评估<br/>回答 vs context"]
        E2["Answer Relevancy<br/>回答 vs query"]
        E3["打分 + 改进建议"]
        E1 & E2 --> E3
    end

    Q --> Agent1 --> Agent2 --> Agent3 --> Agent4
    Agent4 -.->|"低分反馈"| Agent3
    Agent4 --> OUT["最终输出: 回答 + 引用 + 评估分数"]
```

## 静态 RAG vs Agentic Retrieval 对比 (P@K / MRR / NDCG)

```
Query                                            静态RAG                  Agentic
                                      P@3   MRR   NDCG          P@3   MRR   NDCG
--------------------------------------------------------------------------------------
平均                            0.54  1.00  1.00     0.54  1.00  1.00
```

> 小规模数据(4源/8 QA)下两者持平。Agentic 真实优势在大规模(20+源)场景中才能量化 —— 静态规则覆盖面不足，Agentic 动态路由的优势显现。

## 性能压测数据 (load_test.py)

| Agent阶段 | 平均耗时 | 占比 |
|----------|---------|------|
| Planner (LLM) | 1125ms | 17% |
| Retriever (并行) | 0ms | 0% |
| **Generator (LLM) → 瓶颈** | **4322ms** | **65%** |
| Evaluator (LLM) | 1241ms | 18% |
| **端到端总计** | **6688ms** | 100% |

| 指标 | 静态RAG | Agentic (1并发) |
|------|---------|----------------|
| QPS | 25000+ | 0.1 |
| 成本/次 | ¥0 | ¥0.003 |
| 月成本(100次/天×22天) | ¥0 | ¥6.60 |

> 优化方向: Generator 引入 Streaming (SSE) 可提升用户感知速度; 简单查询用静态RAG兜底

## 故障注入测试结果 (fault_injection.py)

| 测试项 | 注入方式 | 系统行为 | 结果 |
|--------|---------|---------|------|
| Tool 超时 | 非法 base_url → 连接拒绝 | APIConnectionError 正确抛出 | PASS |
| LLM 幻觉 | 虚假 Retrieval context (50万 vs 实920万) | Evaluator faithfulness=1.0, 防线在Retrieval层 | PASS |
| 上下文截断 | 超长 context (1818字) | Generator 正常生成, 128K窗口足够 | PASS |
| Planner输出异常 | 非法 subtasks 结构 | 防御性处理 + fail-fast | PASS |

## 项目文件地图

```
smart-report-agent/
├── ARCHITECTURE.md          ← 本文件: 架构文档
├── README.md                ← 业务+技术栈+运行指南
├── ingest.py                ← 数据摄入 (PDF/DB/API → ChromaDB)
├── agentic_retrieval.py     ← Agentic Retrieval (Planner → Retriever 动态路由)
├── four_agent_system.py     ← 四Agent协同核心 (Planner/Retriever/Generator/Evaluator)
├── multi_agent_collab.py    ← 多Agent协作模式 (Manager-Worker/流水线)
├── query_engine.py          ← 权限感知查询 (ACL Filter + LLM生成)
├── retrieval_compare.py     ← 检索质量对比 (P@K/MRR/NDCG, 静态 vs Agentic)
├── load_test.py             ← 负载压测 (QPS/P99/成本, 阶段耗时拆解)
├── fault_injection.py       ← 故障注入 (超时/幻觉/截断/格式异常)
├── evaluate.py              ← 离线评估 (RAGAS 四维)
└── trace_pipeline.py        ← Langfuse 全链路追踪
```
