# 学习计划结束后的持续学习路线

> 四周系统学习完成（2026.06.05-07.03），以下是后续的持续学习方向。
> 核心原则：边实操边学习，项目驱动 > 文档阅读。

## 阶段一：知识体系化（1-2周）

### Agentic Design Patterns 系统阅读
- 重点章节：Planning(6) / Parallelization(3) / ReAct/CoT对比(17) / A2A(15) / 资源优化(16)
- 目标：将四周零散知识串成完整框架，面试时能讲出「从XX模式到XX模式的演进逻辑」

### 知识缺口补齐
- Plan-Execute vs ReAct 的对比话术（面试高频）
- Tool vs Skill 的区别定义
- Agent记忆系统生产级方案（衰减策略、记忆冲突解决）

## 阶段二：工程深化（3-4周）

### 新实战项目方向
选择一个对标目标业务场景的项目方向，以下三选一：

**方向A：Agent评测平台**
- 功能：评估数据集管理（版本控制、标注协作）、多指标评测跑分（RAGAS+NDCG+自定义指标）、实验对比报告（A/B Test）
- 技术栈：Python FastAPI + 前端天基础 + SQLite/PostgreSQL
- 面试价值：展现「评估体系设计能力」+「完整产品思维」

**方向B：Agent网关平台升级版**
- 功能：多模型路由（成本/延迟/质量智能路由）、多MCP Server治理（服务发现+健康检查+版本管理）、Prompt版本管理+A/B实验
- 技术栈：Java Spring AI/LangChain4j + Python MCP Server
- 面试价值：展现「生产级Agent基础设施设计能力」

**方向C：知识库+RAG全链路优化**
- 功能：多格式文档解析（PDF/Word/Excel/图片OCR）、智能Chunking（语义边界检测+二级检索）、HyDE+Query Rewriting+Re-ranker全链路
- 技术栈：Python LlamaIndex/LangChain + PostgreSQL pgvector
- 面试价值：展现「RAG管道深度优化能力」

### 开源贡献
- 目标：LangGraph / LlamaIndex / ChromaDB / LangChain4j 的 good first issue
- 方式：从doc fix或小bug入手，了解开源协作流程
- 频率：每周1-2个PR

## 阶段三：技术深度（长期持续）

### 源码级理解
- LangGraph StateGraph内部状态管理机制
- ChromaDB HNSW索引实现
- LangChain4j AiServices动态代理机制

### Agent安全纵深
- 多轮注入攻击防御
- 越狱攻击（jailbreak）检测
- 模型提取攻击防护

### 前沿跟进
- 每周GitHub trending Agent/LLM项目扫一遍README
- Arxiv每周Agent相关论文摘要速读
- 关注Anthropic/OpenAI/Google Agent产品更新

## 技术输出（持续）

- Java工程师视角的Agent开发技术博客（以教促学）
- Agent网关/评测平台提取为独立开源项目
- 学习过程中的踩坑经验总结和分享

## 学习节奏

不设固定时间表，以项目驱动：选定一个方向→设计架构→动手实现→Review→迭代。每完成一个milestone做一次复盘。
