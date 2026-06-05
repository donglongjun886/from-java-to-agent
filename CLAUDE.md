# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目定位

这是资深 Java 工程师（多年后端/分布式系统经验）用一个月时间系统转型 AI Agent 开发的学习项目。时间起点：2026-06-05，周期 4 周。

**核心目标**：利用 Java 工程师在系统设计、API 编排、状态管理上的天然优势，快速补齐 Python + LLM + Agent 框架能力，成为能打通「业务系统」与「智能算法」的桥梁型人才。

## 项目结构

```
from-java-to-agent/
├── CLAUDE.md              # 项目指南（本文件）
├── learning-plan.md       # 四周学习路径与里程碑
├── journal/               # 学习日志与复盘
│   ├── week-01/
│   ├── week-02/
│   ├── week-03/
│   └── week-04/
├── projects/              # 实战练习项目
│   ├── 01-hello-agent/    # LLM API 调用 + 第一个 Agent
│   ├── 02-tool-calling/   # Function Calling + MCP 协议
│   ├── 03-rag-system/     # RAG 知识库 + 向量检索
│   └── 04-multi-agent/    # 多 Agent 协同系统
├── notes/                 # 学习笔记（按主题）
└── resources/             # 资料索引
```

## 技术栈

- **语言**: Python 3.12（AI Agent 侧），Java 保留为后端服务优势
- **虚拟环境**: `.venv`（Python 3.12），激活: `source .venv/bin/activate`
- **包管理**: uv（安装后使用，当前未配置）
- **主力模型**: DeepSeek V4 Pro（`deepseek-chat`），API Key 配置在 `.env` 的 `DEEPSEEK_API_KEY`
- **API 协议**: OpenAI 兼容格式（使用 `openai` SDK），可低成本切换至 Claude/Gemini/通义千问等
- **核心框架（按学习优先级）**: LangGraph → OpenAI 兼容 API → MCP 协议 → CrewAI
- **IDE**: IntelliJ IDEA（Python 模块）

### 多模型策略

学习过程中用 DeepSeek V4 Pro 作为默认模型（高性价比），需要以下特性时切换到 Claude：
- MCP 协议原生集成
- 复杂 Tool Use 编排
- Computer Use（计算机操控）

切换方式：改 `base_url` + `api_key` + `model` 三个参数，其余代码不变。

## 角色约定

Claude Code 在本项目中承担**技术导师**角色：
- 结构化引导学习，不替用户写用户应该自己写的代码
- 用 Java 生态中的类比帮助理解 AI 概念（如「Agent 的 MCP 协议类似 SPI 机制」）
- 定期（每周）驱动复盘，检查学习进度
- 所有交流使用中文

## 关键认知锚点

以下是为 Java 工程师建立的认知映射，帮助快速建立对 AI Agent 领域的心智模型：

| Java 生态概念 | AI Agent 对应概念 |
|--------------|-------------------|
| Spring Boot 依赖注入 | Agent Tool 注册与绑定 |
| SPI 机制 / 插件化 | MCP 协议（Model Context Protocol） |
| 工作流引擎（Flowable） | LangGraph StateGraph 编排 |
| 消息队列（Kafka） | Agent 间异步通信（消息传递） |
| 事务管理 / Saga | Agent 检查点与断点续传（Checkpointing） |
| REST API / gRPC | Function Calling / Tool Use |
| 数据库连接池 | LLM 连接管理与速率限制 |
| AOP 切面 | Agent 中间件（日志、权限、审计） |
| 缓存（Redis/Caffeine） | 向量缓存 + 短期记忆窗口 |
| 服务注册中心（Nacos） | MCP Server 发现与注册 |

## 核心架构公式

```
Agent = LLM（大脑）+ Planning（规划）+ Memory（记忆）+ Tools（工具）+ Feedback Loop（反馈环）
```

## 开发环境

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装包（建议用 uv 替代 pip）
pip install uv  # 首次
uv pip install <package-name>

# 当前未配置：pyproject.toml、pytest、ruff/mypy
# 随项目推进逐步补充
```