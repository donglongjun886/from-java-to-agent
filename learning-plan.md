# AI Agent 开发转型学习计划（2026.06.05 - 2026.07.02）

> 仅工作日学习，周末休息。共 20 个学习日。
> 核心公式贯穿始终：**Agent = Model（大脑）+ Harness（框架）+ Feedback Loop（反馈环）**

## 模型策略

- **默认模型**: DeepSeek V4 Pro (`deepseek-chat`)，使用 OpenAI 兼容 API
- **特定场景**: 涉及 MCP 协议、复杂 Tool Use 编排时切换到 Claude API
- **切换成本**: 仅需改变 `base_url` + `api_key` + `model`，代码结构不变

## 总览

| 周期 | 日期 | 主题 | 核心认知 |
|------|------|------|----------|
| **第1周** | 06/05 - 06/11 | Python 速通 + LLM 基础 + **Harness 概念** | 理解 Agent = Model + Harness |
| **第2周** | 06/12 - 06/18 | Tool Calling + MCP + **A2A + Agent Skills** | 掌握三大协议：MCP/A2A/Skills |
| **第3周** | 06/19 - 06/25 | RAG + **上下文工程** + 评估体系 | 上下文工程 > Prompt 工程 |
| **第4周** | 06/26 - 07/02 | Multi-Agent + **Harness 深度** + 综合复盘 | 从 Demo 到生产级的完整闭环 |

---

## 第1周：Python 速通 + LLM 基础 + Harness 概念（06/05 - 06/11）

### 学习目标
- 用 Java 类比快速掌握 Python 语法（够用即可，不追求精通）
- 理解 LLM 核心概念：Token、Temperature、Context Window
- 掌握 OpenAI 兼容 API（DeepSeek V4 Pro）
- **建立 Harness 工程的心智模型**：Agent = Model + Harness
- 完成第一个命令行可交互 Agent（带基础 Harness 要素）

### 每日计划

| 天 | 主题 | 内容 | 核心认知 |
|----|------|------|----------|
| **Day1 (06/05 五)** | 环境 + Python 速通 | Python 类型系统、控制流、异步 IO（asyncio）、包管理（uv/pip） | asyncio ≈ CompletableFuture；list comprehension ≈ Stream API |
| **Day2 (06/08 一)** | Python 进阶 + LLM 概念 | Pydantic 数据模型、LLM 基础（Token/Temperature/Context Window） | Pydantic ≈ Lombok @Data + @Validated + Jackson |
| **Day3 (06/09 二)** | LLM API + Agent 概念 | OpenAI Chat Completions API、流式响应（SSE）、System Prompt、Agent 架构定义 | Agent = Model + Harness + Feedback Loop |
| **Day4 (06/10 三)** | Hello Agent + Harness 要素 | 多轮对话、上下文管理、错误重试、Rate Limit、Token 统计、基础 Harness 五件套 | Harness = 文件系统 + 工具系统 + 记忆 + 沙箱 + 上下文管理 |
| **Day5 (06/11 四)** | 周复盘 | 整理笔记、写复盘日志、补 Harness 概念笔记 | — |

### 本周产出
- [ ] `projects/01-hello-agent/` — 命令行 Agent（流式输出 + 错误重试 + 成本统计）
- [ ] `notes/python-for-java-devs.md` — Java vs Python 对比笔记
- [ ] `notes/llm-fundamentals.md` — LLM 基础概念笔记（含 Token/Temperature/Context Window）
- [ ] `notes/harness-fundamentals.md` — **Harness 工程基础笔记（五件套 + Agent = Model + Harness）**
- [ ] `journal/week-01/retrospective.md` — 第一周复盘
- [ ] 🌙 `projects/01-hello-agent-java/` — Spring AI Alibaba 版 Hello Agent

### 关键资源
- [DeepSeek API 文档](https://platform.deepseek.com/api-docs/)
- [Pydantic Models 文档](https://docs.pydantic.dev/latest/concepts/models/)
- [Modern Agent Harness Blueprint 2026](https://gist.github.com/amazingvince/52158d00fb8b3ba1b8476bc62bb562e3)
- [Harness Engineering: The 2026 Guide](https://techiegigs.com/harness-engineering-complete-guide/)

---

## 第2周：Tool Calling + 三大协议（MCP / A2A / Skills）（06/12 - 06/18）

### 学习目标
- 掌握 Function Calling / Tool Use 的完整调用链路
- 掌握 MCP 协议（Server/Client/Transport 架构）
- **新增：理解 A2A 协议（Agent-to-Agent 通信）**
- **新增：理解 Agent Skills 开放标准（Anthropic）**
- 构建能调用多工具的 Agent（含异常处理/熔断/重试）

### 每日计划

| 天 | 主题 | 内容 | 核心认知 |
|----|------|------|----------|
| **Day6 (06/12 五)** | Prompt 工程 + Tool Use 原理 | System Prompt 设计、CoT/ReAct 模式、Function Calling 完整流程（Schema→调用→解析→回传） | Function Calling ≈ OpenAPI Contract；Tool Schema ≈ SPI 接口定义 |
| **Day7 (06/15 一)** | MCP 协议深度 | MCP 架构（Server/Client/Transport）、三原语（Resources/Tools/Prompts）、FastMCP SDK、自建 MCP Server | MCP ≈ USB-C，统一工具调用接口标准 |
| **Day8 (06/16 二)** | **A2A 协议 + Agent Skills** | A2A 1.0（Agent 发现/能力卡片/任务委派）、Anthropic Agent Skills 标准（渐进式披露/Token 优化） | MCP 连接工具，A2A 连接 Agent，Skills 管理能力边界 |
| **Day9 (06/17 三)** | 项目实战：多工具 Agent（上） | 实现多工具 Agent：天气 + 数据库 + 文件操作，完整 Tool 注册/调度/错误处理链路 | 工具链编排 ≈ Chain of Responsibility |
| **Day10 (06/18 四)** | 项目实战（下）+ 周复盘 | 对比 Tool Use 原生 vs MCP 方案优劣、完善项目、整理笔记 | — |

### 本周产出
- [ ] `projects/02-tool-calling/` — 多工具聚合 Agent（天气 + 数据库 + 文件操作 + 异常兜底）
- [ ] `projects/02-tool-calling/mcp-server/` — 自定义 MCP Server
- [ ] `notes/prompt-engineering.md` — Prompt 工程笔记（CoT/ReAct/Few-Shot/JSON Mode）
- [ ] `notes/tool-calling-and-mcp.md` — Tool Calling + MCP 协议笔记
- [ ] `notes/a2a-and-skills.md` — **A2A 协议 + Agent Skills 笔记（新增）**
- [ ] `journal/week-02/retrospective.md` — 第二周复盘
- [ ] 🌙 `projects/02-tool-calling-java/` — LangChain4j 版多工具 Agent（含 MCP Client）
- [ ] 🌙 `notes/面试题-Agent基础.md` — Agent 基础类面经题（15 道）

### 关键资源
- [Anthropic Tool Use 文档](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [A2A 协议官网](https://a2a-protocol.org/)
- [Agent Skills 开放标准](https://agentskills.io/)

---

## 第3周：RAG + 上下文工程 + 评估体系（06/19 - 06/25）

### 学习目标
- 理解 Embedding 原理和向量检索机制
- 掌握 RAG 完整链路（含高级策略：混合检索 + Rerank + GraphRAG 概念）
- **新增：上下文工程核心实践（渐进式披露/上下文重置/上下文分片）**
- **新增：Agent 评估体系（离线评估 + 在线可观测）**
- 入门 ChromaDB / PGVector、LangGraph 框架定位

### 每日计划

| 天 | 主题 | 内容 | 核心认知 |
|----|------|------|----------|
| **Day11 (06/19 五)** | Embedding + 向量数据库 | 文本向量化、相似度计算、ChromaDB 入门、文档切分策略（Chunking） | Embedding ≈ Lucene 倒排索引；向量DB ≈ ES kNN |
| **Day12 (06/22 一)** | RAG 架构 + 上下文工程 | 完整 RAG Pipeline、混合检索 + Rerank、**渐进式披露**、**上下文重置 vs 压缩**、GraphRAG 概念 | Context Window 是稀缺资源；"状态存在文件里，不在上下文窗口里" |
| **Day13 (06/23 二)** | **评估体系 + 可观测** | RAGAS/TruLens 评估框架、Langfuse/LangSmith 链路追踪、准确率/召回率/延迟/成本四维评估 | 评估体系 ≈ 单元测试 + 集成测试 + 性能监控 |
| **Day14 (06/24 三)** | LangGraph 入门 + 项目实战（上） | StateGraph/Node/Edge、条件路由、Checkpoint、RAG Agent 基本框架搭建 | StateGraph ≈ 工作流引擎（Flowable BPMN）；Checkpoint ≈ Saga |
| **Day15 (06/25 四)** | 项目实战（下）+ 周复盘 | 引用溯源、RAG 效果评估（RAGAS 跑分）、上下文工程策略落地、整理笔记 | — |

### 本周产出
- [ ] `projects/03-rag-system/` — RAG 知识库 Agent（文档上传→向量索引→问答+引用溯源+RAGAS评估）
- [ ] `notes/embeddings-and-vector-db.md` — Embedding 与向量数据库笔记
- [ ] `notes/rag-architecture.md` — RAG 架构笔记（含高级策略）
- [ ] `notes/context-engineering.md` — **上下文工程笔记（新增：渐进式披露/重置/分片）**
- [ ] `notes/agent-evaluation.md` — **Agent 评估体系笔记（新增：RAGAS/Langfuse/四维评估）**
- [ ] `notes/agent-frameworks.md` — LangChain/LangGraph/CrewAI 框架对比笔记
- [ ] `journal/week-03/retrospective.md` — 第三周复盘
- [ ] 🌙 `projects/03-rag-system-java/` — LangChain4j + PGVector 版 RAG 系统
- [ ] 🌙 `notes/面试题-RAG+上下文.md` — RAG + 上下文工程类面经题（15 道）

### 关键资源
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [ChromaDB 文档](https://docs.trychroma.com/)
- [RAGAS 评估框架](https://docs.ragas.io/)
- [Langfuse 可观测性](https://langfuse.com/)
- [Anthropic Context Engineering 指南](https://docs.anthropic.com/en/docs/build-with-claude/context-engineering)

---

## 第4周：Multi-Agent + Harness 深度 + 综合复盘（06/26 - 07/02）

### 学习目标
- 掌握多 Agent 协作模式（Manager-Worker、流水线、对等协作）
- **Harness 工程深度：六层架构 + Context Reset + 外部验证**
- Agent 生产化：安全（注入防御）、SDD（Spec-Driven Development）、成本优化
- 完成综合项目：多 Agent 协同系统（带完整 Harness）
- 全面复盘：技能矩阵 + 求职策略 + 面试模拟

### 每日计划

| 天 | 主题 | 内容 | 核心认知 |
|----|------|------|----------|
| **Day16 (06/26 五)** | 多 Agent 模式 + Harness 六层 | Manager-Worker、流水线、对等协作、Human-in-the-Loop、**Harness 六层架构深讲**（上下文编排/工具系统/执行编排/记忆与状态/护栏与验证/评估与可观测） | 多 Agent ≈ 微服务编排；Harness = 模型之外的一切工程要素 |
| **Day17 (06/29 一)** | 生产化 + SDD | Agent 安全（Prompt 注入防御/权限/沙箱）、**SDD（Spec-Driven Development）**、Token 成本优化、项目架构设计 | SDD = 先写 Spec 再生成代码，AI 编程的正确打开方式 |
| **Day18 (06/30 二)** | 综合项目实现（上） | 多 Agent 协同系统：Agent 注册中心 + 任务分发 + Planner→Generator→Evaluator 三 Agent 架构 | 外部验证 > 自我评估；评估 Agent 必须是独立角色 |
| **Day19 (07/01 三)** | 综合项目实现（下）+ 文档 | Context Reset 策略落地、人机协同节点、代码完善、README + 架构图 | "Reboot beats patching" — Context Reset > 压缩 |
| **Day20 (07/02 四)** | 全面复盘 | 四周学习总结、技能矩阵评估、求职方向建议、后续学习路线、完整模拟面试 | — |

### 本周产出
- [ ] `projects/04-multi-agent/` — 多 Agent 协同系统（Planner→Generator→Evaluator + Harness六要素）
- [ ] `notes/multi-agent-patterns.md` — 多 Agent 模式笔记
- [ ] `notes/production-agent.md` — Agent 生产化要点（安全/成本/沙箱）
- [ ] `notes/harness-engineering-deep.md` — **Harness 工程深度笔记（新增：六层架构/Context Reset/外部验证）**
- [ ] `journal/week-04/retrospective.md` — 第四周复盘
- [ ] `journal/final-summary.md` — 月度总结 + 技能矩阵 + 后续计划
- [ ] 🌙 `notes/面试题-系统设计.md` — 系统设计类面经题整理（15 道）
- [ ] 🌙 4 个项目技术复盘文档（架构图 + 设计决策 + 踩坑记录）
- [ ] 🌙 完整模拟面试 4 轮（自评 + 改进记录）

### 关键资源
- [LangGraph Multi-Agent 教程](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/)
- [CrewAI 文档](https://docs.crewai.com/)
- [Langfuse 可观测性](https://langfuse.com/)
- [Harness Engineering 面经汇总](https://notes.kamacoder.com/interview/llm/harness_interview.html)
- [Anthropic Managed Agents Architecture](https://dev.to/luhuidev/anthropic-managed-agents-2026-agent-harness-architecture-for-production-ai-agents-3899)

---

## 学习方法论

### 每日节奏

**白天段（4-5h）**：
1. **输入（1-2h）**：阅读文档/看课程/读代码
2. **编码（2-3h）**：动手写代码，小步快跑
3. **输出（30min）**：写笔记，记录今日收获与问题

**晚段（1-1.5h）**：Java 栈 AI 能力补齐 + 面试准备
1. Spring AI Alibaba / LangChain4j 实战（与 Python 项目并行推进）
2. 面经题刷题（从第2周开始，逐步增量）
3. 项目技术复盘（架构图 + 设计决策 + 踩坑记录）

---

### 晚段专项计划

| 周次 | 晚段重点 | 具体内容 | 每日耗时 |
|------|---------|---------|---------|
| **第1周** | Spring AI Alibaba 入门 | 跑通 Spring Boot + 通义千问 API 调用、理解 Spring AI 的 Function Calling 封装 | 1h |
| **第2周** | LangChain4j 入门 + 面经起步 | LangChain4j 的 Tool 定义/Agent 编排、补面经题 2 道/天（Agent 基础 + MCP 类） | 1h |
| **第3周** | Java 版 RAG 实战 + 面经增量 | 用 LangChain4j + PGVector 做一个 Java 版 RAG 问答、补面经题 3 道/天（RAG + 上下文工程类） | 1.5h |
| **第4周** | 综合模拟面试 + 项目复盘 | 每天 1 轮完整模拟面试（30min 问答 + 自评）、整理 4 个项目复盘文档、**Harness 系统设计题专项** | 1.5h |

### Java → Python 速通策略
- 不要在 Python 语法上花太多时间——前 3 天足够覆盖 80% 的使用场景
- 核心差异就三点：动态类型、列表推导式、async/await
- 遇到不确定的语法直接用 Claude Code 问，不要卡住

### 项目驱动原则
- 每个实战项目都是一个**独立的、可运行的、有 README 的** Python 项目
- 先跑通最小闭环（end-to-end），再加功能
- 每个项目都要有 `pyproject.toml` 和明确的依赖
- 代码风格逐步引入 ruff/mypy，不追求一开始就完美
- **每个项目完成后写技术复盘文档，记录架构决策和踩坑**

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
| DeepSeek API 文档 | https://platform.deepseek.com/api-docs/ | ⭐⭐⭐ |
| Anthropic Claude API 文档 | https://docs.anthropic.com/en/api | ⭐⭐⭐ |
| Anthropic Tool Use 指南 | https://docs.anthropic.com/en/docs/build-with-claude/tool-use | ⭐⭐⭐ |
| Anthropic Context Engineering | https://docs.anthropic.com/en/docs/build-with-claude/context-engineering | ⭐⭐⭐ |
| MCP 协议规范 | https://modelcontextprotocol.io/ | ⭐⭐⭐ |
| A2A 协议官网 | https://a2a-protocol.org/ | ⭐⭐ |
| Agent Skills 开放标准 | https://agentskills.io/ | ⭐⭐ |
| LangGraph 文档 | https://langchain-ai.github.io/langgraph/ | ⭐⭐ |
| ChromaDB 文档 | https://docs.trychroma.com/ | ⭐⭐ |
| Langfuse 文档 | https://langfuse.com/ | ⭐⭐ |
| RAGAS 评估框架 | https://docs.ragas.io/ | ⭐⭐ |

### 2026 前沿资料
| 资源 | 链接 | 说明 |
|------|------|------|
| Modern Agent Harness Blueprint | https://gist.github.com/amazingvince/52158d00fb8b3ba1b8476bc62bb562e3 | Harness 工程全景图 |
| Harness Engineering 面经 | https://notes.kamacoder.com/interview/llm/harness_interview.html | 大厂 Harness 面试题汇总 |
| Anthropic Managed Agents | https://dev.to/luhuidev/anthropic-managed-agents-2026-agent-harness-architecture-for-production-ai-agents-3899 | Anthropic 官方 Harness 架构 |

### 课程
| 课程 | 平台 | 时长 | 优先级 |
|------|------|------|--------|
| Agent Skills with Anthropic | DeepLearning.AI | 2.5h | ⭐⭐⭐ |
| Building RAG and MCP Servers with Claude | Coursera | 3 modules | ⭐⭐ |

### 中文资源
| 资源 | 链接 | 说明 |
|------|------|------|
| AI Agent 学习路线 (GitHub) | https://github.com/EldonZhao/ai-agent-startup | 7阶段系统路线 |
| 2026 Agent 全栈开发指南 (阿里云) | https://developer.aliyun.com/article/1707747 | 系统性的中文培训指南 |
| 从后端到 Agent 工程师 (百度) | https://developer.baidu.com/article/detail.html?id=7006405 | 针对后端转 Agent |
| AI Agent开发框架选型指南 (百度) | https://developer.baidu.com/article/detail.html?id=7069150 | 2026 框架选型 |
