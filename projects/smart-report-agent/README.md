# Smart Report Agent — 企业级 RAG 系统

## 业务场景

**企业研报分析系统**，服务于金融机构的三个部门：

| 部门 | 职责 | 敏感数据 |
|------|------|----------|
| 研报组 (research) | 行业研究、财报分析、趋势研判 | 内部信用风险评估 |
| 交易组 (trading) | 实时行情、仓位管理、交易信号 | 持仓明细、量化信号 |
| 合规组 (compliance) | 监管政策、审计记录、制裁名单 | 内部调查审计报告 |

**核心挑战**：三个部门共享检索基础设施，但数据必须严格隔离。研报组分析师不能看到交易组的机密仓位数据，合规组的内部审计报告只能 manager 级别访问。这就是 Zoom Enterprise RAG JD 中强调的多租户权限检索。

## 技术栈

| 组件 | 选型 | 对标岗位需求 |
|------|------|------------|
| 向量数据库 | ChromaDB (in-memory) | 熟悉向量检索原理 |
| 索引框架 | LlamaIndex | 主流 RAG 框架 |
| Embedding | all-MiniLM-L6-v2 (384d) | 理解 embedding 选型 tradeoff |
| LLM | DeepSeek V4 Pro (OpenAI 兼容) | 多模型切换能力 |
| 评估体系 | RAGAS + NDCG/MRR 双维 | 评估体系设计能力 |
| 可观测 | Langfuse (优雅降级) | 生产级 tracing 意识 |

## 与项目A（03-rag-system）的对比

| 维度 | 项目A: Demo RAG | 本项目: Enterprise RAG |
|------|----------------|----------------------|
| 数据形态 | 6 篇同质化技术文档 | 12 篇异构数据（PDF/DB/API） |
| 权限模型 | 租户+角色 ACL（2 租户） | 租户+角色+访问级别（3 租户） |
| 评估体系 | RAGAS / NDCG-MRR 独立跑 | 双维交叉验证，统一报告 |
| 可观测 | Langfuse 骨架 | Langfuse 全链路 + 优雅降级 |
| 引用链路 | 打印 source_nodes | 来源标注 + 格式化引用列表 |
| 架构文档 | 无 | 完整 Mermaid 图 + 权限矩阵 |

## 项目结构

```
smart-report-agent/
├── README.md           # 本文档
├── ARCHITECTURE.md     # Mermaid 架构图 + 检索时序图 + 评估体系图
├── ingest.py           # 异构数据摄入管道（PDF/DB/API）
├── query_engine.py     # 权限感知查询引擎（ACL + 引用）
├── evaluate.py         # 双维评估（RAGAS + NDCG/MRR）
└── trace_pipeline.py   # Langfuse 追踪集成
```

## 如何运行

```bash
# 1. 激活虚拟环境
source .venv/bin/activate

# 2. 确保依赖
pip install llama-index chromadb python-dotenv ragas datasets langfuse \
            llama-index-embeddings-huggingface llama-index-vector-stores-chroma \
            llama-index-llms-openai-like langchain-huggingface

# 3. 配置 API Key（项目根目录 .env）
DEEPSEEK_API_KEY=sk-xxx

# 4. 依次运行
python projects/smart-report-agent/ingest.py          # 数据摄入
python projects/smart-report-agent/query_engine.py    # 权限查询演示
python projects/smart-report-agent/evaluate.py        # 双维评估报告
python projects/smart-report-agent/trace_pipeline.py  # Langfuse 追踪（可选）
```

## 面试要点

**一句话**："我们参考了 Zoom 的多租户 RAG 架构，权限在检索层做 ChromaDB metadata 预过滤，不在 LLM 生成后校验——既保安全又省 token。评估体系用 RAGAS 测生成质量 + NDCG/MRR 测排序质量，两个维度交叉验证。"

1. **权限在检索层** — where clause 在向量搜索前过滤，敏感文档不进入 prompt
2. **评估交叉验证** — 黑盒（RAGAS LLM 判断）+ 白盒（NDCG 数学公式）互补
3. **异构数据统一摄入** — PDF/DB/API 三种来源，metadata 携带租户+权限+来源完整信息
4. **可审计引用链路** — 每个结果标注 source_type + doc_id，回答末尾附引用列表
