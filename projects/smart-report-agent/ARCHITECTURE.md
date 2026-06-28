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
