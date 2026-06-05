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

## 学习路径

| 周次 | 日期 | 主题 | 实战项目 |
|------|------|------|----------|
| 第1周 | 06/05 - 06/11 | Python 速通 + LLM 基础 | [Hello Agent](./projects/01-hello-agent/) — 命令行对话 Agent |
| 第2周 | 06/12 - 06/18 | Prompt 工程 + Tool Calling + MCP | 多工具聚合 Agent + 自定义 MCP Server |
| 第3周 | 06/19 - 06/25 | RAG + 向量数据库 + Agent 框架 | RAG 知识库问答系统 |
| 第4周 | 06/26 - 07/02 | 多 Agent 协同 + 工程化 | 多 Agent 协作系统 + 全面复盘 |

详细计划见 [learning-plan.md](./learning-plan.md)。

## 项目结构

```
from-java-to-agent/
├── learning-plan.md       # 四周学习路径与里程碑
├── journal/               # 学习日志与每周复盘
├── projects/              # 实战练习项目
│   ├── 01-hello-agent/    # LLM API 调用 + 第一个 Agent
│   ├── 02-tool-calling/   # Function Calling + MCP 协议
│   ├── 03-rag-system/     # RAG 知识库 + 向量检索
│   └── 04-multi-agent/    # 多 Agent 协同系统
├── notes/                 # 学习笔记（按主题）
└── resources/             # 资料索引
```

## 技术栈

- **语言**: Python 3.12
- **主力模型**: DeepSeek V4 Pro（`deepseek-chat`），OpenAI 兼容 API
- **核心框架**: LangGraph / OpenAI SDK / MCP 协议 / CrewAI
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

```
Agent = LLM（大脑）+ Planning（规划）+ Memory（记忆）+ Tools（工具）+ Feedback Loop（反馈环）
```

## License

MIT © 2026 donglongjun
