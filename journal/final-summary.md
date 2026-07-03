# 四周学习总结（2026.06.05 - 2026.07.03）

## 学习轨迹

```
Week 1: Python速通 + LLM基础 + 第一个Agent
  Day1 → Python异步IO、类型系统
  Day2 → Pydantic数据模型、LLM三件套（Token/Temperature/Context）
  Day3 → Chat API、流式响应、System Prompt设计
  Day4 → LLM-as-a-Judge评估器、Feedback Loop、A/B对比
  Day5 → Tool Calling初体验、Week1整合收官

Week 2: LangGraph编排 + MCP协议 + Agent安全 + 服务化
  Day6 → LangGraph图编排（StateGraph/Node/Edge/Router）
  Day7 → MCP协议深度、FastAPI服务化、代码沙箱
  Day8 → A2A概览、记忆层四分类、项目A框架搭建
  Day9 → 安全护栏、MCP集成、SSE流式、容错熔断
  Day10 → 压测报告、架构图、周复盘

Week 3: Enterprise RAG + 信息检索基础 + 上下文工程
  Day11 → IR基础理论、Embedding实战、LlamaIndex首个RAG
  Day12 → 三级管道、知识图谱、上下文工程、混合查询
  Day13 → ACL权限感知检索、RAGAS评估、NDCG/MRR、Langfuse追踪
  Day14-15 → 项目B企业级RAG研报系统（异构数据+多租户+权限）

Week 4: Agentic Retrieval + Multi-Agent + 生产化
  Day16 → Agentic动态检索、多Agent协作模式、Harness六层
  Day17 → 检索质量对比（静态RAG vs Agentic、P@3/MRR/NDCG）
  Day18 → 四Agent联调、Context Reset收尾
  Day19 → 负载压测、故障注入4/4、全量Review+Fix+回归
  Day20 → 全面复盘、月度总结
```

## 知识体系

### 一、LLM与Agent基础
- Token/Temperature/Context Window 核心概念及成本估算
- OpenAI 兼容 API（Chat Completions、Streaming SSE、Function Calling）
- System Prompt 设计（角色+约束+输出格式三段式）
- Agent = Model + Harness + Feedback Loop 架构公式

### 二、Agent编排与框架
- **LangGraph**：StateGraph/Node/Edge/ConditionalEdge/Checkpointer，图编排替代手写if-else
- **MCP协议**：三原语（Tools/Resources/Prompts）、Transport层（stdio/HTTP+SSE）、自定义MCP Server
- **A2A协议**：Agent-to-Agent通信，Agent Card + Task概念
- **多Agent模式**：Manager-Worker（中心化）、流水线（串行）、对等协作（去中心化）
- **Agentic Retrieval**：Agent驱动的动态路由，区别于静态RAG Pipeline

### 三、信息检索与RAG
- **IR基础**：倒排索引→TF-IDF→BM25（TF饱和+文档长度归一化）→稠密检索→混合检索+RRF融合
- **Embedding**：向量化原理、相似度计算、模型选型（维度/性能/领域适配）
- **Chunking策略**：固定规则（字符/递归/句子）vs 语义感知，512-1024 token舒适区
- **Reranker**：Cross-Encoder架构，粗排→精排两阶段策略
- **GraphRAG**：知识图谱解决关系推理（多跳查询），与向量检索互补

### 四、企业级RAG架构
- **多租户隔离**：索引级隔离 vs 元数据过滤，Partition Key实现
- **权限感知检索**：Pre-retrieval filtering，where clause在检索阶段完成权限校验
- **异构数据源**：PDF/DB/API统一Document Schema → 向量化 → 索引存储
- **引用溯源**：强制LLM标注来源chunk_id，前端渲染原文引用链接
- **幻觉缓解**：引用溯源 + 事实核查 + 拒答策略（相关性阈值）

### 五、评估体系
- **RAGAS四维**：Faithfulness / Answer Relevancy / Context Recall / Context Precision，测生成质量
- **NDCG/MRR**：测检索排序质量，白盒数学公式可解释
- **Langfuse**：全链路追踪（Trace→Span→Score），在线漂移检测
- **双维交叉验证**：离线定基线（RAGAS+NDCG），在线做监控（Langfuse）
- **W&B Weave / Braintrust**：评估数据集管理 + 实验对比

### 六、生产化工程
- **安全三层防线**：输入校验（注入防御+Unicode NFKC）→ Tool调用预检 → 输出校验
- **容错熔断**：超时重试+指数退避+30s冷却，asyncio.wait_for
- **代码沙箱**：E2B/Docker/Wasm，五层防御，SandboxExecutor
- **Harness六层**：文件系统/工具系统/记忆系统/上下文管理/反馈环/可观测
- **压测方法**：QPS/P99/成本三维度量，阶段耗时拆解定位瓶颈
- **故障注入**：Tool超时、虚假数据、截断、格式异常四场景验证

## 核心认知升级

### 1. 从「确定性系统」到「概率性系统」
传统后端：输入→处理→输出，相同输入必然相同输出。
Agent系统：LLM输出有随机性（temperature）、检索质量有波动、评估指标有置信区间。工程化不是消除不确定性，而是在不确定性边界内稳定运行。

### 2. 评估驱动开发
不是「写完代码跑一下看看效果」，而是「先定义指标和baseline，再改代码，用数据验证」。Chunking实验证明工程优化的ROI通常高于模型升级——128→256→不切分，数据驱动的决策比凭感觉调参有说服力。

### 3. 权限前置化
权限在检索阶段通过metadata预过滤完成——不是架构偏好，是被token成本和安全风险逼出来的。LLM「看过」的内容不可能事后用正则过滤。

### 4. 检索评估与生成评估分离
RAGAS测生成端质量，NDCG/MRR测检索排序质量。最终回答错误可能是检索没召回相关文档（检索问题），也可能是检索对了但LLM理解偏了（生成问题）——混在一起无法定位根因。

### 5. 故障注入按组件粒度，不是系统粒度
四Agent系统中，Retriever不依赖LLM（本地数据查找），但Planner/Generator/Evaluator全是LLM依赖。故障注入要按组件拆分，否则分不出哪个环节挂了。

### 6. 从低往高用，够用就停
静态RAG够用的场景不引入Agentic。Agent Level越高越复杂、越贵、越难维护。简单查询走静态兜底，复杂多步推理才进Agentic Pipeline。

## 产出统计

| 类别 | 数量 |
|------|------|
| Python文件 | 30+ |
| Java文件 | 24 |
| 笔记（全领域） | 42篇 |
| 技术深度专题 | 25篇（Week2 10篇 + Week3 15篇） |
| 面试题 | 2篇（Agent基础 + RAG检索） |
| 架构文档 | 2篇（agent-gateway + smart-report-agent） |
| 日志 | Day 1-20 全部归档 |
| 项目 | 4个（hello-agent / agent-gateway / rag-system / smart-report-agent） |
| Code Review闭环 | 10+ 轮，200+ 项发现全部清零 |

## 后续学习方向

### 基础巩固
- Agentic Design Patterns 系统化阅读，将四周零散知识串成完整框架
- 源码级理解：LangGraph状态管理机制、ChromaDB HNSW索引实现

### 工程深化
- Agent评测平台/工具链类实战项目
- MCP协议企业级实践（多Server治理、服务发现、版本管理）
- Stream/SSE架构在生产Agent系统中的设计模式
- Prompt版本管理与A/B实验平台

### 前沿跟进
- 每周扫GitHub trending Agent/LLM项目
- Agent安全纵深防御（多轮注入、越狱攻击、模型提取）
- Agent记忆系统的生产级方案（长期记忆衰减、记忆冲突解决）
- 开源贡献：LangGraph / LlamaIndex / ChromaDB good first issue

### 技术输出
- 以教促学：Java工程师视角的Agent开发技术博客
- 开源项目：Agent网关平台提取为独立可复用项目
