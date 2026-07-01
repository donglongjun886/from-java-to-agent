# Smart Report Agent — Java 版 (Spring Boot + LangChain4j)

## 项目定位

**Python 版 `smart-report-agent/` 的 Java 对照实现**，用 Spring Boot + LangChain4j 实现同等核心链路：文档摄入 → 向量化 → 权限过滤检索 → LLM 生成 → 引用溯源。

这是 12 年 Java 工程师的系统转型学习项目，目标是**证明 Java 生态也能做 RAG**，面试时能讲出 Python vs Java 在 RAG 场景下的差异选型。

## 业务场景（和 Python 版一致）

企业研报分析系统，服务于金融机构的三个部门：

| 部门 | 职责 | 敏感数据 |
|------|------|----------|
| 研报组 (research) | 行业研究、财报分析、趋势研判 | 内部信用风险评估 |
| 交易组 (trading) | 实时行情、仓位管理、交易信号 | 持仓明细、量化信号 |
| 合规组 (compliance) | 监管政策、审计记录、制裁名单 | 内部调查审计报告 |

**权限模型**: 租户隔离 + 角色 ACL（intern / engineer / manager），权限在检索层做 filtering，不在 LLM 生成后校验。

## 项目结构

```
smart-report-agent-java/
├── pom.xml                              # Maven 构建（Spring Boot 3.3.5 + LangChain4j 1.16.3）
├── README.md                            # 本文档
├── src/main/resources/
│   ├── application.yml                  # DeepSeek + 向量库配置
│   └── data/                            # 模拟研报文档（6 篇 .txt）
│       ├── research-q3-report.txt       # 研报组-财报+半导体趋势
│       ├── research-credit-risk.txt     # 研报组-信用风险+基本面 (含 CONFIDENTIAL)
│       ├── trading-market-outlook.txt   # 交易组-市场展望+行情数据
│       ├── trading-positions.txt        # 交易组-持仓+交易信号 (含 CONFIDENTIAL)
│       ├── compliance-regulations.txt   # 合规组-法规+审计+制裁
│       └── compliance-investigation.txt # 合规组-内部调查 (CONFIDENTIAL)
└── src/main/java/com/example/smartreport/
    ├── SmartReportApplication.java      # Spring Boot 入口
    ├── config/
    │   ├── RagProperties.java           # @ConfigurationProperties（外置 OpenAI 配置）
    │   └── LangChain4jConfig.java       # ChatModel + EmbeddingModel + EmbeddingStore Bean
    ├── model/
    │   ├── IngestRequest.java           # 摄入请求 DTO
    │   ├── QueryRequest.java            # 查询请求 DTO（tenant + role 上下文）
    │   ├── QueryResponse.java           # 查询响应 DTO（answer + citations）
    │   └── StatsResponse.java           # 统计响应 DTO
    ├── service/
    │   ├── IngestService.java           # 文档摄入：读取 .txt → 向量化 → 存储
    │   └── QueryService.java            # 权限感知查询：filter → 检索 → LLM 生成
    └── controller/
        └── RagController.java           # REST API: POST /ingest, POST /query, GET /stats
```

## 核心链路（和 Python 版对照）

| 步骤 | Python 版 (smart-report-agent/) | Java 版 (本实现) |
|------|-------------------------------|-----------------|
| 数据摄入 | `ingest.py`: Document → HuggingFaceEmbedding → ChromaDB | `IngestService`: TextSegment → OpenAiEmbeddingModel → InMemoryEmbeddingStore |
| 权限过滤 | `build_acl_where()`: ChromaDB where clause `{"$and": [...]}` | `Filter.metadataKey().isEqualTo().and()`: LangChain4j Filter DSL |
| 向量检索 | `collection.query(where=..., n_results=5)` | `embeddingStore.search(EmbeddingSearchRequest.builder().filter().build())` |
| LLM 生成 | `Settings.llm.complete(prompt)` | `chatModel.generate(prompt)` |
| 引用溯源 | `[source_type:doc_id]` 标注 + citations 列表 | `QueryResponse.Citation` 列表 + source 标注 |

## 如何运行

### 前置条件

- JDK 17+
- Maven 3.8+
- 项目根目录 `.env` 已配置 `DEEPSEEK_API_KEY`

### 启动步骤

```bash
# 1. 进入 Java 项目目录
cd projects/smart-report-agent-java

# 2. 编译 + 启动
mvn spring-boot:run

# 3. 调用 API（另开终端）
# 摄入文档
curl -X POST http://localhost:8081/api/rag/ingest

# 权限感知查询（research 租户 manager 角色）
curl -X POST http://localhost:8081/api/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "What is the Q3 revenue and semiconductor outlook?", "tenant": "research", "role": "manager", "topK": 5}'

# 同样的查询，intern 角色（看不到 confidential 文档）
curl -X POST http://localhost:8081/api/rag/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "What is the Q3 revenue and semiconductor outlook?", "tenant": "research", "role": "intern", "topK": 5}'

# 查看索引统计
curl http://localhost:8081/api/rag/stats
```

## Python vs Java — RAG 场景对照表

| 维度 | Python (LlamaIndex + ChromaDB) | Java (LangChain4j + Spring Boot) | 面试/选型要点 |
|------|-------------------------------|----------------------------------|------------|
| **框架范式** | 函数式调用，全局 Settings 对象 | Spring IoC 依赖注入 + Bean 生命周期 | Python 灵活但隐式依赖多；Java 依赖关系显式可追踪 |
| **依赖管理** | pip install + 手动管理版本 | Maven 统一管理 + BOM 版本仲裁 | Maven 传递依赖冲突解决更成熟 |
| **配置方式** | os.getenv + dataclass | @ConfigurationProperties + application.yml | Java 类型安全的配置绑定，IDE 有自动补全 |
| **类型安全** | 鸭子类型，运行时发现错误 | 编译期类型检查，IDE 重构安全 | 大项目重构 Java 更可靠；Python 原型迭代更快 |
| **Embedding 模型** | HuggingFaceEmbedding (本地 all-MiniLM-L6-v2) | OpenAiEmbeddingModel (API 调用) | Python 本地模型启动慢但离线可用；Java 依赖外部 API 更简洁 |
| **向量存储** | ChromaDB EphemeralClient (Python 原生客户端) | InMemoryEmbeddingStore (LangChain4j 内置) | Python chromadb 库生态成熟；Java ChromaDB 客户端差距大 |
| **Metadata 过滤** | ChromaDB where clause (dict DSL) | LangChain4j Filter DSL (编译期校验) | Python DSL 灵活但无类型保障；Java 类型安全但表达力略弱 |
| **AI 服务抽象** | LlamaIndex QueryEngine + Retriever Pipeline | AiServices（未用到，但可扩展） | LangChain4j AiServices 类似 Spring Data JPA 的声明式代理 |
| **冷启动** | 首次加载 HuggingFace 模型 ~5-10s | JVM 启动 ~2-3s（不含模型下载） | Java JVM 预热后有性能优势；Python 冷启动加载模型慢 |
| **生产部署** | FastAPI + uvicorn (轻量) | Spring Boot + 内嵌 Tomcat | Java 运维工具链更成熟（Actuator、Prometheus、Micrometer） |
| **社区生态** | RAG 领域 Python 绝对领先（LangChain/LlamaIndex/ChromaDB 都原生 Python） | LangChain4j 追赶中，1.16 版已基本覆盖核心能力 | Java 适合后端团队已有 Spring 设施的场景 |

## 当前限制和 TODO

### 已知限制

1. **Embedding 模型**: 当前用 `OpenAiEmbeddingModel` 指向 DeepSeek，但 DeepSeek API 可能不支持 `/v1/embeddings` 端点。若报 404，需切换到：
   - DashScope 兼容模式 (`baseUrl=https://dashscope.aliyuncs.com/compatible-mode`, `modelName=text-embedding-v2`)
   - 或用 `langchain4j-embeddings-all-minilm-l6-v2` 做本地 embedding（需 ONNX Runtime）

2. **InMemoryEmbeddingStore 限制**:
   - 数据不持久化（重启丢失），对应 Python 版 `EphemeralClient()`
   - 没有内置 `count()` / 统计 API，生产环境应切换到 PGVector

3. **文档摄入简化**:
   - 文件名编码 metadata，不如 Python 版的 `DocDef` dataclass 灵活
   - 没有 PDF/DB/API 多源异构摄入（Python 版也只模拟了同构 text）

4. **没有评估体系**: Python 版有 RAGAS + NDCG/MRR 双维评估，Java 版暂无（可引入 `langchain4j-evaluation` 或手动实现）

5. **没有追踪集成**: Python 版有 Langfuse tracing，Java 版暂不包含（LangChain4j 可通过 Micrometer + OpenTelemetry 实现）

### TODO（按优先级）

- [ ] 修复 Embedding 端点兼容性（确认 DeepSeek 是否支持，或切换到 DashScope）
- [ ] 添加 PGVector 持久化方案（替换 InMemoryEmbeddingStore）
- [ ] 实现 `IngestService.ingestAll()` 的幂等性（避免重复摄入）
- [ ] 添加 Spring Actuator + Micrometer 监控指标
- [ ] 用 LangChain4j AiServices 重构 `QueryService`（声明式 AI Agent，展示 Java 优势）
- [ ] 补充 RAGAS 评估体系（对标 Python 版 `evaluate.py`）

## 面试要点

**一句话**: "我们用 LangChain4j 的 Filter DSL 在检索层做租户隔离 + 角色 ACL——权限过滤发生在 vector search 阶段，敏感文档不进入 context window，既防 prompt 注入泄露又省 token。"

1. **权限在检索层** — `Filter.metadataKey("tenant").isEqualTo(x)` 在向量检索前过滤，不在 LLM 生成后校验
2. **类型安全的 Filter DSL** — 编译期检查字段名，比 Python dict 更可靠
3. **Spring IoC 优势** — EmbeddingModel / ChatModel / EmbeddingStore 通过依赖注入管理，生产环境切换只需改 Bean 配置
4. **可审计引用** — 每个回答带 Citation 列表（source_type + doc_id + tenant + access_level）
