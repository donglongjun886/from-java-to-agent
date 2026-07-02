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
├── README.md              # 本文档: 业务场景 + 技术栈 + 运行指南
├── ARCHITECTURE.md        # 架构文档: Mermaid图 + 权限矩阵 + 四Agent架构 + 压测报告
│
│   Week 3: 企业级RAG
├── ingest.py              # 异构数据摄入管道 (PDF/DB/API → ChromaDB)
├── query_engine.py        # 权限感知查询 (ACL Filter + LLM 生成 + 引用溯源)
├── evaluate.py            # 离线双维评估 (RAGAS + NDCG/MRR)
├── trace_pipeline.py      # Langfuse 全链路追踪
│
│   Week 4: Agentic Retrieval + Multi-Agent
├── four_agent_system.py   # 四Agent协同核心 (Planner/Retriever/Generator/Evaluator)
├── agentic_retrieval.py   # Agentic Retrieval 独立示例
├── multi_agent_collab.py  # 多Agent协作模式 (Manager-Worker/流水线)
│
│   Day 19: 压测 + 评估 + 故障注入
├── retrieval_compare.py   # 检索质量对比 (静态RAG vs Agentic, P@K/MRR/NDCG)
├── load_test.py           # 负载压测 (QPS/P99/成本/阶段耗时拆解)
└── fault_injection.py     # 故障注入 (超时/幻觉/截断/格式异常, 4项全PASS)
```

## 如何运行

```bash
# 1. 激活虚拟环境
source .venv/bin/activate

# 2. 配置 API Key（项目根目录 .env）
DEEPSEEK_API_KEY=sk-xxx

# 3. Week 3 — 企业级RAG 演示
python projects/smart-report-agent/ingest.py          # 数据摄入
python projects/smart-report-agent/query_engine.py    # 权限查询演示
python projects/smart-report-agent/evaluate.py        # 双维评估报告

# 4. Week 4 — Agentic Retrieval 演示
python projects/smart-report-agent/agentic_retrieval.py     # Agentic 动态检索
python projects/smart-report-agent/multi_agent_collab.py    # 多Agent协作

# 5. Day 19 — 压测 + 故障注入
python projects/smart-report-agent/retrieval_compare.py     # 检索质量对比
python projects/smart-report-agent/load_test.py             # 负载压测
python projects/smart-report-agent/fault_injection.py       # 故障注入 (4/4 PASS)
```

## 面试要点

**一句话**："我们构建了从静态RAG到Agentic Retrieval的完整演进：静态RAG做权限感知检索+双维评估，Agentic用四Agent协同（Planner→Retriever→Generator→Evaluator）实现动态路由。压测发现瓶颈在Generator(占65%耗时)，故障注入4项全通过。"

1. **检索演进路径** — 静态RAG → Agentic Retrieval，能讲清楚"什么时候该用哪个"
2. **权限在检索层** — where clause 在向量搜索前过滤，敏感文档不进入 prompt
3. **评估双维交叉** — RAGAS（黑盒 LLM 判断）+ NDCG/MRR（白盒数学公式）互补
4. **压测数据支撑** — QPS/延迟/成本有量化数字，面试时随口引用
5. **故障注入验证** — 4种故障场景全通过，体现生产级容错意识
