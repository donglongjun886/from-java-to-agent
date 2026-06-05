# AI Agent 开发转型学习计划（2026.06.05 - 2026.07.02）

## 模型策略

- **默认模型**: DeepSeek V4 Pro (`deepseek-chat`)，使用 OpenAI 兼容 API，性价比极高
- **特定场景**: 涉及 MCP 协议、复杂 Tool Use 编排时切换到 Claude API
- **切换成本**: 仅需改变 `base_url` + `api_key` + `model`，代码结构不变

## 总览

| 周期 | 日期 | 主题 | 核心产出 |
|------|------|------|----------|
| **第1周** | 06/05 - 06/11 | Python 速通 + LLM 基础 | Hello Agent：基于 DeepSeek 的命令行 Agent |
| **第2周** | 06/12 - 06/18 | Prompt 工程 + Tool Calling + MCP | 工具调用 Agent：多工具聚合 + MCP 协议理解 |
| **第3周** | 06/19 - 06/25 | RAG + 向量数据库 + Agent 框架 | RAG 知识库系统：文档问答 Agent |
| **第4周** | 06/26 - 07/02 | 多 Agent 协同 + 工程化 | 综合项目：多 Agent 协作系统 + 复盘总结 |

---

## 第1周：Python 速通 + LLM 基础（06/05 - 06/11）

### 学习目标
- 用 Java 类比快速掌握 Python 语法（不追求精通，够用即可）
- 理解 LLM 核心概念：Transformer 架构、Token、Temperature、Context Window
- 掌握 OpenAI 兼容 API（DeepSeek V4 Pro），理解与 Anthropic API 的差异
- 完成第一个命令行可交互 Agent

### 每日计划

| 天 | 主题 | 内容 | Java 类比锚点 |
|----|------|------|--------------|
| **Day1 (06/05)** | 环境 + Python 速通 | Python 类型系统、控制流、异步 IO（asyncio）、包管理（uv/pip） | asyncio ≈ CompletableFuture；list comprehension ≈ Stream API；dict ≈ HashMap |
| **Day2 (06/06)** | Python 进阶 + LLM 概念 | Pydantic 数据模型、FastAPI 基础、LLM 原理（Transformer/Attention）、Token 机制 | Pydantic ≈ Lombok @Data + Bean Validation；API 调用 ≈ HTTP Client |
| **Day3 (06/07)** | LLM API 实战 | OpenAI Chat Completions API（DeepSeek）、流式响应（SSE）、System Prompt、对比 Anthropic Messages API 差异 | System Prompt ≈ 装配好的 Bean Definition |
| **Day4 (06/08)** | Agent 概念入门 | Agent 的定义与架构（LLM + Planning + Memory + Tools + Feedback Loop）、ReAct 模式 | Agent 架构 ≈ MVC 模式（感知→决策→执行≈Controller→Service→Repository） |
| **Day5 (06/09)** | 项目实战1 | 实现「Hello Agent」：多轮对话、历史上下文管理、基于 DeepSeek API 的命令行 Agent | 上下文管理 ≈ Session 管理 |
| **Day6 (06/10)** | 项目完善 + 异常处理 | 错误重试、Rate Limit 处理、Token 计数与成本统计 | Rate Limit ≈ 熔断降级；Token 计数 ≈ 资源配额管理 |
| **Day7 (06/11)** | 周复盘 | 整理笔记、写复盘日志、输出项目 README | — |

### 本周产出
- ✅ `projects/01-hello-agent/` — 可多轮对话的命令行 Agent，支持流式输出、错误重试、成本统计
- ✅ `notes/python-for-java-devs.md` — Java vs Python 对比笔记
- ✅ `notes/llm-fundamentals.md` — LLM 基础概念笔记
- ✅ `journal/week-01/retrospective.md` — 第一周复盘

### 关键资源
- [DeepSeek API 文档](https://platform.deepseek.com/api-docs/)
- [OpenAI Python SDK 文档](https://github.com/openai/openai-python)
- [Python for Java Developers (Real Python)](https://realpython.com/java-vs-python/)

---

## 第2周：Prompt 工程 + Tool Calling + MCP 协议（06/12 - 06/18）

### 学习目标
- 掌握结构化 Prompt 工程（CoT、ReAct、Few-Shot、结构化 JSON 输出）
- 理解 Function Calling / Tool Use 机制
- 掌握 MCP 协议基础（Server/Client 架构）
- 构建能调用多种工具的 Agent

### 每日计划

| 天 | 主题 | 内容 | Java 类比锚点 |
|----|------|------|--------------|
| **Day8 (06/12)** | Prompt 工程基础 | System Prompt 设计模式、Chain-of-Thought、Few-Shot、角色扮演 Prompt | Prompt 模板 ≈ JSP/Thymeleaf 模板引擎 |
| **Day9 (06/13)** | 结构化输出 | JSON Mode、Function Calling 格式、Pydantic 解析与校验、Output Parsers | Function Calling Schema ≈ Swagger/OpenAPI Contract |
| **Day10 (06/14)** | Tool Use 机制 | Tool Definition（JSON Schema）、Tool 注册与调度、Tool Result 处理 | Tool 注册 ≈ Spring Bean 注册 + @Autowired；Tool 调度 ≈ 策略模式 |
| **Day11 (06/15)** | MCP 协议入门 | MCP 架构（Server/Client/Transport）、Resources/Tools/Prompts 三原语、FastMCP SDK | MCP ≈ SPI 机制 + 服务发现 |
| **Day12 (06/16)** | 项目实战2 | 实现多工具 Agent：天气查询 + 数据库查询 + 文件操作，包含 Tool 注册、调用链路、错误处理 | 工具链编排 ≈ Chain of Responsibility 模式 |
| **Day13 (06/17)** | MCP Server 实战 | 用 FastMCP 构建自定义 MCP Server、注册到 Claude Code/Desktop、实现双向调用 | MCP Server ≈ 微服务中的 Provider |
| **Day14 (06/18)** | 周复盘 | 整理笔记、写复盘日志、对比 Tool Use 原生 vs MCP 方案的优劣 | — |

### 本周产出
- ✅ `projects/02-tool-calling/` — 多工具聚合 Agent（天气 + 数据查询 + 文件操作）
- ✅ `projects/02-tool-calling/mcp-server/` — 自定义 MCP Server
- ✅ `notes/prompt-engineering.md` — Prompt 工程笔记
- ✅ `notes/tool-calling-and-mcp.md` — Tool Calling 与 MCP 协议笔记
- ✅ `journal/week-02/retrospective.md` — 第二周复盘

### 关键资源
- [Anthropic Tool Use 文档](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)

---

## 第3周：RAG + 向量数据库 + Agent 框架（06/19 - 06/25）

### 学习目标
- 理解 Embedding 原理和向量检索机制
- 掌握 RAG 基础架构（Indexing → Retrieval → Augmented Generation）
- 入门 ChromaDB / PGVector
- 了解 LangChain/LangGraph 框架定位（先理解原理再接触框架）

### 每日计划

| 天 | 主题 | 内容 | Java 类比锚点 |
|----|------|------|--------------|
| **Day15 (06/19)** | Embedding 原理 | 文本向量化、相似度计算（Cosine/欧氏距离）、Embedding 模型选型 | Embedding ≈ 特征提取 + 全文索引的 Lucene 倒排索引 |
| **Day16 (06/20)** | 向量数据库 | ChromaDB 入门、文档切分策略（Chunking）、检索流程、元数据过滤 | 向量数据库 ≈ Elasticsearch 的 kNN 搜索 |
| **Day17 (06/21)** | RAG 架构 | Indexing Pipeline、Retrieval（基础检索 + Rerank）、Generation（Prompt 模板 + 引用溯源）、Agentic RAG 概念 | RAG Pipeline ≈ ETL 流程；Rerank ≈ SQL ORDER BY + LIMIT 优化 |
| **Day18 (06/22)** | LangChain 速览 | Chain/LCEL、Prompt Templates、Document Loaders、内置 Tool 生态 | LangChain ≈ Spring 生态（提供各种 Starter 和集成） |
| **Day19 (06/23)** | LangGraph 入门 | StateGraph 概念、Node/Edge 定义、条件路由、Checkpoint 机制 | StateGraph ≈ 工作流引擎（Flowable/Camunda BPMN）；Checkpoint ≈ Saga 事务日志 |
| **Day20 (06/24)** | 项目实战3 | 实现 RAG 知识库 Agent：文档上传 → 向量索引 → 智能问答，支持引用溯源 | — |
| **Day21 (06/25)** | 周复盘 | 整理笔记、RAG 效果评估（准确率/召回率）、框架选型思考 | — |

### 本周产出
- ✅ `projects/03-rag-system/` — RAG 知识库问答系统（支持 PDF/TXT 文档上传、引用溯源）
- ✅ `notes/embeddings-and-vector-db.md` — Embedding 与向量数据库笔记
- ✅ `notes/rag-architecture.md` — RAG 架构笔记
- ✅ `notes/agent-frameworks.md` — LangChain/LangGraph/CrewAI 框架对比笔记
- ✅ `journal/week-03/retrospective.md` — 第三周复盘

### 关键资源
- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [ChromaDB 文档](https://docs.trychroma.com/)
- [Anthropic RAG 指南](https://docs.anthropic.com/en/docs/build-with-claude/embeddings)

---

## 第4周：多 Agent 协同 + 工程化落地 + 综合复盘（06/26 - 07/02）

### 学习目标
- 掌握多 Agent 协作模式（Manager-Worker、顺序流水线、对等协作）
- 理解 Agent 生产化要点（日志/监控/成本控制/安全）
- 完成综合项目：多 Agent 协同系统
- 全面复盘，输出转型成果总结与求职计划

### 每日计划

| 天 | 主题 | 内容 | Java 类比锚点 |
|----|------|------|--------------|
| **Day22 (06/26)** | 多 Agent 模式 | Manager-Worker、顺序流水线（A→B→C→D）、对等协作、Human-in-the-Loop | 多 Agent 协同 ≈ 微服务编排（Orchestration vs Choreography） |
| **Day23 (06/27)** | Agent 生产化（上） | 日志与链路追踪（LangSmith/Langfuse）、Token 成本统计与优化、速率限制与重试策略 | 可观测性 ≈ SkyWalking/Prometheus + Grafana |
| **Day24 (06/28)** | Agent 生产化（下） | Agent 安全（Prompt 注入防御、权限控制）、评估体系（准确率/延迟/成本）、CI/CD | 安全 ≈ Spring Security Filter Chain；评估 ≈ 单元测试 + 集成测试 |
| **Day25 (06/29)** | 综合项目设计 | 设计多 Agent 协同系统架构、定义 Agent 角色与通信协议、搭建项目骨架 | 系统设计 ≈ 微服务架构设计评审 |
| **Day26 (06/30)** | 综合项目实现 | 编码实现：Agent 注册中心 + 任务分发 + 结果聚合 + 人机协同节点 | — |
| **Day27 (07/01)** | 项目完善 + 文档 | 代码完善、README、架构图、运行演示 | — |
| **Day28 (07/02)** | 全面复盘 | 四周学习总结、技能矩阵评估、求职方向建议、后续学习路线 | — |

### 本周产出
- ✅ `projects/04-multi-agent/` — 多 Agent 协同系统（如：研究员→分析师→写手→审核员流水线）
- ✅ `notes/multi-agent-patterns.md` — 多 Agent 模式笔记
- ✅ `notes/production-agent.md` — Agent 生产化要点
- ✅ `journal/week-04/retrospective.md` — 第四周复盘
- ✅ `journal/final-summary.md` — 月度总结 + 技能矩阵 + 后续计划

### 关键资源
- [LangGraph Multi-Agent 教程](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/)
- [CrewAI 文档](https://docs.crewai.com/)
- [Langfuse 可观测性](https://langfuse.com/)

---

## 学习方法论

### 每日节奏
1. **输入（1-2h）**：阅读文档/看课程/读代码
2. **编码（2-3h）**：动手写代码，小步快跑
3. **输出（30min）**：写笔记，记录今日收获与问题

### Java → Python 速通策略
- 不要在 Python 语法上花太多时间——前 3 天足够覆盖 80% 的使用场景
- 核心差异就三点：动态类型、列表推导式、async/await
- 遇到不确定的语法直接用 Claude Code 问，不要卡住

### 项目驱动原则
- 每个实战项目都是一个**独立的、可运行的、有 README 的** Python 项目
- 先跑通最小闭环（end-to-end），再加功能
- 每个项目都要有 `pyproject.toml` 和明确的依赖
- 代码风格逐步引入 ruff/mypy，不追求一开始就完美

### 复盘框架
每周复盘回答三个问题：
1. 这周学到了什么？（知识增量）
2. 和 Java 生态比，AI Agent 开发的核心差异是什么？（认知升级）
3. 下周需要调整什么？（行动优化）

---

## 学习资料索引

### 官方文档（必读）
| 资源 | 链接 | 优先级 |
|------|------|--------|
| Anthropic Claude API 文档 | https://docs.anthropic.com/en/api | ⭐⭐⭐ |
| Anthropic Tool Use 指南 | https://docs.anthropic.com/en/docs/build-with-claude/tool-use | ⭐⭐⭐ |
| MCP 协议规范 | https://modelcontextprotocol.io/ | ⭐⭐⭐ |
| LangGraph 文档 | https://langchain-ai.github.io/langgraph/ | ⭐⭐ |
| ChromaDB 文档 | https://docs.trychroma.com/ | ⭐⭐ |

### 在线课程（推荐）
| 课程 | 平台 | 时长 | 优先级 |
|------|------|------|--------|
| Agent Skills with Anthropic | DeepLearning.AI | 2.5h | ⭐⭐⭐ |
| Building RAG and MCP Servers with Claude | Coursera | 3 modules | ⭐⭐ |
| Functions, Tools and Agents with LangChain | DeepLearning.AI | ~2h | ⭐⭐ |

### 中文资源
| 资源 | 链接 | 说明 |
|------|------|------|
| AI Agent 学习路线 (GitHub) | https://github.com/EldonZhao/ai-agent-startup | 7阶段系统路线 |
| 2026 Agent 全栈开发指南 (阿里云) | https://developer.aliyun.com/article/1707747 | 系统性的中文培训指南 |
| 从后端到 Agent 工程师 (百度) | https://developer.baidu.com/article/detail.html?id=7006405 | 针对后端转 Agent |
| 多 Agent 框架对比 (百度) | https://developer.baidu.com/article/detail.html?id=7434780 | LangGraph/CrewAI/AutoGen 深度对比 |