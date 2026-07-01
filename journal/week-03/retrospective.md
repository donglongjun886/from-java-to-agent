# Week 3 复盘（2026.06.22 - 2026.06.28）

## 计划 vs 实际

| 天数 | 计划 | 实际 | 偏差 |
|------|------|------|------|
| Day11 | IR基础 + Embedding + LlamaIndex + ChromaDB | ✅ embedding_explorer.py + first_rag.py | 如期 |
| Day12 | 全理论日 | ✅ RAG三级管道 + 知识图谱 + 上下文工程 | 如期 |
| Day13 | 权限检索 + RAGAS + NDCG/MRR + Langfuse | ✅ 4 Part全完成，4文件~1100行 | 深度超出计划 |
| Day14 | 项目B（上）框架搭建 | ✅ smart-report-agent 6文件904行 | 如期 |
| Day15 | 项目B（下）+ 周复盘 | ✅ 周复盘（今天） | 推后2天（周末补） |

> 周末补工2天，但工作是计划3倍。用时间换深度，值。

## 一、这周学到了什么？

### 知识增量

**IR基础体系**：倒排索引→TF-IDF→BM25→稠密检索→混合检索，不是并列方案而是递进关系。BM25的两大改进——TF饱和（边际递减）+ 文档长度归一化——是面试里区别于背概念的关键。

**Enterprise RAG ≠ Demo RAG**：核心差异在三点——异构数据摄入、权限隔离、可审计引用链路。权限必须在检索阶段通过metadata预过滤完成，不等LLM生成后校验（安全+成本+合规三重约束）。

**评估体系三件套**：
- RAGAS 四维（Faithfulness/Answer Relevancy/Context Recall/Context Precision）测生成质量
- NDCG/MRR 测检索排序质量，人工qrels白盒可解释
- Langfuse 在线追踪做漂移检测和告警

三者分工：离线定基线（RAGAS+NDCG），在线做监控（Langfuse）。这是大多数RAG候选人的知识盲区。

**Chunking实验方法**：3轮实验（chunk_size=128/256/不切分）得出反直觉结论——短文档不切分效果最好。Chunking不是银弹，实验数据驱动决策比凭感觉调参数有说服力。

**Agentic Retrieval认知**：Agent驱动的检索决策（什么时候用向量、什么时候用关键词、什么时候查数据库）vs 静态RAG Pipeline。静态管道够用时不引入Agent，Agent的价值在「不确定性和多步推理」。

### 工程方法

- pip国内镜像 + HuggingFace镜像网络配置
- ChromaDB where clause的$and/$contains/布尔字段限制和workaround
- LlamaIndex的OpenAILike替代OpenAI hack方案
- RAGAS embedding兼容性问题（openai SDK版本冲突）的解决路径
- LlamaIndex MetadataFilters对布尔值组合的限制及ChromaDB直接调用的trade-off

## 二、和Java生态比，核心认知升级

**1. RAG评估 ≠ 传统软件测试**

传统后端：单元测试→集成测试→压测，确定性输入输出。
RAG：评估体系是分层的——检索端用NDCG/MRR（有ground truth），生成端用RAGAS（LLM-as-a-Judge），在线端用Langfuse追踪。三层各测不同维度的不确定性，没有一站式工具。

**2. 权限模型前置化**

传统Java：Controller层@PreAuthorize → Service层业务逻辑，权限和业务分离。
Enterprise RAG：权限必须在检索阶段嵌入where clause——不是架构偏好，是被token成本和安全风险逼出来的。检索回来的文档已经进prompt了，LLM「看过」的内容不可能事后用正则过滤。

**3. 数据管线 > 模型调优**

传统直觉是「换个更好的模型」，但实验证明：短文档不切分 + top_k=3 的效果优于复杂chunking方案。工程优化（分片策略、混合检索、Reranker）的ROI通常高于模型升级——这也是Zoom JD里强调「RAG管道设计与优化」的原因。

**4. 评估驱动开发**

不是「写完代码跑一下看看效果」，而是「先定义评估指标和baseline，再改代码，用数据验证」。Day13的3轮chunking实验就是用评估数据驱动决策的典型案例——跑出Faithfulness 0.50才知道128切太碎，跑出0.67才知道原始方案最优。

## 三、下周调整

**继续加强的**：
- 评估驱动的开发方式——每个产出先定义衡量标准
- code review闭环——写→审→修→验，保持清零状态
- 笔记即时整理——边学边写，不拖到周末批量补

**需要调整的**：
- 笔记债务一次性还完6篇虽然痛快，但周中分散写效率更高
- MCP code review速度慢（4个文件12分钟），大项目应该拆批并行
- journal日志缺了Day11-15的每日记录，周复盘只有总结没有过程

**Week 4 重点**：
- Agentic Retrieval（Agent驱动的检索决策）— 区别于静态RAG Pipeline的核心能力
- 多Agent协作模式（Manager-Worker / 流水线 / 对等协作）
- Harness工程六层架构深度
- 项目B多Agent扩展：Retrieval Planner → Multi-Source Retriever → Generator → Evaluator
- 全面复盘 + 对标Zoom JD自评

---

## 产出统计

| 类别 | 数量 | 说明 |
|------|------|------|
| Python文件 | 10个 | Day11-13代码 + 项目B |
| 笔记 | 6篇 | ~1300行，写+审+修闭环 |
| 提交 | 12个 | Week 3累计 |
| Code Review | 3轮 | 共44项发现，全部清零 |
| 总代码量 | ~2400行 | 不含笔记 |
