# Day 8 (2026.06.16) — A2A 概览 + 项目A 框架搭建 + 记忆层分类

## Part 1: A2A 协议概览 ✅

### 核心认知
- A2A 连接 Agent 与 Agent（MCP 连接 Agent 与工具）
- Agent Card = Agent 的名片（能力声明）
- Task = 跨 Agent 委派的工作单元
- 目前 v0.3→v1.0 演进中，生产案例少，半天认知即可

## Part 2: 记忆层四种类型 ✅

| 类型 | 存什么 | 用什么 | 类比 |
|------|--------|--------|------|
| 短期记忆 | 当前会话对话历史 | messages 数组 | HTTP Session |
| 长期语义记忆 | 跨会话的知识 | 向量数据库 | Elasticsearch |
| 情节摘要记忆 | 过往会话摘要 | KV 存储 | 操作日志归档 |
| 事实 KV 记忆 | 精确事实数据 | Redis/DB | Redis key-value |

## Part 3: 项目A 框架搭建 ✅

### 产出
- `projects/agent-gateway/` — Agent 网关平台脚手架
- `server.py` — FastAPI 统一入口
- `agent_graph.py` — LangGraph 编排（llm→tool→eval 三层图）

### 图结构
```
llm → [有tool_calls?] → tool → llm → [无?] → eval → END
```

### 1 个 commit
```
cb97f73 feat(agent-gateway): Day 8 Part2 — 项目A 框架搭建
```
