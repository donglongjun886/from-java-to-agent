# AI Agent 开发转型学习计划（2026.06.05 - 2026.07.02）

> 仅工作日学习，周末休息。共 20 个学习日。
> 核心公式贯穿始终：**Agent = Model（大脑）+ Harness（框架）+ Feedback Loop（反馈环）**
> 评价驱动开发：从 Day1 开始就用评估指标衡量产出。

## 模型策略

- **默认模型**: DeepSeek V4 Pro (`deepseek-chat`)，使用 OpenAI 兼容 API
- **特定场景**: 涉及 MCP 协议、复杂 Tool Use 编排时切换到 Claude API
- **切换成本**: 仅需改变 `base_url` + `api_key` + `model`，代码结构不变

## 总览

| 周期 | 日期 | 主题 | 主线项目 |
|------|------|------|----------|
| **第1周** | 06/05 - 06/11 | Python 速通 + LLM 基础 + 评估入门 | **项目A 启动**：Agent 网关平台（Hello Agent → Tool Calling → MCP） |
| **第2周** | 06/12 - 06/18 | LangGraph 编排 + MCP / A2A + 代码沙箱 | **项目A 完成**：带 MCP Server + LangGraph 的多工具 Agent 网关 |
| **第3周** | 06/19 - 06/25 | RAG + 上下文工程 + Auth RBAC | **项目B 启动**：智能研报 Agent（RAG + 评估体系） |
| **第4周** | 06/26 - 07/02 | Multi-Agent + Harness 深度 + 综合复盘 | **项目B 完成**：多 Agent 协同研报系统（含沙箱 + 权限） |

---

## 第1周：Python 速通 + LLM 基础 + 评估入门（06/05 - 06/11）

### 学习目标
- 用 Java 类比快速掌握 Python 语法（够用即可，不追求精通）
- 理解 LLM 核心概念：Token、Temperature、Context Window
- 掌握 OpenAI 兼容 API（DeepSeek V4 Pro）
- **建立评估驱动开发的心智模型**：每个产出都要有衡量标准
- **启动项目A：Agent 网关平台**，完成基础命令行交互

### 每日计划

| 天 | 主题 | 内容 | 核心认知 |
|----|------|------|----------|
| **Day1 (06/05 五)** | 环境 + Python 速通 | Python 类型系统、控制流、异步 IO（asyncio）、包管理（uv/pip） | asyncio ≈ CompletableFuture；list comprehension ≈ Stream API |
| **Day2 (06/08 一)** | Python 进阶 + LLM 概念 | Pydantic 数据模型、LLM 基础（Token/Temperature/Context Window） | Pydantic ≈ Lombok @Data + @Validated + Jackson |
| **Day3 (06/09 二)** | LLM API + Agent 概念 | OpenAI Chat Completions API、流式响应（SSE）、System Prompt、Agent 架构定义 | Agent = Model + Harness + Feedback Loop |
| **Day4 (06/10 三)** | **项目A（上）+ 评估入门** | 实现多轮对话 Agent、流式输出、错误重试、Token 统计、**LLM-as-a-Judge 评估 Agent 输出质量** | Harness = 文件系统 + 工具 + 记忆 + 沙箱 + 上下文；评估驱动开发 |
| **Day5 (06/11 四)** | 项目A（下）+ 周复盘 | 完成 Hello Agent + 评估框架、Harness 概念笔记、输出第一份评估报告 | — |

### 本周产出
- [ ] `projects/agent-gateway/` — 命令行 Agent（流式 + 重试 + 成本统计 + **评估打分**）
- [ ] `notes/python-for-java-devs.md` — Java vs Python 对比笔记
- [ ] `notes/llm-fundamentals.md` — LLM 基础概念笔记
- [ ] `notes/harness-fundamentals.md` — Harness 工程基础笔记
- [ ] `journal/week-01/retrospective.md` — 第一周复盘
- [ ] 🌙 `projects/agent-gateway-java/` — Spring AI Alibaba 版 Hello Agent（对照实现）

### 关键资源
- [DeepSeek API 文档](https://platform.deepseek.com/api-docs/)
- [Pydantic Models 文档](https://docs.pydantic.dev/latest/concepts/models/)
- [Modern Agent Harness Blueprint 2026](https://gist.github.com/amazingvince/52158d00fb8b3ba1b8476bc62bb562e3)
- [Harness Engineering: The 2026 Guide](https://techiegigs.com/harness-engineering-complete-guide/)

---

## 第2周：LangGraph 编排 + MCP / A2A + 代码沙箱（06/12 - 06/18）

### 学习目标
- 掌握 **LangGraph** 图编排（StateGraph/Node/Edge/Checkpoint），作为所有 Agent 的编排基座
- 掌握 MCP 协议（Server/Client 架构），构建自定义 MCP Server
- 理解 A2A 协议（Agent 发现/能力卡片/任务委派）
- **新增：代码沙箱（E2B/Docker）**，让 Agent 能安全执行代码
- **完成项目A：Agent 网关平台**（多工具 + MCP + 沙箱 + 可观测）

### 每日计划

| 天 | 主题 | 内容 | 核心认知 |
|----|------|------|----------|
| **Day6 (06/12 五)** | **LangGraph 入门** + Tool Use | StateGraph/Node/Edge/条件路由/Checkpoint、Function Calling 完整流程 | LangGraph ≈ Flowable BPMN；用图编排替代手写 if-else |
| **Day7 (06/15 一)** | MCP 协议深度 + **代码沙箱** | MCP 架构/Transport/三原语、FastMCP SDK、**E2B/Docker 沙箱安全执行代码** | MCP ≈ USB-C；沙箱 = Agent 自主执行的安全边界 |
| **Day8 (06/16 二)** | A2A 协议 + 项目A（上） | A2A 1.0 概念（Agent 发现/任务委派）、项目A 框架搭建（LangGraph 编排 + 多工具集成） | MCP 连接工具，A2A 连接 Agent |
| **Day9 (06/17 三)** | 项目A：核心实现 | 多工具 Agent 网关完整实现：Tool + MCP Server + 沙箱 + 容错熔断 + 可观测 | 工具链编排 ≈ Chain of Responsibility；外部验证 > 自评 |
| **Day10 (06/18 四)** | 项目A：压测 + 复盘 | **压测报告（QPS/P99/成本）、架构图/时序图**、对比原生 vs MCP 优劣、周复盘 | 用传统高并发标准度量 Agent，体现 Java 工程优势 |

### 本周产出
- [ ] `projects/agent-gateway/` — **Agent 网关平台**（LangGraph 编排 + 多工具 + MCP Server + 沙箱 + 压测报告）
- [ ] `notes/prompt-engineering.md` — Prompt 工程笔记
- [ ] `notes/tool-calling-and-mcp.md` — Tool Calling + MCP + A2A 笔记
- [ ] `notes/code-sandbox.md` — **代码沙箱笔记（E2B/Docker 安全执行）**
- [ ] `journal/week-02/retrospective.md` — 第二周复盘
- [ ] 🌙 `projects/agent-gateway-java/` — LangChain4j 版 Agent 网关（对照实现）
- [ ] 🌙 `notes/面试题-Agent基础.md` — Agent 基础类面经题（15 道）

### 关键资源
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [A2A 协议官网](https://a2a-protocol.org/)
- [E2B 代码沙箱](https://e2b.dev/docs)

---

## 第3周：RAG + 上下文工程 + Auth RBAC（06/19 - 06/25）

### 学习目标
- 理解 Embedding 原理和向量检索机制
- 掌握 RAG 完整链路（混合检索 + Rerank + GraphRAG 概念）
- 上下文工程核心实践（渐进式披露/上下文重置/分片）
- 评估体系：RAGAS / Langfuse 深度实践
- **新增：Agent Auth RBAC**，Tool 级权限控制
- **启动项目B**：带评估和权限的 RAG 系统

### 每日计划

| 天 | 主题 | 内容 | 核心认知 |
|----|------|------|----------|
| **Day11 (06/19 五)** | Embedding + 向量数据库 | 文本向量化、相似度计算、ChromaDB 入门、文档切分策略（Chunking） | Embedding ≈ Lucene 倒排索引；向量DB ≈ ES kNN |
| **Day12 (06/22 一)** | RAG 架构 + 上下文工程 | 完整 RAG Pipeline、混合检索+Rerank、渐进式披露、上下文重置、GraphRAG 概念 | Context Window 是稀缺资源；状态在文件里不在窗口里 |
| **Day13 (06/23 二)** | **Auth RBAC + 评估体系** | Tool 级权限校验（Agent 执行时继承用户 RBAC）、RAGAS 评估、Langfuse 全链路追踪 | Auth RBAC ≈ Spring Security Filter Chain for Agents |
| **Day14 (06/24 三)** | 项目B（上） | RAG 研报 Agent 框架搭建：文档上传→向量索引→带权限的问答+引用溯源 | — |
| **Day15 (06/25 四)** | 项目B（下）+ 周复盘 | RAGAS 评估跑分、上下文工程策略落地、**压测+成本报告**、整理笔记 | — |

### 本周产出
- [ ] `projects/smart-report-agent/` — **RAG 研报 Agent**（混合检索+Rerank+RAGAS+Auth RBAC+压测报告）
- [ ] `notes/embeddings-and-vector-db.md` — Embedding 与向量数据库笔记
- [ ] `notes/rag-architecture.md` — RAG 架构笔记（含高级策略）
- [ ] `notes/context-engineering.md` — 上下文工程笔记
- [ ] `notes/agent-evaluation.md` — Agent 评估体系笔记（RAGAS/Langfuse/四维评估）
- [ ] `notes/agent-auth-rbac.md` — **Agent Auth RBAC 笔记（新增）**
- [ ] `journal/week-03/retrospective.md` — 第三周复盘
- [ ] 🌙 `projects/smart-report-agent-java/` — LangChain4j + PGVector 对照实现
- [ ] 🌙 `notes/面试题-RAG+上下文.md` — RAG + 上下文工程面经题（15 道）

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
- Harness 工程深度：六层架构 + Context Reset + 外部验证
- SDD（Spec-Driven Development）+ Agent 安全
- **完成项目B 多 Agent 扩展**：Planner→Generator→Evaluator 三 Agent 架构
- 全面复盘：技能矩阵 + 求职策略 + 面试模拟

### 每日计划

| 天 | 主题 | 内容 | 核心认知 |
|----|------|------|----------|
| **Day16 (06/26 五)** | 多 Agent 模式 + Harness 六层 | Manager-Worker、流水线、对等协作、Human-in-the-Loop、**Harness 六层架构深讲** | 多 Agent ≈ 微服务编排；Harness = 模型之外的一切 |
| **Day17 (06/29 一)** | 生产化 + SDD + 项目B 架构设计 | Agent 安全（注入防御/权限/沙箱）、SDD（Spec-Driven Development）、Token 成本优化、项目B 多 Agent 架构设计 | SDD = 先写 Spec 再生成代码 |
| **Day18 (06/30 二)** | 项目B：多 Agent 实现 | Planner→Generator→Evaluator 三 Agent 架构 + Context Reset 策略 + 完整 Harness 六要素 | 外部验证 > 自我评估；Evaluator 必须是独立 Agent |
| **Day19 (07/01 三)** | 项目B：压测 + 文档 | 高并发压测（QPS/P99/成本）、故障注入测试、架构图/时序图/状态机流转图、README | 面试官要看量化数据，不是 Demo |
| **Day20 (07/02 四)** | 全面复盘 | 四周学习总结、技能矩阵评估、求职策略、后续学习路线、完整模拟面试 | — |

### 本周产出
- [ ] `projects/smart-report-agent/` — **多 Agent 协同研报系统**（Planner→Generator→Evaluator + Harness + 压测 + 故障注入）
- [ ] `notes/multi-agent-patterns.md` — 多 Agent 模式笔记
- [ ] `notes/production-agent.md` — Agent 生产化要点
- [ ] `notes/harness-engineering-deep.md` — Harness 工程深度笔记
- [ ] `journal/week-04/retrospective.md` — 第四周复盘
- [ ] `journal/final-summary.md` — 月度总结 + 技能矩阵 + 后续计划
- [ ] 🌙 `notes/面试题-系统设计.md` — 系统设计类面经题（15 道）
- [ ] 🌙 2 个项目技术复盘文档（架构图 + 设计决策 + 踩坑）
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

**晚段（30-45min）**：Java 栈 AI 能力对比 + 面试准备
- 用 Java 对照实现白天 Python 项目的关键模块（不写完整项目，只写核心代码片段）
- 面经题刷题（从第2周开始，2-3 道/天）
- 项目技术复盘文档

### 晚段专项计划

| 周次 | 晚段重点 | 具体内容 | 每日耗时 |
|------|---------|---------|---------|
| **第1周** | Spring AI 对照实现 | Spring Boot + 通义千问 API 调用、Spring AI 的 ChatClient 核心用法 | 30min |
| **第2周** | LangChain4j Tool/MCP 对照 + 面经 | LangChain4j Tool 定义、MCP Client、面经 2 道/天 | 45min |
| **第3周** | LangChain4j RAG 对照 + 面经 | PGVector + Embedding + RAG 核心链路、面经 3 道/天 | 45min |
| **第4周** | 模拟面试 + 系统设计 | 每天 1 轮 30min 问答 + 自评、系统设计题专项 | 45min |

### Java → Python 速通策略
- 核心差异：动态类型、列表推导式、async/await
- 用 Claude Code 问「Java 的 XX 在 Python 里怎么写？」

### 项目标准（两大主线项目必须满足）
1. **架构图**（Mermaid/PlantUML）：核心链路时序图 + 状态机流转图
2. **压测报告**：QPS、P99 延迟、单次调用 Token 成本、并发瓶颈分析
3. **故障注入测试**：Tool 超时、LLM 幻觉、上下文截断 → 状态回滚 + 自动重试 + Fallback
4. **README**：业务场景 + 技术选型理由 + 踩坑记录 + 可运行

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
| LangGraph 文档 | https://langchain-ai.github.io/langgraph/ | ⭐⭐⭐ |
| A2A 协议官网 | https://a2a-protocol.org/ | ⭐⭐ |
| ChromaDB 文档 | https://docs.trychroma.com/ | ⭐⭐ |
| Langfuse 文档 | https://langfuse.com/ | ⭐⭐ |
| RAGAS 评估框架 | https://docs.ragas.io/ | ⭐⭐ |
| E2B 代码沙箱 | https://e2b.dev/docs | ⭐⭐ |

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
| 2026 Agent 全栈开发指南 (阿里云) | https://developer.aliyun.com/article/1707747 | 系统性中文培训指南 |
| 从后端到 Agent 工程师 (百度) | https://developer.baidu.com/article/detail.html?id=7006405 | 后端转 Agent |
| AI Agent开发框架选型指南 (百度) | https://developer.baidu.com/article/detail.html?id=7069150 | 2026 框架选型 |
