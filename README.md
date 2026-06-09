# From Java to Agent

资深 Java 工程师用一个月时间系统转型 AI Agent 开发的学习项目。

## 为什么会有这个项目

作为一个写了多年 Java 的后端/分布式系统工程师，我发现 AI Agent 开发和自己熟悉的领域有大量共通之处：

- **Agent 工具注册** ≈ Spring Bean 依赖注入
- **MCP 协议插件化** ≈ SPI 机制
- **LangGraph 编排** ≈ 工作流引擎（Flowable/Camunda）
- **Agent 检查点机制** ≈ Saga 事务日志
- **多 Agent 协同** ≈ 微服务编排

既然底层思维模型相通，缺的只是 Python 语法和 AI 领域知识。这个项目记录了整个转型过程——从写出第一个 Hello Agent，到构建完整的多 Agent 协同系统。

## 当前进度

- ✅ **Day 1（06/05）**：Python 速通 + asyncio
- ✅ **Day 2（06/08）**：Pydantic 进阶 + LLM 三件套 + Spring AI 晚段调通 qwen3.7-plus
- ✅ **Day 3（06/09）**：Chat Completions API + SSE 流式 + System Prompt 设计 + Agent 架构公式
- 详细见 `journal/week-01/` 和 `notes/`

## 学习路径

v5 计划采用 **2 条主线项目** 跨越 4 周，基于真实面经做了 4 项微调（评测前置 + 记忆层显性化 + GraphRAG 升级 + 行业视野习惯）：

| 周次 | 日期 | 主题 | 主线项目 |
|------|------|------|----------|
| **第1周** | 06/05 - 06/11 | Python 速通 + LLM 基础 + 评估入门 | **项目A 启动**：Agent 网关平台（Hello Agent → Tool Calling → MCP） |
| **第2周** | 06/12 - 06/18 | LangGraph 编排 + MCP/A2A + 代码沙箱 | **项目A 完成**：带 MCP Server + LangGraph 的多工具 Agent 网关 |
| **第3周** | 06/19 - 06/25 | RAG + 上下文工程 + Auth RBAC | **项目B 启动**：智能研报 Agent（RAG + 评估体系） |
| **第4周** | 06/26 - 07/02 | Multi-Agent + Harness 深度 + 综合复盘 | **项目B 完成**：多 Agent 协同研报系统（沙箱 + 权限） |

详细计划见 [learning-plan.md](./learning-plan.md)。

## 项目结构

```
from-java-to-agent/
├── learning-plan.md       # 四周学习路径与里程碑
├── journal/               # 学习日志与每周复盘
├── notes/                 # 学习笔记（按主题）
├── resources/             # 资料索引
└── projects/
    ├── agent-gateway/             # 项目A：Agent 网关平台（Week 1-2）
    ├── smart-report-agent/        # 项目B：智能研报 Agent（Week 3-4）
    ├── agent-gateway-java/        # 晚段对照：Spring AI / LangChain4j
    └── smart-report-agent-java/   # 晚段对照：LangChain4j + PGVector
```

## 技术栈

- **语言**: Python 3.12（AI Agent 侧），Java 17（对照实现）
- **主力模型**: DeepSeek V4 Pro（`deepseek-chat`），OpenAI 兼容 API
- **核心框架**: LangGraph（编排基座）/ OpenAI SDK / MCP 协议 / A2A 协议 / CrewAI
- **评估与可观测**: RAGAS（评估）/ Langfuse（全链路追踪）
- **代码沙箱**: E2B / Docker
- **Java 对照栈**: LangChain4j / Spring AI
- **包管理**: uv

## 快速开始

```bash
# 1. 克隆仓库
git clone git@github.com:donglongjun886/from-java-to-agent.git
cd from-java-to-agent

# 2. 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install uv
uv pip install -r requirements.txt

# 4. 配置 API Key（在 .env 文件中）
# DEEPSEEK_API_KEY=sk-xxx

# 5. 运行第一个 Agent
python projects/01-hello-agent/main.py
```

## 核心公式

v4 用更工程的视角重新定义 Agent：

```
Agent = Model（大脑）+ Harness（框架）+ Feedback Loop（反馈环）
```

其中 `Harness = 文件系统 + 工具 + 记忆 + 沙箱 + 上下文`——模型之外的一切工程基建。

## License

MIT © 2026 donglongjun
